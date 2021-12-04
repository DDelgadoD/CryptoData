from coinbase.wallet.client import Client
from utilitiesAndSecrets import secret_coinbase, key_coinbase
from datetime import datetime

client = Client(key_coinbase, secret_coinbase)


def get_ts(dt, sec=0, day=0, formt="%Y-%m-%d %H:%M:%S"):
    dt = datetime.strptime(dt, formt) if type(dt) is str else dt
    ts = datetime.timestamp(dt) if sec == 1 else int(datetime.timestamp(dt) * 1000)
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


def get_accounts(client, limit=100):
    return _get_paginated_items(client.get_accounts, limit)


def get_transactions(account, limit=100):
    return _get_paginated_items(account.get_transactions, limit)


# Use them.
accounts = get_accounts(client)
print("dateH, sentAmount, sentCurrency, netWorthAmount, netWorthCurrency, Label, Description")
for account in accounts:
    txs = get_transactions(account)
    if txs:
        for tx in txs:
            print(str(get_ts(tx.created_at, formt="%Y-%m-%dT%H:%M:%SZ")) + ", " + str(tx.amount.amount) + ", " + tx.amount.currency + ", " +
                  str(tx.native_amount.amount) + ", " + tx.native_amount.currency + ", " + str(tx.description) + ", " +
                  tx.details.subtitle)
