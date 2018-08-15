"""
Benchmark suite for SQLite operations

Needs pytest, just run pytest in the test directory or pytest a_file.py to run on a single file.
"""

import asyncio
import json
import logging
import sys
import time
import aiosqlite3
import sqlite3


sys.path.append('../modules')
import posblock
import poschain
import poscrypto
import test_helpers

NB = 0

async def digest_txs(test_poschain, block):
    res = await test_poschain.async_execute("delete from pos_messages")
    res = await test_poschain.async_execute("delete from pos_chain")
    await test_poschain._insert_block(block)


async def poschain_count(test_poschain):
    res = await test_poschain.async_fetchone("select count(*) from pos_messages")
    print(res[0])


def sync_poschain_count(loop, test_poschain):
    loop.run_until_complete(poschain_count(test_poschain))


def sync_digest_txs(loop, test_poschain, txs):
    loop.run_until_complete(digest_txs(test_poschain, txs))


def test_poschain_digest(benchmark):
    global NB
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        logger = logging.getLogger('foo')
        test_helpers.remove_pc()
        poscrypto.load_keys('./bench_wallet.json')
        test_poschain = poschain.SqlitePosChain(app_log=logger, db_path='./')
        test_poschain.check()
        n = 100
        # Generate random tx for the block
        txs = test_helpers.create_txs(n, sign=True, block_height=1)
        block = posblock.PosBlock()
        block.height = 1
        block.round = 1
        block.sir = 1
        block.txs = txs
        # temp = block.to_dict(as_hex=True)
        # logger.warning(json.dumps(temp))
        if benchmark:
            benchmark(sync_digest_txs, loop, test_poschain, block)
        else:
            start = time.time()
            sync_digest_txs(loop, test_poschain, block)
            print("{} txs digested in {} sec".format(n, time.time() - start))
            sync_poschain_count(loop, test_poschain)

        test_helpers.remove_pc()
        NB += 1
    finally:
        loop.close()


if __name__ == "__main__":
    print("Run pytest for tests.\n")
    test_poschain_digest(None)



