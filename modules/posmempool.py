"""
A Safe thread object interfacing the PoS mempool
"""
import threading
import json

# Our modules
import common
import poscrypto

__version__ = '0.0.1'


class Mempool:
    """
    Generic Class
    """

    def __init__(self, verbose = False):
        self.verbose = verbose

    def status(self):
        print("Virtual Method Status")

    def _insert_tx(self, tx):
        print("Virtual Method _insert_tx")

    def _delete_tx(self, tx):
        print("Virtual Method _delete_tx")

    def digest_tx(self, tx, timestamp=0):
        # todo: validity checks
        self._insert_tx(tx)


class MemoryMempool(Mempool):
    """
    Memory Storage, POC only
    """

    def __init__(self, verbose = False):
        super().__init__(verbose=verbose)
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
    def __init__(self, verbose = False, db_path='.data/'):
        super().__init__(verbose=verbose)
        self.db_path = db_path+'posmempool.db'
        # Create path
        # Create DB
        # Load
