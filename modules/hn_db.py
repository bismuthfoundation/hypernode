"""
An object interfacing the Hypernodes SqliteDB.
"""

import threading
import json
import time
import os
import sys
import sqlite3

# Our modules
from sqlitebase import SqliteBase


__version__ = '0.0.1'

SQL_CREATE_HYPERNODES = ''

SQL_CLEAR = ''


class HNDB:
    """
    Generic Parent Class
    """

    def __init__(self, verbose=False, app_log=None):
        self.verbose = verbose
        self.app_log = app_log


class SqliteHNDB(HNDB, SqliteBase):
    """
    Sqlite storage backend.
    """

    def __init__(self, verbose=False, db_path='./data/', app_log=None, ram=False):
        HNDB.__init__(self, verbose=verbose, app_log=app_log)
        SqliteBase.__init__(self, verbose=verbose, db_path=db_path, db_name='hndb.db', app_log=app_log, ram=ram)

    # ========================= Generic DB Handling Methods ====================

    def check(self):
        """
        Checks and creates mempool. This is not async yet, so we close afterward.

        :return:
        """
        self.app_log.info("HNDB Check")
        if not os.path.isfile(self.db_path):
            res = -1
        else:
            # Test DB
            # FR: RAM Mode?
            self.db = sqlite3.connect(self.db_path, timeout=1)
            self.db.text_factory = str
            self.cursor = self.db.cursor()
            # check if mempool needs recreating
            self.cursor.execute("PRAGMA table_info('hypernodes')")
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
            self.execute(SQL_CREATE_HYPERNODES)
            self.commit()
            self.app_log.info("Status: Recreated hndb.db file")
        self.db.close()
        self.db = None
        self.cursor = None

    # ========================= Real useful Methods ====================


    async def clear(self):
        """
        Async. Empty mempool

        :return:
        """
        await self.async_execute(SQL_CLEAR, commit=True)
        # Good time to cleanup
        await self.async_execute("VACUUM", commit=True)

