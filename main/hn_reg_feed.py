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


__version__ = '0.0.3'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bismuth HyperNode Registration feed')
    parser.add_argument("-f", "--force", action="count", default=False, help='Read until last block, do not use real limit.')
    parser.add_argument("-r", "--round", default=0, help='Query for up to that round')

    parser.add_argument("-v", "--verbose", action="count", default=False, help='Be verbose.')
    parser.add_argument("-d", "--distinct", action="count", default=False, help='Use the distinct process (debug)')
    # parser.add_argument("-j", "--json", action="count", default=False, help='Return json content')
    args = parser.parse_args()
    force = True if args.force else False
    distinct = True if args.distinct else False
    verbose = True if args.verbose else False
    config.load()
    # check if db exists
    if not path.isfile(config.POW_LEDGER_DB):
        raise ValueError("Bismuth Full ledger not found at {}".format(config.POW_LEDGER_DB))
    pow = pow_interface.PowInterface(verbose=verbose)

    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(pow.load_hn_pow(datadir='./data', a_round=int(args.round), inactive_last_round=None,
                                                  force_all=force, no_cache=True, ignore_config=True,
                                                  distinct_process=distinct))
    print(json.dumps(res))
