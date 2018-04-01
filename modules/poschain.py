"""
A Safe thread object interfacing the PoS chain
"""
import threading
import json

# Our modules
import common
import poscrypto

__version__ = '0.0.1'


class PosChain:
    """
    Generic Class
    """

    def __init__(self, verbose = False):
        self.verbose = verbose
        self.block_height=0

    def status(self):
        print("Virtual Method Status")

    def digest_block(self, block, timestamp=0):
        # todo: validity checks
        pass


class MemoryPosChain(PosChain):
    """
    Memory Storage, POC only
    """

    def __init__(self, verbose = False):
        super().__init__(verbose=verbose)
        # Just a list
        self.blocks=[common.GENESIS]

    def status(self):
        return json.dumps(self.blocks)


class SqlitePosChain(PosChain):

    def __init__(self, verbose = False, db_path='.data/'):
        super().__init__(verbose=verbose)
        self.db_path = db_path+'poschain.db'
        # Create path
        # Create DB
        # Load
