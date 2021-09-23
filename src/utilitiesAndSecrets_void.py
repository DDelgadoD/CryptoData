from time import altzone, time
import mysql.connector

# Secrets
# API Key from Binance
api_key = ""
api_secret = ""

# Production SQL Server
host = ""
user = ""
password = ""

# Local/Test SQL Server
local_host = ''
local_user = ''
local_password = ""

# Utilities
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
sep = "\n##############################################\n"

# Database connection


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
