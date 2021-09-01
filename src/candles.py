from database import my_db, cursor
import time
import gc

from simply import month_timestamp_ns, utc_zero, zero_day_s


def initial_time(pair):
    sql = "SELECT MAX(openTime) FROM crypto.candles WHERE pair = %s"
    cursor.execute(sql, [pair, ])
    from_date = cursor.fetchall()[0][0]

    if from_date is None:
        from_date = zero_day_s

    return from_date


async def get_candles(client):
    # fetch 1 minute klines for the last day up until now
    sql = "SELECT DISTINCT(name) FROM crypto.assets"
    cursor.execute(sql)
    assets_db = cursor.fetchall()

    pairs_db = [asset[0] + "EUR" for asset in assets_db if asset != "EUR"] + \
               ["EUR" + asset[0] for asset in assets_db if asset != "EUR"] + \
               ["USDT" + asset[0] for asset in assets_db if asset != "EUR" or "USDT"] + \
               [asset[0] + "USDT" for asset in assets_db if asset != "EUR" or "USDT"]
    pairs_db = list(set(pairs_db))

    pairs = sorted([price['symbol'] for price in await client.get_all_tickers()])
    now_db = int(time.time() * 1000)
    for pair in pairs:
        if ("EUR" in pair or "USDT" in pair) and pair in pairs_db:
            print("GETTING historical klines in db for " + pair + " ...")
            from_date = initial_time(pair)

            for start_date in range((from_date + utc_zero + 60) * 1000, now_db, month_timestamp_ns):
                print("-- Loading klines  --")
                t = await client.get_historical_klines(pair, "1m", start_date, start_date + month_timestamp_ns - 1000)
                sql = "INSERT INTO crypto.candles VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                val = []
                for tick in t:
                    val.append((tick[0], tick[1], tick[2], tick[3], tick[4], tick[5], tick[6], pair,))

                cursor.executemany(sql, val)
                my_db.commit()
                gc.collect()

    print("\n##############################################\n")
