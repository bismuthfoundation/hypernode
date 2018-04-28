"""
A Safe thread/process object interfacing the PoS chain
"""
# import threading
import json
import sqlite3

# Our modules
import common
import poscrypto

__version__ = '0.0.2'


class PosChain:
    """
    Generic Class
    """

    def __init__(self, verbose = False):
        self.verbose = verbose
        self.block_height=0

    def status(self):
        print("Virtual Method Status")

    def genesis_dict(self):
        """
        Build up genesis block info
        :return:
        """
        block = {'height': 0, 'round': 0, 'sir': 0, 'timestamp': common.ORIGIN_OF_TIME,
                 'previous_hash': poscrypto.blake('BIG_BANG_HASH').digest(),
                 'msg_count': 0, 'unique_sources': 0,
                 }


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

    def __init__(self, verbose = False, db_path='data/'):
        super().__init__(verbose=verbose)
        self.db_path = db_path+'poc_pos_chain.db'
        # Create path
        # Create DB if needed
        # insert genesis block with fixed TS
        # Load


if __name__ == "__main__":
    print("I'm a module, can't run!")