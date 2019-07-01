"""
Full ram naive pos mempool impl.
"""

from time import time

from posmempool import Mempool, NOT_OLDER_THAN_SECONDS
from posblock import PosMessage


class NaiveMempool(Mempool):
    """A Very naive mempool implementation on top of a native python dict.
    Not thread safe, but async safe: every op is atomic and very fast with the tx amount we handle (less than 1000)
    and no async code is used, so every call is atomic vs the calling code.

    Would need locks to be used in a threaded context."""

    def __init__(self, verbose=False, app_log=None):
        Mempool.__init__(self, verbose=verbose, app_log=app_log)
        self._dict = {}

    def check(self):
        pass

    async def async_close(self):
        await self.clear()

    async def _insert_tx(self, tx: PosMessage):
        """
        Async. Save to tx (=PosMessage) object in db

        :param tx: a native PosMessage object
        :return: None
        """
        self._dict[tx.txid] = tx

    async def tx_exists(self, txid):
        """
        Tell is the given txid is in our mempool.

        :return: Boolean
        """
        return txid in self._dict

    async def async_purge(self):
        """
        Async. Purge old txs (5 hours)
        """
        ts_limit = time() - 5 * 3600
        self._dict = {txid: tx for txid, tx in self._dict.items() if tx.timestamp > ts_limit}

    async def async_purge_test(self, ts_limit :int):
        """
        Async. Purge old txs
        """
        self._dict = {txid: tx for txid, tx in self._dict.items() if tx.timestamp > ts_limit}

    async def async_purge_start(self, address):
        """
        Async. Purge our old start messages if they are too numerous or too old
        This is called only once at start, so perf is not an issue.
        Temp. deactivated, since this is an in ram only mempool, with no disk persistence so far.
        """
        self.app_log.warning("Reminder, deactivated async_purge_start, no persistence so far")
        # Check posmempool, sqliteMempool for reference

    async def clear(self):
        """
        Async. Empty mempool

        :return:
        """
        self._dict.clear()

    async def async_since(self, date=0):
        """
        Async. Return the list of transactions we got since the given date (unix timestamp)

        :param date:
        :return: a list of posblock.PosMessage objects
        """
        return [tx for tx in self._dict.values() if tx.received >= date]

    async def async_all(self, block_height=0):
        """
        Return all transactions in current mempool

        :return: list() of PosMessages instances
        """
        ts_limit = int(time()) - NOT_OLDER_THAN_SECONDS
        res = [tx for tx in self._dict.values() if tx.timestamp >= ts_limit]
        if block_height:
            # Set blockheight to be embedded in.
            for tx in res:
                tx.block_height = block_height
        return res

    async def async_alltxids(self):
        """
        Return all txids from mempool.

        :return: list()
        """
        return [tx.txid for tx in self._dict.values()]

    async def async_del_txids(self, txids):
        """
        Delete a list of the txs from mempool.

        :param txids: binary txid (bytes)
        :return: True
        """
        self._dict = {txid: tx for txid, tx in self._dict.items() if txid not in txids}
        return True

    async def async_del_hex_txids(self, hex_txids):
        """
        Delete a list of the txs from mempool.

        :param hex_txids: list of "X'hex_encoded_string'" strings for sqlite.
        :return: True
        """
        raise RuntimeError("Not supported in that impl, because non optimized. Use async_del_txids")

    async def status(self):
        """
        Async. Return mempool status. Count only in current naivemempool impl.

        :return: status as dict()
        """
        # key "NB" is important, ued by poshn.
        return {"NB": len(self._dict)}

    async def tx_count(self):
        """
        Async. Mempool current transactions count.

        :return: int
        """
        return len(self._dict)
