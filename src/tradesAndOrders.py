from tqdm import tqdm

from customAPI import binance_fiat_deposits, binance_fiat_orders
from utilitiesAndSecrets import zero_day_ns, now_ns, sep, my_db, cursor


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


async def get_trades(client):
    pairs = get_pairs()
    binance_pairs = await get_binance_pairs(client)

    sql = "INSERT INTO crypto.trades VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    print("GETTING TRADES...")
    for pair in pairs.keys():

        if pair in binance_pairs:

            trades = await client.get_my_trades(symbol=pair, fromId=get_max_id("trades", pair))

            for trade in tqdm(trades):
                if trade:
                    print("GETTING TRADES for " + pair)
                    cursor.execute(sql, list(trade.values()))

    my_db.commit()
    print(sep)


async def get_orders(client):
    pairs = get_pairs()
    binance_pairs = await get_binance_pairs(client)
    sql_or = "INSERT INTO crypto.orders VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    print("GETTING ORDERS...")
    for pair in pairs.keys():

        if pair in binance_pairs:

            orders = await client.get_all_orders(symbol=pair, orderId=get_max_id("orders", pair))

            for order in orders:
                if order:
                    print("GETTING ORDERS for " + pair)
                    val_or = (order['symbol'], order['orderId'], order['orderListId'], order['clientOrderId'],
                              order['price'], order['origQty'], order['executedQty'], order['cummulativeQuoteQty'],
                              order['status'], order['timeInForce'], order['type'], order['side'], order['stopPrice'],
                              order['icebergQty'], order['time'], order['updateTime'], order['isWorking'],
                              order['origQuoteOrderQty'])

                    cursor.execute(sql_or, val_or)

    my_db.commit()
    print(sep)


async def get_dust(client):
    dust = await client.get_dust_log()
    print("\nGETTING DUST EXCHANGE...")
    sql_max = "SELECT count(transId) FROM crypto.dust"
    cursor.execute(sql_max)
    dust_db = cursor.fetchall()[0][0]
    if not dust_db:
        dust_db = 0

    for i in range(dust_db, dust["total"]):
        details = dust['userAssetDribblets'][i]['userAssetDribbletDetails'][0]
        sql = "INSERT INTO crypto.dust VALUES (%s, %s,%s, %s, %s, %s)"
        cursor.execute(sql, list(details.values()))

    my_db.commit()
    print(sep)


async def get_dividends(client, values=6):
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
