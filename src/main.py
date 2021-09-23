import asyncio
from binance import AsyncClient

from candles import get_candles
from utilitiesAndSecrets import api_secret, api_key
from assets import get_assets_snap
import tradesAndOrders as tao


async def main():
    client = await AsyncClient.create(api_key=api_key, api_secret=api_secret)
    await get_candles(client)
    await tao.get_dividends(client)
    await tao.get_fiat_dep_withdraws(1)
    await tao.get_fiat_dep_withdraws(0)

    """
    while True:
       selection = input("[1] get candles | [2] get operations | [3] get daily snapshots: ")

        if selection in ("1", "2", "3"):
            if selection == "1":
    """

    """
            elif selection == "2":
    
    await tao.get_trades(client)
    await tao.get_orders(client)
    await tao.get_dust(client)
    await tao.get_dividends(client)
    await tao.get_fiat_deposits(1)
    await tao.get_fiat_withdraws(0)
    await tao.get_fiat_orders()
   
            elif selection == "3":
   
    await get_assets_snap(client)
    await get_candles(client)
   
            break

        else:
            print("Selection not implemented")
    """
    await client.close_connection()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
