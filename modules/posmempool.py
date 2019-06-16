"""
A Safe thread object interfacing the PoS mempool.

FR: Dump mempool to disk when closing, and re-import/filter out on load so we don't loose potentially important
messages when things go wrong and everyone crashes.

See https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup
or https://github.com/husio/python-sqlite3-backup
"""
import threading
import json
import time
import os
import sys
import sqlite3

# import asyncio
# https://github.com/zeromake/aiosqlite3 - Tested https://github.com/jreese/aiosqlite without success.
# Maybe also see https://github.com/aio-libs/aioodbc
# import aiosqlite3

# Our modules
# import common
import config
import posblock
import poscrypto
from sqlitebase import SqliteBase


__version__ = "0.0.43"

SQL_CREATE_MEMPOOL = "CREATE TABLE pos_messages (\
    txid         BLOB (64)    PRIMARY KEY,\
    block_height INTEGER,\
    timestamp    INTEGER,\
    sender       VARCHAR (34),\
    recipient    VARCHAR (34),\
    what         INTEGER,\
    params       STRING,\
    value        INTEGER,\
    pubkey       BLOB (64),\
    received     INTEGER\
);"
# TODO: add indices: timestamp, definitely. and why not sender, recipient, what as covering

SQL_INSERT_TX = (
    "INSERT OR IGNORE INTO pos_messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)

# Purge old txs that may be stuck
SQL_PURGE = (
    "DELETE FROM pos_messages WHERE timestamp <= strftime('%s', 'now', '-5 hour')"
)

# Purge old txs that may be stuck
SQL_PURGE_30 = (
    "DELETE FROM pos_messages WHERE timestamp <= strftime('%s', 'now', '-30 minute')"
)


# Purge old start txs from our address
SQL_PURGE_START1 = "DELETE FROM pos_messages WHERE timestamp <= strftime('%s', 'now', '-1 hour') AND sender=? AND recipient=? AND what=202"
# Count our messages to alleviate if necessary
SQL_COUNT_START_MESSAGES = (
    "SELECT COUNT(txid) from pos_messages WHERE sender=? AND recipient=? AND what=202"
)
# Delete a random subset of our start messages not to spam and preserve some info still.
SQL_PURGE_START2 = (
    "DELETE FROM pos_messages WHERE txid in "
    "(SELECT txid FROM pos_messages WHERE sender=? AND recipient=? AND what=202 "
    "ORDER BY RANDOM() LIMIT ?)"
)

# Delete all transactions
SQL_CLEAR = "DELETE FROM pos_messages"

SQL_SINCE = "SELECT * FROM pos_messages WHERE timestamp >= ? ORDER BY timestamp ASC"

SQL_TXID_EXISTS = "SELECT txid FROM pos_messages WHERE txid = ?"

SQL_STATUS = (
    "SELECT COUNT(*) AS NB, COUNT(distinct sender) as SENDERS, count(distinct recipient) as RECIPIENTS "
    "FROM pos_messages"
)

SQL_COUNT = "SELECT COUNT(*) AS NB FROM pos_messages"

SQL_LIST_TXIDS = "SELECT txid FROM pos_messages"
SQL_REMOVE_TXID = "DELETE FROM pos_messages where txid = ?"

SQL_REMOVE_TXID_IN = "DELETE FROM pos_messages where txid IN "

# How old a transaction can be to be embedded in a block ? Don't pick too large a delta T
NOT_OLDER_THAN_SECONDS = 60 * 30 * 1000


class Mempool:
    """
    Generic Parent Class
    """

    def __init__(self, verbose=False, app_log=None):
        self.verbose = verbose
        self.app_log = app_log

    async def status(self):
        print("Mempool Virtual Method Status")

    async def tx_count(self):
        print("Virtual Method tx_count")

    async def _insert_tx(self, tx):
        print("Virtual Method _insert_tx")

    async def _delete_tx(self, tx):
        print("Virtual Method _delete_tx")

    async def digest_tx(self, tx, poschain=None):
        """
        Async. Check validity of the transaction and insert if mempool if ok.
        TODO: 2 steps when getting batch: first checks, then a single insert
        FR: We could also keep just the txids in a ram dict to filter out faster. (no need if ram mempool)

        :param tx:
        :param poschain:
        :return:
        """
        if "TX" == tx.__class__.__name__:
            # Protobuf, convert to object
            tx = posblock.PosMessage().from_proto(tx)
        # TODO: if list, convert also
        if self.verbose and "txdigest" in config.LOG:
            self.app_log.info("Digesting {}".format(tx.to_json()))
        try:

            if await self.tx_exists(tx.txid):
                # TODO: useless since we have an index, we can raise or ignore commit if exists.
                return False
            if poschain:
                if await poschain.tx_exists(tx.txid):
                    return False
            # Validity checks, will raise
            tx.check()

            # TODO: batch, so we can do a global commit?
            await self._insert_tx(tx)
            # TODO: also add the pubkey in index if present.
            # returns the native tx object
            return tx
        except Exception as e:
            self.app_log.error("mempool digest_tx: {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(exc_type, fname, exc_tb.tb_lineno)
            raise

    async def tx_exists(self, txid):
        """
        Tell is the given txid is in our mempool already.

        :return:
        """
        print("Virtual Method tx_exists")

    async def async_all(self, block_height=0):
        """
        Return all tx to embed in current block

        :return:
        """
        print("Virtual Method all_tx")


class MemoryMempool(Mempool):
    """
    Memory Storage, POC only - Deprecated
    """

    def __init__(self, verbose=False, app_log=None):
        super().__init__(verbose=verbose, app_log=app_log)
        # Just a list
        self.txs = []
        self.lock = threading.Lock()

    async def status(self):
        return json.dumps(self.txs)

    async def _insert_tx(self, tx):
        with self.lock:
            self.txs.append(tx)

    async def _delete_tx(self, tx):
        with self.lock:
            self.txs.remove(tx)


class SqliteMempool(Mempool, SqliteBase):
    """
    Sqlite storage backend.
    """

    def __init__(self, verbose=False, db_path="./data/", app_log=None, ram=False):
        if ram:
            # Allow for memory mempool: replaces boolean by schema definition
            ram = SQL_CREATE_MEMPOOL
        Mempool.__init__(self, verbose=verbose, app_log=app_log)
        SqliteBase.__init__(
            self,
            verbose=verbose,
            db_path=db_path,
            db_name="posmempool.db",
            app_log=app_log,
            ram=ram,
        )

    # ========================= Generic DB Handling Methods ====================

    def check(self):
        """
        Check and creates mempool. This is not async yet, so we close afterward.

        :return:
        """
        self.app_log.info("Mempool Check")
        if not os.path.isfile(self.db_path):
            res = -1
        else:
            # Test DB
            # TODO: RAM Mode
            self.db = sqlite3.connect(self.db_path, timeout=1)
            self.db.text_factory = str
            self.cursor = self.db.cursor()
            # check if mempool needs recreating
            self.cursor.execute("PRAGMA table_info('pos_messages')")
            res = len(self.cursor.fetchall())
            # print(len(res), res)
        # No file or structure not matching
        if res != 10:
            try:
                self.db.close()
            except:
                pass
            try:
                os.remove(self.db_path)
            except:
                pass
            self.db = sqlite3.connect(self.db_path, timeout=1)
            self.db.text_factory = str
            self.cursor = self.db.cursor()
            self.execute(SQL_CREATE_MEMPOOL)
            self.commit()
            self.app_log.info("Status: Recreated mempool file")
        self.db.close()
        self.db = None
        self.cursor = None

    # ========================= Real useful Methods ====================

    async def status(self):
        """
        Async. Return mempool status.

        :return: status as dict()
        """
        res = await self.async_fetchall(SQL_STATUS)
        if res:
            return dict(res[0])
        else:
            return {}

    async def tx_count(self):
        """
        Async. Mempool current transactions count.

        :return: int
        """
        res = await self.async_fetchone(SQL_COUNT)
        # Safety: if we have too many tx, drop the older than 30 min ones
        if res[0] > 100:
            await self.async_execute(SQL_PURGE_30, commit=True)
        return res

    async def async_purge(self):
        """
        Async. Purge old txs
        """
        await self.async_execute(SQL_PURGE, commit=True)

    async def async_purge_start(self, address):
        """
        Async. Purge our old start messages if they are too numerous or too old
        """
        try:
            await self.async_execute(SQL_PURGE_START1, (address, address), commit=True)
            how_many = await self.async_fetchone(
                SQL_COUNT_START_MESSAGES, (address, address)
            )
            how_many = how_many[0]
            # print("how many", how_many)
            await self.async_execute(
                SQL_PURGE_START2, (address, address, how_many - 5), commit=True
            )
            await self.async_execute("VACUUM", commit=True)
        except Exception as e:
            self.app_log.error("async_purge_start: {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(exc_type, fname, exc_tb.tb_lineno)
            raise

    async def clear(self):
        """
        Async. Empty mempool

        :return:
        """
        await self.async_execute(SQL_CLEAR, commit=True)
        # Good time to cleanup
        await self.async_execute("VACUUM", commit=True)

    async def async_since(self, date=0):
        """
        Async. Return the list of transactions we got since the given date

        :param date:
        :return: a list of posblock.PosMessage objects
        """
        res = await self.async_fetchall(SQL_SINCE, (date,))
        res = [posblock.PosMessage().from_list(tx) for tx in res]
        return res

    async def _insert_tx(self, tx):
        """
        Async. Save to tx (=PosMessage) object in db

        :param tx: a notive PosMessage object
        :return: None
        """
        await self.async_execute(SQL_INSERT_TX, tx.to_db(), commit=True)

    async def async_all(self, block_height=0):
        """
        Return all transactions in current mempool

        :return: list() of PosMessages instances
        """
        res = await self.async_fetchall(
            SQL_SINCE, (int(time.time()) - NOT_OLDER_THAN_SECONDS,)
        )
        res = [posblock.PosMessage().from_list(tx) for tx in res]
        if block_height:
            # Set blockheight to be embedded in.
            for tx in res:
                tx.block_height = block_height
        return res

    async def tx_exists(self, txid):
        """
        Tell is the given txid is in our mempool.

        :return: Boolean
        """
        exists = await self.async_fetchone(SQL_TXID_EXISTS, (txid,))
        if exists:
            if "txdigest" in config.LOG:
                self.app_log.info(
                    "{}[...] already in our mempool".format(
                        poscrypto.raw_to_hex(txid)[:16]
                    )
                )
            return True
        return False

    async def async_alltxids(self):
        """
        Return all txids from mempool.

        :return: list()
        """
        try:
            res = await self.async_fetchall(SQL_LIST_TXIDS)
            res = [tx["txid"] for tx in res]
            return res
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            raise

    async def async_del_txids_old(self, txids):
        """
        Delete a list of the txs from mempool. Older and slower version, kept for temp. reference.

        :param txids:
        :return: True
        """
        # optimize, build a single "WHERE txid IN (,,,,)" request
        params = ((txid,) for txid in txids)
        await self.async_execute(SQL_REMOVE_TXID, params, commit=True, many=True)
        """
        # Even slower
        try:
            for tx in txids:
                await self.async_execute(SQL_REMOVE_TXID, (tx, ), commit=False)
        finally:
            await self.async_db.commit()
            # tx = 0
            # await self.async_execute(SQL_REMOVE_TXID, (tx, ), commit=True)
        """
        return True

    async def async_del_txids(self, txids):
        """
        Delete a list of the txs from mempool. Optimized, more than 100x executemany()

        :param txids: binary txid (bytes)
        :return: True
        """
        #
        # FR: Slice to cut in reasonable batches (like 100 to 500)
        params = ["X'" + poscrypto.raw_to_hex(txid) + "'" for txid in txids]
        sql = SQL_REMOVE_TXID_IN + "(" + ", ".join(params) + ")"
        # print(params)
        await self.async_execute(sql, commit=True)
        return True

    async def async_del_hex_txids(self, hex_txids):
        """
        Delete a list of the txs from mempool. Optimized, more than 100x executemany()

        :param hex_txids: list of "X'hex_encoded_string'" strings for sqlite.
        :return: True
        """
        #
        # FR: Slice to cut in reasonable batches (like 100 to 500)
        sql = SQL_REMOVE_TXID_IN + "(" + ", ".join(hex_txids) + ")"
        await self.async_execute(sql, commit=True)
        return True
