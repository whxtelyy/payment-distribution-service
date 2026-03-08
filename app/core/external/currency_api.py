from httpx import AsyncClient, HTTPStatusError
from decimal import Decimal

from app.schemas.wallet import WalletCurrency

async def get_exchange_rate(base_currency: WalletCurrency, target_currency: WalletCurrency) -> Decimal:
    base, target = base_currency.value.upper(), target_currency.value.upper()
    if base == target:
        return Decimal(1)
    else:
        async with AsyncClient(timeout=5) as client:
                response = await client.get("https://www.cbr-xml-daily.ru/daily_json.js")
                try:
                    response.raise_for_status()
                except HTTPStatusError as error:
                    raise error
                data = response.json()
                if base == 'RUB':
                    base_value = Decimal(1)
                else:
                    try:   
                        base_value = Decimal(str(data['Valute'][base]['Value'])) / Decimal(str(data['Valute'][base]['Nominal']))
                    except KeyError as error:
                        raise error
                if target== "RUB":
                    target_value = Decimal(1)
                else:
                    try:
                        target_value = Decimal(str(data['Valute'][target]['Value'])) / Decimal(str(data['Valute'][target]['Nominal']))
                    except KeyError as error:
                        raise error
                final_course = base_value / target_value


    return final_course
