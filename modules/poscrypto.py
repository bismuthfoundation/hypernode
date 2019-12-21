"""
PoS related crypto helpers
==========================

Low level cryptographic functions for Bismuth Hypernodes.
"""

# Third party modules
import json
import os
import random
import re
import sys
import time
from base64 import b64encode, b64decode
from hashlib import blake2b
from os import urandom
from typing import Tuple, Union

from ecdsa import SigningKey, SECP256k1, VerifyingKey

# our modules
import base58

try:
    # Fail safe so we can use without config.py module
    import config
except:
    # Network Byte ID - 0x19 = Main PoS Net 'B' - 0x55 Test PoS Net 'b'
    config.NETWORK_ID = b'\x19'

# A previous Feature request was to move from python ecdsa to libsecp256k1, way faster to sign and verify transactions.
# Use test cases and test vectors to make sure all is the same.
# https://github.com/ofek/coincurve  seems up to date and pretty good however it only supports sha256 message hashing,
# whereas python ecdsa (don't ask me why) uses sha1 by default.
# In order to keep compatibility, avoid more conditionnal code and a fork,
# we're using https://github.com/AntonKueltz/fastecdsa instead.

__version__ = '0.0.43'

# Do not change, impact addresses format
BLAKE_DIGEST_SIZE = 20

# Signatures and pubkeys are 64 bytes

PUB_KEY = None
PRIV_KEY = None
ADDRESS = None

RE_VALID_ADDRESS = re.compile("[A-Za-z0-9]{34}")


def version() -> str:
    return "Using slow Python-ecdsa"


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
    :return: bytes
    """
    bytes_array = []
    # remove extra formatting zeroes that may be there
    hex_str = ''.join(hex_str.split(" "))
    for i in range(0, len(hex_str), 2):
        # bytes_array.append(chr(int(hex_str[i:i + 2], 16)))
        bytes_array.append(int(hex_str[i:i + 2], 16))
    # return ''.join(bytes_array)
    return bytes(bytes_array)


def blake(buffer):
    """
    Blake hash of a raw buffer or string/

    :param buffer: str or bytes
    :return: binary hash
    """
    global BLAKE_DIGEST_SIZE
    if isinstance(buffer, str):
        buffer = buffer.encode('utf-8')
    return blake2b(buffer, digest_size=BLAKE_DIGEST_SIZE)


def hash_to_addr(hash20, network=None):
    """
    Converts a hash of len 20 bytes to a checksum'd + network id address, to compare to an address

    :param hash20: bytes
    :param network: byte
    :return: string
    """
    if not network:
        network = config.NETWORK_ID
    v = network + hash20
    digest = blake2b(v, digest_size=4).digest()
    return base58.b58encode(v + digest).decode('ascii')


def pub_key_to_addr(pub_key: bytes, network=None):
    """
    Converts a public key to a checksum'd + network id address

    :param pub_key:
    :param network: byte
    :return: string
    """
    # print("pub_key_to_addr", pub_key)
    hash20 = blake2b(pub_key, digest_size=BLAKE_DIGEST_SIZE).digest()
    return hash_to_addr(hash20, network)


def validate_address_quick(address, network=None):
    """
    Verify an address, just charset and len.

    :param address: the address string to validate
    :param network: The network id to validate against
    :return: True or False
    """
    return RE_VALID_ADDRESS.match(address)


def validate_address(address, network=None):
    """
    Decode and verify the checksum of a Base58 encoded string.

    :param address: the address string to validate
    :param network: The network id to validate against
    :return: The 20 bytes hash of the pubkey if address matches format and network, or throw an exception
    """
    # TODO: can be time consuming, check it's not called more often than really needed.
    if not RE_VALID_ADDRESS.match(address):
        raise ValueError("Invalid address format: {}".format(address))
    if not network:
        network = config.NETWORK_ID
    raw = base58.b58decode(address)
    result, check = raw[:-4], raw[-4:]
    digest = blake2b(result, digest_size=4).digest()
    if check != digest:
        raise ValueError("Invalid address checksum for {}".format(address))
    if result[0] != ord(network):
        raise ValueError("Invalid Network: 0x{:02x} instead of 0x{:02x}".format(result[0], ord(network)))
    return result[1:]


def load_keys(pos_filename='poswallet.json', verbose=False):
    """
    Load the keys from wallet json file.

    :param pos_filename:
    :param verbose: boolean, print out address and pubkey
    :return: True or raise.
    """
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
    # print("PRIVKEY", PRIV_KEY.to_string())
    # TODO: We could verify pubkey also, and warn if there is an error
    PUB_KEY = VerifyingKey.from_string(b64decode(wallet['pubkey'].encode('ascii')), curve=SECP256k1)
    # We recreate address rather than relying on address.txt
    ADDRESS = pub_key_to_addr(PUB_KEY.to_string())
    # print("PUB_KEY.to_string(), ADDRESS", PUB_KEY.to_string(), ADDRESS)
    # sys.exit()
    assert ADDRESS == wallet['address']
    if verbose:
        print("Loaded address ", ADDRESS)
        print("Loaded pubkey ", raw_to_hex(PUB_KEY.to_string()))
    return True


def sign(message: Union[str, bytes], verify: bool=True, priv_key=None, pub_key=None):
    """
    Sign a message with the default keys and return its signature.

    :param message: A string or byte object
    :param verify: Shall we verify the signature? default to True
    :param priv_key: opt
    :param pub_key: opt
    :return: bytes (signature)
    """
    global PUB_KEY
    global PRIV_KEY
    if not priv_key:
        priv_key = PRIV_KEY
        # Instance of signing/privkey
    if isinstance(message, str):
        # encode is this is a string only
        message = message.encode("utf-8")

    # print("Sign", message, priv_key, pub_key)

    signature = priv_key.sign(message)
    if verify:
        if not pub_key:
            pub_key = PUB_KEY
        assert pub_key.verify(signature, message)
    return signature


def check_sig(signature: bytes, pubkey_string: bytes, message:bytes):
    """
    Raise ValueError if the signature of message does not match pubkey

    :param signature:
    :param pubkey_string: the pubkey, string version.
    :param message:
    :return: None
    """
    # print("check_sig", signature, pubkey_string, message)
    pub_key = VerifyingKey.from_string(pubkey_string, curve=SECP256k1)
    # Will raise
    try:
        pub_key.verify(signature, message)
    except:
        raise ValueError("Invalid Signature")


def gen_keys(seed: str="") -> Tuple[bytes, bytes, str]:
    """
    Generates a new set of keys.

    :return: tuple (priv:bytes, pub: bytes, address:str)
    """
    if seed != "":
        print("gen_keys: Seed was provided but not implemented")
        sys.exit()
    privkey = SigningKey.generate(curve=SECP256k1)
    pubkey = privkey.get_verifying_key().to_string()
    address = pub_key_to_addr(pubkey, config.NETWORK_ID)
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
        if config.VERBOSE:
            print("Generated address for network 0x{:02x} is {}".format(ord(config.NETWORK_ID), address))
        wallet = {"encrypted": False, "pubkey": b64encode(pubkey).decode('ascii'),
                  "privkey": b64encode(privkey).decode('ascii'),
                  "address": address, "label": "", "created": int(time.time())}
        print(wallet)
        with open(pos_filename, 'w') as fp:
            json.dump(wallet, fp)
    else:
        raise ValueError("File Exists: {}".format(pos_filename))
    return wallet


try:
    # print("Trying to monkey patch fastkeys...")
    from fastkeys import PrivkeyFast, PubkeyFast

    def _version_fast() -> str:
        return "Using Fastecdsa"


    def _load_keys_fast(pos_filename='poswallet.json', verbose=False):
        """
        Load the keys from wallet json file.

        :param pos_filename:
        :param verbose: boolean, print out address and pubkey
        :return: True or raise.
        """
        global PUB_KEY
        global PRIV_KEY
        global ADDRESS
        try:
            if not os.path.exists(pos_filename):
                # Create new keys if none there.
                gen_keys_file(pos_filename)
            with open(pos_filename, 'r') as fp:
                wallet = json.load(fp)
            # TODO: handle encrypted wallet
            PRIV_KEY = PrivkeyFast.from_bytes(b64decode(wallet['privkey'].encode('ascii')))
            # print("_load_keys_fast PRIVKEY", PRIV_KEY.to_string())
            # TODO: We could verify pubkey also, and warn if there is an error
            PUB_KEY = PRIV_KEY.get_public_key()
            pub_key_hex = PUB_KEY.to_string().hex()
            from_wallet = b64decode(wallet['pubkey'].encode('ascii')).hex()
            if pub_key_hex != from_wallet:
                print("pubkey mismatch \n{} vs \n{}".format(from_wallet, pub_key_hex))
                sys.exit()
            ADDRESS = pub_key_to_addr(PUB_KEY.to_string())
            # print(ADDRESS, wallet['address'])
            # print("PUB_KEY.to_string(), ADDRESS", PUB_KEY.to_string(), ADDRESS)
            assert ADDRESS == wallet['address']
            if verbose:
                print("Loaded address ", ADDRESS)
                print("Loaded pubkey ", pub_key_hex)
            # sys.exit()
            return True
        except Exception as e:
            print("Fatal _load_keys_fast", e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))
            sys.exit()


    def _sign_fast(message, verify:bool=True, priv_key=None, pub_key=None):
        """
        Sign a message with the default keys and return its signature.

        :param message: A string or byte object
        :param verify: Shall we verify the signature? default to True
        :param priv_key: opt
        :param pub_key: opt
        :return: bytes (signature)
        """
        global PUB_KEY
        global PRIV_KEY
        try:
            if not priv_key:
                priv_key = PRIV_KEY
            if isinstance(message, str):
                # encode if this is a string only
                message = message.encode("utf-8")
            # print("_sign_fast", message, priv_key, pub_key)
            signature = priv_key.sign(message)
            if verify:
                if not pub_key:
                    pub_key = PUB_KEY
                valid = pub_key.check_signature(signature, message)
                assert valid
            return signature
        except Exception as e:
            print("_sign_fast", e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))
            raise


    def _check_sig_fast(signature: bytes, pubkey_string: bytes, message: bytes):
        """
        Raise ValueError if the signature of message does not match pubkey

        :param signature:
        :param pubkey_string: the pubkey, string version.
        :param message:
        :return: None
        """
        pubkey = PubkeyFast.from_bytes(pubkey_string)
        valid = pubkey.check_signature(signature, message)
        if not valid:
            raise ValueError("Invalid signature _check_sig_fast")
        return valid


    def _gen_keys_fast(seed: str = "") -> Tuple[bytes, bytes, str]:
        """
        Generates a new set of keys.

        :return: tuple (priv:bytes, pub: bytes, address:str)
        """
        if seed != "":
            print("gen_keys fast: Seed was provided but not implemented")
            sys.exit()

        privkey = PrivkeyFast()
        pubkey = privkey.get_public_key().to_string()
        address = pub_key_to_addr(pubkey, config.NETWORK_ID)
        return privkey.to_string(), pubkey, address

    # Monkey patching, so systems without the right lib still can work in degraded mode.
    version = _version_fast
    load_keys = _load_keys_fast
    sign = _sign_fast
    check_sig = _check_sig_fast
    gen_keys = _gen_keys_fast

    # print("Monkey patch successful...")

except:
    pass


if __name__ == "__main__":
    print("I'm a module, can't run!")
