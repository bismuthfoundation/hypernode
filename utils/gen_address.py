"""
Temp Util. Generates a PoS address
Run from the command line

"""

import sys
import os.path

# custom modules
sys.path.append('../modules')
# import common
import poscrypto

__version__ = '0.0.1'

wallet_filename = 'poswallet.json'


def ensure_no_file(filename):
    if os.path.isfile(filename):
        print("{} already exists. Aborted.")
        exit()


if __name__ == "__main__":
    """
    # Generates 50 mn addresses
    for i in range(49):
        poscrypto.gen_keys_file("mn{}.json".format(i+1))
    """
    ensure_no_file(wallet_filename)
    print("Generating keys...")
    try:
        poscrypto.gen_keys_file(wallet_filename)
    except Exception as e:
        print("Error", e)
    print("{} file created".format(wallet_filename))
