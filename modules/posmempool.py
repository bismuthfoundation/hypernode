"""
A Safe thread object interfacing the PoS mempool
"""
import threading
import json
import time
import os
import sys
import sqlite3
import asyncio
# https://github.com/zeromake/aiosqlite3 - Tested https://github.com/jreese/aiosqlite without success.
# Maybe also see https://github.com/aio-libs/aioodbc
import aiosqlite3

# Our modules
# import common
# import poscrypto
import posblock
from sqlitebase import SqliteBase


__version__ = '0.0.4'

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

SQL_INSERT_TX = "INSERT INTO pos_messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

# Purge old txs that may be stuck
SQL_PURGE = "DELETE FROM pos_messages WHERE timestamp <= strftime('%s', 'now', '-1 hour')"

# Delete all transactions
SQL_CLEAR = "DELETE FROM pos_messages"

SQL_SINCE = "SELECT * FROM pos_messages WHERE timestamp >= ? ORDER BY timestamp ASC"

SQL_TXID_EXISTS = "SELECT txid FROM pos_messages WHERE txid = ?"

SQL_STATUS = "SELECT COUNT(*) AS NB, COUNT(distinct sender) as SENDERS, count(distinct recipient) as RECIPIENTS FROM pos_messages"

# How old a transaction can be to be embedded in a block ? Don't pick too large a delta T
NOT_OLDER_THAN_SECONDS = 60*30 * 1000


class Mempool:
    """
    Generic Class
    """

    def __init__(self, verbose=False, app_log=None):
        self.verbose = verbose
        self.app_log = app_log

    async def status(self):
        print("Mempool Virtual Method Status")

    async def _insert_tx(self, tx):
        print("Virtual Method _insert_tx")

    async def _delete_tx(self, tx):
        print("Virtual Method _delete_tx")

    async def digest_tx(self, tx, poschain=None):
        if 'TX' == tx.__class__.__name__:
            # Protobuf, convert to object
            tx = posblock.PosMessage().from_proto(tx)
        # TODO: if list, convert also
        if self.verbose:
            self.app_log.info("Digesting {}".format(tx.to_json()))
        try:
            if await self.tx_exists(tx.txid):
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
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            raise


    async def tx_exists(self, txid):
        """
        Tell is the given txid is in our mempool
        :return:
        """
        print("Virtual Method tx_exists")

    async def async_all(self):
        """
        Returns all tx to embed in current block
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

    # TODO: Allow for memory mempool
    def __init__(self, verbose=False, db_path='./data/', app_log=None, ram=False):
        Mempool.__init__(self, verbose=verbose, app_log=app_log)
        SqliteBase.__init__(self, verbose=verbose, db_path=db_path, db_name='posmempool.db', app_log=app_log, ram=ram)
        """
        # Moved to ancestor
        self.db_path = db_path + 'posmempool.db'
        self.db = None
        self.cursor = None
        self.check()
        self.async_db = None
        """

    # ========================= Generic DB Handling Methods ====================

    def check(self):
        """
        Checks and creates mempool. This is not async yet, so we close afterward.
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
        status = {}
        res = await self.async_fetchall(SQL_STATUS)
        return dict(res[0])

    async def async_purge(self):
        """
        Purge old txs
        :return:
        """
        # TODO: To be called somehow (start of a round?)
        await self.async_execute(SQL_PURGE, commit=True)

    async def clear(self):
        """
        Empty mempool
        :return:
        """
        await self.async_execute(SQL_CLEAR, commit=True)
        # Good time to cleanup
        await self.async_execute("VACUUM", commit=True)

    async def async_since(self, date=0):
        """
        returns the list of transactions we got since the given date
        :param date:
        :return: a list of posblock.PosMessage objects
        """
        res = await self.async_fetchall(SQL_SINCE, (date, ))
        res = [posblock.PosMessage().from_list(tx) for tx in res]
        return res

    async def _insert_tx(self, tx):
        """
        Saves to tx (=PosMessage) object in db
        :param tx:
        :return:
        """
        res = await self.async_execute(SQL_INSERT_TX, tx.to_db(), commit=True)

    async def async_all(self):
        """
        Returns all tx from mempool
        :return:
        """
        res = await self.async_fetchall(SQL_SINCE, (int(time.time()) - NOT_OLDER_THAN_SECONDS, ))
        res = [posblock.PosMessage().from_list(tx) for tx in res]
        return res

    async def tx_exists(self, txid):
        """
        Tell is the given txid is in our mempool
        :return:
        """
        exists = await self.async_fetchone(SQL_TXID_EXISTS, (txid, ) )
        if exists:
            self.app_log.info("{} already in our mempool".format(txid))
            return True
        return False
