"""
keys class using fastecdsa crypto

EggdraSyl, Bismuth Foundation, September 2019
"""

from fastecdsa import ecdsa, keys, point
from fastecdsa.curve import secp256k1
from fastecdsa.keys import get_public_key
from fastecdsa.encoding.util import int_to_bytes, bytes_to_int
from hashlib import sha1, sha256


class PubkeyFast:
    __slots__ = ("point", "hasher")

    def __init__(self, x: int, y: int, hasher=None) -> None:
        self.point = point.Point(x, y, curve=secp256k1)
        # Use sha1 as messaqe hasher by default, like python ecdsa
        self.hasher = hasher if hasher else sha1

    def to_string(self) -> bytes:
        """
        Beware, like python-ecdsa, bytes and not string
        REQUIRED for duck typing and use as PUB_KEY
        """
        pub_key_bytes = int_to_bytes(self.point.x).rjust(32, b'\x00') + int_to_bytes(self.point.y).rjust(32, b'\x00')
        return pub_key_bytes

    @classmethod
    def from_bytes(cls, raw: bytes, hasher=None) -> 'PubkeyFast':
        assert len(raw) == 64
        x = bytes_to_int(raw[:32])
        y = bytes_to_int(raw[32:])
        return PubkeyFast(x, y, hasher)

    def check_signature(self, signature: bytes, message: bytes) -> bool:
        r = bytes_to_int(signature[:32])
        s = bytes_to_int(signature[32:])
        return ecdsa.verify((r, s), message, self.point, curve=secp256k1, hashfunc=self.hasher)


class PrivkeyFast:
    __slots__ = ("pk", "pubkey", "hasher")

    def __init__(self, pk: int=0, hasher=None) -> None:
        self.pk = pk if pk else keys.gen_private_key(secp256k1)
        # Use sha1 as messaqe hasher by default, like python ecdsa
        self.hasher = hasher if hasher else sha1
        self.pubkey = None

    def to_string(self) -> bytes:
        """
        Beware, like python-ecdsa, bytes and not string
        REQUIRED for duck typing and use as PUB_KEY
        """
        return int_to_bytes(self.pk).rjust(32, b'\x00')

    @classmethod
    def from_bytes(cls, raw: bytes, hasher=None) -> 'PrivkeyFast':
        assert len(raw) == 32
        i = bytes_to_int(raw)
        return PrivkeyFast(i, hasher)

    def get_public_key(self) -> PubkeyFast:
        if not self.pubkey:
            pubkey_point = get_public_key(self.pk, secp256k1)
            self.pubkey = PubkeyFast(pubkey_point.x, pubkey_point.y)
        return self.pubkey

    def sign(self, message: bytes) -> bytes:
        """Raw sig, like python-ecdsa"""
        r, s = ecdsa.sign(message, self.pk, hashfunc=self.hasher, curve=secp256k1)
        # print("Sig r, s", hex(r), hex(s))  # r and s are int.
        return int_to_bytes(r).rjust(32, b'\x00') + int_to_bytes(s).rjust(32, b'\x00')

    def sign_der(self, message: bytes) -> bytes:
        """Der sig, like coincurve"""
        raise RuntimeError("Not implemented")
        r, s = ecdsa.sign(message, self.pk, hashfunc=self.hasher, curve=secp256k1)
        # sig_der = pyecdsa.util.sigencode_der_canonize(r, s, pyecdsa.SECP256k1.order)  # Bytes
        return b''

