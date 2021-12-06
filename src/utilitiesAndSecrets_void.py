from time import altzone, time
import mysql.connector
from datetime import datetime

# Secrets
api_key = ""
api_secret = ""

key_coinbase = ""
secret_coinbase = ""

# LOG
log_path = ""
m_log = {"start": 'Started Crypto Database process',
         "end": 'Ended Crypto Database process',
         "pauseM": '#### Pause Needed on Margin Orders',
         "pauseO" : '#### Pause Needed on Orders'}

# Custom api frontends
BASE_URL = 'https://api.binance.com'
fiat_orders = '/sapi/v1/fiat/orders'
fiat_payments = '/sapi/v1/fiat/payments'
old_dividends = '/sapi/v1/lending/union/interestHistory'
swap = '/sapi/v1/bswap/swap'
cross_margin = '/sapi/v1/margin/allPairs'
headers = {'X-MBX-APIKEY': api_key}

# date and time
zero_day_s = 1619301600
zero_day_ns = zero_day_s * 1000
day_timestamp_s = 86400
day_timestamp_ns = 86400000
week_timestamp_s = day_timestamp_s * 7
week_timestamp_ns = day_timestamp_ns * 7
month_timestamp_s = day_timestamp_s * 30
month_timestamp_ns = day_timestamp_ns * 30
utc_zero = -altzone
utc_zero_ns = utc_zero * 1000
now = int(time())
now_ns = now * 1000


def get_dt(ts, sec=0, day=0):
    srt = "%d/%m/%Y " if day == 1 else "%d/%m/%Y %H:%M:%S"
    ts = ts if sec == 1 else int(ts / 1000)
    dt = datetime.strptime((datetime.fromtimestamp(ts)).strftime(srt), srt)
    return dt


def get_ts(dt, sec=0, day=0, formt="%Y-%m-%d %H:%M:%S"):
    dt = datetime.strptime(dt, formt) if type(dt) is str else dt
    ts = datetime.timestamp(dt) if sec == 1 else int(datetime.timestamp(dt) * 1000)
    return ts

sep = "\n##############################################\n"

# Database connection

host = ""
user = ""
password = ""

local_host = ''
local_user = ''
local_password = ""


def connect():
    return mysql.connector.connect(
          host=host,
          user=user,
          password=password
   )


# Connect to Local Database
my_db = connect()

# Creating a cursor to make the sql callings
cursor = my_db.cursor()
