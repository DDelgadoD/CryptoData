import time
from datetime import datetime
# import pandas as pd

from database import my_db, cursor
from simply import month_timestamp_ns, zero_day_s, day_timestamp_s


def assets_snap_db(line):
    sql = "INSERT INTO crypto.assets VALUES (%s, %s, %s)"
    date = line[0]

    for key, value in line[1].items():
        val = (date, key, str(value))
        cursor.execute(sql, val)

    my_db.commit()


# Get the assets from Binance
async def get_assets_snap(client, op_type='SPOT', file=""):
    # Creating a dictionary for the values
    snapshot = {}

    sql = "SELECT MAX(date) FROM crypto.assets"
    cursor.execute(sql)
    start_time = int(datetime.timestamp(cursor.fetchall()[0][0])) + day_timestamp_s

    if start_time is None:
        start_time = zero_day_s

    # Call the function get_account_snapshot with the start time in start_time, the end time is current time in
    # milliseconds and month_timestamp is a 30 days period in milliseconds because the function get_account_snapshot
    # returns a maximum of 30 days from the startTime
    print("GETTING SNAPSHOTS OF DAILY ASSETS BALANCES ...")
    for i in range(start_time * 1000, int(time.time() * 1000), month_timestamp_ns):
        print("--- LOADING ASSETS ---")
        ts = await client.get_account_snapshot(type=op_type, startTime=i, limit=30)

        for chunk in ts['snapshotVos']:
            assets = {}

            if op_type == 'SPOT':

                for data in chunk['data']['balances']:
                    assets[data['asset']] = float(data['free']) + float(data['locked'])

            elif op_type == 'MARGIN':

                for data in chunk['data']['userAssets']:
                    assets[data['asset']] = float(data['free']) + float(data['borrowed']) + float(data['interest']) \
                                            + float(data['locked'])

            ld_assets = []

            for ld_asset in assets:
                if ld_asset.startswith("LD"):
                    assets[ld_asset[2:]] = assets[ld_asset[2:]] + assets[ld_asset]
                    ld_assets.append(ld_asset)

            for ld_asset in ld_assets:
                assets.pop(ld_asset)

            date = datetime.utcfromtimestamp(chunk['updateTime'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            snapshot[date] = assets
            assets_snap_db([date, snapshot[date]])

    if file != "":
        print("In order to use this feature you need to install and import pandas, uncomment line 3 and uncomment",
              "the code below assets.py line 61")
        # df = pd.DataFrame.from_dict(snapshot, orient='index')
        # df.to_csv(file)

    print("\n##############################################\n")
