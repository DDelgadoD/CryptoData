from tqdm import tqdm

from customAPI import binance_fiat_deposits, binance_fiat_orders, binance_old_dividends
from utilitiesAndSecrets import zero_day_ns, now_ns, day_timestamp_ns, sep, my_db, cursor, get_dt, get_ts


def get_pairs():
    sql = "SELECT DISTINCT(name) FROM crypto.assets"
    cursor.execute(sql)
    result = cursor.fetchall()
    pairs = {}

    for coin in result:
        for coin2 in result:
            pairs[coin[0] + coin2[0]] = [coin[0], coin2[0]]

    return pairs


async def get_binance_pairs(client):
    prices = sorted([price['symbol'] for price in await client.get_all_tickers()])
    return prices


def get_max_id(where, pair):
    sql_max = "SELECT MAX(orderId) FROM crypto." + where + " WHERE symbol=\"" + pair + "\""
    cursor.execute(sql_max)
    max_id = cursor.fetchall()[0][0]
    return max_id + 1 if max_id else 0


async def get_ord_and_trad(client, is_order=1):
    message = "orders" if is_order else "trades"
    values = 18 if is_order else 13

    pairs = get_pairs()
    binance_pairs = await get_binance_pairs(client)
    sql = "INSERT INTO crypto." + message + " VALUES (" + (values-1)*"%s,"+" %s)"
    print("GETTING " + message.upper() + "...")
    for pair in pairs.keys():

        if pair in binance_pairs:
            ops = await client.get_all_orders(symbol=pair, orderId=get_max_id(message, pair)) if is_order else \
                await client.get_my_trades(symbol=pair, fromId=get_max_id(message, pair))

            for op in ops:
                if op:
                    print("GETTING " + message.upper() + " for " + pair)
                    cursor.execute(sql, list(op.values()))

    my_db.commit()
    print(sep)


async def get_dust(client):
    dust = await client.get_dust_log()
    print("\nGETTING DUST EXCHANGE...")
    sql_max = "SELECT max(operateTime) FROM crypto.dust"
    cursor.execute(sql_max)
    dust_db = cursor.fetchall()[0][0]
    if not dust_db:
        dust_db = 0

    for i in range(dust["total"]):
        if dust_db < dust['userAssetDribblets'][i]['operateTime']:
            j = 0
            try:
                while dust['userAssetDribblets'][i]['userAssetDribbletDetails'][j]:
                    details = dust['userAssetDribblets'][i]['userAssetDribbletDetails'][j]
                    sql = "INSERT INTO crypto.dust VALUES (%s, %s,%s, %s, %s, %s)"
                    cursor.execute(sql, list(details.values()))
                    j = j + 1
            except IndexError:
                None
    my_db.commit()
    print(sep)


async def get_dividends(client, values=6):
    # We know for a fact that there are older transactions that can be fetched from the
    # /lending/union/interestHistory endpoint.
    sql_max = "SELECT max(divTime) FROM crypto.dividends"
    cursor.execute(sql_max)
    div_db = cursor.fetchall()[0][0]

    if not div_db:
        div_db = zero_day_ns

    sql = "INSERT INTO crypto.dividends VALUES (" + (values-1)*"%s,"+" %s)"
    more = " "
    q = now_ns
    div = {'total': 500}

    while div['total'] == 500:
        print("\nGETTING" + more + "DIVIDENDS...")
        div = await client.get_asset_dividend_history(limit=500, startTime=div_db + 1, endTime=q)

        [cursor.execute(sql, list((div['rows'][i]).values())) for i in tqdm(range(0, div["total"]))]

        if div["total"] == 500:
            more = " MORE "
            q = div['rows'][499]['divTime'] - 1

    my_db.commit()
    # if div_db == zero_day_ns:
    sql_min = "SELECT min(divTime) FROM crypto.dividends where enInfo != 'BNB Vault' or asset= 'BNB'"
    cursor.execute(sql_min)
    div_db = get_ts(get_dt(cursor.fetchall()[0][0]), day=1)
    print(div_db)

    sql = "INSERT INTO crypto.dividends VALUES (" + (values - 1) * "%s," + " %s)"

    for lending_type in ['DAILY', 'ACTIVITY', 'CUSTOMIZED_FIXED']:
        a = list(range(100))

        while len(a) == 100:
            print("\nGETTING" + more + " OLD DIVIDENDS...")
            a = await binance_old_dividends(lending_type=lending_type, end_time=div_db-1)

            for op in tqdm(a):
                print(op)
                b = {'id': "000000", 'tranId': op['time'] * op["interest"], 'asset': op['asset'],
                     'amount': op['interest'], 'divTime': op['time'], 'enInfo': 'OLD ' + op['lendingType']}
                cursor.execute(sql, b)

            if len(a) == 100:
                more = " MORE "
                div_db = a[100]['time']

    print(sep)


async def get_fiat_dep_withdraws(is_withdraw=0, nvalues=9):
    orders = await binance_fiat_deposits(is_withdraw=is_withdraw)
    message1 = "fiatWithdraws" if is_withdraw else "fiatDeposits"
    print("\nGETTING FIAT " + (message1[4:]).upper() + "...")

    sql_max = "SELECT count(orderNo) FROM crypto." + message1
    cursor.execute(sql_max)
    wd_db = cursor.fetchall()

    if orders is None:
        print("NO FIAT " + (message1[4:]).upper())
    else:
        if wd_db is None:
            to_final = 0
        else:
            to_final = orders["total"] - wd_db[0][0]
        print("YOU HAVE GOT " + str(to_final) + " NEW " + (message1[4:]).upper())
        for i in tqdm(range(0, to_final)):
            sql = "INSERT INTO crypto." + message1 + " VALUES (" + (nvalues-1)*"%s, " + "%s)"
            cursor.execute(sql, list((orders["data"][i]).values()))

        my_db.commit()

    print(sep)


async def get_fiat_orders():
    orders = await binance_fiat_orders()
    print("\nGETTING FIAT ORDERS...")

    sql_max = "SELECT count(orderNo), typeOrder FROM crypto.fiatOrders GROUP BY typeOrder"
    cursor.execute(sql_max)
    ord_db = cursor.fetchall()

    if orders is None:
        print("NO FIAT ORDERS")
    else:
        for loop_i, typeOrder in enumerate(["sell", "buy"]):

            if not ord_db or len(ord_db) < loop_i + 1:
                from_w = 0
            else:
                from_w = ord_db[loop_i][0]

            to_final = orders[typeOrder]["total"] - from_w
            print("YOU HAVE GOT " + str(to_final) + " NEW " + typeOrder.upper())
            for i in range(from_w, to_final):
                val = (list((orders[typeOrder]["data"][i]).values()))
                sql = "INSERT INTO crypto.fiatOrders VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                val.append(typeOrder)
                cursor.execute(sql, val)

        my_db.commit()

    print(sep)


async def get_dep_with(client, is_deposit=1):
    message = "deposits" if is_deposit else "withdraws"
    values = 12
    tim = "insertTime" if is_deposit else "applyTime"

    sql_max = "SELECT max(" + tim + ") FROM crypto." + message
    cursor.execute(sql_max)
    from_date = cursor.fetchall()[0][0]

    if from_date and tim == "applyTime":
        from_date = int(from_date.timestamp())*1000 + 1
        
    if not from_date:
        from_date = zero_day_ns

    print("\nGETTING " + message.upper() + "...")
    for start_date in range(from_date + 1000, now_ns, 90 * day_timestamp_ns):
        final = (start_date + 90 * day_timestamp_ns)
        div = await client.get_deposit_history(startTime=start_date, endTime=final) if is_deposit else \
            await client.get_withdraw_history(startTime=start_date, endTime=final)
        for op in div:
            sql = "INSERT INTO crypto." + message + " VALUES (" + (values-1)*"%s, " + "%s)"
            if op:
                cursor.execute(sql, list(op.values()))
        my_db.commit()
    print(sep)
