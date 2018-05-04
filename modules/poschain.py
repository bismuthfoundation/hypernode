"""
A Safe thread/process object interfacing the PoS chain
"""

# import threading
import json
import sqlite3


# Our modules
import common
import poscrypto
from posblock import PosBlock, PosMessage
from sqlitebase import SqliteBase

__version__ = '0.0.4'


SQL_CREATE_POSCHAIN = ""

SQL_LAST_BLOCK = "SELECT * FROM pos_chain ORDER BY height DESC limit 1"

SQL_INSERT_BLOCK = "INSERT INTO pos_chain VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

SQL_INSERT_TX = "INSERT INTO pos_messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

SQL_TX_FOR_HEIGHT = "SELECT * FROM pos_messages WHERE block_height = ? ORDER BY timestamp ASC"

SQL_TX_STATS_FOR_HEIGHT = "SELECT COUNT(txid) AS NB, COUNT(DISTINCT(sender)) AS SOURCES FROM pos_messages WHERE block_height = ? "


class PosChain:
    """
    Generic Class
    """

    def __init__(self, verbose = False, app_log=None):
        self.verbose = verbose
        self.block_height = 0
        self.app_log = app_log

    def status(self):
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

    async def last_block(self):
        """
        Returns last know block as a dict
        :return:
        """
        print("PosChain Virtual Method last_block")


class MemoryPosChain(PosChain):
    """
    Memory Storage, POC only
    """

    def __init__(self, verbose = False, app_log=None):
        super().__init__(verbose=verbose, app_log=app_log)
        # Just a list
        self.blocks = [self.genesis_block()]

    def status(self):
        return json.dumps(self.blocks)


class SqlitePosChain(PosChain, SqliteBase):

    def __init__(self, verbose = False, db_path='data/', app_log=None):
        PosChain.__init__(self, verbose=verbose, app_log=app_log)
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
        # Create DB
        self.db = sqlite3.connect(self.db_path, timeout=1)
        self.db.text_factory = str
        self.cursor = self.db.cursor()
        # check if db needs recreating
        self.cursor.execute("PRAGMA table_info('addresses')")
        res = self.cursor.fetchall()
        #print(len(res), res)
        self.cursor.execute("PRAGMA table_info('pos_chain')")
        res = self.cursor.fetchall()
        #print(len(res), res)
        self.cursor.execute("PRAGMA table_info('pos_messages')")
        res = self.cursor.fetchall()
        #print(len(res), res)
        self.cursor.execute("PRAGMA table_info('pos_rounds')")
        res = self.cursor.fetchall()
        #print(len(res), res)
        # TODO
        """
        5 [(0, 'address', 'VARCHAR (34)', 0, None, 1), (1, 'pubkey', 'BLOB (64)', 0, None, 0), (2, 'ip', 'VARCHAR (32)', 0, None, 0), (3, 'alias', 'VARCHAR (32)', 0, None, 0), (4, 'extra', 'STRING', 0, None, 0)]
        11 [(0, 'height', 'INTEGER', 0, None, 1), (1, 'round', 'INTEGER', 0, None, 0), (2, 'sir', 'INTEGER', 0, None, 0), (3, 'timestamp', 'INTEGER', 0, None, 0), (4, 'previous_hash', 'BLOB (20)', 0, None, 0), (5, 'msg_count', 'INTEGER', 0, None, 0), (6, 'uniques_sources', 'INTEGER', 0, None, 0), (7, 'signature', 'BLOB (64)', 0, None, 0), (8, 'block_hash', 'BLOB (20)', 0, None, 0), (9, 'received_by', 'STRING', 0, None, 0), (10, 'forger', 'VARCHAR (34)', 0, None, 0)]
        10 [(0, 'txid', 'BLOB (64)', 0, None, 1), (1, 'block_height', 'INTEGER', 0, None, 0), (2, 'timestamp', 'INTEGER', 0, None, 0), (3, 'sender', 'VARCHAR (34)', 0, None, 0), (4, 'recipient', 'VARCHAR (34)', 0, None, 0), (5, 'what', 'INTEGER', 0, None, 0), (6, 'params', 'STRING', 0, None, 0), (7, 'value', 'INTEGER', 0, None, 0), (8, 'pubkey', 'BLOB (64)', 0, None, 0), (9, 'received', 'INTEGER', 0, None, 0)]
        4 [(0, 'round', 'INTEGER', 0, None, 1), (1, 'active_mns', 'TEXT', 0, None, 0), (2, 'slots', 'STRING', 0, None, 0), (3, 'test_slots', 'STRING', 0, None, 0)]
        """

        """
        if len(res) != 10:
            self.db.close()
            os.remove(self.db_path)
            self.db = sqlite3.connect(self.db_path, timeout=1)
            self.db.text_factory = str
            self.cursor = self.db.cursor()
            self.execute(SQL_CREATE_MEMPOOL)
            self.commit()
            self.app_log.info("Status: Recreated mempool file")
        """
        test = self.execute(SQL_LAST_BLOCK).fetchone()
        if not test:
            # empty db, try to bootstrap
            gen = self.genesis_block()
            self.execute(SQL_INSERT_BLOCK, gen.to_db(), commit=True)

        self.db.close()
        self.db = None
        self.cursor = None

    async def last_block(self, with_tx=False):
        """
        Returns last know block as a dict
        :return:
        """
        block = await self.async_fetchone(SQL_LAST_BLOCK, as_dict=True)
        # print(block)
        return block

    async def insert_block(self, block):
        """
        Saves to block object in db
        :param block: a native PosBlock object
        :return:
        """
        # Save the txs
        for tx in block.txs:
            await self.async_execute(SQL_INSERT_TX, tx.to_db(), commit=False)
        # Then the block and commit
        res = await self.async_execute(SQL_INSERT_BLOCK, block.to_db(), commit=True)


if __name__ == "__main__":
    print("I'm a module, can't run!")