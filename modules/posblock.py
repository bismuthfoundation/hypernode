"""
An object representing a PoS block and it transaction
Allow for different formats: json, dict, raw, protobuff
and conversion between them all
"""

import json

# Our modules
import common
import poscrypto

__version__ = '0.0.1'


class PosBlock:
    """
    Generic Class
    """
    # TODO: Slots
    
    props = ('height', 'round', 'sir', 'timestamp', 'previous_hash', 'msg_count',
             'unique_sources', 'signature', 'block_hash', 'received_by', 'forger')

    # Properties that need encoding for string representation
    hex_encodable = ('previous_hash', 'block_hash', 'signature')

    def __init__(self, verbose = False):
        self.verbose = verbose
        self.height = 0
        self.round =0
        self.sir = 0
        self.timestamp = 0
        self.previous_hash = None
        self.msg_count = 0
        self.unique_sources = 0
        self.signature = None
        self.block_hash = None
        self.received_by = ''
        self.forger = ''
        self.txs = list()

    def status(self):
        print("PosBlock, virtual Method Status")
        
    def from_dict(self, block_dict):
        """
        Converts a dict representing a block to the native object format
        :param block_dict:
        :return:
        """
        # Main block values
        for prop in self.props:
            value = block_dict[prop] if prop in block_dict else None
            self.__dict__[prop] = value
        # txs
        self.txs = [PosMessage().from_list(tx) for tx in block_dict['txs']]
        return self

    def to_dict(self):
        """
        Converts the native object format to a dict representing a block
        :return:
        """
        # txs
        block_dict = {'txs': [tx.to_list() for tx in self.txs]}
        # Main block values
        for prop in self.props:
            block_dict[prop] = self.__dict__[prop]
        return block_dict

    def to_json(self):
        """
        Returns a json representation of the current block object
        :return:
        """
        # Get a raw image of the datas
        block = self.to_dict()
        # Then convert the bin data to base64 for proper json encoding
        for key in self.hex_encodable:
            block[key] = poscrypto.raw_to_hex(block[key])
        block['txs'] = [tx.to_json() for tx in self.txs]
        return json.dumps(block)

    def to_raw(self):
        """
        Gives a raw binary buffer image of the signed block elements
        :return: bytearray
        """
        raw = b''
        # block datation
        raw += self.height.to_bytes(4, byteorder='big')
        raw += self.round.to_bytes(4, byteorder='big')
        raw += self.sir.to_bytes(4, byteorder='big')
        raw += self.timestamp.to_bytes(4, byteorder='big')
        # ordered txids - by ts, if any (only genesis can have none)
        if len(self.txs):
            for tx in self.txs:
                raw += tx.txid
        # previous hash
        raw += self.previous_hash
        return raw

    def sign(self):
        """
        sign the raw block and calc it's hash
        :param block:
        :return: signature, bytearray
        """
        # exception if we are not the forger
        assert poscrypto.ADDRESS == self.forger
        raw = self.to_raw()
        if self.verbose:
            print(raw)
        self.signature = poscrypto.sign(raw, verify=True)
        self.block_hash = poscrypto.blake(raw).digest()

    def digest_block(self, block, timestamp=0):
        # todo: validity checks
        pass


class PosMessage():
    """
    PoS Messages are the Tx
    This object represents a single tx/message
    """

    def __init__(self, verbose = False):
        self.verbose = verbose
        self.txid = None
        self.block_height = 0
        self.timestamp = 0
        self.sender = ''
        self.recipient = ''
        self.what = 0
        self.value = 0

    def from_list(self, tx_list):
        """
        Convert from list to object format
        :param tx_list:
        :return:
        """
        self.txid, self.block_height, self.timestamp, self.sender,
        self.recipient, self.what, self.value = tx_list
        return self

    def to_list(self):
        """
        List representation of the tx object
        :return:
        """
        return [self.txid, self.block_height, self.timestamp, self.sender,
        self.recipient, self.what, self.value]

    def to_json(self):
        """
        Json readable version of the tx object
        :return:
        """
        tx = self.to_list()
        tx['txid'] = poscrypto.raw_to_hex(tx['txid'])
        return json.dumps(tx)


if __name__ == "__main__":
    print("I'm a module, can't run!")