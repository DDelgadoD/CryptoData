import asyncio
from binance import AsyncClient

from candles import get_candles
from utilitiesAndSecrets import api_secret, api_key
from assets import get_assets_snap
import tradesAndOrders as tao


async def main():
    client = await AsyncClient.create(api_key=api_key, api_secret=api_secret)

    await get_assets_snap(client)
    await get_candles(client)
    await tao.get_dividends(client)
    await tao.get_dust(client)
    await tao.get_ord_and_trad(client, 0)
    await tao.get_ord_and_trad(client, 1)
    await tao.get_fiat_orders()
    await tao.get_fiat_dep_withdraws(is_withdraw=1)
    await tao.get_fiat_dep_withdraws(is_withdraw=0)
    await client.close_connection()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
