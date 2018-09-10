#!/usr/bin/env python3
"""
Helper to convert pos/pow round and heights to timestamp and vice versa

--action=ts2posround --param=1536393600

--action=posround2ts --param=466

--action=ts2powheight --param=1536393600

--action=powheight2ts --param=810000

# quick balance of hn pot at given pow block
--action=hnbalance --param=811159

"""


import argparse
import sys
import time
from os import path

# custom modules
sys.path.append('../modules')
import config
import pow_interface

from determine import timestamp_to_round_slot
from determine import round_to_timestamp


__version__ = '0.0.2'


def ts2utc(ts):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bismuth HyperNode convert helper')
    parser.add_argument("-v", "--verbose", action="count", default=False, help='Be verbose.')
    parser.add_argument("-a", "--action", type=str, default='', help='Action: ts2posround, posround2ts, ts2powheight, powheight2ts')
    parser.add_argument("-p", "--param", type=str, default='', help='Param')
    parser.add_argument("-j", "--json", action="count", default=False, help='Return json content (WIP)')
    args = parser.parse_args()
    verbose = True if args.verbose else False
    config.load('../main/')
    config.COMPUTING_REWARD = True
    pow = None
    if args.action in ['ts2powheight', 'powheight2ts', 'hnbalance']:
        if not path.isfile(config.POW_LEDGER_DB):
            raise ValueError("Bismuth Full ledger not found at {}".format(config.POW_LEDGER_DB))
        pow = pow_interface.PowInterface(verbose=verbose)

    if args.action == 'ts2posround':
        ts = int(args.param)
        a_round, a_slot = timestamp_to_round_slot(ts)
        print("TS", args.param)
        print("-------------")
        print("UTC  ", ts2utc(ts))
        print("Round", a_round)
        print("Slot ", a_slot)

    elif args.action == 'posround2ts':
        round = int(args.param)
        ts = round_to_timestamp(round)
        print("Round", args.param)
        print("-------------")
        print("UTC ", ts2utc(ts))
        print("TS  ", ts)

    elif args.action == 'ts2powheight':
        ts = int(args.param)
        height = pow.pow_chain.get_block_before_ts(ts)
        print("TS", args.param)
        print("-------------")
        print("UTC", ts2utc(ts))
        print("PoW Height", height)
        ts1 = pow.pow_chain.get_ts_of_block(height)
        print("Real TS", ts1)
        ts2 = pow.pow_chain.get_ts_of_block(height + 1)
        if ts2:
            print("Next TS", ts2)
        else:
            print("End of chain - ts too far in the future.")

    elif args.action == 'powheight2ts':
        height = int(args.param)
        print("PoW Height", args.param)
        print("-------------")
        ts = pow.pow_chain.get_ts_of_block(height)
        if ts:
            print("Block TS", ts)
            print("UTC", ts2utc(ts))
        else:
            print("End of chain - Unknown block")

    elif args.action == 'hnbalance':
        height = int(args.param)
        print("PoW Height", args.param)
        print("-------------")
        balance = pow.quick_check_balance('3e08b5538a4509d9daa99e01ca5912cda3e98a7f79ca01248c2bde16', height)
        if balance:
            print("Balance", balance)
        else:
            print("No balance")

    else:
        parser.print_usage()
        parser.print_help()
