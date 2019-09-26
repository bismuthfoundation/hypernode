"""
A Safe thread/process object interfacing the PoS chain
"""

import json
import os
import sqlite3
import sys
from asyncio import get_event_loop, CancelledError
from random import choice
from time import time
from typing import Union

from tornado.iostream import StreamClosedError
from tornado.tcpclient import TCPClient

import com_helpers
import commands_pb2

# Our modules
import config
import poscrypto
import poshelpers
from posblock import PosBlock, PosMessage, PosHeight
from sqlitebase import SqliteBase
from ttlcache import asyncttlcache

__version__ = "0.2.0"


SQL_LAST_BLOCK = "SELECT * FROM pos_chain ORDER BY height DESC limit 1"
# TODO: Benchmark vs "SELECT * FROM pos_chain where height = (select max(height) from pos_chain)"
# and "SELECT * FROM pos_chain where rowid = (select last_insert_rowid() from pos_chain)"  # KO, not the last one

SQL_INSERT_BLOCK = "INSERT INTO pos_chain VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

# Partial sql for batch insert.
SQL_INSERT_INTO_VALUES = (
    "INSERT INTO pos_messages (txid, block_height, timestamp, sender, recipient, what, "
    "params, value, pubkey, received) VALUES "
)

SQL_INSERT_TX = "INSERT INTO pos_messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

SQL_TXS_FOR_HEIGHT = "SELECT * FROM pos_messages WHERE block_height = ? ORDER BY timestamp ASC"

# sender and recipient indices would only really be useful for here
SQL_TXS_FOR_ADDRESS = "SELECT * FROM pos_messages WHERE sender = ? or recipient = ? " \
                      "ORDER BY block_height, timestamp DESC LIMIT 100"

SQL_TXS_FOR_ADDRESS_FROM_HEIGHT = (
    "SELECT * FROM pos_messages WHERE (sender = ? or recipient = ?) "
    "AND block_height >= ? ORDER BY block_height, timestamp ASC LIMIT 100"
)

SQL_TXID_EXISTS = "SELECT txid FROM pos_messages WHERE txid = ?"

SQL_TX_FOR_TXID = "SELECT * FROM pos_messages WHERE txid = ?"

SQL_TX_STATS_FOR_HEIGHT = (
    "SELECT COUNT(txid) AS NB, COUNT(DISTINCT(sender)) AS SOURCES FROM pos_messages "
    "WHERE block_height = ?"
)

# TODO: bench vs SELECT height, round, sir, block_hash FROM pos_chain
# WHERE height = (select max(height) from pos_chain) limit 1
# to use covering index
SQL_STATE_1 = "SELECT height, round, sir, block_hash FROM pos_chain ORDER BY height DESC LIMIT 1"  # FR: opt

# Q: duplicate round in pos_messages table to avoid these extra requests?
SQL_HEIGHT_OF_ROUND = "SELECT height FROM pos_chain WHERE round = ? ORDER BY height ASC LIMIT 1"

SQL_LAST_HEIGHT_OF_ROUND = "SELECT height FROM pos_chain WHERE round = ? ORDER BY height DESC LIMIT 1"

SQL_LAST_HEIGHT_BEFORE_ROUND = "SELECT height FROM pos_chain WHERE round < ? ORDER BY height DESC LIMIT 1"

SQL_LAST_ROUND_AND_HEIGHT_BEFORE_HEIGHT = "SELECT round, height FROM pos_chain " \
                                          "WHERE height <= ? ORDER BY height DESC LIMIT 1"

SQL_LAST_HASH_OF_ROUND = "SELECT block_hash FROM pos_chain WHERE round = ? ORDER BY height DESC LIMIT 1"

SQL_MINMAXHEIGHT_OF_ROUNDS = "SELECT min(height) as min, max(height) as max " \
                             "FROM pos_chain WHERE round >= ? and round <= ?"

# TODO: these request is huge and slows down everything.
SQL_STATE_2_REPLACE = "SELECT COUNT(DISTINCT(forger)) AS forgers FROM pos_chain"

SQL_STATE_3 = "SELECT COUNT(DISTINCT(forger)) AS forgers_round FROM pos_chain WHERE round = ?"

# TODO: these request is huge and slows down everything.
SQL_STATE_4_REPLACE = "SELECT COUNT(DISTINCT(sender)) AS uniques FROM pos_messages"  # uses sender as covering index

SQL_STATE_5 = "SELECT COUNT(DISTINCT(sender)) AS uniques_round FROM pos_messages WHERE block_height >= ?"
# Uses block_height index, not sender. Ok because it's for last round, so few pos_messages are concerned.

# Block info for a given height. no xx10 info
SQL_INFO_1 = "SELECT height, round, sir, block_hash FROM pos_chain WHERE height = ?"
# TODO: these 2 requests are huge and slow down everything.
SQL_INFO_2_REPLACE = "SELECT COUNT(DISTINCT(forger)) AS forgers FROM pos_chain WHERE height <= ?"
SQL_INFO_4_REPLACE = "SELECT COUNT(DISTINCT(sender)) AS uniques FROM pos_messages WHERE block_height <= ?"

# New requests to incrementaly determine chain stats
SQL_FORGERS_BETWEEN_HEIGHTS_INCLUDED = "SELECT DISTINCT(forger) AS forgers FROM pos_chain WHERE height >= ? AND height <= ?"
SQL_SENDERS_BETWEEN_HEIGHTS_INCLUDED = "SELECT DISTINCT(sender) AS uniques FROM pos_messages WHERE block_height >= ? AND block_height <= ?"

SQL_BLOCKS_SYNC = "SELECT * FROM pos_chain WHERE height >= ? ORDER BY height LIMIT ?"
SQL_BLOCKS_LAST = "SELECT * FROM pos_chain ORDER BY height DESC LIMIT ?"
SQL_ROUND_BLOCKS = "SELECT * FROM pos_chain WHERE round = ? ORDER BY height ASC"
SQL_HEIGHT_BLOCK = "SELECT * FROM pos_chain WHERE height = ? LIMIT 1"

SQL_ROLLBACK_BLOCKS = "DELETE FROM pos_chain WHERE height >= ?"
SQL_ROLLBACK_BLOCKS_TXS = "DELETE FROM pos_messages WHERE block_height >= ?"

SQL_DELETE_BLOCK = "DELETE FROM pos_chain WHERE height = ?"
SQL_DELETE_BLOCK_TXS = "DELETE FROM pos_messages WHERE block_height = ?"

SQL_COUNT_TX_FOR_HEIGHT = "SELECT COUNT(*) FROM pos_messages WHERE block_height = ?"

SQL_COUNT_DISTINCT_BLOCKS_IN_MESSAGES = "SELECT COUNT(DISTINCT(block_height)) FROM pos_messages"

SQL_DELETE_ROUND_TXS = "DELETE FROM pos_messages WHERE block_height IN (SELECT height FROM pos_chain WHERE round = ?)"

SQL_DELETE_ROUND = "DELETE FROM pos_chain WHERE round = ?"

SQL_DELETE_LIST_TXS = "DELETE FROM pos_messages WHERE block_height IN ({})"

SQL_DELETE_LIST = "DELETE FROM pos_chain WHERE height IN ({})"

SQL_ROUNDS_FORGERS = "SELECT DISTINCT(forger) FROM pos_chain WHERE round >= ? AND round <= ?"

SQL_ROUNDS_SOURCES = "SELECT DISTINCT(sender) FROM pos_messages WHERE block_height >= ? AND block_height <= ?"

# ----------------- KPIs -----------------

SQL_ROUNDS_FORGERS_COUNT = (
    "SELECT forger, count(*) as blocks FROM pos_chain "
    "WHERE round >= ? AND round <= ? GROUP BY forger"
)

SQL_ROUNDS_SOURCES_COUNT = (
    "SELECT sender, count(*) as messages FROM pos_messages "
    "WHERE block_height >= ? AND block_height <= ? GROUP BY sender"
)

# recipient=self.address, what=202, params='START'
SQL_ROUNDS_START_COUNT = (
    "SELECT sender, count(*) as messages FROM pos_messages "
    "WHERE block_height >= ? AND block_height <= ? "
    "AND what=202 and params='START' GROUP BY sender"
)

# recipient=self.address, what=201, params='NO_TEST:2'/ NO_TEST:1
SQL_ROUNDS_NO_TESTS_COUNT = (
    "SELECT sender, count(*) as messages FROM pos_messages "
    "WHERE block_height >= ? AND block_height <= ? "
    "AND what=201 GROUP BY sender"
)

# test[1], 202
SQL_ROUNDS_OK_TESTS_COUNT = (
    "SELECT sender, count(*) as messages FROM pos_messages "
    "WHERE block_height >= ? AND block_height <= ? "
    "AND what=202 and params != 'START' GROUP BY sender"
)

# test[1], 204
SQL_ROUNDS_KO_TESTS_COUNT = (
    "SELECT sender, count(*) as messages FROM pos_messages "
    "WHERE block_height >= ? AND block_height <= ? "
    "AND what=204 GROUP BY sender"
)

# hn['address'], what=200, params='R.SYNC:{}' or C.SYNC
SQL_ROUNDS_OK_ACTION_COUNT = (
    "SELECT recipient, count(*) as messages FROM pos_messages "
    "WHERE block_height >= ? AND block_height <= ? "
    "AND what=200 GROUP BY recipient"
)

# hn['address'], what=101, params='P.FAIL:{}' or C.FAIL - Only count one sender per round to avoid flood from broken HNs
SQL_ROUNDS_KO_ACTION_COUNT = (
    "SELECT recipient, count(distinct(sender)) as messages FROM pos_messages "
    "WHERE block_height >= ? AND block_height <= ? "
    "AND what=101 GROUP BY recipient"
)

# hn['address'], what=101, params='P.FAIL:{}' or C.FAIL - Only count one recipient per round
SQL_ROUNDS_KO2_ACTION_COUNT = (
    "SELECT sender, count(distinct(recipient)) as messages FROM pos_messages "
    "WHERE block_height >= ? AND block_height <= ? "
    "AND what=101 GROUP BY sender"
)

""" pos chain db structure """

# TODO: Index missing!!!

SQL_CREATE_ADDRESSES = "CREATE TABLE addresses (\
    address VARCHAR (34) PRIMARY KEY,\
    pubkey  BLOB (64),\
    ip      VARCHAR (32),\
    alias   VARCHAR (32),\
    extra   STRING\
    );"

SQL_CREATE_POS_CHAIN = "CREATE TABLE pos_chain (\
    height          INTEGER      PRIMARY KEY,\
    round           INTEGER,\
    sir             INTEGER,\
    timestamp       INTEGER,\
    previous_hash   BLOB (20),\
    msg_count       INTEGER,\
    uniques_sources INTEGER,\
    signature       BLOB (64),\
    block_hash      BLOB (20),\
    received_by     VARCHAR34,\
    forger          VARCHAR (34),\
    UNIQUE (\
        round,\
        sir\
    )\
    ON CONFLICT FAIL\
    );"

SQL_CREATE_POS_MESSAGES = "CREATE TABLE pos_messages (\
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

SQL_CREATE_POS_ROUNDS = "CREATE TABLE pos_rounds (\
    round      INTEGER PRIMARY KEY,\
    active_hns TEXT,\
    slots      STRING,\
    test_slots STRING\
    );"

# POC GENESIS
"""
SQL_INSERT_GENESIS = "INSERT INTO pos_chain (forger, received_by, block_hash,\
                          signature, uniques_sources, msg_count, previous_hash,\
                          timestamp, sir, round, height) VALUES (\
                          'BLYkQwGZmwjsh7DY6HmuNBpTbqoRqX14ne',\
                          NULL,\
                          X'9094D7B35AC3E924C20545486F75D6E10C8B1EA7',\
                          X'323C6766C8C0267C6CB5B8D4161F1D4E0F7DB0F64DD52942A086240AE9561B2D2A3E1DC91FEBBF83C636E7E092931E8FD96E2EB4103BA466C225128A6339F9B7',\
                          0,\
                          0,\
                          X'C0CB310E2877D73E2F29A949AABB8FEF0EA00EDF',\
                          1522419000,\
                          0,\
                          0,\
                          0\
                      );\
                    "
"""

# Real settings genesis
SQL_INSERT_GENESIS = """INSERT INTO pos_chain (
                          forger,
                          received_by,
                          block_hash,
                          signature,
                          uniques_sources,
                          msg_count,
                          previous_hash,
                          timestamp,
                          sir,
                          round,
                          height
                      )
                      VALUES (
                          'BKYnuT4Pt8xfZrSKrY3mUyf9Cd9qJmTgBn',
                          '',
                          X'87D5AD9988B88DDA92AA988267E30C89479FC2D2',
                          X'4F9BE873ED7F4EF047ABEE6A2266C7586B019CB69D76B782988A574642604C5F31CE7597A49E018F76253C1418CB0549A3B8DB3D42453C661C15EEE8A62D4215',
                          0,
                          0,
                          X'C0CB310E2877D73E2F29A949AABB8FEF0EA00EDF',
                          1534716000,
                          0,
                          0,
                          0
                      );

                    """

# Dict of index name: create sql
SQL_INDICES = {
    "round": "CREATE INDEX round ON pos_chain (round)",
    "height_ts": "CREATE INDEX height_ts ON pos_messages (block_height, timestamp)",
    "recipient": "CREATE INDEX recipient ON pos_messages (recipient)",
    "sender": "CREATE INDEX sender ON pos_messages (sender)",
}


HN_CACHE_DIR = "./.cache/"


class SqlitePosChain(SqliteBase):
    def __init__(self, verbose=False, db_path="data/", app_log=None, mempool=None):
        self.custom_data_dir = db_path
        self.verbose = verbose
        # self.block_height = 0  # double usage with height_status and block ?
        self.block = None
        self.app_log = app_log
        self.height_status = None
        self.mempool = mempool
        # Avoid re-entrance
        self.inserting_block = False
        self.bans = {"huge_blocks": [],
                    "duptx_blocks": [],
                    "partial_blocks": []}
        self.last_cache_cleanup = 0
        self.purge_cache()
        self.debug = None
        self.last_debug_load = 0
        self.check_debug()
        # Each ban entry is a list of list: [end_timestamp, block_hash(hex), peer_ip] - peer_ip is only needed for partial_blocks entry
        SqliteBase.__init__(
            self,
            verbose=verbose,
            db_path=db_path,
            db_name="poc_pos_chain.db",
            app_log=app_log,
        )
        try:
            os.mkdir(HN_CACHE_DIR)
        except:
            pass

    def purge_bans(self) -> None:
        """Check time of bans to clear them
        These lists are supposed to be very short, empty most of the time so this is not intensive a process.
        """
        now = time()
        for key in ("huge_blocks", "duptx_blocks", "partial_blocks"):
            # keep only the valid ones (in the future)
            self.bans[key] = [entry for entry in self.bans[key] if entry[0] > now]

    def is_banned(self, block_hash: str) -> bool:
        """Tells whether that block hash is banned or not"""
        for key in ("huge_blocks", "duptx_blocks"):
            for entry in self.bans[key]:
                if entry[1] == block_hash:
                    return True
        return False

    def ban_hash(self, block_hash: str, key:str="duptx_blocks", ttl: int=15*60) -> None:
        """Ban a block hash for ttl seconds"""
        self.bans[key].append([time()+ttl, block_hash])

    def check_debug(self):
        try:
            if config.DEBUG_MODE:
                if self.last_debug_load < os.path.getmtime("debug.json"):
                    with open("debug.json") as fp:
                        self.debug = json.load(fp)
                    self.last_debug_load = time()
        except:
            pass

    def get_debug(self, key: str):
        """Safe read access to debug dict"""
        if self.debug is None:
            return None
        try:
            return self.debug.get(key)
        except:
            return None

    def missing_blocks(self) -> set:
        """
        Not in async mode yet. id the missing or corrupted block so we can fix them.
        returns a set of heights
        """
        missings = set()
        sql = "SELECT MAX(height) FROM pos_chain"
        res = self.execute(sql)
        max_height = res.fetchone()[0]
        # print("max_height", max_height)
        # sys.exit()
        sql1 = "SELECT msg_count FROM pos_chain WHERE height=?"
        sql2 = "SELECT count(*) FROM pos_messages WHERE block_height=?"
        for height in range(max_height - 1):
            # self.app_log.info("Trying to add missing {}...".format(height))
            # get txn count from header
            res = self.execute(sql1, (height,))
            temp = res.fetchone()
            if temp is None:
                missings.add(height)
                # print("Height {} is None".format(height))
            msg_count1 = temp[0] if temp else 0
            # get txn count from pos_messages
            res = self.execute(sql2, (height,))
            temp = res.fetchone()
            msg_count2 = temp[0] if temp else 0
            if msg_count1 != msg_count2:
                # print("{}: {} - {}".format(height, msg_count1, msg_count2))
                missings.add(height)
        return missings

    def check_block_hash(self, block: PosBlock) -> bool:
        raw = block.to_raw()
        msg_count = len(block.txs)
        # set removes duplicates.
        block.uniques_sources = len(set([tx.sender for tx in block.txs]))
        # TODO: verify sig signature = poscrypto.sign(raw, verify=True)
        block_hash = poscrypto.blake(raw).digest()
        if msg_count != block.msg_count:
            print("Bad Txn count")
            return False
        if 90000 < block.height < 105000:
            # hack to cope with corrupted blocks at that time.
            return True
        return block_hash == block.block_hash

    def direct_insert_block(self, block):
        """
        Saves block object to file db - mostly copy from async code

        :param block: a native PosBlock object
        :return:
        """
        # Save the txs
        # TODO: if error inserting block, delete the txs... transaction?
        tx_ids = []
        # this is now an array of array. batch store the txs.
        str_txs = []
        batch = []
        batch_count = 0
        if block.height in [76171]:
            # Delete the existing block
            sql1 = "DELETE from pos_messages WHERE block_height=?"
            self.execute(sql1, (block.height,))
            self.commit()
        else:
            for tx in block.txs:
                if tx.block_height != block.height:
                    print(
                        "TX had bad height {} instead of {}, fixed. - TODO: do not digest?".format(
                            tx.block_height, block.height
                        )
                    )
                    return
                    # tx.block_height = block.height
                temp = tx.to_str_list()
                if temp[0] in tx_ids:
                    print(temp[0], "Double!!")
                else:
                    tx_ids.append(temp[0])
                    batch.append(" (" + ", ".join(temp) + ") ")
                    batch_count += 1
                    if batch_count >= 100:
                        str_txs.append(batch)
                        batch_count = 0
                        batch = []
                # optimize push in a batch and do a single sql with all tx in a row
                # await self.async_execute(SQL_INSERT_TX, tx.to_db(), commit=False)
            # print(tx_ids)
            # Delete the existing block
            sql1 = "DELETE from pos_messages WHERE block_height=?"
            self.execute(sql1, (block.height,))
            self.commit()
            if len(batch):
                str_txs.append(batch)
            if len(tx_ids):
                if block.uniques_sources < 2:
                    print("block unique sources seems incorrect")
                    return
                # TODO: halt on these errors? Will lead to db corruption. No, because should have been tested by digest?
                if block.msg_count != len(tx_ids):
                    print("block msg_count seems incorrect")
                    return
                try:
                    for batch in str_txs:
                        # TODO: there is some mess here, some batches do not go through.
                        values = SQL_INSERT_INTO_VALUES + ",".join(batch)
                        self.execute(values)
                        self.commit()
                except Exception as e:
                    print(e)
                    return
        sql2 = "DELETE from pos_chain WHERE height=?"
        self.execute(sql2, (block.height,))
        self.commit()
        # Then the block and commit
        self.execute(SQL_INSERT_BLOCK, block.to_db())
        self.commit()
        return True

    async def get_block_again(self, block_height: int) -> bool:
        """Try to get the missing or corrupted local blocks from other reference peers."""
        if block_height == 76171:
            # TODO: special processing TBD
            return True
        try:
            self.app_log.info("Trying to get missing block {}".format(block_height))
            previous_block = PosBlock()
            sql = "SELECT * FROM pos_chain WHERE height=?"
            res = self.execute(sql, (block_height - 1,))
            previous = dict(res.fetchone())
            previous_block.from_dict(previous)
            # print(previous)
            peers = ("192.99.248.44", "91.121.87.99", "192.99.34.19")
            peer = choice(peers)
        except Exception as e:
            # We get an exception there if the previous block was not found in our chain
            # (Then we can't be sure this one would be good)
            self.app_log.warning("get_block_again: Missing predecessor of {}".format(block_height))
            return
            """
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))
            raise
            """
        try:
            stream = await TCPClient().connect(peer, 6969, timeout=45)
            hello_string = poshelpers.hello_string(port=6969, address=poscrypto.ADDRESS)
            full_peer = "{}:{}".format(peer, 6969)
            await com_helpers.async_send_string(
                commands_pb2.Command.hello, hello_string, stream, full_peer
            )
            msg = await com_helpers.async_receive(stream, full_peer, timeout=45)
            # print("Client got {}".format(com_helpers.cmd_to_text(msg.command)))
            if msg.command == commands_pb2.Command.hello:
                # decompose posnet/address and check.
                if "hello" in config.LOG:
                    print("Client got Hello {} from {}".format(msg.string_value, full_peer))
                # self.clients[full_peer]['hello'] = msg.string_value  # nott here, it's out of the client biz
            if msg.command == commands_pb2.Command.ko:
                self.app_log.info("Client got Ko {}".format(msg.string_value))
                return False
            # now we can enter a long term relationship with this node.
            await com_helpers.async_send_int32(
                commands_pb2.Command.getblock, block_height, stream, full_peer
            )
            msg = await com_helpers.async_receive(stream, full_peer, timeout=45)
            block = PosBlock()
            block.from_proto(msg.block_value[0])
            # print(block.to_dict(as_hex=True))
            if block_height == 76171:  # Broken block
                ok = True
            else:
                ok = self.check_block_hash(block)
            if not ok:
                self.app_log.info("Block {} hash KO".format(block_height))
                return False
            if block.previous_hash != previous_block.block_hash:
                self.app_log.info("Block {} does not fit previous block".format(block_height))
                return False
            # Ok, insert
            self.direct_insert_block(block)
            return True

        except StreamClosedError as e:
            # print(e)
            return False
        except Exception as e:
            """
            print("get_block_again2: {}".format(str(e)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))
            """
            return False
            # raise

    def check(self):
        """
        Checks and creates db. This is not async yet, so we close afterward.

        :return:
        """
        # Create path
        # Create DB if needed
        # insert genesis block with fixed TS
        if self.app_log:
            self.app_log.info("pos chain Check")
        try:
            if not os.path.isfile(self.db_path):
                res = -1
            else:
                # Test DB
                res = 1
                self.db = sqlite3.connect(self.db_path, timeout=1)
                self.db.text_factory = str
                self.db.row_factory = sqlite3.Row
                self.cursor = self.db.cursor()
                # check if db needs recreating
                self.cursor.execute("PRAGMA table_info('addresses')")
                res1 = self.cursor.fetchall()
                ## print(len(res1), res1)
                if res1 != 5:
                    res = 0
                self.cursor.execute("PRAGMA table_info('pos_chain')")
                res2 = self.cursor.fetchall()
                # print(len(res2), res2)
                if res2 != 11:
                    res = 0
                self.cursor.execute("PRAGMA table_info('pos_messages')")
                res3 = self.cursor.fetchall()
                # print(len(res3), res3)
                if res3 != 10:
                    res = 0
                self.cursor.execute("PRAGMA table_info('pos_rounds')")
                res4 = self.cursor.fetchall()
                # print(len(res4), res4)
                if res4 != 4:
                    res = 0

            """
            5 [(0, 'address', 'VARCHAR (34)', 0, None, 1), (1, 'pubkey', 'BLOB (64)', 0, None, 0), (2, 'ip', 
            'VARCHAR (32)', 0, None, 0), (3, 'alias', 'VARCHAR (32)', 0, None, 0), (4, 'extra', 'STRING', 0, None, 0)]
            11 [(0, 'height', 'INTEGER', 0, None, 1), (1, 'round', 'INTEGER', 0, None, 0), (2, 'sir', 'INTEGER', 0, 
            None, 0), (3, 'timestamp', 'INTEGER', 0, None, 0), (4, 'previous_hash', 'BLOB (20)', 0, None, 0), (5, 
            'msg_count', 'INTEGER', 0, None, 0), (6, 'uniques_sources', 'INTEGER', 0, None, 0), (7, 'signature', 
            'BLOB (64)', 0, None, 0), (8, 'block_hash', 'BLOB (20)', 0, None, 0), (9, 'received_by', 'STRING', 0, 
            None, 0), (10, 'forger', 'VARCHAR (34)', 0, None, 0)]
            10 [(0, 'txid', 'BLOB (64)', 0, None, 1), (1, 'block_height', 'INTEGER', 0, None, 0), (2, 'timestamp', 
            'INTEGER', 0, None, 0), (3, 'sender', 'VARCHAR (34)', 0, None, 0), (4, 'recipient', 'VARCHAR (34)', 0, 
            None, 0), (5, 'what', 'INTEGER', 0, None, 0), (6, 'params', 'STRING', 0, None, 0), (7, 'value', 'INTEGER', 
            0, None, 0), (8, 'pubkey', 'BLOB (64)', 0, None, 0), (9, 'received', 'INTEGER', 0, None, 0)]
            4 [(0, 'round', 'INTEGER', 0, None, 1), (1, 'active_hns', 'TEXT', 0, None, 0), (2, 'slots', 'STRING', 0, 
            None, 0), (3, 'test_slots', 'STRING', 0, None, 0)]
            """

            if res == -1:
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
                self.execute(SQL_CREATE_ADDRESSES)
                self.execute(SQL_CREATE_POS_CHAIN)
                self.execute(SQL_CREATE_POS_MESSAGES)
                self.execute(SQL_CREATE_POS_ROUNDS)
                self.commit()
                if self.app_log:
                    self.app_log.info("Status: Recreated poschain database")
            # check and add missing indices
            for name, sql_add_index in SQL_INDICES.items():
                if not self.index_exists(name):
                    self.execute(sql_add_index)
                    self.commit()
                    self.app_log.info("Status: Added {} index".format(name))
            # Now test data
            test = self.execute(SQL_LAST_BLOCK).fetchone()
            if not test:
                # empty db, try to bootstrap - only Genesis HN can do this
                if poscrypto.ADDRESS == config.GENESIS_ADDRESS:
                    gen = self.genesis_block()
                    self.execute(SQL_INSERT_BLOCK, gen.to_db(), commit=True)
                    if com_helpers.MY_NODE:
                        com_helpers.MY_NODE.stop()
                    else:
                        sys.exit()
                else:
                    self.execute(SQL_INSERT_GENESIS)
                    self.commit()
            else:
                # fail safe: delete tx more recent than lastheight
                self.execute(
                    SQL_ROLLBACK_BLOCKS_TXS, (test[0] + 1,), commit=True
                )  # Unwanted: this closes the cursor?!?
                # sys.exit()
            missing_blocks = sorted(list(self.missing_blocks()))
            # print("Missing1:", missing_blocks)
            test2 = self.execute(SQL_COUNT_DISTINCT_BLOCKS_IN_MESSAGES).fetchone()
            test2 = test2[0] if test2 else 0
            if 76171 in missing_blocks:
                # Ignore that missing one, broken block net-wide.
                test2 += 1
            if test2 != test[0]:
                self.app_log.warning(
                    "Inconsistency height {} but only messages for {}".format(
                        test[0], test2
                    )
                )
            loop = get_event_loop()
            for block_height in missing_blocks:
                try:
                    loop.run_until_complete(self.get_block_again(block_height))
                except:
                    pass
            # self.app_log.warning("Hopefully fixed corrupted blocks 1/2")
            missing_blocks = sorted(list(self.missing_blocks()))

            # print("Missing2:", missing_blocks)
            # TODO: factorize in a loop, try 3 times maybe, use more default seeders..
            for block_height in missing_blocks:
                try:
                    loop.run_until_complete(self.get_block_again(block_height))
                except:
                    pass
            # self.app_log.warning("Hopefully fixed corrupted blocks 2/2")
            # Remove offending 104021 block if present
            hash104021 = self.execute("select block_hash from pos_chain where height=104021").fetchone()
            hash104021 = hash104021[0] if hash104021 else None
            if hash104021 == b'n\x07:\xfa\xbe\xb1\xfa\xf4t\x1e\xf9\x90\xd8g\xe4=i\x91\xdb\xa2':
                self.app_log.warning("Removing offending block")
                self.execute("delete from pos_chain where height>104020")
                self.execute("delete from pos_messages where block_height>104020")
                self.commit()
            # Remove offending 104070 block if present
            hash104070 = self.execute("select block_hash from pos_chain where height=104070").fetchone()
            hash104070 = hash104070[0] if hash104070 else None
            if hash104070 == b'\xf6\xbdj\xa4\x139\xfagsRg\x00\x97\x94ge\xa9\x98\x08\xca':
                self.app_log.warning("Removing offending block")
                self.execute("delete from pos_chain where height>=104070")
                self.execute("delete from pos_messages where block_height>=104070")
                self.commit()
            # Remove offending 104160 block if present
            hash104160 = self.execute("select block_hash from pos_chain where height=104160").fetchone()
            hash104160 = hash104160[0] if hash104160 else None
            if hash104160 == b'g\x87\x14\xe2wF\x9d|8\x9eE8\x87D6Xa\xdd)y':
                self.app_log.warning("Removing offending block")
                self.execute("delete from pos_chain where height>=104160")
                self.execute("delete from pos_messages where block_height>=104160")
                self.commit()

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            if self.app_log:
                self.app_log.error("Error {}".format(e))
                self.app_log.error(
                    "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
                )
            else:
                print("Error {}".format(e))
                print("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))

        finally:
            if self.db:
                self.db.commit()
                self.db.close()
                self.db = None
                self.cursor = None
            self.app_log.warning("Poschain check end")

    def genesis_block(self):
        """
        Build up genesis block info

        :return:
        """
        # No tx for genesis
        txids = []
        block_dict = {
            "height": 0,
            "round": 0,
            "sir": 0,
            "timestamp": config.ORIGIN_OF_TIME,
            "previous_hash": poscrypto.blake(
                config.GENESIS_SEED.encode("utf-8")
            ).digest(),
            "msg_count": 0,
            "uniques_sources": 0,
            "txs": txids,
            "forger": config.GENESIS_ADDRESS,
            "block_hash": b"",
            "signature": b"",
        }
        # print(block_dict)
        block = PosBlock().from_dict(block_dict)
        # print(block.to_json())
        block.sign()
        # print(block.to_json())
        if self.verbose:
            print(block.to_json())
        return block

    async def last_block(self):
        """
        Returns last know block as a dict

        :return:
        """
        if not self.block:
            self.block = await self._last_block()
        return self.block

    def _invalidate(self):
        """
        Something changed in our chain, invalidate the status.
        It will then be recalc when needed.

        :return:
        """
        self.height_status = None
        self.block = None

    async def async_height(self):
        """
        Returns a BlockHeight object with our current state

        :return:
        """
        if not self.height_status:
            self.height_status = await self._height_status()
        return self.height_status

    async def digest_block(self, proto_block, from_miner=False, relaxed_checks=False) -> bool:
        """
        Checks if the block is valid and saves it

        :param proto_block: a protobuf 'block' object
        :param from_miner: True if came from a live miner (current slot)
        :param relaxed_checks: True if we want light checks (like our own block)

        :return:
        """
        self.purge_bans()
        try:
            block_from = "from Peer"
            if from_miner:
                block_from = "from Miner"
            if relaxed_checks:
                block_from += " (Relaxed checks)"
            # Avoid re-entrance
            if self.inserting_block:
                self.app_log.warning("Digestion of block {} aborted, already digesting".format(block_from))
                return False
            start = time()
            # print(">> protoblock", proto_block)
            block = PosBlock().from_proto(proto_block)
            if self.is_banned(block.block_hash):
                self.app_log.warning("Digestion of block {} {} aborted, banned {}".format(block.height, block_from, block.block_hash.hex()))
                return False

            # print(">> dictblock", block.to_dict())
            if "txdigest" in config.LOG:
                self.app_log.info(
                    "Digesting block {} {} : {}".format(
                        block.height, block_from, block.to_json()
                    )
                )
            else:
                # TODO: this is upside down. fix all config.LOG items
                self.app_log.info(
                    "Digesting block {} {} : {} txs, {} uniques sources ({} async_uniques_at_height).".format(
                        block.height, block_from, len(block.txs), block.uniques_sources, block.block_hash.hex()
                    )
                )
            # Good height? - FR: harmonize, use objects everywhere?
            if block.height != self.block["height"] + 1:
                self.app_log.warning(
                    "Digesting block {} : bad height, our current height is {}".format(
                        block.height, self.block["height"]
                    )
                )
                return False
            # Good hash?
            if block.previous_hash != self.block["block_hash"]:
                self.app_log.warning(
                    "Digesting block {} : bad hash {} vs our {}".format(
                        block.height, block.previous_hash, self.block["block_hash"]
                    )
                )
                return False
            if block.msg_count != len(block.txs):
                self.app_log.warning(
                    "Digesting block {} : {} txs reported but {} included".format(
                        block.height, block.msg_count, len(block.txs)
                    )
                )
                if block.height != 76171:
                    # bad hack for edge case
                    return False
            # TODO: more checks
            # TODO: like, rechecking the tx hash....
            # TODO: if from miner, make sure we refreshed the round first.
            # timestamp of blocks
            # fits with current round?
            # TODO : only tx from valid HNs (registered for that round?)
            # recount uniques_sources?
            # msg_count = tx# ?
            # right juror?
            # Checks will depend on from_miner (state = sync) or not (relaxed checks when catching up)
            # see also tx checks from mempool. Maybe lighter
            self.inserting_block = True
            res = await self._insert_block(block)  # returns with a 'sqlite3.IntegrityError' from a bad block
            if res:
                self.app_log.info(
                    "Digested block {} in {:0.2f} sec.".format(block.height, time() - start)
                )
            else:
                self.app_log.warning(
                    "Digest block {} failed in {:0.2f} sec.".format(block.height, time() - start)
                )
            return res

        except sqlite3.IntegrityError as e:
            try:
                height, hash = block.height, block.block_hash
            except:
                height = -1
                hash = 'N/A'
                pass
            self.app_log.error("digest_block {} integrity error hash {} - banning".format(height, hash.hex()))
            self.ban_hash(hash.hex())
            return False
        except Exception as e:
            try:
                height, hash = block.height, block.block_hash
            except:
                height = -1
                hash = 'N/A'
                pass
            self.app_log.error("digest_block {} Error {}, hash {}".format(height, e, hash))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            return False
        finally:
            self.inserting_block = False

    async def check_round(
        self, a_round: int, blocks: commands_pb2.Command, fast_check: bool = True
    ):
        """
        Given a round number and all blocks for this round, checks that these blocks are valid candidates.
        Does not modify the chain, can be used on existing current round to check validity alternate chains.

        :param a_round:
        :param blocks: a protobuf
        :param fast_check:
        :return: a height dict, containing the simulated final state of the chain, or False if blocks are not valid.

        ``{'height': 3631, 'round': 6420, 'sir': 1, 'block_hash': 'a03ffeea35a48f0773bc993289213c3c72165ee0',
        'uniques': 4, 'uniques_round': 0, 'forgers': 4, 'forgers_round': 1, 'count': 0, 'peers': []'``
        """
        try:
            start_time = time()
            if self.verbose:
                self.app_log.info("check_round start {:0.2f}".format(time()))
            # Get the last block of the a-round -1 round from our chain
            height = await self.async_height_of_round(a_round)
            # print("\nheight", height)
            # get height stats at that level - TODO: that's CPU intensive. Can we cache that somehow?
            # Will always be stats at end of a round, called multiple times with same info when swapping chains in a round.
            # Only the latest height is needed, we won't need previous height afterward. 1 cache slot is enough.
            # only called from here, can do naive cache.
            ref_height_dict = await self.async_blockinfo(height)  # TODO: That's the intensive part
            ref_height = PosHeight().from_dict(ref_height_dict)
            # print("\nref_height", ref_height.to_dict(as_hex=True))
            # for each block, validate and inc stats
            uniques_round = []
            forgers_round = []
            ref_blockheight = ref_height.height
            ref_hash = ref_height.block_hash
            end_block = None
            for block in blocks.block_value:
                """
                if self.verbose:
                    self.app_log.info(
                        "check_round block {} : {:0.2f}".format(block.height, time())
                    )
                """
                # Good height?
                if block.height != ref_blockheight + 1:
                    self.app_log.warning(
                        "Checking block {} : bad height, ref height is {}".format(
                            block.height, ref_blockheight
                        )
                    )
                    return False
                # Good hash?
                if block.previous_hash != ref_hash:
                    self.app_log.warning(
                        "Checking block {} : bad hash {} vs our {}".format(
                            block.height, block.previous_hash, ref_hash
                        )
                    )
                    return False
                # right count of txs?
                if block.msg_count != len(block.txs):
                    self.app_log.warning(
                        "Checking block {} : tx count mismatch {} vs announced {}".format(
                            block.height, len(block.txs), block.msg_count
                        )
                    )
                    return False
                # count uniques
                if block.forger not in forgers_round:
                    forgers_round.append(block.forger)
                if block.txs:
                    for tx in block.txs:
                        if tx.sender not in uniques_round:
                            uniques_round.append(tx.sender)
                # move to next block
                ref_blockheight += 1
                ref_hash = block.block_hash
                end_block = block  # So we can access it out of the loop.
            ref_height.height = end_block.height
            ref_height.round = end_block.round
            ref_height.sir = end_block.sir
            ref_height.block_hash = end_block.block_hash
            ref_height.uniques_round = len(uniques_round)
            ref_height.forgers_round = len(forgers_round)
            # Beware: uniques and forgers (not _round) are not good since this would mean recount all since the begin
            # with both sqlite and local data, too costly.
            # print(">> final_height", ref_height.to_dict(as_hex=True))
            if self.verbose:
                self.app_log.info(
                    "check_round done in {}s.".format(time() - start_time)
                )
            # return Simulated height.
            return ref_height.to_dict(as_hex=True)
        except CancelledError:
            self.app_log.error("check_round Cancelled")
            return False
        except Exception as e:
            self.app_log.error("check_round Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            return False

    async def _last_block(self, with_tx=False):
        """
        Returns last know block as a dict

        :return:
        """
        block = await self.async_fetchone(SQL_LAST_BLOCK, as_dict=True)
        # print("last block", block)
        # self.block_height = block['height']
        self.block = block
        return block

    async def status(self):
        last_block = await self.last_block()
        status = {
            "block_height": last_block["height"],
            "Genesis": config.GENESIS_ADDRESS,
        }
        height_status = await self.async_height()
        status.update(height_status.to_dict(as_hex=True))
        return status

    async def _insert_block(self, block):
        """
        Saves block object to file db

        :param block: a native PosBlock object
        :return: True of False
        """
        # Save the txs
        # TODO: if error inserting block, delete the txs... transaction?
        try:
            height = block.height
        except:
            self.app_log.error("No height for block")
            return False
        try:
            tx_ids = []
            bin_txids = []
            start_time = time()
            # this is now an array of array. batch store the txs.
            str_txs = []
            batch = []
            batch_count = 0
            for tx in block.txs:
                if tx.block_height != block.height:
                    self.app_log.warning(
                        "TX had bad height {} instead of {}, fixed. - TODO: do not digest?".format(
                            tx.block_height, block.height
                        )
                    )
                    tx.block_height = block.height
                temp = tx.to_str_list()
                tx_ids.append(temp[0])
                bin_txids.append(tx.txid)

                batch.append(" (" + ", ".join(temp) + ") ")
                batch_count += 1
                if batch_count >= 100:
                    str_txs.append(batch)
                    batch_count = 0
                    batch = []
                # optimize push in a batch and do a single sql with all tx in a row
                # await self.async_execute(SQL_INSERT_TX, tx.to_db(), commit=False)
            if len(batch):
                str_txs.append(batch)
            if len(tx_ids):

                if block.uniques_sources < 2:
                    self.app_log.error("block {} unique sources seems incorrect".format(block.height))
                    return False
                if block.msg_count < config.REQUIRED_MESSAGES_PER_BLOCK:
                    self.app_log.error("Not enough txs in block {}".format(block.height))
                    return False
                # TODO: halt on these errors? Will lead to db corruption. No, because should have been tested by digest?
                if block.msg_count != len(tx_ids):
                    self.app_log.error("block {} msg_count seems incorrect, corrupted".format(block.height))
                    return False

                if "timing" in config.LOG or "blockdigest" in config.LOG:
                    self.app_log.warning(
                        "TIMING: poschain create sql for {} txs : {} sec".format(
                            len(tx_ids), time() - start_time
                        )
                    )
                    start_time = time()
                # print(values)
                # Make sure there are no tx left from something else
                await self.async_execute(SQL_DELETE_BLOCK_TXS, (block.height,))
                if "timing" in config.LOG or "blockdigest" in config.LOG:
                    self.app_log.warning(
                        "TIMING: poschain delete block txs: {} sec".format(
                            time() - start_time
                        )
                    )
                    start_time = time()

                for batch in str_txs:
                    # TODO: there is some mess here, some batches do not go through.
                    values = SQL_INSERT_INTO_VALUES + ",".join(batch)
                    await self.async_execute(values, commit=True)

            if "timing" in config.LOG or "blockdigest" in config.LOG:
                self.app_log.warning(
                    "TIMING: poschain _insert {} tx: {} sec".format(
                        len(tx_ids), time() - start_time
                    )
                )
                start_time = time()
            # batch delete from mempool
            if len(bin_txids) and self.mempool:
                await self.mempool.async_del_txids(bin_txids)
            if "timing" in config.LOG or "blockdigest" in config.LOG:
                self.app_log.warning(
                    "TIMING: mempool del: {} sec".format(time() - start_time)
                )
                start_time = time()
            # Double check we have the right number of stored txs
            saved = await self.async_fetchone(SQL_COUNT_TX_FOR_HEIGHT, (block.height,))
            if "timing" in config.LOG or "blockdigest" in config.LOG:
                self.app_log.warning(
                    "TIMING: safety check: {} sec".format(time() - start_time)
                )
                start_time = time()
            if saved[0] != block.msg_count:
                # We did not save all we wanted to.
                self.app_log.error(
                    "Error while saving block {}: only {}/{} saved txns".format(
                        block.height, saved[0], block.msg_count
                    )
                )
                # Delete leftover
                await self.async_execute(
                    SQL_DELETE_BLOCK_TXS, (block.height,), commit=True
                )
                # Delete the block also
                await self.async_execute(SQL_DELETE_BLOCK, (block.height,), commit=True)
                return False

            # Then the block and commit
            # First remove it in case it exists.
            await self.async_execute(SQL_DELETE_BLOCK, (block.height,))
            if "timing" in config.LOG or "blockdigest" in config.LOG:
                self.app_log.warning(
                    "TIMING: delete block: {} sec".format(time() - start_time)
                )
                start_time = time()

            await self.async_execute(SQL_INSERT_BLOCK, block.to_db(), commit=True)
            if "timing" in config.LOG or "blockdigest" in config.LOG:
                self.app_log.warning(
                    "TIMING: insert block {}: {} sec".format(height, time() - start_time)
                )
                start_time = time()
            self._invalidate()
            self.block = block.to_dict()
            # force Recalc - could it be an incremental job ?
            await self._height_status()
            if "timing" in config.LOG or "blockdigest" in config.LOG:
                self.app_log.warning(
                    "TIMING: recalc status: {} sec".format(time() - start_time)
                )
            return True
        except sqlite3.IntegrityError as e:
            # Let level above catch?
            await self.async_execute(SQL_DELETE_BLOCK_TXS, (height,))
            await self.async_execute(SQL_DELETE_BLOCK, (height,), commit=True)
            raise
        except Exception as e:
            self.app_log.error("_insert_block {} Error {}".format(height, e))
            await self.async_execute(SQL_DELETE_BLOCK_TXS, (height,))
            await self.async_execute(SQL_DELETE_BLOCK, (height,), commit=True)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            raise

    async def _insert_block_old(self, block):
        """
        Saves block object to file db

        :param block: a native PosBlock object
        :return:
        """
        # Save the txs
        # TODO: if error inserting block, delete the txs... transaction?
        tx_ids = []
        start_time = time()
        params = []
        for tx in block.txs:
            if tx.block_height != block.height:
                self.app_log.warning(
                    "TX had bad height {} instead of {}, fixed. - TODO: do not digest?".format(
                        tx.block_height, block.height
                    )
                )
                tx.block_height = block.height
            tx_ids.append(tx.txid)
            # TODO: do a single insert
            params.append(tx.to_db())
            # optimize push in a batch and do a single sql with all tx in a row
            # await self.async_execute(SQL_INSERT_TX, tx.to_db(), commit=False)
        if len(tx_ids):
            if block.uniques_sources < 2:
                self.app_log.error("block unique sources seems incorrect")
        # TODO: halt on these errors? Will lead to db corruption. No, because should have been tested by digest?
        if block.msg_count != len(tx_ids):
            self.app_log.error("block msg_count seems incorrect")

        if "timing" in config.LOG:
            self.app_log.warning(
                "TIMING: poschain create sql for {} txs : {} sec".format(
                    len(tx_ids), time() - start_time
                )
            )

        await self.async_execute(SQL_INSERT_TX, tuple(params), commit=True, many=True)
        if "timing" in config.LOG:
            self.app_log.warning(
                "TIMING: poschain _insert {} tx: {} sec".format(
                    len(tx_ids), time() - start_time
                )
            )
        # batch delete from mempool
        if len(tx_ids) and self.mempool:
            await self.mempool.async_del_txids(tx_ids)
        if "timing" in config.LOG:
            self.app_log.warning(
                "TIMING: poschain _insert after mempool del: {} sec".format(
                    time() - start_time
                )
            )
        # Then the block and commit
        await self.async_execute(SQL_INSERT_BLOCK, block.to_db(), commit=True)
        if "timing" in config.LOG:
            self.app_log.warning(
                "TIMING: poschain _insert after block: {} sec".format(
                    time() - start_time
                )
            )
        self._invalidate()
        self.block = block.to_dict()
        # force Recalc - could it be an incremental job ?
        await self._height_status()
        if "timing" in config.LOG:
            self.app_log.warning(
                "TIMING: poschain _insert after recalc status: {} sec".format(
                    time() - start_time
                )
            )
        return True

    async def rollback(self, block_count=1):
        """
        revert latest block_count blocks

        :return:
        """
        # FR: block_count not used
        res = await self.async_execute(
            SQL_ROLLBACK_BLOCKS, (self.height_status.height,), commit=True
        )
        if not res:
            self.app_log.error(
                "Error rollback block {}".format(self.height_status.height)
            )
        # TODO: this deletes the TX, but we want to move them back to mempool I suppose
        # Since they were already validated, do not recheck again, only that they are no in poschain.
        res = await self.async_execute(
            SQL_ROLLBACK_BLOCKS_TXS, (self.height_status.height,), commit=True
        )
        if not res:
            self.app_log.error(
                "Error rollback block txs {}".format(self.height_status.height)
            )
        self._invalidate()
        # force Recalc - could it be an incremental job ?
        last = await self._last_block()
        await self._height_status()
        asyncttlcache.purge()
        self.delete_rounds_above(last["round"])
        return True

    async def tx_exists(self, txid):
        """
        Tell if the given txid is in our chain

        :return:
        """
        # TODO: WARNING, see binary blob sqlite3 and conversion. Seems ok, double check
        # self.app_log.warning("tx_exists?")
        # print(txid)  # debug
        # What is fed to this function? Bytes or hex string?
        exists = await self.async_fetchone(SQL_TXID_EXISTS, (txid,))
        if exists:
            if "txdigest" in config.LOG:
                self.app_log.info(
                    "{}[...] already in our chain".format(
                        poscrypto.raw_to_hex(txid)[:16]
                    )
                )
            return True
        return False

    async def delete_blocks(self, a_list_of_height: list) -> None:
        """
        Remove header and transactions data for this list
        The caller is responsible for updating state if necessary

        :param a_list_of_height:
        :return: None
        """
        # First delete the tx
        # TODO: this deletes the TX, but we want to move them back to mempool !important
        # Make sure we only have ints and convert to str
        a_list_of_height = [str(int(h)) for h in a_list_of_height]
        in_str = ",".join(a_list_of_height)
        await self.async_execute(SQL_DELETE_LIST_TXS.format(in_str), commit=True)
        # Then the block data itself
        await self.async_execute(SQL_DELETE_LIST.format((in_str)), commit=True)
        # reset status so future block digestions will be ok.
        self._invalidate()
        asyncttlcache.purge()

    async def delete_round(self, a_round):
        """
        Remove round and transactions data for this round
        The caller is responsible for updating state if necessary

        :param a_round:
        :return: None
        """
        # First delete the tx
        # TODO: this deletes the TX, but we want to move them back to mempool !important
        # TEMP
        self.app_log.warning("TEMP: Delete round {}".format(a_round))
        await self.async_execute(SQL_DELETE_ROUND_TXS, (a_round,), commit=True)
        # Then the block data itself
        await self.async_execute(SQL_DELETE_ROUND, (a_round,), commit=True)
        # reset status so future block digestions will be ok.
        self._invalidate()
        asyncttlcache.purge()

    async def _height_status(self):
        """
        returns a BlockHeight object with our current state

        :return:
        """
        # global SQL_STATE_1
        # global SQL_STATE_2
        # global SQL_STATE_3
        # global SQL_STATE_4
        # global SQL_STATE_5
        if self.height_status:
            # cached info
            return self.height_status
        # Or compute and store
        # FR: All this needs way too many requests. Refactor to a single one, or adjust db structure to alleviate
        # Some things could also be incremental and not queried each time.
        # TODO: wrap in try/except and log when error, happen on rollback block 0, maybe at other times.
        status1 = await self.async_fetchone(SQL_STATE_1, as_dict=True)
        height_of_round = await self.async_fetchone(
            SQL_HEIGHT_OF_ROUND, (status1["round"],), as_dict=True
        )
        # self.app_log.info("Height of round {} is {}".format(status1['round'], height_of_round['height']))

        uniques = await self.async_uniques_at_height(height_of_round["height"])

        status1["uniques"] = len(uniques["senders"])
        if config.TEST_ROUND_CACHE:
            status2 = await self.async_fetchone(SQL_STATE_2_REPLACE, as_dict=True)
            if status2["uniques"] != status1["uniques"]:
                self.app_log.error("Round cache error uniques, sql {} vs cache {}".format(status2["uniques"], status1["uniques"]))
            status1.update(status2)

        status3 = await self.async_fetchone(
            SQL_STATE_3, (status1["round"],), as_dict=True
        )
        status1.update(status3)

        status1["forgers"] = len(uniques["forgers"])
        if config.TEST_ROUND_CACHE:
            status4 = await self.async_fetchone(SQL_STATE_4_REPLACE, as_dict=True)
            if status4["forgers"] != status1["forgers"]:
                self.app_log.error("Round cache error forgers , sql {} vs cache {}".format(status4["forgers"], status1["forgers"]))
            status1.update(status4)

        status5 = await self.async_fetchone(
            SQL_STATE_5, (height_of_round["height"],), as_dict=True
        )
        status1.update(status5)
        # print(">>> ", status1, len(uniques['forgers']), len(uniques["senders"]), '*Fake')
        #
        self.height_status = PosHeight().from_dict(status1)
        return self.height_status

    async def async_round_and_height_before_height(self, height: int):
        res = await self.async_fetchone(SQL_LAST_ROUND_AND_HEIGHT_BEFORE_HEIGHT, (height,), as_dict=True)
        height = res.get("height")
        a_round = res.get("round")
        return a_round, height

    async def async_height_of_round(self, pos_round: int):
        """height at start of the round (no bloc yet)"""
        res = await self.async_fetchone(SQL_LAST_HEIGHT_BEFORE_ROUND, (pos_round,), as_dict=True)
        height = res.get("height")
        return height

    # ------------------------ NEW CACHE -------------------------------------------

    def uniques_and_round_from_cache(self, pos_round) -> tuple:
        """given a pos round, gives the unique lists at *start* of round (no block yet)"""
        all_cache = os.listdir(HN_CACHE_DIR)
        rounds = [int(file[:-11]) for file in all_cache]  # strip .round.json
        rounds = sorted(rounds, reverse=True)
        uniques = {"forgers": [], "senders": []}
        checkpoint = 0
        try:
            for a_round in rounds:
                if a_round <= pos_round:
                    with open("{}{}.round.json".format(HN_CACHE_DIR, a_round)) as fp:
                        uniques = json.load(fp)
                        self.app_log.warning("Found cached round {}".format(a_round))
                        return uniques, a_round
        except Exception as e:
            self.app_log.warning("Error reading round {} cache: {}".format(a_round, e))
        return uniques, checkpoint

    def delete_rounds_above(self, pos_round):
        """deletes rounds above (and including) given round from cache"""
        all_cache = os.listdir(HN_CACHE_DIR)
        rounds = [int(file[:-5]) for file in all_cache]  # strip .json
        rounds = [num for num in rounds if num >= pos_round]  # filter rounds to delete
        for num in rounds:
            os.remove("{}{}.round.json".format(HN_CACHE_DIR, num))

    def purge_cache(self):
        """empty cache every 23h of run to avoid drifts"""
        if time() - self.last_cache_cleanup > 3600 * 23:
            all_cache = os.listdir(HN_CACHE_DIR)
            self.app_log.info("Purge cache: {} files".format(len(all_cache)))
            for file in all_cache:
                os.remove("{}/{}".format(HN_CACHE_DIR, file))
            self.last_cache_cleanup = time()

    async def __async_uniques_at_round(self, pos_round: int):
        """
        Calcs forged and uniques from live data and file cache/
        :param pos_round:
        :return:
        """

    async def async_uniques_at_height(self, pos_height: int):
        """
        Uses partial info from previous round, then complete with latest info
        :param pos_height:
        :return:
        """
        try:
            pos_round, pos_round_height = await self.async_round_and_height_before_height(pos_height)
            uniques, round_checkpoint = self.uniques_and_round_from_cache(pos_round)
            self.app_log.info("async_uniques_at_height {}: round {} checkpoint {}".format(pos_height, pos_round, round_checkpoint))
            uniques['forgers'] = set(uniques['forgers'])
            uniques['senders'] = set(uniques['senders'])
            if round_checkpoint < pos_round:
                start = time()
                # Extract the data from checkpoint to start of pos_round...
                # We first need the height of the last round before pos_round
                try:
                    pos_checkpoint_height = await self.async_height_of_round(round_checkpoint)
                except:
                    pos_checkpoint_height = 0
                round_height = await self.async_height_of_round(pos_round)
                forgers = await self.async_fetchall(SQL_FORGERS_BETWEEN_HEIGHTS_INCLUDED, (pos_checkpoint_height + 1, round_height))
                senders = await self.async_fetchall(SQL_SENDERS_BETWEEN_HEIGHTS_INCLUDED, (pos_checkpoint_height + 1, round_height))
                # Then merge...
                uniques['forgers'] = uniques['forgers'].union([forger[0] for forger in forgers])
                uniques['senders'] = uniques['senders'].union([sender[0] for sender in senders])
                # and save as new cache for round pos_round
                with open("{}{}.round.json".format(HN_CACHE_DIR, pos_round), 'w') as fp:
                    # a set is not json serializable.
                    json.dump({key: list(value) for key, value in uniques.items()}, fp)
                # sys.exit()
                delta = time() - start
                self.app_log.info("async_uniques_at_height {}: round {} calc'd in {:0.2f}s".format(pos_height, pos_round, delta))
            if pos_round_height < pos_height:
                # we want more, include the current round info
                forgers = await self.async_fetchall(SQL_FORGERS_BETWEEN_HEIGHTS_INCLUDED,
                                                    (pos_round_height + 1, pos_height), as_dict=True)
                senders = await self.async_fetchall(SQL_SENDERS_BETWEEN_HEIGHTS_INCLUDED,
                                                    (pos_round_height + 1, pos_height), as_dict=True)
                print(forgers)
                # Then merge...
                uniques['forgers'] = uniques['forgers'].union([forger[0] for forger in forgers])
                uniques['senders'] = uniques['senders'].union([sender[0] for sender in senders])
            return uniques

            # Now check if we wanted more than that (like extra blocks after pos_round, to reach pos_height
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            raise

    async def async_trim_uniques_cache(self, a_round: int=0, height: int=0):
        """
        Purge cached info more recent than given a_round or height.
        Only one param is supposed to be given, round will be derived from height if height is given.
        height will be ignored if a_round is given.

        :param a_round:
        :param height:
        :return:
        """
        # TODO
        pass

    async def async_purge_uniques_cache(self):
        """
        Clean up - keeps at most 255 most recent cache files.
        :return:
        """
        # TODO
        pass

    # @asyncttlcache(ttl=3600*4)
    async def async_blockinfo(self, height: int) -> dict:
        """
        Returns partial height info of a given block

        :return:
        """
        # global SQL_INFO_1
        # global SQL_INFO_2
        # global SQL_INFO_4
        uniques = await self.async_uniques_at_height(height)
        status1 = {}
        try:
            status1 = await self.async_fetchone(SQL_INFO_1, (height,), as_dict=True)
            if config.TEST_ROUND_CACHE:
                # Forgers
                status2 = await self.async_fetchone(SQL_INFO_2_REPLACE, (height,), as_dict=True)
                status1.update(status2)
                # uniques
                status4 = await self.async_fetchone(SQL_INFO_4_REPLACE, (height,), as_dict=True)
                status1.update(status4)
                if status1["forgers"] != len(uniques['forgers']) or  status1["uniques"] != len(uniques['senders']):
                    # print(">>>2 ", status1, len(uniques['forgers']), len(uniques["senders"]))
                    self.app_log.error("Round cache fail sql {} vs forgers {} uniques {}".format(json.dumps(status1), len(uniques['forgers']), len(uniques["senders"])))
            else:
                status1["forgers"] = len(uniques['forgers'])
                status1["uniques"] = len(uniques['senders'])
        except:
            pass
        finally:
            if not status1:
                status1 = {}
            # height_info = PosHeight().from_dict(status1)
            # return height_info
            return status1

    async def async_blocksync(self, height):
        """
        returns N blocks starting with the given height.

        FR: Harmonize. this one needs a proto as output (proto command with list of blocks)

        :param height:
        :return:
        """
        try:
            protocmd = commands_pb2.Command()
            protocmd.Clear()
            protocmd.command = commands_pb2.Command.blocksync

            blocks = await self.async_fetchall(
                SQL_BLOCKS_SYNC, (height, config.BLOCK_SYNC_COUNT)
            )
            for block in blocks:
                block = PosBlock().from_dict(dict(block))
                # Add the block txs
                txs = await self.async_fetchall(SQL_TXS_FOR_HEIGHT, (block.height,))
                for tx in txs:
                    tx = PosMessage().from_dict(dict(tx))
                    block.txs.append(tx)
                # check block integrity
                if len(txs) != block.msg_count:
                    self.app_log.error(
                        "Only {} tx for block {} instead of {} announced".format(
                            len(txs), height, block.msg_count
                        )
                    )
                    raise ValueError("Corrupted block {} - ignoring.".format(height))
                    """
                    if height != 76171:
                        # bad hack to cover an edge case.
                        # bad hack to cover an edge case.
                        com_helpers.MY_NODE.stop()
                    """
                block.add_to_proto(protocmd)
            # print(protocmd)
            return protocmd
        except Exception as e:
            self.app_log.error("SRV: async_blocksync: Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            raise

    async def async_roundblocks(self, a_round):
        """
        Command id 13
        returns all blocks of the given round.

        FR: Harmonize. this one needs a proto as output (proto command with list of blocks)

        :param a_round:
        :return: protocmd with all blocks
        """
        try:
            protocmd = commands_pb2.Command()
            protocmd.Clear()
            protocmd.command = commands_pb2.Command.roundblocks

            blocks = await self.async_fetchall(SQL_ROUND_BLOCKS, (a_round,))
            for block in blocks:
                block = PosBlock().from_dict(dict(block))
                # Add the block txs
                txs = await self.async_fetchall(SQL_TXS_FOR_HEIGHT, (block.height,))
                for tx in txs:
                    tx = PosMessage().from_dict(dict(tx))
                    block.txs.append(tx)
                block.add_to_proto(protocmd)
                # check block integrity
                if len(txs) != block.msg_count:
                    self.app_log.error(
                        "Only {} tx for block {} instead of {} announced".format(
                            len(txs), block.height, block.msg_count
                        )
                    )
                    raise ValueError(
                        "Corrupted block {} - ignoring.".format(block.height)
                    )
                    # com_helpers.MY_NODE.stop()

            return protocmd

        except Exception as e:
            self.app_log.error("SRV: async_roundblocks: Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            raise

    async def async_getblock(self, a_height):
        """
        Command id 14
        returns the block of the given height.

        :param a_height: int
        :return: protocmd with the block if exists or None
        """
        try:
            protocmd = commands_pb2.Command()
            protocmd.Clear()
            protocmd.command = commands_pb2.Command.getblock

            block = await self.async_fetchone(
                SQL_HEIGHT_BLOCK, (a_height,), as_dict=True
            )
            if not block:
                return protocmd
            block = PosBlock().from_dict(dict(block))
            # Add the block txs
            txs = await self.async_fetchall(SQL_TXS_FOR_HEIGHT, (block.height,))
            for tx in txs:
                tx = PosMessage().from_dict(dict(tx))
                block.txs.append(tx)
            block.add_to_proto(protocmd)
            return protocmd

        except Exception as e:
            self.app_log.error("SRV: async_getblock: Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            raise

    async def async_getblockheader(self, a_height):
        """
        returns the block header of the given height, no tx

        :param a_height: int
        :return: dict with the block header if exists or None
        """
        try:
            block = await self.async_fetchone(
                SQL_HEIGHT_BLOCK, (a_height,), as_dict=True
            )
            return block

        except Exception as e:
            self.app_log.error("SRV: async_getblockheader: Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            raise

    async def async_getaddtxs(self, params):
        """
        Command id 15
        returns a list of txs.

        :param params: str: an address or address,extra
        :return: protocmd with the txs list or None
        """
        try:
            protocmd = commands_pb2.Command()
            protocmd.Clear()
            protocmd.command = commands_pb2.Command.getaddtxs
            if "," not in params:
                # address only
                txs = await self.async_fetchall(SQL_TXS_FOR_ADDRESS, (params, params))
            else:
                address, option = params.split(",")
                if len(option) < 10:
                    # Say this is a block height
                    option = int(option)
                    txs = await self.async_fetchall(
                        SQL_TXS_FOR_ADDRESS_FROM_HEIGHT, (address, address, option)
                    )
                else:
                    # consider as a tx signature
                    # FR: not sure this param useful after all
                    option = poscrypto.hex_to_raw(str(option))
                    # Get the height of the given signature
                    tx = await self.async_fetchone(
                        SQL_TX_FOR_TXID, (sqlite3.Binary(option),), as_dict=True
                    )
                    # Then the following txs
                    txs = await self.async_fetchall(
                        SQL_TXS_FOR_ADDRESS_FROM_HEIGHT,
                        (address, address, tx.get("block_height")),
                    )
            # Fill the protobuf in
            for tx in txs:
                tx = PosMessage().from_dict(dict(tx))
                tx.add_to_proto(protocmd)

            return protocmd

        except Exception as e:
            self.app_log.error("SRV: async_getaddtxs: Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            raise

    async def async_gettx(self, params):
        """
        Command id 16
        returns the tx or empty protocmd.

        :param params: str: a transaction signature
        :return: protocmd with the tx or None
        """
        try:
            protocmd = commands_pb2.Command()
            protocmd.Clear()
            protocmd.command = commands_pb2.Command.gettx
            txid = poscrypto.hex_to_raw(str(params))
            tx = await self.async_fetchone(
                SQL_TX_FOR_TXID, (sqlite3.Binary(txid),), as_dict=True
            )
            if tx:
                tx = PosMessage().from_dict(dict(tx))
                tx.add_to_proto(protocmd)
            return protocmd

        except Exception as e:
            self.app_log.error("SRV: async_gettx: Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            raise

    async def async_getheaders(self, param):
        """
        Async. Return 20 latest block headers.

        :param param: (string) empty: last 20 blocks headers. start_height,count or ,count (last N headers)
        :return:
        """
        try:
            protocmd = commands_pb2.Command()
            protocmd.Clear()
            protocmd.command = commands_pb2.Command.getheaders
            if param is None or param == "None":
                param = ""
            if param == "":
                blocks = await self.async_fetchall(
                    SQL_BLOCKS_LAST, (config.BLOCK_SYNC_COUNT,)
                )
            else:
                start, count = param.split(",")
                if "" == start:
                    blocks = await self.async_fetchall(SQL_BLOCKS_LAST, (count,))
                else:
                    blocks = await self.async_fetchall(SQL_BLOCKS_SYNC, (start, count))
            for block in blocks:
                block = PosBlock().from_dict(dict(block))
                block.add_to_proto(protocmd)
            return protocmd
        except Exception as e:
            self.app_log.error("SRV: async_getheaders: Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            raise

    async def async_active_hns(self, start_round, end_round=0):
        """
        Returns a list of active HN for the round range.

        :param start_round:
        :param end_round: optional, will use start_round if = 0
        :return: list of PoS addresses
        """
        if not end_round:
            end_round = start_round
        forgers = await self.async_fetchall(
            SQL_ROUNDS_FORGERS, (start_round, end_round)
        )
        forgers = [list(forger)[0] for forger in forgers]
        h_min, h_max = await self.async_fetchone(
            SQL_MINMAXHEIGHT_OF_ROUNDS, (start_round, end_round)
        )
        # print("minmax", h_min, h_max)
        sources = await self.async_fetchall(SQL_ROUNDS_SOURCES, (h_min, h_max))
        if sources:
            sources = [list(source)[0] for source in sources]
            forgers.extend(list(sources))
        # Uniques only
        return list(set(forgers))

    async def async_active_hns_details(self, start_round, end_round=0):
        """
        Returns a list of active HN for the round range with several metrics.

        :param start_round:
        :param end_round: optional, will use start_round if = 0
        :return: dict(PoS addresses = dict())
        """
        if not end_round:
            end_round = start_round
        forgers = await self.async_fetchall(
            SQL_ROUNDS_FORGERS_COUNT, (start_round, end_round)
        )
        # print(dict(forgers))
        res = {
            forger: {"forged": value, "sources": 0}
            for forger, value in dict(forgers).items()
        }
        # print("res forge", res)
        h_min, h_max = await self.async_fetchone(
            SQL_MINMAXHEIGHT_OF_ROUNDS, (start_round, end_round)
        )
        print("min, max", h_min, h_max)
        sources = await self.async_fetchall(SQL_ROUNDS_SOURCES_COUNT, (h_min, h_max))
        for address, sources in dict(sources).items():
            if address in res:
                res[address]["sources"] = sources
            else:
                res[address] = {"sources": sources, "forged": 0}
        # This means only nodes who sent at least a transaction for the round will be evaluated.
        sources = await self.async_fetchall(SQL_ROUNDS_OK_ACTION_COUNT, (h_min, h_max))
        for address, sources in dict(sources).items():
            if address in res:
                res[address]["ok_actions_received"] = sources
            else:
                # With that, half stuck nodes still get rewarded for ok actions.
                # temp. workaround until pos net stabilizes.
                res[address] = {
                    "sources": 0,
                    "forged": 0,
                    "ok_actions_received": sources,
                }

        sources = await self.async_fetchall(SQL_ROUNDS_START_COUNT, (h_min, h_max))
        for address, sources in dict(sources).items():
            if address in res:
                res[address]["start_count"] = sources

        sources = await self.async_fetchall(SQL_ROUNDS_NO_TESTS_COUNT, (h_min, h_max))
        for address, sources in dict(sources).items():
            if address in res:
                res[address]["no_tests_sent"] = sources

        sources = await self.async_fetchall(SQL_ROUNDS_OK_TESTS_COUNT, (h_min, h_max))
        for address, sources in dict(sources).items():
            if address in res:
                res[address]["ok_tests_sent"] = sources

        sources = await self.async_fetchall(SQL_ROUNDS_KO_TESTS_COUNT, (h_min, h_max))
        for address, sources in dict(sources).items():
            if address in res:
                res[address]["ko_tests_sent"] = sources

        sources = await self.async_fetchall(SQL_ROUNDS_KO_ACTION_COUNT, (h_min, h_max))
        for address, sources in dict(sources).items():
            if address in res:
                res[address]["ko_actions_received"] = sources

        # TODO: move in a metric of its own so we can warn
        sources = await self.async_fetchall(SQL_ROUNDS_KO2_ACTION_COUNT, (h_min, h_max))
        for address, sources in dict(sources).items():
            if address in res:
                res[address]["ko_actions_received"] = sources + res[address].get(
                    "ko_actions_received", 0
                )

        # print("res forge", res)
        # sys.exit()
        return res

    async def last_hash_of_round(self, a_round: int) -> Union[bytes, None]:
        last_hash = await self.async_fetchone(SQL_LAST_HASH_OF_ROUND, (a_round,))
        if last_hash:
            return last_hash[0]
        return None


if __name__ == "__main__":
    print("I'm a module, can't run!")
