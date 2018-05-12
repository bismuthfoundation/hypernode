"""
Test MN Instance
Run from the command line with the instance index from common .py
"""

import sys
import argparse
import time

# custom modules
sys.path.append('../modules')
import common
import posmn
from posmn import Posmn
from poschain import SqlitePosChain
import poscrypto
import com_helpers

__version__ = '0.0.3'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bismuth Proof of concept PoS node')
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
            my_info = common.POC_MASTER_NODES_LIST[args.index]
            ip = my_info[1]
            port = my_info[2]
            address = my_info[0]
            peers = common.POC_MASTER_NODES_LIST
            if args.index >= 0:
                wallet_name = "mn_temp/mn{}.json".format(args.index)
                # allows to run several MN on the same machine - debug/dev only
                datadir = "./data{}".format(args.index)
            else:
                wallet_name = "poswallet.json"
                datadir = "./data"
            com_helpers.MY_NODE = Posmn(ip, port, address=address, peers=peers, verbose = args.verbose, wallet=wallet_name, datadir=datadir)
            com_helpers.MY_NODE.serve()
            # only ctrl-c will stop it
    except Exception as e:
        print(e)
