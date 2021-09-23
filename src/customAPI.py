import hashlib
# import json
import hmac
import time
from urllib.parse import urljoin, urlencode

import requests
import utilitiesAndSecrets


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


BASE_URL = 'https://api.binance.com'

headers = {
    'X-MBX-APIKEY': utilitiesAndSecrets.api_key
}


async def base_get(path, params):
    query_string = urlencode(params)
    params['signature'] = hmac.new(utilitiesAndSecrets.api_secret.encode('utf-8'), query_string.encode('utf-8'),
                                   hashlib.sha256).hexdigest()

    url = urljoin(BASE_URL, path)
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        data = r.json()
        # print(json.dumps(data, indent=2))
    else:
        raise BinanceException(status_code=r.status_code, data_a=r.json())

    return data


async def binance_fiat_deposits(is_withdraw=0, begin_time=utilitiesAndSecrets.zero_day_s * 1000,
                                timestamp=int(time.time() * 1000)):
    return await base_get(path='/sapi/v1/fiat/orders', params={'transactionType': is_withdraw, 'beginTime': begin_time,
                                                               'timestamp': timestamp, 'rows': 500,
                                                               "recvWindow": 60000})


async def binance_fiat_orders(begin_time=utilitiesAndSecrets.zero_day_s * 1000, timestamp=int(time.time() * 1000)):

    data_j = {"sell": await base_get(path='/sapi/v1/fiat/payments',
                                     params={'transactionType': 0, 'beginTime': begin_time,
                                             'timestamp': timestamp, "recvWindow": 60000}),
              "buy": await base_get(path='/sapi/v1/fiat/payments',
                                    params={'transactionType': 1, 'beginTime': begin_time,
                                            'timestamp': timestamp, "recvWindow": 60000})}

    return data_j
