"""
List the HN reg/unreg events and their state.
"""

import argparse
import json
from os import path
import sys

# custom modules
sys.path.append('../modules')
import config
import poshn
import poscrypto
import pow_interface
import asyncio


__version__ = '0.0.1'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bismuth HyperNode Registration feed')
    parser.add_argument("-v", "--verbose", action="count", default=False, help='Be verbose.')
    # parser.add_argument("-j", "--json", action="count", default=False, help='Return json content')
    args = parser.parse_args()
    config.load()
    # check if db exists
    if not path.isfile(config.POW_LEDGER_DB):
        raise ValueError("Bismuth Full ledger not found at {}".format(config.POW_LEDGER_DB))
    pow = pow_interface.PowInterface(verbose=True)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(pow.load_hn_pow(datadir='./data', inactive_last_round=None, force_all=True))
