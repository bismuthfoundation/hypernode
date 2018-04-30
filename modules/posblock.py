"""
An object representing a PoS block and it transaction
Allow for different formats: json, dict, raw, protobuff
and conversion between them all
"""

import json
import sqlite3

# Our modules
import common
import time
import poscrypto
import commands_pb2

__version__ = '0.0.3'


class PosBlock:
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

    # ======================== Helper conversion methods ===========================

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

    # =========================== Really useful methods ===========================

    def sign(self):
        """
        sign the raw block and calc it's hash
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
        self.params = ''
        self.value = 0
        self.pubkey = None
        self.received = 0

    # ======================== Helper conversion methods ===========================

    def from_values(self, timestamp=0, sender='', recipient='', what=0, params='', value=0, pubkey=None):
        """
        Manually creates from user values
        :param timestamp:
        :param sender:
        :param recipient:
        :param what:
        :param params:
        :param value:
        :return:
        """
        self.txid = 0
        self.block_height = 0
        self.timestamp = int(timestamp) if timestamp else int(time.time())
        self.sender = str(sender) if sender else poscrypto.ADDRESS
        self.recipient = str(recipient) if recipient else poscrypto.ADDRESS
        self.pubkey = pubkey if pubkey else poscrypto.PUB_KEY.to_string()
        self.what = int(what)
        self.params = str(params)
        self.value = int(value)
        return self

    def from_proto(self, TX):
        """
        Convert from protobuf to object format
        :param TX:
        :return:
        """
        # Since all fields are the same and same order, should be an easier way to do this.
        self.txid, self.block_height, self.timestamp, self.sender, self.recipient, \
        self.what, self.params, self.value, self.pubkey = \
        TX.txid, TX.block_height, TX.timestamp, TX.sender, TX.recipient, TX.what, TX.params, TX.value, TX.pubkey
        self.received = int(time.time())
        return self

    def from_list(self, tx_list):
        """
        Convert from list to object format
        :param tx_list:
        :return:
        """
        self.txid, self.block_height, self.timestamp, self.sender, self.recipient, self.what, self.params, self.value, \
        self.pubkey, self.received = tx_list
        return self

    def to_raw(self):
        """
        Raw representation of the tx object, signed parts
        :return:
        """
        print(self.sender, self.recipient, self.params)
        raw = b''
        raw += self.timestamp.to_bytes(4, byteorder='big')
        raw += self.sender.encode('ascii')
        raw += self.recipient.encode('ascii')
        raw += self.what.to_bytes(4, byteorder='big')
        raw += self.params.encode('ascii')
        raw += self.value.to_bytes(4, byteorder='big')
        return raw

    def to_list(self):
        """
        List representation of the tx object
        :return:
        """
        return [self.txid, self.block_height, self.timestamp, self.sender,
                self.recipient, self.what, self.params, self.value, self.pubkey,
                self.received]

    def to_db(self):
        """
        List representation of the tx object for db insert. in the db order, with  received as last extra field
        :return:
        """
        # sqlite3.Binary encodes bin data for sqlite.
        return tuple([sqlite3.Binary(self.txid), self.block_height, self.timestamp, self.sender,
                     self.recipient, self.what, self.params, self.value, sqlite3.Binary(self.pubkey),
                     self.received])

    def to_json(self):
        """
        Json readable version of the tx object
        :return:
        """
        tx = self.to_list()
        if tx[0]:
            # hex for txid
            tx[0] = poscrypto.raw_to_hex(tx[0])
        if tx[8]:
            # and for pubkey
            tx[8] = poscrypto.raw_to_hex(tx[8])
        return json.dumps(tx)

    def add_to_proto(self, protocmd):
        """
        Adds the tx into the given protobuf
        :param protocmd:
        :return:
        """
        proto_tx = protocmd.tx_values.add()
        proto_tx.txid, proto_tx.block_height, proto_tx.timestamp, proto_tx.sender, \
            proto_tx.recipient, proto_tx.what, proto_tx.params, proto_tx.value, \
            proto_tx.pubkey = \
            self.txid, self.block_height, self.timestamp, self.sender,\
            self.recipient, self.what, self.params, self.value, self.pubkey

    # =========================== Really useful methods ===========================

    def sign(self):
        """
        sign the raw tx
        :return: signature, bytearray
        """
        # exception if we are not the forger
        raw = self.to_raw()
        if self.verbose:
            print(raw)
        self.pubkey = poscrypto.PUB_KEY.to_string()
        self.txid = poscrypto.sign(raw, verify=True)

    def check(self):
        """
        Validity check when a node receives a tx.
        Raise on error
        :return:
        """
        # Check 1. timestamp not in the future
        if self.timestamp > time.time() + common.FUTURE_ALLOWED:
            raise ValueError("Transaction in the future, not allowed")
        # Check 2. sender is valid address
        poscrypto.validate_address(self.sender)
        # Check 3. recipient is valid address
        poscrypto.validate_address(self.recipient)
        # Check 4. pubkey matches sender for current network
        check_address = poscrypto.pub_key_to_addr(self.pubkey)
        if self.sender != check_address:
            raise ValueError("Address mismatch pubkey {} instead of {}".format(self.sender, check_address))
        # Check 5. Verify signature validity
        poscrypto.check_sig(self.txid, self.pubkey, self.to_raw())


if __name__ == "__main__":
    print("I'm a module, can't run!")