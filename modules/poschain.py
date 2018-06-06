"""
A Safe thread/process object interfacing the PoS chain
"""

# import threading
import os
import sys
import json
import sqlite3
import asyncio

# Our modules
import common
import poscrypto
import commands_pb2
from posblock import PosBlock, PosMessage, PosHeight
from sqlitebase import SqliteBase

__version__ = '0.0.5'


SQL_LAST_BLOCK = "SELECT * FROM pos_chain ORDER BY height DESC limit 1"

SQL_INSERT_BLOCK = "INSERT INTO pos_chain VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

SQL_INSERT_TX = "INSERT INTO pos_messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

SQL_TX_FOR_HEIGHT = "SELECT * FROM pos_messages WHERE block_height = ? ORDER BY timestamp ASC"

SQL_TXID_EXISTS = "SELECT txid FROM pos_messages WHERE txid = ?"

SQL_TX_STATS_FOR_HEIGHT = "SELECT COUNT(txid) AS NB, COUNT(DISTINCT(sender)) AS SOURCES FROM pos_messages WHERE block_height = ?"

SQL_STATE_1 = "SELECT height, round, sir, block_hash FROM pos_chain ORDER BY height DESC LIMIT 1"
SQL_HEIGHT_OF_ROUND = "SELECT height FROM pos_chain WHERE round = ? ORDER BY height ASC LIMIT 1"

# TODO: some of these may be costly. check perfs.
SQL_STATE_2 = "SELECT COUNT(DISTINCT(forger)) AS forgers FROM pos_chain"
SQL_STATE_3 = "SELECT COUNT(DISTINCT(forger)) AS forgers_round FROM pos_chain WHERE round = ?"

SQL_STATE_4 = "SELECT COUNT(DISTINCT(sender)) AS uniques FROM pos_messages"
SQL_STATE_5 = "SELECT COUNT(DISTINCT(sender)) AS uniques_round FROM pos_messages WHERE block_height >= ?"

# Block info for a given height. no xx10 info
SQL_INFO_1 = "SELECT height, round, sir, block_hash FROM pos_chain WHERE height = ?"
SQL_INFO_2 = "SELECT COUNT(DISTINCT(forger)) AS forgers FROM pos_chain WHERE height <= ?"
SQL_INFO_4 = "SELECT COUNT(DISTINCT(sender)) AS uniques FROM pos_messages WHERE block_height <= ?"

SQL_BLOCK_SYNC = "SELECT * FROM pos_chain WHERE height >= ? ORDER BY height LIMIT ?"

SQL_ROLLBACK_BLOCK = "DELETE FROM pos_chain WHERE height >= ?"
SQL_ROLLBACK_BLOCKTX = "DELETE FROM pos_messages WHERE block_height >= ?"

""" pos chain db structure """

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
    active_mns TEXT,\
    slots      STRING,\
    test_slots STRING\
    );"

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


class PosChain:
    """
    Generic Class
    """

    def __init__(self, verbose = False, app_log=None, mempool=None):
        self.verbose = verbose
        # self.block_height = 0  # double usage with height_status and block ?
        self.block = None
        self.app_log = app_log
        self.height_status = None
        self.mempool = mempool

    async def status(self):
        print("PosChain Virtual Method Status")

    def genesis_block(self):
        """
        Build up genesis block info
        :return:
        """
        # No tx for genesis
        txids = []
        block_dict = {'height': 0, 'round': 0, 'sir': 0, 'timestamp': common.ORIGIN_OF_TIME,
                      'previous_hash': poscrypto.blake(common.GENESIS_SEED.encode('utf-8')).digest(),
                      'msg_count': 0, 'unique_sources': 0, 'txs': txids, 'forger': common.GENESIS_ADDRESS,
                      'block_hash': b'', 'signature': b''}
        # print(block_dict)
        block = PosBlock().from_dict(block_dict)
        # print(block.to_json())
        block.sign()
        print(block.to_json())
        if self.verbose:
            print(block.to_json())
        return block

    async def insert_block(self, block):
        """
        Saves to block object in db
        :param block: a native PosBlock object
        :return:
        """
        print("PosChain Virtual Method insert_block")

    async def rollback(self, block_count=1):
        """
        revert latest block_count blocks
        :return:
        """
        print("PosChain Virtual Method rollback")

    async def last_block(self):
        """
        Returns last know block as a dict
        :return:
        """
        if not self.block:
            self.block = await self._last_block()
        return self.block

    async def _last_block(self):
        print("PosChain Virtual Method _last_block")

    async def tx_exists(self, txid):
        """
        Tell is the given txid is in our mempool
        :return:
        """
        print("Virtual Method tx_exists")

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
        returns a BlockHeight object with our current state
        :return:
        """
        if not self.height_status:
            self.height_status = await self._height_status()
        return self.height_status

    async def _height_status(self):
        print("Virtual Method async_height")

    async def digest_block(self, proto_block, from_miner=False):
        """
        Checks if the block is valid and saves it
        :param proto_block: a protobuf 'block' object
        :param from_miner: True if came from a live miner (current slot)
        :return:
        """
        try:
            # print(">> protoblock", proto_block)
            block = PosBlock().from_proto(proto_block)
            block_from = 'from Peer'
            if from_miner :
                block_from = 'from Miner'
            self.app_log.warning("Digesting block {} {} : {}".format(block.height, block_from, block.to_json()))
            # Good height? - TODO: harmonize, use objects everywhere?
            if block.height != self.block['height'] + 1:
                self.app_log.error("Digesting block {} : bad height, our current height is {}".format(block.height, self.block['height']))
                return False;
            # Good hash?
            if block.previous_hash != self.block['block_hash']:
                self.app_log.error("Digesting block {} : bad hash {} vs our {}".format(block.height, block.previous_hash, self.block['block_hash']))
                return False;

            # TODO: more checks
            # Checks will depend on from_miner (state = sync) or not (relaxed checks when catching up)
            await self.insert_block(block)
            self.app_log.warning("Digested block {}".format(block.height))
            return True
        except Exception as e:
            self.app_log.error("digest_block Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            return False


class MemoryPosChain(PosChain):
    """
    Memory Storage, POC only
    """

    def __init__(self, verbose = False, app_log=None):
        super().__init__(verbose=verbose, app_log=app_log)
        # Just a list
        self.blocks = [self.genesis_block()]

    async def status(self):
        return self.blocks


class SqlitePosChain(PosChain, SqliteBase):

    def __init__(self, verbose = False, db_path='data/', app_log=None, mempool=None):
        PosChain.__init__(self, verbose=verbose, app_log=app_log, mempool=mempool)
        SqliteBase.__init__(self, verbose=verbose, db_path=db_path, db_name='poc_pos_chain.db', app_log=app_log)

    def check(self):
        """
        Checks and creates db. This is not async yet, so we close afterward.
        :return:
        """
        # Create path
        # Create DB if needed
        # insert genesis block with fixed TS

        self.app_log.info("pos chain Check")
        try:
            if not os.path.isfile(self.db_path):
                res = -1
            else:
                # Test DB
                res = 1
                self.db = sqlite3.connect(self.db_path, timeout=1)
                self.db.text_factory = str
                self.cursor = self.db.cursor()
                # check if db needs recreating
                self.cursor.execute("PRAGMA table_info('addresses')")
                res1 = self.cursor.fetchall()
                print(len(res1), res1)
                if res1 != 5:
                    res = 0
                self.cursor.execute("PRAGMA table_info('pos_chain')")
                res2 = self.cursor.fetchall()
                print(len(res2), res2)
                if res2 != 11:
                    res = 0
                self.cursor.execute("PRAGMA table_info('pos_messages')")
                res3 = self.cursor.fetchall()
                print(len(res3), res3)
                if res3 != 10:
                    res = 0
                self.cursor.execute("PRAGMA table_info('pos_rounds')")
                res4 = self.cursor.fetchall()
                print(len(res4), res4)
                if res4 != 4:
                    res = 0

            # TODO
            """
            5 [(0, 'address', 'VARCHAR (34)', 0, None, 1), (1, 'pubkey', 'BLOB (64)', 0, None, 0), (2, 'ip', 'VARCHAR (32)', 0, None, 0), (3, 'alias', 'VARCHAR (32)', 0, None, 0), (4, 'extra', 'STRING', 0, None, 0)]
            11 [(0, 'height', 'INTEGER', 0, None, 1), (1, 'round', 'INTEGER', 0, None, 0), (2, 'sir', 'INTEGER', 0, None, 0), (3, 'timestamp', 'INTEGER', 0, None, 0), (4, 'previous_hash', 'BLOB (20)', 0, None, 0), (5, 'msg_count', 'INTEGER', 0, None, 0), (6, 'uniques_sources', 'INTEGER', 0, None, 0), (7, 'signature', 'BLOB (64)', 0, None, 0), (8, 'block_hash', 'BLOB (20)', 0, None, 0), (9, 'received_by', 'STRING', 0, None, 0), (10, 'forger', 'VARCHAR (34)', 0, None, 0)]
            10 [(0, 'txid', 'BLOB (64)', 0, None, 1), (1, 'block_height', 'INTEGER', 0, None, 0), (2, 'timestamp', 'INTEGER', 0, None, 0), (3, 'sender', 'VARCHAR (34)', 0, None, 0), (4, 'recipient', 'VARCHAR (34)', 0, None, 0), (5, 'what', 'INTEGER', 0, None, 0), (6, 'params', 'STRING', 0, None, 0), (7, 'value', 'INTEGER', 0, None, 0), (8, 'pubkey', 'BLOB (64)', 0, None, 0), (9, 'received', 'INTEGER', 0, None, 0)]
            4 [(0, 'round', 'INTEGER', 0, None, 1), (1, 'active_mns', 'TEXT', 0, None, 0), (2, 'slots', 'STRING', 0, None, 0), (3, 'test_slots', 'STRING', 0, None, 0)]
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
                self.app_log.info("Status: Recreated poschain database")

            # Now test data
            test = self.execute(SQL_LAST_BLOCK).fetchone()
            if not test:
                # empty db, try to bootstrap - only Genesis MN can do this
                if poscrypto.ADDRESS == common.GENESIS_ADDRESS:
                    gen = self.genesis_block()
                    self.execute(SQL_INSERT_BLOCK, gen.to_db(), commit=True)
                else:
                    self.execute(SQL_INSERT_GENESIS)
                    self.commit()
        except Exception as e:
            self.app_log.error("Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        self.db.close()
        self.db = None
        self.cursor = None

    async def _last_block(self, with_tx=False):
        """
        Returns last know block as a dict
        :return:
        """
        block = await self.async_fetchone(SQL_LAST_BLOCK, as_dict=True)
        # print(block)
        # self.block_height = block['height']
        self.block = block
        return block

    async def status(self):
        last_block = await self.last_block()
        status = {"block_height": last_block['height'], "Genesis": common.GENESIS_ADDRESS}
        height_status = await self.async_height()
        status.update(height_status.to_dict(as_hex=True))
        return status

    async def insert_block(self, block):
        """
        Saves to block object in db
        :param block: a native PosBlock object
        :return:
        """
        # Save the txs
        # TODO: if error inserting block, delete the txs... transaction?
        tx_ids = []
        for tx in block.txs:
            tx_ids.append(tx.txid)
            await self.async_execute(SQL_INSERT_TX, tx.to_db(), commit=False)
        # batch delete from mempool
        if len(tx_ids):
            await self.mempool.async_del_txids(tx_ids)
        # Then the block and commit
        res = await self.async_execute(SQL_INSERT_BLOCK, block.to_db(), commit=True)
        self._invalidate()
        self.block = block.to_dict()
        # force Recalc - could it be an incremental job ?
        await self._height_status()
        return True

    async def rollback(self, block_count=1):
        """
        revert latest block_count blocks
        :return:
        """
        global SQL_ROLLBACK_BLOCK
        global SQL_ROLLBACK_BLOCKTX
        res = await self.async_execute(SQL_ROLLBACK_BLOCK, (self.height_status.height, ), commit=True)
        res = await self.async_execute(SQL_ROLLBACK_BLOCKTX, (self.height_status.height, ), commit=True)
        self._invalidate()
        # force Recalc - could it be an incremental job ?
        await self._last_block()
        await self._height_status()
        return True


    async def tx_exists(self, txid):
        """
        Tell is the given txid is in our chain
        :return:
        """
        exists = await self.async_fetchone(SQL_TXID_EXISTS, (txid, ) )
        if exists:
            self.app_log.info("{} already in our chain".format(txid))
            return True
        return False

    async def _height_status(self):
        """
        returns a BlockHeight object with our current state
        :return:
        """
        global SQL_STATE_1
        global SQL_STATE_2
        global SQL_STATE_3
        global SQL_STATE_4
        global SQL_STATE_5
        if self.height_status:
            # cached info
            return self.height_status
        # Or compute and store
        # TODO: All this need way too many requests. Refactor to a single one, or adjust db structure to alleviate
        # Some things could also be incremental and not queried each time.
        status1 = await self.async_fetchone(SQL_STATE_1, as_dict=True)
        height_of_round = await self.async_fetchone(SQL_HEIGHT_OF_ROUND, (status1['round'], ), as_dict=True)
        # self.app_log.info("Height of round {} is {}".format(status1['round'], height_of_round['height']))
        status2 = await self.async_fetchone(SQL_STATE_2, as_dict=True)
        status1.update(status2)
        status3 = await self.async_fetchone(SQL_STATE_3, (status1['round'], ), as_dict=True)
        status1.update(status3)
        status4 = await self.async_fetchone(SQL_STATE_4, as_dict=True)
        status1.update(status4)
        status5 = await self.async_fetchone(SQL_STATE_5, (height_of_round['height'], ), as_dict=True)
        status1.update(status5)
        # print(status1)
        self.height_status = PosHeight().from_dict(status1)
        return self.height_status

    async def async_blockinfo(self, height):
        """
        Returns partial height info of a given block
        :return:
        """
        global SQL_INFO_1
        global SQL_INFO_2
        global SQL_INFO_4
        status1 = {}
        try:
            status1 = await self.async_fetchone(SQL_INFO_1, (height, ), as_dict=True)
            status2 = await self.async_fetchone(SQL_INFO_2, (height, ), as_dict=True)
            status1.update(status2)
            status4 = await self.async_fetchone(SQL_INFO_4, (height, ), as_dict=True)
            status1.update(status4)
        except:
            pass
        finally:
            if not status1:
                status1 = {}
            height_info = PosHeight().from_dict(status1)
            return height_info

    async def async_blocksync(self, height):
        """
        returns N blocks starting with the given height.
        TODO: Harmonize. this one needs a proto as output (proto command with list of blocks)
        :param height:
        :return:
        """

        """
        self.app_log.error("async_blocksync NOT done yet")
        await asyncio.sleep(10)
        return
        """
        try:
            protocmd = commands_pb2.Command()
            protocmd.Clear()
            protocmd.command = commands_pb2.Command.blocksync

            blocks = await self.async_fetchall(SQL_BLOCK_SYNC, (height, common.BLOCK_SYNC_COUNT))
            for block in blocks:
                block = PosBlock().from_dict(dict(block))
                # Add the block txs
                txs = await self.async_fetchall(SQL_TX_FOR_HEIGHT, (block.height, ))
                for tx in txs:
                    tx = PosMessage().from_dict(dict(tx))
                    block.txs.append(tx)
                block.add_to_proto(protocmd)
            # await asyncio.sleep(1)
            return protocmd

        except Exception as e:
            self.app_log.error("SRV: async_blocksync: Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            raise


if __name__ == "__main__":
    print("I'm a module, can't run!")