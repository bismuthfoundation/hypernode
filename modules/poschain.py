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

__version__ = '0.0.3'


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
        # No tx for genesis
        txids = []
        block_dict = {'height': 0, 'round': 0, 'sir': 0, 'timestamp': common.ORIGIN_OF_TIME,
                      'previous_hash': poscrypto.blake(common.GENESIS_SEED.encode('utf-8')).digest(),
                      'msg_count': 0, 'unique_sources': 0,'txs': txids,'forger': common.GENESIS_ADDRESS}
        block = PosBlock().from_dict(block_dict)
        block.sign()
        if self.verbose:
            print(block.to_json())
        return block.to_dict()


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