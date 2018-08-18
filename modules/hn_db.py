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
import poshelpers
from sqlitebase import SqliteBase


__version__ = '0.0.5'

SQL_CREATE_HYPERNODES = """CREATE TABLE hypernodes (
    round       BIGINT,
    address     VARCHAR (34),
    ip          VARCHAR (16),
    port        INTEGER      DEFAULT (6969),
    weight      INTEGER      DEFAULT (1),
    registrar   VARCHAR (56),
    reward      VARCHAR (56),
    ts_register INTEGER,
    ts_edit     INTEGER,
    active      BOOLEAN      DEFAULT false,
    CONSTRAINT idx_hn UNIQUE (
        round,
        address,
        ip,
        port
    )
    ON CONFLICT REPLACE
    );"""

SQL_CLEAR = 'DELETE FROM hypernodes'

SQL_DEL_OLDER_THAN_ROUND = "DELETE FROM hypernodes WHERE round < ?"

SQL_HN_FROM_ADDRESS_ROUND = "SELECT * FROM hypernodes WHERE address = ? AND round = ?"

SQL_HN_FROM_IP_PORT_ROUND = "SELECT * FROM hypernodes WHERE ip = ? AND port = ? AND round = ?"

# Incomplete sql for fast batch insert.
SQL_INSERT_HN_VALUES = "INSERT INTO hypernodes (round, address, ip, port, weight, registrar, reward, " \
                       "ts_register, ts_edit, active) VALUES"


class SqliteHNDB(SqliteBase):
    """
    Sqlite storage backend.
    """

    def __init__(self, verbose=False, db_path='./data/', app_log=None, ram=False):
        self.verbose = verbose
        self.app_log = app_log
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
        Async. Empty hypernodes local index

        :return: None
        """
        await self.async_execute(SQL_CLEAR, commit=True)
        # Good time to cleanup
        await self.async_execute("VACUUM", commit=True)

    async def clear_rounds_before(self, a_round):
        """
        Async. Empty history from rounds older than a_round

        :param: a_round: oldest round to keep.
        :return: None
        """
        await self.async_execute(SQL_DEL_OLDER_THAN_ROUND, (a_round,), commit=True)
        # Good time to cleanup
        await self.async_execute("VACUUM", commit=True)

    async def hn_from_address(self, address:str, round:int):
        """
        Async. Return a dict with all info from local hn db

        :param address: pos address of the hn
        :param round: the related round (current one, older rounds may been pruned)
        :return: dict, with keys: address, ip, port, weight, registrar, reward, ts_register, ts_edit,  active
        """

        hn = await self.async_fetchone(SQL_HN_FROM_ADDRESS_ROUND, (address, round), as_dict=True)
        # TEST DEV ONLY
        # hn['port'] = 6969  # instance 0
        return hn

    async def hn_from_peer(self, peer:str, round:int):
        """
        Async. Return a dict with all info from local hn db

        :param peer: a ip:port or ip:00port
        :param round: the related round (current one, older rounds may been pruned)
        :return: dict, with keys: address, ip, port, weight, registrar, reward, ts_register, ts_edit,  active
        """
        ip, port = peer.split(':')
        port = int(port)  # will drop the leading 0s
        hn = await self.async_fetchone(SQL_HN_FROM_IP_PORT_ROUND, (ip, port, round), as_dict=True)
        # TEST DEV ONLY
        # hn['port'] = 6969  # instance 0
        return hn


    async def save_hn_from_regs(self, regs:dict, round:int):
        """
        Async. Stores the HN info from the pow in local index.

        :param regs:  is a dict, with keys = pow address,
        value = dict : 'ip', 'port', 'pos', 'reward', 'weight', 'timestamp', 'active'
        :param round:
        :return:
        """
        values = [" (" + ", ".join([str(round), "'"+value['pos']+"'", "'"+value['ip']+"'", str(value['port']),
                                    str(value['weight']), "'"+registrar+"'", "'"+value['reward']+"'",
                                    str(value['timestamp']), str(0), poshelpers.bool_to_dbstr(value['active'])]) + ") "
                  for registrar, value in regs.items()]
        if len(values):
            values = SQL_INSERT_HN_VALUES + ",".join(values)
            await self.async_execute(values, commit=True)
