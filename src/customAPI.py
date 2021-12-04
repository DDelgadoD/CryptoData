import hashlib
import hmac
import time
from urllib.parse import urljoin, urlencode

import requests

import utilitiesAndSecrets as us


class BinanceException(Exception):
    def __init__(self, status_code, data_a):

        self.status_code = status_code
        if data_a:
            self.code = data_a['code']
            self.msg = data_a['msg']
        else:
            self.code = None
            self.msg = None
        message = f"{status_code} [{self.code}] {self.msg}"

        super().__init__(message)


async def base_get(path, params):
    query_string = urlencode(params)
    params['signature'] = hmac.new(us.api_secret.encode('utf-8'), query_string.encode('utf-8'),
                                   hashlib.sha256).hexdigest()

    url = urljoin(us.BASE_URL, path)
    r = requests.get(url, headers=us.headers, params=params)
    if r.status_code == 200:
        data = r.json()
    else:
        raise BinanceException(status_code=r.status_code, data_a=r.json())

    return data


async def binance_fiat_deposits(is_withdraw=0, begin_time=us.zero_day_s * 1000):
    return await base_get(path=us.fiat_orders, params={'transactionType': is_withdraw, 'beginTime': begin_time,
                                                       'timestamp': int(time.time() * 1000), 'rows': 500,
                                                       "recvWindow": 60000})


async def binance_fiat_orders(begin_time=us.zero_day_s * 1000):
    data_j = {"sell": await base_get(path=us.fiat_payments,
                                     params={'transactionType': 0, 'beginTime': begin_time,
                                             'timestamp': int(time.time() * 1000), "recvWindow": 60000}),
              "buy": await base_get(path=us.fiat_payments,
                                    params={'transactionType': 1, 'beginTime': begin_time,
                                            'timestamp': int(time.time() * 1000), "recvWindow": 60000})}

    return data_j


async def binance_old_dividends(start_time=us.zero_day_ns, end_time=us.zero_day_ns + us.month_timestamp_ns,
                                lending_type='DAILY'):
    return await base_get(path=us.old_dividends, params={'lendingType': lending_type, 'transactionType': 0, 'size': 100,
                                                         'startTime': start_time, 'endTime': end_time,
                                                         'timestamp': int(time.time() * 1000)})


async def binance_swap():
    return await base_get(path=us.swap, params={'timestamp': int(time.time() * 1000)})

async def cross_pairs():
    return await base_get(path=us.cross_margin)

