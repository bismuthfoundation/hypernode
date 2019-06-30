"""
Benchmark framework for the mempool object

Test in memory sqlite vs pure ram custom structures.
"""

import asyncio
import json
import os
import sys
from time import time

sys.path.append('../modules')

from posmempool import SqliteMempool
from naivemempool import NaiveMempool
import posblock
import poscrypto

TESTABLE = None

COUNT = 10000
TXS = []


TEST_COUNT = 100


def create_txs():
    global TXS
    for i in range(COUNT):
        tx = posblock.PosMessage().from_values(timestamp=i, sender=poscrypto.ADDRESS, recipient=poscrypto.ADDRESS, what=0, params='', value=0, pubkey=None)
        tx.sign()
        TXS.append(tx)


async def arange(count):
    for i in range(count):
        yield(i)


async def bench1():
    """Test and insert"""
    start = time()
    #async for i in arange(COUNT):
    for i in range(COUNT):
        if not await TESTABLE.tx_exists(TXS[i].txid):
            await TESTABLE._insert_tx(TXS[i])
    print(time() - start)


async def bench_test():
    start = time()
    for i in range(TEST_COUNT):
        for tx in TESTS100:
            assert(await TESTABLE.tx_exists(tx.txid) == True)
    print(time() - start)


async def bench_purge():
    """Purge half"""
    start = time()
    await TESTABLE.async_purge_test(5000)
    print(time() - start)


def bench(name: str):
    print("{}, test & insert".format(name))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bench1())

    print("{}, test {}".format(name, TEST_COUNT))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bench_test())

    print("{}, purge".format(name))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bench_purge())


if __name__ == "__main__":
    start = time()
    poscrypto.load_keys("poswallet.json")
    if not os.path.isfile('txs.json'):
        create_txs()
        txs_as_list = [tx.to_list(as_hex=True) for tx in TXS]
        with open("txs.json", "w") as fp:
            json.dump(txs_as_list, fp)
    else:
        with open("txs.json", "r") as fp:
            txs_as_list = json.load(fp)
        for i, tx in enumerate(txs_as_list):
            tx_object = posblock.PosMessage().from_list(tx, as_hex=True)
            tx_object.received = i  # Force a received value for tests.
            TXS.append(tx_object)

    # 1/10 of txs
    TESTS10 = [tx for tx in TXS if tx.received % 10 == 0]
    # 1/100 of txs
    TESTS100 = [tx for tx in TXS if tx.received % 100 == 0]

    print("Init", time() - start)
    print("timestamp from {} to {}".format(TXS[0].timestamp, TXS[COUNT - 1].timestamp))
    print("received from {} to {}".format(TXS[0].received, TXS[COUNT - 1].received))

    TESTABLE = SqliteMempool(verbose=False, db_path="./", app_log=None, ram=True)
    bench("SqliteMempool")

    TESTABLE = NaiveMempool(verbose=False, app_log=None, ram=True)
    bench("NaiveMempool")
