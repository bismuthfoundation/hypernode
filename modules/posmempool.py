"""
A Safe thread object interfacing the PoS mempool
"""
import threading
import json

# Our modules
import common
import poscrypto
import posblock

__version__ = '0.0.1'

SQL_CREATE_MEMPOOL = "CREATE TABLE pos_messages (\
    txid         BLOB (64)    PRIMARY KEY,\
    block_height INTEGER,\
    timestamp    INTEGER,\
    sender       VARCHAR (34),\
    recipient    VARCHAR (34),\
    what         INTEGER,\
    params       STRING,\
    value        INTEGER,\
    received     INTEGER,\
);"

SQL_INSERT_TX = "INSERT INTO pos_message VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"


class Mempool:
    """
    Generic Class
    """

    def __init__(self, verbose = False, app_log=None):
        self.verbose = verbose
        self.app_log = app_log

    def status(self):
        print("Virtual Method Status")

    def _insert_tx(self, tx):
        print("Virtual Method _insert_tx")

    def _delete_tx(self, tx):
        print("Virtual Method _delete_tx")

    def digest_tx(self, tx, timestamp=0):
        if 'TX' == tx.__class__.__name__:
            # Protobuff, convert to object
            tx = posblock.PosMessage().from_proto(tx)
        # TODO: if list, convert also
        if self.verbose:
            self.app_log.info("Digesting {}".format(tx.to_json()))
        # Validity checks, will raise
        tx.check()
        self._insert_tx(tx)
        # TODO: also add the pubkey in index if present.


class MemoryMempool(Mempool):
    """
    Memory Storage, POC only
    """

    def __init__(self, verbose = False, app_log=None):
        super().__init__(verbose=verbose, app_log=app_log)
        # Just a list
        self.txs=[]
        self.lock = threading.Lock()

    def status(self):
        return json.dumps(self.txs)

    def _insert_tx(self, tx):
        with self.lock:
            self.txs.append(tx)

    def _delete_tx(self, tx):
        with self.lock:
            self.txs.remove(tx)


class SqliteMempool(Mempool):
    """
    Sqlite storage backend.
    """
    # TODO: Allow for memory mempool
    def __init__(self, verbose = False, db_path='./data/', app_log=None):
        super().__init__(verbose=verbose, app_log=app_log)
        self.db_path = db_path+'posmempool.db'
        # TODO Create path
        # Create DB
        # Load

    def since(self, date):
        """
        returns the list of transactions we got since the given date
        :param date:
        :return:
        """
        # TODO - return a list of posblock.PosMessage objects
        pass

    def _insert_tx(self, tx):
        # TODO
        print("TODO insert tx")
        SQL_INSERT_TX
