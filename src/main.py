import asyncio
from binance import AsyncClient
import logging

import tradesAndOrders as tao
# from assets import get_assets_snap
# from candles import get_candles
from utilitiesAndSecrets import api_secret, api_key, m_log, log_path


async def main():
    client = await AsyncClient.create(api_key=api_key, api_secret=api_secret)
    logging.info(m_log["start"])

    # Candles
    # await get_assets_snap(client)
    # await get_candles(client)

    # Operations
    ## python-binance
    await tao.get_ord_and_trad(client, 0)
    await tao.get_dividends(client)
    await tao.get_ord_and_trad(client, 1)
    await tao.get_dust(client)
    await tao.get_dep_with(client, 1)
    await tao.get_dep_with(client, 0)
    await tao.get_iso_margin(client)
    ## Custom
    await tao.get_fiat_orders()
    await tao.get_fiat_dep_withdraws(is_withdraw=1)
    await tao.get_fiat_dep_withdraws(is_withdraw=0)
    await tao.get_margin(client)

    await client.close_connection()
    logging.info(m_log["end"])

if __name__ == "__main__":
    logging.basicConfig(filename=log_path, filemode='a', format='%(asctime)s %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
