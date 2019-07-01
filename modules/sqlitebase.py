"""
A common ancestor for sqlite related storage objects.

Used by mempool and poschain
"""

import asyncio
import logging
import os
import sqlite3
import sys
import time
import traceback
from pathlib import Path

import aiosqlite3

import com_helpers

# from fakelog import FakeLog

__version__ = "0.0.31"


XLOG = False
# XLOG = "./logs/xlogs.log"

SLOW_QUERIES_LOG = "./logs/slow.log"
SLOW_TRIGGER = 5.0  # seconds for slow query


class SqliteBase:
    """
    Generic Sqlite storage backend.
    """

    def __init__(
        self,
        verbose=False,
        db_path: str = "./data/",
        db_name: str = "posmempool.db",
        app_log: logging.log = None,
        ram: str = False,
    ):
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
            app_log = logging.getLogger("foo")  # FakeLog()
        self.app_log = app_log
        self.cursor = None
        self.check()
        self.async_db = None
        self.ram = ram
        self.req = 0
        if XLOG:
            if not os.path.isfile(XLOG):
                Path(XLOG).touch()
        if SLOW_QUERIES_LOG:
            if not os.path.isfile(SLOW_QUERIES_LOG):
                Path(SLOW_QUERIES_LOG).touch()

    # ========================== temp logging ==================================

    def xlog(self, info: str, req: int = 0) -> None:
        try:
            if XLOG and self.db_name == "posmempool.db":
                with open(XLOG, "a+") as f:
                    f.write(str(time.time()) + " : " + str(req) + " : " + self.db_name + " : " + info + "\n")
        except Exception as e:
            print(e)

    def slowlog(self, info: str, duration: float) -> None:
        try:
            if SLOW_QUERIES_LOG:
                with open(SLOW_QUERIES_LOG, "a+") as f:
                    f.write(str(time.time()) + " : " + str(duration) + " : " + self.db_name + " : " + info + "\n")
        except Exception as e:
            print(e)

    # ========================= Generic DB Handling Methods ====================

    def check(self):
        """
        Checks and creates db. This is not async yet, so we close afterward.

        :return:
        """
        self.app_log.info("Virtual Method {} Check".format(self.db_name))

    def index_exists(self, index_name: str) -> bool:
        """
        Tells whether that index exists
        :param index_name:
        :return:
        """
        self.cursor.execute("PRAGMA index_info('{}')".format(index_name))
        res = len(self.cursor.fetchall())
        return res > 0

    def execute(
        self,
        sql: str,
        param: tuple = None,
        cursor=None,
        commit: bool = False,
        many: bool = False,
    ):
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
                    if com_helpers.MY_NODE:
                        com_helpers.MY_NODE.stop()
                    else:
                        sys.exit()
                time.sleep(0.1)

        if commit:
            self.commit()
            return None
        return cursor

    def fetchone(self, sql: str, param: tuple = None, as_dict: bool = False):
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

    async def async_execute(
        self, sql: str, param: tuple = None, commit: bool = False, many: bool = False
    ):
        """
        Async. Safely execute the request

        :param sql:
        :param param:
        :param commit: If True, will commit after the request.
        :param many: If True, will use an executemany call with param being a list of params.
        :return: a cursor async proxy, or None if commit. If not commit, cursor() has to be closed.
        """
        self.req += 1
        req = self.req
        if False:  # self.db_name == "posmempool.db":
            print(sql)
            for line in traceback.format_stack():
                print(line.strip())
        self.xlog("execute {}".format(sql), req)
        start = time.time()
        try:
            cursor = None
            """
            if 'ledger' in self.db_path:
                self.app_log.info("async_execute {}, {}, commit {}, many {}".format(sql, str(param), commit, many))
                # self.app_log.info("async_execute {}".format(self.async_db))
            """
            if not self.async_db:
                self.xlog("create dbh")
                try:
                    # open
                    if self.verbose:
                        self.app_log.info(
                            "Opening async {} {} db - Ram {}".format(self.db_path, self.db_name, self.ram)
                        )
                    if self.ram:
                        self.xlog("ram mode")
                        self.async_db = await aiosqlite3.connect(
                            "file:temp?mode=memory",
                            loop=asyncio.get_event_loop(),
                            isolation_level="",  # None would turn auto commit
                            check_same_thread=False,
                            uri=True,
                        )
                        await self.async_db.execute('pragma journal_mode=wal')
                        # Since we create in ram, the db is empty, so we recreate it here
                        if type(self.ram) == str:
                            self.ram = [self.ram]
                        for the_sql in self.ram:
                            await self.async_db.execute(the_sql)
                            self.xlog("did {}".format(the_sql))
                            # print(the_sql, "ok")
                        await self.async_commit()
                    else:
                        if self.db_name == "posmempool.db":
                            print("path open")
                        self.async_db = await aiosqlite3.connect(
                            self.db_path,
                            loop=asyncio.get_event_loop(),
                            isolation_level="",
                        )
                    self.async_db.row_factory = sqlite3.Row
                    self.async_db.text_factory = str
                    self.async_db.isolation_level = ""  # None would turn auto commit
                    await self.async_db.execute("PRAGMA journal_mode=wal")
                    await self.async_db.execute("PRAGMA temp_store=memory")  # not sure this helps, but does no harm.
                    await self.async_db.execute("PRAGMA page_size=4096")
                    # self.cursor = await self.async_db.cursor()
                    # self.async_db.execute("PRAGMA synchronous=OFF")  # Not so much faster
                except Exception as e:
                    self.app_log.warning("async_execute {}: {}".format(self.db_name, e))
                    """
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))
                    """

            # Try count so we can die if we lock
            max_tries = 10
            while max_tries:
                try:
                    if many:
                        # await cursor.executemany(sql, param)
                        cursor = await self.async_db.executemany(sql, param)
                    elif param:
                        cursor = await self.async_db.execute(sql, param)
                    else:
                        cursor = await self.async_db.execute(sql)
                    break
                except sqlite3.IntegrityError as e:
                    # 'UNIQUE constraint failed'
                    raise
                except Exception as e:
                    self.xlog("Exception retry {}: {}".format(max_tries, e))
                    if str(e) == "not an error":
                        self.app_log.warning(
                            "Database {} query: {} {}, Exception NAE '{}'".format(
                                self.db_name, sql, param, e
                            )
                        )
                        test = await self.async_db.execute(".schema")
                        res = await test.fetchall()
                        print(list(res))
                        self.xlog("schema {}".format(str(list(res))))

                    self.app_log.warning(
                        "Database {} query: {} {}, retry because {}".format(
                            self.db_name, sql, param, e
                        )
                    )
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    self.app_log.warning(
                        "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
                    )
                    if "syntax error" in str(e):
                        # No need to retry
                        com_helpers.MY_NODE.stop()
                    # TODO: Bad hack to sort out
                    if "cannot start a transaction within a transaction" in str(e):
                        self.app_log.info("Auto-committing")
                        await self.async_commit()
                    if cursor:
                        await cursor.close()
                    asyncio.sleep(0.1)
                    max_tries -= 1
            if not max_tries:
                self.app_log.error("Too many retries")
                com_helpers.MY_NODE.stop()
            if commit:
                await self.async_commit()
                try:
                    await cursor.close()
                except:
                    pass
                cursor = None
            return cursor
        finally:
            duration = time.time() - start
            if SLOW_QUERIES_LOG and duration > SLOW_TRIGGER:
                if " VALUES(X" in sql:
                    # INSERT INTO pos_messages (txid, block_height, timestamp, sender, recipient, what, params, value, pubkey, received) VALUES  (X'09aa456
                    sql = str[:132] + ' ...'
                self.slowlog(sql + "  " + str(param), duration)
            self.xlog("Done", req)

    def commit(self):
        """
        Safe commit
        """
        if not self.db:
            raise ValueError("Closed {} DB".format(self.db_name))
        max_tries = 10
        while max_tries:
            try:
                self.db.commit()
                break
            except Exception as e:
                self.app_log.warning(
                    "Database {} retry reason: {}".format(self.db_name, e)
                )
                time.sleep(0.1)
            max_tries -= 1
        if not max_tries:
            self.app_log.error("Too many retries")
            com_helpers.MY_NODE.stop()

    async def async_commit(self):
        """
        Async. Safe commit
        """
        self.xlog("commit")
        max_tries = 1
        while max_tries:
            try:
                await self.async_db.commit()
                break
            except Exception as e:
                self.app_log.warning(
                    "Database {} retry reason: {}".format(self.db_name, e)
                )
                # asyncio.sleep(0.1)
            max_tries -= 1
        """
        if not max_tries:
            self.app_log.error("Too many retries")
            com_helpers.MY_NODE.stop()
        """
        self.xlog("commit end")

    async def async_fetchone(
        self, sql: str, param: tuple = None, as_dict: bool = False
    ):
        """
        Async. Fetch one and Returns data.

        :param sql:
        :param param:
        :param as_dict: returns result as a dict, default False.
        :return: tuple()
        """
        self.xlog("fetchone")
        cursor = await self.async_execute(sql, param)
        data = await cursor.fetchone()
        await cursor.close()
        self.xlog("fetchone end")
        if not data:
            return None
        if as_dict:
            return dict(data)
        return tuple(data)

    async def async_fetchall(self, sql: str, param: tuple = None):
        """
        Async. Fetch all and Returns data

        :param sql:
        :param param:
        :return:
        """
        self.xlog("fetchall")
        cursor = await self.async_execute(sql, param)
        data = await cursor.fetchall()
        await cursor.close()
        self.xlog("fetchall end")
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
