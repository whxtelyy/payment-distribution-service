import json
from decimal import Decimal

import redis.asyncio
from httpx import AsyncClient, HTTPStatusError

from app.core.config import settings
from app.schemas.wallet import WalletCurrency


async def fetch_rates_from_api() -> dict:
    """
    Запрашивает актуальные курсы валют с зеркала API ЦБ РФ.

    Особенности:
    1) Используется внешний ресурс cbr-xml-daily.ru
    2) Установлен таймаут 5с для предотвращения блокировки event loop при сбоях сети.

    Raises:
        HTTPStatusError: Если ответ сервера отличен от 2xx.
    """
    async with AsyncClient(timeout=5) as client:
        response = await client.get("https://www.cbr-xml-daily.ru/daily_json.js")
        try:
            response.raise_for_status()
        except HTTPStatusError as error:
            raise error
        return response.json()


async def get_exchange_rate(
    base_currency: WalletCurrency, target_currency: WalletCurrency
) -> Decimal:
    """
    Вычисляет курс между двумя валютами с использованием кэширования.

    Логика:
    1) Сначала проверяется наличие данных в Redis.
    2) При отсутствии кэша вызывается внешний API, данные сохраняются в Redis на 1 час (TTL 3600).
    3) Расчёт учитывает 'Nominal' валюты (например, курс может быть указан за 100 единиц).

    Raises:
        KeyError: Если запрашиваемый код валюты отсутствует в данных ЦБ.
        ConnectionError: При проблемах со связью с Redis.
    """
    try:
        connect = await redis.asyncio.from_url(
            f"redis://localhost:{settings.REDIS_PORT}/{settings.REDIS_DB}",
            decode_responses=True,
        )
        cashed_data = await connect.get("cbr_rates")
        if cashed_data:
            data = json.loads(cashed_data)
        else:
            data = await fetch_rates_from_api()
            await connect.set("cbr_rates", json.dumps(data), ex=3600)
    finally:
        await connect.aclose()
    base, target = base_currency.value.upper(), target_currency.value.upper()
    if base == target:
        return Decimal(1.00)
    if base == "RUB":
        base_value = Decimal(1.00)
    else:
        try:
            base_value = Decimal(str(data["Valute"][base]["Value"])) / Decimal(
                str(data["Valute"][base]["Nominal"])
            )
        except KeyError as error:
            raise error
    if target == "RUB":
        target_value = Decimal(1)
    else:
        try:
            target_value = Decimal(str(data["Valute"][target]["Value"])) / Decimal(
                str(data["Valute"][target]["Nominal"])
            )
        except KeyError as error:
            raise error
    final_course = base_value / target_value

    return final_course
