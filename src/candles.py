from database import my_db, cursor
import gc

from simply import month_timestamp_ns, utc_zero_ns, zero_day_ns, now_ns


def initial_time(pair):
    sql = "SELECT MAX(openTime) FROM crypto.candles WHERE pair = %s"
    cursor.execute(sql, [pair, ])
    from_date = cursor.fetchall()[0][0]

    if from_date is None:
        from_date = zero_day_ns

    return from_date


def create_row(pair):
    sql = "SELECT * FROM crypto.candles WHERE pair = %s limit 1"
    cursor.execute(sql, [pair, ])
    paired = cursor.fetchall()

    if paired is []:
        sql = "ALTER  TABLE crypto.mPrice ADD COLUMN " + pair + " DOUBLE"
        cursor.execute(sql)


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

    for pair in pairs:
        if ("EUR" in pair or "USDT" in pair) and pair in pairs_db:
            create_row(pair)
            print("GETTING historical klines in db for " + pair + " ...")
            from_date = initial_time(pair)
            for start_date in range(from_date + 60000, now_ns, month_timestamp_ns):
                print("-- Loading klines  --")
                t = await client.get_historical_klines(pair, "1m", start_date, start_date + month_timestamp_ns - 1000)

                sql = "INSERT INTO crypto.candles VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                val = []
                val2 = []
                for tick in t:
                    val.append((tick[0], tick[1], tick[2], tick[3], tick[4], tick[5], tick[6], pair, None, None, None,
                                None, None))
                    val2.append(((float(tick[1])+float(tick[4]))/2, tick[0], tick[6]))
                cursor.executemany(sql, val)
                sql2 = "UPDATE crypto.mPrice SET " + pair + "=%s WHERE openTime = %s  and closeTime = %s"
                cursor.executemany(sql2, val2)
                my_db.commit()
                gc.collect()

    print("\n##############################################\n")
