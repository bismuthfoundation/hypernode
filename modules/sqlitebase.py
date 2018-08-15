"""
A common ancestor for sqlite related storage objects.

Used by mempool and poschain
"""

import asyncio
import logging
import sqlite3
import sys
import time

import aiosqlite3

from fakelog import FakeLog

__version__ = '0.0.26'


class SqliteBase:
    """
    Generic Sqlite storage backend.
    """
    def __init__(self, verbose=False, db_path: str='./data/', db_name: str='posmempool.db', app_log: logging.log=None,
                 ram: str=False):
        """

        :param verbose:
        :param db_path:
        :param db_name:
        :param app_log:
        :param ram: empty or SQL definition of the ram table to create.
        """
        self.db_path = db_path + db_name
        self.db_name = db_name
        self.db = None
        self.verbose = verbose
        if not app_log:
            app_log = FakeLog()
        self.app_log = app_log
        self.cursor = None
        self.check()
        self.async_db = None
        self.ram = ram

    # ========================= Generic DB Handling Methods ====================

    def check(self):
        """
        Checks and creates db. This is not async yet, so we close afterward.

        :return:
        """
        self.app_log.info("Virtual Method {} Check".format(self.db_name))

    def execute(self, sql: str, param: tuple=None, cursor=None, commit: bool=False, many: bool=False):
        """
        Safely execute the request

        :param sql:
        :param param:
        :param cursor: optional. will use the locked shared cursor if None
        :param commit: optional. will commit after sql
        :param many: If True, will use an executemany call with param being a list of params.
        :return: cursor
        """
        if not self.db:
            raise ValueError("Closed {} DB".format(self.db_name))
        tries = 0
        while True:
            try:
                if not cursor:
                    cursor = self.cursor
                if many:
                    cursor.executemany(sql, param)
                elif param:
                    cursor.execute(sql, param)
                else:
                    cursor.execute(sql)
                break
            except Exception as e:
                self.app_log.warning("Database query {}: {}".format(self.db_name, sql))
                self.app_log.warning("Database retry reason: {}".format(e))
                tries += 1
                if tries >= 10:
                    self.app_log.error("Database Error, closing")
                    # raise ValueError("Too many retries")
                    sys.exit()
                time.sleep(0.1)

        if commit:
            self.commit()
            cursor.close()
            cursor = None
        return cursor

    def fetchone(self, sql: str, param: tuple=None, as_dict: bool=False):
        """
        Fetch one and Returns data.

        :param sql:
        :param param:
        :param as_dict: returns result as a dict, default False.
        :return: tuple()
        """
        cursor = self.execute(sql, param)
        data = cursor.fetchone()
        if not data:
            return None
        if as_dict:
            return dict(data)
        return tuple(data)

    async def async_execute(self, sql: str, param: tuple=None, commit: bool=False, many: bool=False):
        """
        Async. Safely execute the request

        :param sql:
        :param param:
        :param commit: If True, will commit after the request.
        :param many: If True, will use an executemany call with param being a list of params.
        :return: a cursor async proxy, or None if commit. If not commit, cursor() has to be closed.
        """
        cursor = None
        if not self.async_db:
            # TODO: RAM Mode
            try:
                # open
                self.app_log.info("Opening async {} db".format(self.db_name))
                if self.ram:
                    self.async_db = await aiosqlite3.connect('file:temp?mode=memory', loop=asyncio.get_event_loop(),
                                                             isolation_level = None, uri = True)
                    # Since we create in ram, the db is empty, so we recreateit here
                    await self.async_execute(self.ram)
                else:
                    self.async_db = await aiosqlite3.connect(self.db_path, loop=asyncio.get_event_loop(),
                                                             isolation_level=None)
                self.async_db.row_factory = sqlite3.Row
                self.async_db.text_factory = str
                self.async_db.isolation_level = None
                await self.async_db.execute('PRAGMA journal_mode = WAL;')
                await self.async_db.execute('PRAGMA page_size = 4096')
                # self.async_db.execute("PRAGMA synchronous=OFF")  # Not so much faster
            except Exception as e:
                self.app_log.warning("async_execute {}: {}".format(self.db_name, e))
        # TODO: add a try count and die if we lock
        max_tries = 10
        while max_tries:
            try:
                # FR: Do we have to create a new cursor? Why not use async_db directly?
                cursor = await self.async_db.cursor()
                if many:
                    await cursor.executemany(sql, param)
                elif param:
                    await cursor.execute(sql, param)
                else:
                    await cursor.execute(sql)
                break
            except sqlite3.IntegrityError as e:
                # 'UNIQUE constraint failed'
                raise
            except Exception as e:
                # TODO: Bad hack to sort out
                self.app_log.warning("Database {} query: {} {}, retry because {}".format(self.db_name, sql, param, e))
                if 'cannot start a transaction within a transaction' in str(e):
                    self.app_log.info("Auto-committing")
                    await self.async_commit()
                asyncio.sleep(0.1)
                max_tries -= 1
        if not max_tries:
            self.app_log.error("Too many retries")
            sys.exit()
            # raise ValueError("Too many retries")
        if commit:
            await self.async_commit()
            try:
                await cursor.close()
            except:
                pass
            cursor = None
        return cursor

    def commit(self):
        """
        Safe commit
        """
        if not self.db:
            raise ValueError("Closed {} DB".format(self.db_name))
        while True:
            try:
                self.db.commit()
                break
            except Exception as e:
                self.app_log.warning("Database {} retry reason: {}".format(self.db_name, e))
                time.sleep(0.1)

    async def async_commit(self):
        """
        Async. Safe commit
        """
        while True:
            try:
                await self.async_db.commit()
                break
            except Exception as e:
                self.app_log.warning("Database {} retry reason: {}".format(self.db_name, e))
                asyncio.sleep(0.1)

    async def async_fetchone(self, sql: str, param: tuple=None, as_dict: bool=False):
        """
        Async. Fetch one and Returns data.

        :param sql:
        :param param:
        :param as_dict: returns result as a dict, default False.
        :return: tuple()
        """
        cursor = await self.async_execute(sql, param)
        data = await cursor.fetchone()
        await cursor.close()
        if not data:
            return None
        if as_dict:
            return dict(data)
        return tuple(data)

    async def async_fetchall(self, sql: str, param: tuple=None):
        """
        Async. Fetch all and Returns data

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
        Async. Maintenance (Vacuum)
        """
        await self.async_execute("VACUUM", commit=True)

    def close(self):
        """
        Closes the db handle.
        """
        if self.db:
            self.db.close()

    async def async_close(self):
        """
        Async. Closes the db handle.
        """
        # TODO: make sure we call when closing.
        if self.async_db:
            await self.async_db.close()
        if self.verbose:
            self.app_log.info("Closed async {} db".format(self.db_name))
