"""
Bismuth
Base58 encoding, decoding, checksum of PoS addresses

Adapted from various public domain sources
"""

# Third party modules

# our modules

__version__ = '0.0.2'


# 58 character alphabet
alphabet = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


iseq, bseq, buffer = (
    lambda s: s,
    bytes,
    lambda s: s.buffer,
)


def scrub_input(v):
    """
    Converts string to byte object

    :param v:
    :return:
    """
    if isinstance(v, str) and not isinstance(v, bytes):
        v = v.encode('ascii')
    if not isinstance(v, bytes):
        raise TypeError(
            "a bytes-like object is required (also str), not '%s'" %
            type(v).__name__)
    return v


def b58encode_int(i):
    """
    Encode an integer using Base58

    :param i:
    :return:
    """
    string = b""
    while i:
        i, idx = divmod(i, 58)
        string = alphabet[idx:idx+1] + string
    return string


def b58encode(v):
    """
    Encode a string or byte object using Base58

    :param v:
    :return:
    """
    v = scrub_input(v)
    nPad = len(v)
    v = v.lstrip(b'\0')
    nPad -= len(v)
    p, acc = 1, 0
    for c in iseq(reversed(v)):
        acc += p * c
        p = p << 8
    result = b58encode_int(acc)
    return (alphabet[0:1] * nPad + result)


def b58decode_int(v):
    """
    Decode a Base58 encoded string as an integer

    :param v:
    :return:
    """
    v = scrub_input(v)
    decimal = 0
    for char in v:
        decimal = decimal * 58 + alphabet.index(char)
    return decimal


def b58decode(v):
    """
    Decode a Base58 encoded string and returns a byte object

    :param v:
    :return:
    """
    v = scrub_input(v)
    origlen = len(v)
    v = v.lstrip(alphabet[0:1])
    newlen = len(v)
    acc = b58decode_int(v)
    result = []
    while acc > 0:
        acc, mod = divmod(acc, 256)
        result.append(mod)
    return (b'\0' * (origlen - newlen) + bseq(reversed(result)))


if __name__ == "__main__":
    print("I'm a module, can't run!")
