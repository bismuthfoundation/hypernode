"""
An object representing a PoS block and its transaction
Allow for different formats: json, dict, raw, protobuf
and conversion between them all.
"""

import json
import sqlite3
import os
import sys

# Our modules
import common
import time
import poscrypto
import commands_pb2


__version__ = '0.0.8'


class PosMessage:
    """
    PoS Messages are the Transactions
    This object represents a single tx/message
    """

    props = ('txid', 'block_height', 'timestamp', 'sender', 'recipient',
             'what', 'params', 'value', 'pubkey', 'received')

    # Properties that need encoding for string representation
    hex_encodable = ('txid', 'pubkey')

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.txid = b''
        self.block_height = 0
        self.timestamp = 0
        self.sender = ''
        self.recipient = ''
        self.what = 0
        self.params = ''
        self.value = 0
        self.pubkey = b''
        self.received = 0

    # ======================== Helper conversion methods ===========================

    def from_values(self, timestamp=0, sender='', recipient='', what=0, params='', value=0, pubkey=None):
        """
        Manually creates the transaction object from user values

        :param timestamp:
        :param sender:
        :param recipient:
        :param what:
        :param params:
        :param value:
        :param pubkey:
        :return: the PosMessage instance
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

    def from_proto(self, proto_tx):
        """
        Convert from protobuf to object format.

        :param proto_tx: a protobuf object
        :return: a PosMessage instance
        """
        # Since all fields are the same and same order, should be an easier way to do this.
        self.txid, self.block_height, self.timestamp, self.sender, self.recipient, \
            self.what, self.params, self.value, self.pubkey = \
            proto_tx.txid, proto_tx.block_height, proto_tx.timestamp, proto_tx.sender, proto_tx.recipient, \
            proto_tx.what, proto_tx.params, proto_tx.value, proto_tx.pubkey
        self.received = int(time.time())
        return self

    def from_list(self, tx_list):
        """
        Convert from list to object format.

        :param tx_list: list()
        :return: a PosMessage instance
        """
        self.txid, self.block_height, self.timestamp, self.sender, self.recipient, self.what, self.params, self.value, \
            self.pubkey, self.received = tx_list
        return self

    def from_dict(self, tx_dict):
        """
        Converts a dict representing a message to the native object format.

        :param tx_dict: a python dict()
        :return: a PosMessage instance
        """
        # Main block values
        for prop in self.props:
            if prop in tx_dict:
                # do not override what may not be passed
                value = tx_dict[prop]
                self.__dict__[prop] = value
        return self

    def to_raw(self):
        """
        Raw representation of the PosMessage instance, signed parts only.

        :return: Bytes, a raw buffer
        """
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
        List representation of the PosMessage instance.

        :return: list()
        """
        return [self.txid, self.block_height, self.timestamp, self.sender,
                self.recipient, self.what, self.params, self.value, self.pubkey,
                self.received]

    def to_db(self):
        """
        Tuple representation of the PosMessage instance for db insert. In the db order, with  received as last extra field.

        :return: tuple()
        """
        # sqlite3.Binary encodes bin data for sqlite.
        return tuple([sqlite3.Binary(self.txid), self.block_height, self.timestamp, self.sender,
                     self.recipient, self.what, self.params, self.value, sqlite3.Binary(self.pubkey),
                     self.received])

    def to_json(self):
        """
        Json readable version of the PosMessage instance content,
        with *binary content as hex encoded string*.

        :return: string
        """
        tx = self.to_list()
        if tx[0]:
            # hex for txid
            tx[0] = poscrypto.raw_to_hex(tx[0])
        if tx[8]:
            # and for pubkey
            tx[8] = poscrypto.raw_to_hex(tx[8])
        return json.dumps(tx)

    def add_to_proto(self, protocmd):
        """
        Adds the tx into the given protobuf command (not in a block).

        :param protocmd:
        :return: None
        """
        proto_tx = protocmd.tx_values.add()
        proto_tx.txid, proto_tx.block_height, proto_tx.timestamp, proto_tx.sender, \
            proto_tx.recipient, proto_tx.what, proto_tx.params, proto_tx.value, \
            proto_tx.pubkey = \
            self.txid, self.block_height, self.timestamp, self.sender,\
            self.recipient, self.what, self.params, self.value, self.pubkey

    def add_to_proto_block(self, protoblock):
        """
        Adds the tx into the given block.

        :param protoblock: a block value of a proto command
        :return: None
        """
        proto_tx = protoblock.txs.add()
        proto_tx.txid, proto_tx.block_height, proto_tx.timestamp, proto_tx.sender, \
            proto_tx.recipient, proto_tx.what, proto_tx.params, proto_tx.value, \
            proto_tx.pubkey = \
            self.txid, self.block_height, self.timestamp, self.sender,\
            self.recipient, self.what, self.params, self.value, self.pubkey

    # =========================== Really useful methods ===========================

    def sign(self):
        """
        Sign the raw tx. Uses keys from poscrypto module.

        :return: Signature as bytearray.
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

        :return: None
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


class PosBlock:

    props = ('height', 'round', 'sir', 'timestamp', 'previous_hash', 'msg_count',
             'unique_sources', 'signature', 'block_hash', 'received_by', 'forger')

    # Properties that need encoding for string representation
    hex_encodable = ('previous_hash', 'block_hash', 'signature')

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.height = 0
        self.round = 0
        self.sir = 0
        self.timestamp = 0
        self.previous_hash = b''
        self.msg_count = 0
        self.unique_sources = 0
        self.signature = b''
        self.block_hash = b''
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
        :return: self
        """
        # Main block values
        for prop in self.props:
            if prop in block_dict:
                # do not override what may not be passed
                value = block_dict[prop]
                self.__dict__[prop] = value
        # txs
        try:
            self.txs = [PosMessage().from_list(tx) for tx in block_dict['txs']]
        except KeyError:
            # print(">> Empty block")
            self.txs = []
        except Exception as e:
            print("posblock from_dict exception ", e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
            self.txs = []
        return self

    def to_dict(self):
        """
        Converts the native object format to a dict representing a block.

        :return: dict()
        """
        # txs
        block_dict = {'txs': [tx.to_list() for tx in self.txs]}
        # Main block values
        for prop in self.props:
            block_dict[prop] = self.__dict__[prop]
        return block_dict

    def to_json(self):
        """
        Returns a json representation of the current block object
        with *binary content as hex encoded string*.

        :return: string
        """
        # Get a raw image of the datas
        block = self.to_dict()
        # Then convert the bin data to base64 for proper json encoding
        for key in self.hex_encodable:
            block[key] = poscrypto.raw_to_hex(block[key])
        # We need to_json to convert to hex, but then decode again to have a list we will json encode in the block.
        block['txs'] = [json.loads(tx.to_json()) for tx in self.txs]
        return json.dumps(block)

    def to_db(self):
        """
        Tuple representation of the block object for db insert, without tx. In the db order, with binary types.

        :return: tuple()
        """
        # sqlite3.Binary encodes bin data for sqlite.
        return tuple([self.height, self.round, self.sir, self.timestamp, sqlite3.Binary(self.previous_hash),
                      self.msg_count, self.unique_sources, sqlite3.Binary(self.signature),
                      sqlite3.Binary(self.block_hash), self.received_by, self.forger])

    def to_raw(self):
        """
        Gives a raw binary buffer image of the signed block elements.

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

    def from_proto(self, block_proto):
        """
        Inits the instance properties with the provided protobuff data.

        :param block_proto: a protobuff object
        :return: self
        """
        self.height, self.round, self.sir = block_proto.height, block_proto.round, block_proto.sir
        self.timestamp, self.previous_hash = block_proto.ts, block_proto.previous_hash
        self.txs = list()
        for tx in block_proto.txs:
            my_tx = PosMessage().from_proto(tx)
            self.txs.append(my_tx)
        # Todo: unify sources / names
        self.msg_count, self.unique_sources = block_proto.msg_count, block_proto.sources
        self.signature, self.block_hash = block_proto.signature, block_proto.block_hash
        self.forger = block_proto.forger
        return self

    def to_proto(self):
        """
        Create a protobuf object from current native format.

        :return: a protobuf object.
        """
        protocmd = commands_pb2.Command()
        protocmd.Clear()
        protocmd.command = commands_pb2.Command.block
        block = protocmd.block_value.add()  # protocmd.block_value  # commands_pb2.Block()
        block.height, block.round, block.sir = self.height, self.round, self.sir
        block.ts, block.previous_hash = self.timestamp, self.previous_hash
        for tx in self.txs:
            tx.add_to_proto_block(block)
        # todo: unify sources / names
        block.msg_count, block.sources = self.msg_count, self.unique_sources
        block.signature, block.block_hash = self.signature, self.block_hash
        block.forger = self.forger
        # protocmd.block_value = block
        return protocmd

    def add_to_proto(self, protocmd):
        """
        Adds the block to an existing protobuf command object.

        :return: None
        """
        try:
            block = protocmd.block_value.add()
            block.height, block.round, block.sir = self.height, self.round, self.sir
            block.ts, block.previous_hash = self.timestamp, self.previous_hash
            for tx in self.txs:
                tx.add_to_proto_block(block)
            # todo: unify sources / names
            block.msg_count, block.sources = self.msg_count, self.unique_sources
            block.signature, block.block_hash = self.signature, self.block_hash
            block.forger = self.forger
            # protocmd.block_value = block
            return protocmd
        except Exception as e:
            print("add_to_proto: Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            raise

    # =========================== Really useful methods ===========================

    def sign(self):
        """
        Sign the raw block and calc it's hash

        :return: signature, bytearray
        """
        # exception if we are not the forger
        if self.verbose:
            print(poscrypto.ADDRESS, self.forger)
        if poscrypto.ADDRESS != self.forger:
            raise RuntimeError("Bad Forger")
        raw = self.to_raw()
        if self.verbose:
            print(raw)
        self.msg_count = len(self.txs)
        # set removes duplicates.
        self.unique_sources = len(set([tx.sender for tx in self.txs]))
        self.signature = poscrypto.sign(raw, verify=True)
        self.block_hash = poscrypto.blake(raw).digest()

    def old_digest_block(self, block, timestamp=0):
        # validity checks - done here or rather in poschain?
        pass


class PosHeight:
    """
    PoS Height is the status of the chain state.
    This object represents the current height and content of a given node.
    """

    props = ('height', 'round', 'sir', 'block_hash', 'uniques', 'uniques_round', 'forgers', 'forgers_round')

    # Properties that need encoding for string representation
    hex_encodable = ('block_hash', )

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.height = 0
        self.round = 0
        self.sir = 0
        self.block_hash = b''
        self.uniques = 0
        self.uniques_round = 0
        self.forgers = 0
        self.forgers_round = 0

    def to_proto(self, height):
        """
        Fills in the protobuf object "Height" section

        :return: None
        """
        height.height, height.round, height.sir = self.height, self.round, self.sir
        height.block_hash = self.block_hash
        height.uniques, height.uniques_round = self.uniques, self.uniques_round
        height.forgers, height.forgers_round = self.forgers, self.forgers_round

    def from_proto(self, height_proto):
        """
        Creates from a protobuf Height object.

        :return: self
        """
        self.height, self.round, self.sir = height_proto.height, height_proto.round, height_proto.sir
        self.block_hash = height_proto.block_hash
        self.uniques, self.uniques_round = height_proto.uniques, height_proto.uniques_round
        self.forgers, self.forgers_round = height_proto.forgers, height_proto.forgers_round
        return self

    def from_dict(self, height_dict):
        """
        Converts a dict to the native object format

        :param height_dict: dict()
        :return: self
        """
        for prop in self.props:
            if prop in height_dict:
                # do not override what may not be passed
                value = height_dict[prop]
                self.__dict__[prop] = value
        return self

    def to_dict(self, as_hex=False):
        """
        Converts the native object format to a dict representing a height status

        :param as_hex: convert raw buffers to hex string encoding so we can json_encode later.
        :return: dict()
        """
        # txs
        height_dict = dict()
        # Main block values
        for prop in self.props:
            height_dict[prop] = self.__dict__[prop]
            if as_hex and prop in self.hex_encodable:
                height_dict[prop] = poscrypto.raw_to_hex(height_dict[prop])
        return height_dict


if __name__ == "__main__":
    print("I'm a module, can't run!")
