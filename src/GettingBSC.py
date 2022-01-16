from bscscan import BscScan
from utilitiesAndSecrets import BSC_KEY, BSC_ADDRESSES, cursor, my_db
import asyncio
from time import sleep
# import logging

bnb_val = {}

shit_coins = {'BestAir.io': '0xbc6675de91e3da8eac51293ecb87c359019621cf',
              'Minereum BSC': '0xd22202d23fe7de9e3dbe11a2a88f42f4cb9507cf',
              'AlpacaDrop.Org': '0xb926beb62d7a680406e06327c87307c1ffc4ab09',
              'TheVera.io': '0x0df62d2cd80591798721ddc93001afe868c367ff',
              'ARKR.org': '0x04645027122c9f152011f128c7085449b27cb6d7',
              'Zepe.io': '0xb0557906c617f0048a700758606f64b33d0c41a6',
              'ALPACAFIN.COM': '0x026222b0954457b5b12fa5fd8471238cf4e6749c',
              'TheEver.io': '0x5190b01965b6e3d786706fd4a999978626c19880',
              'BSCTOKEN.IO': '0x569b2cf0b745ef7fad04e8ae226251814b3395f9',
              'FF18.io': '0x491b25000d386cd31307580171a510d32d7e64ee',
              'Def8.io': '0x556798dd55db12562a6950ea8339a273539b0495',
              'AirStack.net': '0x8ee3e98dcced9f5d3df5287272f0b2d301d97c57',
              'BNBw.io': '0xc33fc11b55465045b3f1684bde4c0aa5c5f40124',
              'GemSwap.net': '0x0d05a204e27e4815f1f5afdb9d82aa221aa0bdfa',
              'LinkP.io': '0xd5e3bf9045cfb1e6ded4b35d1b9c34be16d6eec3',
              'KK8.io': '0x2ba6204c23fbd5698ed90abc911de263e5f41266'
              }


def get_max_id(col, db, mod=""):
    sql_max = "SELECT MAX(" + col + ") FROM crypto." + db + mod
    cursor.execute(sql_max)
    max_id = cursor.fetchall()[0][0]
    return max_id + 1 if max_id else 0


async def get_tx(call, address, start_block):
    txs = {}
    try:
        tx = await call(address=address, startblock=start_block, endblock=99999999, sort="asc")
        dec_fee = 9
        sql = "INSERT INTO crypto.transactionsBSC VALUES (" + 11 * "%s, " + "%s)"
        for i, t in enumerate(tx):
            dec = int(t["tokenDecimal"]) if "tokenDecimal" in t else 18
            token_name = t["tokenName"] if "tokenName" in t else "Smart Chain"
            token_symbol = t["tokenSymbol"] if "tokenSymbol" in t else "BNB"

            txs[i] = {"dateTs": int(t["timeStamp"])*1000,
                      "wallet": list(BSC_ADDRESSES.keys())[list(BSC_ADDRESSES.values()).index(address)],
                      "from": t["from"], "to": t["to"], "value": int(t["value"]) / 10 ** dec, "symbol": token_symbol,
                      "tokenName": token_name, "tokenContract": t["contractAddress"], "Fee": int(t["gas"]) / 10 ** dec_fee,
                      "feePrice": int(t["gasPrice"]) / 10 ** dec_fee, "tokenDecimal": dec, "block": t["blockNumber"]}

            cursor.execute(sql, list(txs[i].values()))

        my_db.commit()
    except AssertionError:
        print("No Transactions")
    return txs


async def main():
    # logging.info(m_log["BSCStart"])
    async with BscScan(BSC_KEY) as bsc:

        for key, value in BSC_ADDRESSES.items():
            start_block = get_max_id("block", "transactionsBSC", " WHERE walletName='" +
                                     list(BSC_ADDRESSES.keys())[list(BSC_ADDRESSES.values()).index(value)] + "'")
            bnb_val[key] = {}
            bnb_val[key]["BNB amount"] = int(await bsc.get_bnb_balance(address=value))/10**18
            bnb_val[key]["txs"] = await get_tx(bsc.get_normal_txs_by_address, value, start_block)
            bnb_val[key]["token_txs"] = await get_tx(bsc.get_bep20_token_transfer_events_by_address, value, start_block)
            sleep(1)
            bnb_val[key]["tokenAmounts"] = {}
            contract_list = []
            i = 0
            for token in bnb_val[key]["token_txs"].values():

                if token["tokenContract"] not in (list(shit_coins.values()) + contract_list):
                    val = int(await bsc.get_acc_balance_by_token_contract_address(
                        address=value, contract_address=token["tokenContract"])) / 10 ** int(token["tokenDecimal"])
                    if val > 0:
                        bnb_val[key]["amounts"] = token["tokenName"] + ": " + str(val)
                    i = i + 1
                    contract_list.append(token["tokenContract"])
                if i == 4:
                    sleep(1)
                    i = 0

            print(bnb_val[key])

    # logging.info(m_log["BSCEnd"])


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
