"""
Bismuth
PoS related crypto helpers
"""

# Third party modules
import json
import os
import sys
from ecdsa import SigningKey, SECP256k1, VerifyingKey, BadSignatureError
from hashlib import blake2b
import time
import re

# our modules
import base58
from base64 import b64encode, b64decode
import common

__version__ = '0.0.3'

# Do not change, impact addresses format
BLAKE_DIGEST_SIZE = 20

# Signatures and pubkeys are 64 bytes
# d3ccc2eb64d578582d39924246f2c2bf0768491b85235f242e37f65c3a7ce77569fec4c67cba6d457a5d9a6ad8cecc15584f51bc401e1d7683db6c470acbe776

PUB_KEY = None
PRIV_KEY = None
ADDRESS = None


def bin_convert(hex_hash):
    # TODO: this is copied from Bismuth, need to use more efficient method,
    # no need to take the bin string conversion path.
    return ''.join(format(ord(x), '8b').replace(' ', '0') for x in hex_hash)


def raw_to_hex(digest):
    """Return the **printable** hex digest ofa byte buffer.
    :return: The hash digest, Hexadecimal encoded.
    :rtype: string
    """
    return "".join(["%02x" % x for x in tuple(digest)])


def hex_to_raw(hex_str):
    """
    Convert an hex string into a byte string. The Hex Byte values may
    or may not be space separated.
    :param hex_str:
    :return:
    """
    bytes = []
    hex_str = ''.join(hex_str.split(" "))
    for i in range(0, len(hex_str), 2):
        bytes.append(chr(int(hex_str[i:i + 2], 16)))
    return ''.join(bytes)


def blake(buffer):
    """
    Blake hash of a raw buffer or string
    :param buffer:
    :return: binary hash
    """
    global BLAKE_DIGEST_SIZE
    if isinstance(buffer, str):
        buffer = buffer.encode('utf-8')
    return blake2b(buffer, digest_size=BLAKE_DIGEST_SIZE)


def hash_from_ordered_dict(block):
    """

    :param json_block:
    :return:
    """
    # TODO: decide if we base upon the protobuf block message (shorter, binary, no conversion) - issue: hash may change if protobuff block structure changes.
    # or on a string or json encoding of the block? (means many conversions and slower checks)
    base = json.dumps(block)
    return blake(base)


def hash_to_addr(hash, network=None):
    """
    Converts a hash20 to a checksum'd + network id address, to compare to an address
    :param hash:
    :param network:
    :return:
    """
    if not network:
        network = common.NETWORK_ID
    v = network + hash
    digest = blake2b(v, digest_size=4).digest()
    return base58.b58encode(v + digest).decode('ascii')


def pub_key_to_addr(pub_key, network=None):
    """
    Converts a public key to a checksum'd + network id address
    :param pub_key:
    :param network:
    :return:
    """
    hash = blake2b(pub_key, digest_size=BLAKE_DIGEST_SIZE).digest()
    return hash_to_addr(hash, network)


def validate_address(address, network=None):
    """
    Decode and verify the checksum of a Base58 encoded string
    :param v: the address string to validate
    :param network: The network id to validate against
    :return: The 20 bytes hash of the pubkey if address matches format and network, or throw an exception
    """
    if not re.match('[A-Za-z0-9]{34}', address):
        # B9oMPPW5hZEAAuq8oCpT6i6pavPJhgXViq
        raise ValueError("Invalid address format: {}".format(address))
    if not network:
        network = common.NETWORK_ID
    raw = base58.b58decode(address)
    result, check = raw[:-4], raw[-4:]
    digest = blake2b(result, digest_size=4).digest()
    if check != digest:
        raise ValueError("Invalid address checksum for {}".format(address))
    if result[0] != ord(network):
        raise ValueError("Invalid Network: 0x{:02x} instead of 0x{:02x}".format(result[0], ord(network)))
    return result[1:]


def load_keys(pos_filename='poswallet.json'):
    global PUB_KEY
    global PRIV_KEY
    global ADDRESS
    if not os.path.exists(pos_filename):
        # Create new keys if none there.
        gen_keys_file(pos_filename)
    with open(pos_filename, 'r') as fp:
        wallet = json.load(fp)
    # TODO: handle encrypted wallet
    PRIV_KEY = SigningKey.from_string(b64decode(wallet['privkey'].encode('ascii')), curve=SECP256k1)
    # TODO: We could verify pubkey also, and warn if there is an error
    PUB_KEY = VerifyingKey.from_string(b64decode(wallet['pubkey'].encode('ascii')), curve=SECP256k1)
    # We recreate address rather than relying on address.txt
    ADDRESS = pub_key_to_addr(PUB_KEY.to_string())
    assert ADDRESS == wallet['address']
    if common.VERBOSE:
        print("Loaded address ", ADDRESS)
        print("Loaded pubkey ", raw_to_hex(PUB_KEY.to_string()))
    return True


def sign(message, verify=True, priv_key=None, pub_key=None):
    """
    Sign a message with the default keys and return its signature
    :param message: A string or byte object
    :param verify: Shall we verify the signature? default to True
    :param priv_key:
    :param pub_key:
    :return:
    """
    global PUB_KEY
    global PRIV_KEY
    if not priv_key:
        priv_key = PRIV_KEY
    if isinstance(message, str):
        # encode is this is a string only
        message = message.encode("utf-8")
    signature = priv_key.sign(message)
    if verify:
        if not pub_key:
            pub_key = PUB_KEY
        assert pub_key.verify(signature, message)
    return signature


def gen_keys():
    """
    Generates a new set of keys
    :return: tuple (priv, pub, address), all as string
    """
    privkey = SigningKey.generate(curve=SECP256k1)
    pubkey = privkey.get_verifying_key().to_string()
    address = pub_key_to_addr(pubkey, common.NETWORK_ID)
    return (privkey.to_string(), pubkey, address)


def gen_keys_file(pos_filename='poswallet.json'):
    """
    Generates a new set of keys and saves to json wallet
    :param pos_priv:
    :param pos_pub:
    :param address_filename:
    :return: the generated wallet as a dict
    """
    # we are supposed to have checked before, but make sure anyway.
    if not os.path.exists(pos_filename):
        privkey, pubkey, address = gen_keys()
        if common.VERBOSE:
            print("Generated address for network 0x{:02x} is {}".format(ord(common.NETWORK_ID), address))
        wallet = {"encrypted": False, "pubkey": b64encode(pubkey).decode('ascii') , "privkey": b64encode(privkey).decode('ascii'),
                  "address": address, "label":"", "created": int(time.time())}
        print(wallet)
        with open(pos_filename, 'w') as fp:
            json.dump(wallet, fp)
    else:
        raise ValueError("File Exists: {}".format(pos_filename))
    return wallet


"""
if not PRIV_KEY:
    if not hasattr(sys, '_called_from_test'):
        # Don't mess with keys of testing.
        load_keys()
"""


if __name__ == "__main__":
    print("I'm a module, can't run!")
