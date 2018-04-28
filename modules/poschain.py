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
        # No tx for genesis
        txids= []
        block = {'height': 0, 'round': 0, 'sir': 0, 'timestamp': common.ORIGIN_OF_TIME,
                 'previous_hash': poscrypto.blake(common.GENESIS_SEED.encode('utf-8')).digest(),
                 'msg_count': 0, 'unique_sources': 0,
                 'txids': txids,
                 'forger': common.GENESIS_ADDRESS
                 }
        raw = self.dict_to_raw(block)
        block['signature'] = self.sign_raw_block(raw)
        block['block_hash'] = poscrypto.blake(raw).digest()

        hex_block = {}
        hex_block.update(block)
        hex_block['previous_hash'] = poscrypto.raw_to_hex(hex_block['previous_hash'])
        hex_block['block_hash'] = poscrypto.raw_to_hex(hex_block['block_hash'])
        hex_block['signature'] = poscrypto.raw_to_hex(hex_block['signature'])
        print(hex_block)
        return block

    def dict_to_raw(self, block):
        """
        Gives a raw binary buffer image of the signed block elements
        :param block:
        :return: bytearray
        """
        raw = b''
        # block datation
        raw += block['height'].to_bytes(4, byteorder='big')
        raw += block['round'].to_bytes(4, byteorder='big')
        raw += block['sir'].to_bytes(4, byteorder='big')
        raw += block['timestamp'].to_bytes(4, byteorder='big')
        # ordered txids - by ts, if any (only genesis can have none)
        if len(block['txids']):
            for txid in block['txids']:
                raw += txid
        # previous hash
        raw += block['previous_hash']
        return raw

    def sign_raw_block(self, block):
        """
        sign the raw block
        :param block:
        :return: signature, bytearray
        """
        return poscrypto.sign(block, verify=True)


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