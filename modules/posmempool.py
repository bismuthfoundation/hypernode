"""
A Safe thread object interfacing the PoS mempool
"""
import threading
import json
import time
import os
import sqlite3
import asyncio
# https://github.com/zeromake/aiosqlite3 - Tested https://github.com/jreese/aiosqlite without success.
# Maybe also see https://github.com/aio-libs/aioodbc
import aiosqlite3

# Our modules
# import common
# import poscrypto
import posblock

__version__ = '0.0.3'

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


class Mempool:
    """
    Generic Class
    """

    def __init__(self, verbose=False, app_log=None):
        self.verbose = verbose
        self.app_log = app_log

    async def status(self):
        print("Virtual Method Status")

    async def _insert_tx(self, tx):
        print("Virtual Method _insert_tx")

    async def _delete_tx(self, tx):
        print("Virtual Method _delete_tx")

    async def digest_tx(self, tx):
        if 'TX' == tx.__class__.__name__:
            # Protobuf, convert to object
            tx = posblock.PosMessage().from_proto(tx)
        # TODO: if list, convert also
        if self.verbose:
            self.app_log.info("Digesting {}".format(tx.to_json()))
        # Validity checks, will raise
        tx.check()
        await self._insert_tx(tx)
        # self._insert_tx(tx)
        # TODO: also add the pubkey in index if present.


class MemoryMempool(Mempool):
    """
    Memory Storage, POC only
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


class SqliteMempool(Mempool):
    """
    Sqlite storage backend.
    """
    # TODO: Allow for memory mempool
    def __init__(self, verbose=False, db_path='./data/', app_log=None, ram=False):
        super().__init__(verbose=verbose, app_log=app_log)
        self.db_path = db_path + 'posmempool.db'
        self.db = None
        self.cursor = None
        self.check()
        self.async_db = None

    # ========================= Generic DB Handling Methods ====================

    def check(self):
        """
        Checks and creates mempool. This is not async yet, so we close afterward.
        :return:
        """
        self.app_log.info("Mempool Check")
        # Create DB
        # TODO: RAM Mode
        self.db = sqlite3.connect(self.db_path, timeout=1)
        self.db.text_factory = str
        self.cursor = self.db.cursor()
        # check if mempool needs recreating
        self.cursor.execute("PRAGMA table_info('pos_messages')")
        res = self.cursor.fetchall()
        # print(len(res), res)
        if len(res) != 10:
            self.db.close()
            os.remove(self.db_path)
            self.db = sqlite3.connect(self.db_path, timeout=1)
            self.db.text_factory = str
            self.cursor = self.db.cursor()
            self.execute(SQL_CREATE_MEMPOOL)
            self.commit()
            self.app_log.info("Status: Recreated mempool file")
        self.db.close()
        self.db = None
        self.cursor = None

    def execute(self, sql, param=None, cursor=None, commit=False):
        """
        Safely execute the request
        :param sql:
        :param param:
        :param cursor: optional. will use the locked shared cursor if None
        :param commit: optional. will commit after sql
        :return:
        """
        if not self.db:
            raise ValueError("Closed mempool DB")
        # TODO: add a try count and die if we lock
        while True:
            try:
                if not cursor:
                    cursor = self.cursor
                if param:
                    cursor.execute(sql, param)
                else:
                    cursor.execute(sql)
                break
            except Exception as e:
                self.app_log.warning("Database query: {} {}".format(cursor, sql))
                self.app_log.warning("Database retry reason: {}".format(e))
                time.sleep(0.1)
        if commit:
            self.commit()
            cursor.close()
            cursor = None
        return cursor

    async def async_execute(self, sql, param=None, commit=False):
        """
        Safely execute the request
        :param sql:
        :param param:
        :param commit: If True, will commit after the request.
        :return: a cursor async proxy, or None if commit. If not commit, cursor() has to be close.
        """
        if not self.async_db:
            # TODO: RAM Mode
            try:
                # open
                self.app_log.info("Opening async db")
                self.async_db = await aiosqlite3.connect(self.db_path, loop=asyncio.get_event_loop())
                self.async_db.text_factory = str
            except Exception as e:
                self.app_log.warning("async_execute: {}".format(e))
        # TODO: add a try count and die if we lock
        while True:
            try:
                cursor = await self.async_db.cursor()
                if param:
                    # print(sql, param)
                    await cursor.execute(sql, param)
                else:
                    await cursor.execute(sql)
                break
            except Exception as e:
                self.app_log.warning("Database query: {} {}".format(sql, param))
                self.app_log.warning("Database retry reason: {}".format(e))
                asyncio.sleep(0.1)
        if commit:
            await self.async_commit()
            await cursor.close()
            cursor = None
        return cursor

    def commit(self):
        """
        Safe commit
        :return:
        """
        if not self.db:
            raise ValueError("Closed mempool DB")
        while True:
            try:
                self.db.commit()
                break
            except Exception as e:
                self.app_log.warning("Database retry reason: {}".format(e))
                time.sleep(0.1)

    async def async_commit(self):
        """
        Safe commit
        :return:
        """
        while True:
            try:
                await self.async_db.commit()
                break
            except Exception as e:
                self.app_log.warning("Database retry reason: {}".format(e))
                asyncio.sleep(0.1)

    async def async_fetchone(self, sql, param=None):
        """
        Fetch one and Returns data
        :param sql:
        :param param:
        :return:
        """
        cursor = await self.async_execute(sql, param)
        data = await cursor.fetchone()
        await cursor.close()
        return data

    async def async_fetchall(self, sql, param=None):
        """
        Fetch all and Returns data
        :param sql:
        :param param:
        :return:
        """
        cursor = await self.async_execute(sql, param)
        data = await cursor.fetchall()
        await cursor.close()
        return data

    async def async_vacuum(self):
        """
        Maintenance
        :return:
        """
        await self.async_execute("VACUUM", commit=True)

    def close(self):
        if self.db:
            self.db.close()

    async def async_close(self):
        # TODO: make sure we call when closing.
        if self.async_db:
            await self.async_db.close()
        print('async close')

    # ========================= Real useful Methods ====================

    async def async_purge(self):
        """
        Purge old txs
        :return:
        """
        await self.async_execute(SQL_PURGE, commit=True)

    def clear(self):
        """
        Empty mempool
        :return:
        """
        self.async_execute(SQL_CLEAR, commit=True)

    async def async_since(self, date=0):
        """
        returns the list of transactions we got since the given date
        :param date:
        :return:
        """
        # TODO - return a list of posblock.PosMessage objects
        res = await self.async_fetchall(SQL_SINCE, (date, ))
        res = [posblock.PosMessage().from_list(tx) for tx in res]
        return res

    async def _insert_tx(self, tx):
        """
        Saves to tx (=PosMessage) object in db
        :param tx:
        :return:
        """
        print("TODO insert tx", tx.to_db())
        res = await self.async_execute(SQL_INSERT_TX, tx.to_db(), commit=True)
        # res = self.execute(SQL_INSERT_TX, tx.to_db(), commit=True)
        print('inserted', res)
