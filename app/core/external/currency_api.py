import json
from decimal import Decimal

import redis.asyncio
from httpx import AsyncClient, HTTPStatusError

from app.core.config import settings
from app.schemas.wallet import WalletCurrency


async def fetch_rates_from_api() -> dict:
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
        return Decimal(1)
    if base == "RUB":
        base_value = Decimal(1)
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
