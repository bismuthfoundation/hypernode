"""
Bismuth
PoS related crypto helpers
"""

# Third party modules
from hashlib import blake2b

# our modules
import common

__version__ = '0.0.1'


BLAKE_DIGEST_SIZE = 16


def bin_convert(hex_hash):
    # TODO: this is copied from Bismuth, need to use more efficient method, no need to take the bin string conversion path.
    return ''.join(format(ord(x), '8b').replace(' ', '0') for x in hex_hash)


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



if __name__ == "__main__":
    print("I'm a module, can't run!")
