import pandas as pd
from coinbase.wallet.client import Client
from utilitiesAndSecrets import secret_coinbase, key_coinbase, cursor, my_db
import datetime as dt
from tqdm import tqdm


def get_max_id(col, db, mod=""):
    sql_max = "SELECT MAX(" + col + ") FROM crypto." + db + mod
    cursor.execute(sql_max)
    max_id = cursor.fetchall()[0][0]
    return max_id + 1 if max_id else 0


def get_ts(dt_, sec=0, formt="%Y-%m-%d %H:%M:%S"):
    dt_ = (dt.datetime.strptime(dt_, formt) if type(dt_) is str else dt_) if dt_ is not None else \
        dt.datetime.strptime("2020-01-01T00:00:00Z", formt)
    ts = dt.datetime.timestamp(dt_) if sec == 1 else int(dt.datetime.timestamp(dt_) * 1000)
    return ts


def _get_paginated_items(api_method, limit=100):
    """Generic getter for paginated items"""
    all_items = []
    starting_after = None
    while True:
        items = api_method(limit=limit, starting_after=starting_after)
        if items.pagination.next_starting_after is not None:
            starting_after = items.pagination.next_starting_after
            all_items += items.data
        else:
            all_items += items.data
            break
    return all_items


def get_accounts(client_, limit=100):
    return _get_paginated_items(client_.get_accounts, limit)


def get_transactions(account_, limit=100):
    return _get_paginated_items(account_.get_transactions, limit)


def process_tx(transactions, trades_df, datets, sql):
    for tx in transactions:
        # Evitamos la actualización tras la última transacción de la cuenta
        if get_ts(tx.created_at, formt='%Y-%m-%dT%H:%M:%SZ') > datets:
            s_a, s_c, r_a, r_c, t_fa, t_fc = None, None, None, None, None, None
            if float(tx.amount.amount) < 0:
                s_a, s_c, n_t = str(-float(tx.amount.amount)), tx.amount.currency, str(-float(tx.native_amount.amount))
            else:
                r_a, r_c, n_t = tx.amount.amount, tx.amount.currency, tx.native_amount.amount
            if "network" in tx:
                if "transaction_fee" in tx.network:
                    t_fa, t_fc = tx.network.transaction_fee.amount, tx.network.transaction_fee.currency
            ls = [str(get_ts(tx.created_at, formt="%Y-%m-%dT%H:%M:%SZ")), None, s_a, s_c, r_a, r_c, t_fa, t_fc, n_t,
                  tx.native_amount.currency, tx.details.title, tx.details.subtitle]
            if "Ha usado" in ls[11]:
                trades_df = (trades_df.append(pd.Series(ls, index=trades_df.columns), ignore_index=True))
            else:
                cursor.execute(sql, ls)
    return trades_df


def process_trades(trades_df, sql):
    trades_df = trades_df.sort_values("dateTS")
    for i in range(trades_df.shape[0]):
        if i % 2 == 0:
            if trades_df.iloc[i]["sentAmount"] is None:
                a, b = i, i + 1
            else:
                a, b = i + 1, i
            d_ = max(trades_df.iloc[a]["dateTS"], trades_df.iloc[b]["dateTS"])
            s_a = trades_df.iloc[b]["sentAmount"]
            s_c = trades_df.iloc[b]["sentCurrency"]
            r_a = trades_df.iloc[a]["receivedAmount"]
            r_c = trades_df.iloc[a]["receivedCurrency"]
            f_a = float(trades_df.iloc[b]["netWorthAmount"]) - float(trades_df.iloc[a]["netWorthAmount"])
            f_c = trades_df.iloc[a]["netWorthCurrency"]
            n_a = trades_df.iloc[b]["netWorthAmount"]
            n_c = trades_df.iloc[b]["netWorthCurrency"]
            if trades_df.iloc[b]["Label"] == trades_df.iloc[a]["Label"]:
                la_ = trades_df.iloc[a]["Label"].capitalize()
            else:
                la_ = (((trades_df.iloc[b]["Label"] + " " + trades_df.iloc[a]["Label"])
                        .replace("Se ha convertido ", "")).replace("Conversión ", "")).capitalize()
            ds_ = trades_df.iloc[a]["Description"]
            ls = [d_, None, s_a, s_c, r_a, r_c, f_a, f_c, n_a, n_c, la_, ds_]
            cursor.execute(sql, ls)


##### main #####
def main():
    client = Client(key_coinbase, secret_coinbase)
    coin_df = pd.DataFrame(columns=["dateTS", "dateH", "sentAmount", "sentCurrency", "receivedAmount",
                                    "receivedCurrency", "feeAmount", "feeCurrency", "netWorthAmount",
                                    "netWorthCurrency", "Label", "Description"])
    sql = "INSERT INTO crypto.movementsCoinbase VALUES (" + 11*"%s,"+" %s)"
    datets = get_max_id("dateTS", "movementsCoinbase")
    accounts = get_accounts(client)

    for account in tqdm(accounts):
        txs = get_transactions(account)
        # Evitamos accounts no actualizadas
        if get_ts(account.updated_at, formt='%Y-%m-%dT%H:%M:%SZ') > datets and txs:
            coin_df = process_tx(txs, coin_df, datets, sql)

    if coin_df.shape[0] != 0:
        process_trades(coin_df, sql)

    my_db.commit()
