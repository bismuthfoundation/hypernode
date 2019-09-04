

import sys
import base64
import pytest
# import pytest_benchmark
from time import time


sys.path.append('../modules')
import poscrypto
import ecdsa as pyecdsa
from ecdsa import SECP256k1
from coincurve import ecdsa, utils, PublicKey

message = b"Empty message for signature testing"


def test_make_addresses():
    pub_key = "d3ccc2eb64d578582d39924246f2c2bf0768491b85235f242e37f65c3a7ce77569fec4c67cba6d457a5d9a6ad8cecc15584f51bc401e1d7683db6c470acbe776".encode('ascii')
    print("pub_key", pub_key, "network", b'\x19')
    address = poscrypto.pub_key_to_addr(pub_key, b'\x19')
    print("address", address)
    assert address == 'B9oMPPW5hZEAAuq8oCpT6i6pavPJhgXViq'
    print("pub_key", pub_key, "network", b'\x55')
    address = poscrypto.pub_key_to_addr(pub_key, b'\x55')
    print("address", address)
    assert address == 'bJ5YTuPNJP2jEvCLGNoaCES2MBquR1nsLF'

    address = 'B9oMPPW5hZEAAuq8oCpT6i6pavPJhgXViq'
    poscrypto.validate_address(address, b'\x19')


def get_sig():
    poscrypto.load_keys("../main/poswallet.json")
    signature = poscrypto.sign(message, verify=True)
    print("Sign", signature, "Len", len(signature))
    return signature


def raw64_to_der(sig: bytes, rec_id: bytes=b"\x00") -> bytes:
    sig_obj = ecdsa.deserialize_recoverable(sig + rec_id)
    sigb = ecdsa.recoverable_convert(sig_obj)
    sigc = ecdsa.cdata_to_der(sigb)
    return sigc


def raw64_to_rec(sig: bytes, rec_id: bytes=b"\x00") -> bytes:
    sig_obj = ecdsa.deserialize_recoverable(sig + rec_id)
    return sig_obj


def raw64_to_pubkeys(sig: bytes) -> list:
    res = list()
    for rec_id in (b"\x00", b"\x01", b"\x02", b"\x03"):
        sig_rec = raw64_to_rec(sig, rec_id)
        try:
            pubkey = PublicKey(ecdsa.recover(message, sig_rec)).to_string()
            res.append(pubkey.hex())
        except:
            pass
    return res


def sig_to_pubkeys(sig) -> list:
    cdata = ecdsa.der_to_cdata(sig)
    try:
        pubkey = PublicKey(ecdsa.recover(message, cdata)).to_string()
    except Exception as e:
        print(e)
    return pubkey.hex()


if __name__ == "__main__":
    print("Run pytest -v for tests.\n")

    print(poscrypto.version())


    COUNT = 50

    pub_key = base64.b64decode("f2sLa8ME/ZhgchQX8Mv5TNWIaVDant7cI6WLxY+Rxr5buRsSXbEjmvkk9tPBoTxR+G0VmOZ8CoZHUrsVZMSiuQ==")
    pub_key_full = b"\x04" + pub_key
    print("Pubkey full hex", pub_key_full.hex())

    print("\necdsa")
    # poscrypto.USE_CC = False
    #test_make_addresses()
    sig1 = get_sig()

    print("check", poscrypto.check_sig(sig1, pub_key, message))

    start = time()
    for i in range(COUNT):
        poscrypto.check_sig(sig1, pub_key, message)
    print(time() - start)

    sys.exit()

    print("\ncoincurve")
    poscrypto.USE_CC = True
    #test_make_addresses()
    sig2 = get_sig()

    # sig1c = raw64_to_der(sig1, b"\x01")
    sig1b = ecdsa.deserialize_recoverable(sig1 + b"\x01")

    # benchmark this vs coincurve
    r, s = pyecdsa.util.sigdecode_string(sig1, SECP256k1.order)
    print("sig1 r, s", hex(r), hex(s))
    der_sig1 = pyecdsa.util.sigencode_der_canonize(r, s, SECP256k1.order)
    print("der sig1", der_sig1)

    print(sig2, len(sig2))
    r, s = pyecdsa.util.sigdecode_der(sig2, SECP256k1.order)
    # print(sig2, sig2raw)
    # r, s = pyecdsa.util.sigdecode_string(sig2raw, SECP256k1.order)
    print("sig2 r, s", hex(r), hex(s))
    # der_sig2 = pyecdsa.util.sigencode_der_canonize(r, s, SECP256k1.order)
    # print("der sig2", der_sig2)

    sig1b = ecdsa.recoverable_convert(sig1b)  # ok until there
    print("Sig1b", sig1b)
    sig1c = ecdsa.cdata_to_der(sig1b)
    print("sig1c", sig1c, "len", len(sig1c))
    print("pub_key", pub_key_full)
    # pubkey_object = PublicKey(pub_key)
    res = utils.verify_signature(sig1c, message, pub_key_full)
    print("res", res)
    res1b = utils.verify_signature(der_sig1, message, pub_key_full)
    print("res1b", res1b)

    print("keys1")
    print(raw64_to_pubkeys(sig1))

    print("keys2")
    sig2recode = pyecdsa.util.sigencode_string(r, s, SECP256k1.order)
    print(raw64_to_pubkeys(sig2recode))

    print(sig_to_pubkeys(sig2))
    """sig1_0 = raw64_to_rec(sig1, b"\x00")

    print(PublicKey(ecdsa.recover(message, sig1_0)).to_string().hex())
    sig1_1 = raw64_to_rec(sig1, b"\x01")
    print(PublicKey(ecdsa.recover(message, sig1_1)).to_string().hex())
    sig1_2 = raw64_to_rec(sig1, b"\x02")
    try:
        print(PublicKey(ecdsa.recover(message, sig1_2)).to_string())
    except:
        pass
    sig1_3 = raw64_to_rec(sig1, b"\x03")
    try:
        print(PublicKey(ecdsa.recover(message, sig1_3)).to_string())
    except:
        pass
    """

    """
    start = time()
    for i in range(COUNT):
        poscrypto.check_sig(der_sig1, pub_key, message)
    print(time() - start)
    """



