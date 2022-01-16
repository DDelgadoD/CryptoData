import asyncio
from binance import AsyncClient
import logging

import tradesAndOrders as tao
from assets import get_assets_snap
from candles import get_candles
from utilitiesAndSecrets import api_secret, api_key, m_log, log_path
import GettingCoinbase


async def main():
    client = await AsyncClient.create(api_key=api_key, api_secret=api_secret)
    # await tao.margin_loans(client)
    await tao.get_dep_with(client, 0)
    # TODO: get BSC, ETH, WAX, COSMOS.
    await client.close_connection()

if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
