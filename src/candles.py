import gc
from time import time

from tqdm import tqdm

from utilitiesAndSecrets import month_timestamp_ns, zero_day_ns, sep, my_db, cursor


def initial_time(pair):
    sql = "SELECT MAX(openTime) FROM crypto.candles WHERE pair = %s"
    cursor.execute(sql, [pair, ])
    from_date = cursor.fetchall()[0][0]

    if from_date is None:
        from_date = zero_day_ns

    return from_date


def pairs_assets():
    sql = "SELECT DISTINCT(name) FROM crypto.assets"
    cursor.execute(sql)
    assets_db = cursor.fetchall()

    pairs_db = ["BETHETH"] + [asset[0] + "EUR" for asset in assets_db if asset != "EUR"] + \
               ["EUR" + asset[0] for asset in assets_db if asset != "EUR"] + \
               ["USDT" + asset[0] for asset in assets_db if asset != "EUR" or "USDT"] + \
               [asset[0] + "USDT" for asset in assets_db if asset != "EUR" or "USDT"]

    pairs_db = list(set(pairs_db))

    return pairs_db


async def parallelize_candles(pair, now_db, client):
    print("GETTING HISTORICAL KLINES FOR " + pair + " ...")
    from_date = initial_time(pair)
    for start_date in range(from_date + 60000, now_db, month_timestamp_ns):
        print("-- Loading klines for " + pair + "--")
        final = (start_date + month_timestamp_ns - 1000) if (start_date + month_timestamp_ns - 1000) < now_db \
            else now_db

        t = await client.get_historical_klines(pair, "1m", start_date, final)

        sql = "INSERT INTO crypto.candles VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

        for tick in tqdm(t):
            val = [tick[0], tick[1], tick[2], tick[3], tick[4], tick[5], tick[6], pair, None, None, None, None, None]
            cursor.execute(sql, val)

        my_db.commit()
        gc.collect()


async def get_candles(client):
    # fetch 1 minute klines for the last day up until now
    pairs_db = pairs_assets()
    pairs = sorted([price['symbol'] for price in await client.get_all_tickers()])
    now_db = int(time()) * 1000

    [await parallelize_candles(pair, now_db, client) for pair in pairs if ("EUR" in pair or "USDT" in pair or pair == "BETHETH") and pair in pairs_db]

    print(sep)
