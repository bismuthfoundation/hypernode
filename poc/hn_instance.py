"""
Test Hypernode Instance
Run from the command line with the instance index from common .py
"""

import sys
import argparse
import time

# custom modules
sys.path.append('../modules')
import os
import common
import poshn
from poshn import Poshn
from poschain import SqlitePosChain
import poscrypto
import com_helpers

__version__ = '0.0.4'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bismuth Proof of concept PoS HyperNode')
    parser.add_argument("-i", "--index", type=int, default = -1, help='Demo address index [0-4]')
    parser.add_argument("-v", "--verbose", action="count", default=False, help='Be verbose.')
    parser.add_argument("--action", type=str, default=None, help='Specific action. ')
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit()
    try:
        if args.action == 'genesis':
            # Displays genesis block info for db insert
            poscrypto.load_keys("mn_temp/mn0.json")
            pos_chain = SqlitePosChain(verbose=True)
            genesis = pos_chain.genesis_dict()
        else:
            # If we are updating, let our previous instance close.
            time.sleep(1)
            peers = common.POC_HYPER_NODES_LIST
            if args.index >= 0:
                my_info = common.POC_HYPER_NODES_LIST[args.index]
                ip = my_info[1]
                port = my_info[2]
                address = my_info[0]
                wallet_name = "mn_temp/mn{}.json".format(args.index)
                # allows to run several HN on the same machine - debug/dev only
                datadir = "./data{}".format(args.index)
            else:
                wallet_name = "poswallet.json"
                datadir = "./data"
                my_info = common.POC_HYPER_NODES_LIST[args.index]
                ip = '127.0.0.1'  # TODO DEV only
                port = 6960
                address = "BAnNdHZSWBJxEya5o33Qbqrzg1m13GZmxy"  # TODO: take from wallet
            com_helpers.MY_NODE = Poshn(ip, port, address=address, peers=peers, verbose = args.verbose, wallet=wallet_name, datadir=datadir)
            com_helpers.MY_NODE.serve()
            # only ctrl-c will stop it
    except Exception as e:
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
