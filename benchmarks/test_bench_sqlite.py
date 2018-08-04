"""
Benchmark suite for SQLite operations

Needs pytest, just run pytest in the test directory.
"""

import asyncio
import logging
import sys


sys.path.append('../modules')
import posmempool
import poscrypto
import test_helpers

# FR: refactor, move purely crypto related tests (tx, sign) to bench_crypto, only keep sql benchmarks here.


async def digest_txs(mempool, txs):
    for tx in txs:
        await mempool.digest_tx(tx)


def sync_digest_txs(loop, mempool, txs):
        loop.run_until_complete(digest_txs(mempool, txs))


def test_mempool_digest(benchmark):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        logger = logging.getLogger('foo')
        test_helpers.remove_mp()
        mempool = posmempool.SqliteMempool(app_log=logger, db_path='./')
        mempool.check()
        poscrypto.load_keys('./bench_wallet.json')
        # Generate random tx
        txs = test_helpers.create_txs(100, True)
        if benchmark:
            benchmark(sync_digest_txs, loop, mempool, txs)
        else:
            sync_digest_txs(loop, mempool, txs)
        test_helpers.remove_mp()
    finally:
        loop.close()


if __name__ == "__main__":
    print("Run pytest for tests.\n")
    test_mempool_digest(None)
