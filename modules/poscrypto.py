"""
Bismuth
PoS related crypto helpers
"""

# Third party modules
import json
import os
from ecdsa import SigningKey, SECP256k1, VerifyingKey, BadSignatureError
from hashlib import blake2b
import time
import re
from base64 import b64encode, b64decode


# our modules
import base58
try:
    # Failsafe so we can use without common.py module
    import common
except:
    # Network Byte ID - 0x19 = Main PoS Net 'B' - 0x55 Test PoS Net 'b'
    common.NETWORK_ID = b'\x19'


__version__ = '0.0.3'

# Do not change, impact addresses format
BLAKE_DIGEST_SIZE = 20

# Signatures and pubkeys are 64 bytes

PUB_KEY = None
PRIV_KEY = None
ADDRESS = None


def raw_to_hex(digest):
    """Return the **printable** hex digest of a byte buffer.
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
    bytes_array = []
    hex_str = ''.join(hex_str.split(" "))
    for i in range(0, len(hex_str), 2):
        bytes_array.append(chr(int(hex_str[i:i + 2], 16)))
    return ''.join(bytes_array)


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


def hash_to_addr(hash20, network=None):
    """
    Converts a hash of len 20 bytes to a checksum'd + network id address, to compare to an address
    :param hash20:
    :param network:
    :return:
    """
    if not network:
        network = common.NETWORK_ID
    v = network + hash20
    digest = blake2b(v, digest_size=4).digest()
    return base58.b58encode(v + digest).decode('ascii')


def pub_key_to_addr(pub_key, network=None):
    """
    Converts a public key to a checksum'd + network id address
    :param pub_key:
    :param network:
    :return:
    """
    hash20 = blake2b(pub_key, digest_size=BLAKE_DIGEST_SIZE).digest()
    return hash_to_addr(hash20, network)


def validate_address(address, network=None):
    """
    Decode and verify the checksum of a Base58 encoded string
    :param address: the address string to validate
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


def load_keys(pos_filename='poswallet.json', verbose=False):
    global PUB_KEY
    global PRIV_KEY
    global ADDRESS
    if not os.path.exists(pos_filename):
        # Create new keys if none there.
        gen_keys_file(pos_filename)
    with open(pos_filename, 'r') as fp:
        wallet = json.load(fp)
    # TODO: handle encrypted wallet
    PRIV_KEY = SigningKey.from_string(b64decode(wallet['privkey'].encode('ascii')), curve=SECP256k1)
    # TODO: We could verify pubkey also, and warn if there is an error
    PUB_KEY = VerifyingKey.from_string(b64decode(wallet['pubkey'].encode('ascii')), curve=SECP256k1)
    # We recreate address rather than relying on address.txt
    ADDRESS = pub_key_to_addr(PUB_KEY.to_string())
    assert ADDRESS == wallet['address']
    if verbose:
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


def check_sig(signature, pubkey_string, message):
    """
    Raise if the signature does not match
    :param signature:
    :param pubkey_string:
    :param message:
    :return:
    """
    pub_key = VerifyingKey.from_string(pubkey_string, curve=SECP256k1)
    # Will raise
    try:
        pub_key.verify(signature, message)
    except:
        raise ValueError("Invalid Signature")


def gen_keys():
    """
    Generates a new set of keys
    :return: tuple (priv, pub, address), all as string
    """
    privkey = SigningKey.generate(curve=SECP256k1)
    pubkey = privkey.get_verifying_key().to_string()
    address = pub_key_to_addr(pubkey, common.NETWORK_ID)
    return privkey.to_string(), pubkey, address


def gen_keys_file(pos_filename='poswallet.json'):
    """
    Generates a new set of keys and saves to json wallet
    :param pos_filename:
    :return: the generated wallet as a dict
    """
    # we are supposed to have checked before, but make sure anyway.
    if not os.path.exists(pos_filename):
        privkey, pubkey, address = gen_keys()
        if common.VERBOSE:
            print("Generated address for network 0x{:02x} is {}".format(ord(common.NETWORK_ID), address))
        wallet = {"encrypted": False, "pubkey": b64encode(pubkey).decode('ascii'),
                  "privkey": b64encode(privkey).decode('ascii'),
                  "address": address, "label": "", "created": int(time.time())}
        print(wallet)
        with open(pos_filename, 'w') as fp:
            json.dump(wallet, fp)
    else:
        raise ValueError("File Exists: {}".format(pos_filename))
    return wallet


if __name__ == "__main__":
    print("I'm a module, can't run!")
