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


__version__ = '0.0.1'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bismuth Proof of concept PoS node')
    parser.add_argument("-i", "--index", type=int, default = 0, help='Demo address index [0-4]')
    parser.add_argument("-v", "--verbose", action="count", default=False, help='Be verbose.')
    parser.add_argument("--action", type=str, default=None, help='Specific action. ')
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit()
    try:
        my_info = common.POC_MASTER_NODES_LIST[args.index]
        ip = my_info[1]
        port = my_info[2]
        address = my_info[0]
        peers = common.POC_MASTER_NODES_LIST
        posmn.MY_NODE = Posmn(ip, port, address=address, peers=peers, verbose = args.verbose)
        posmn.MY_NODE.serve()
        posmn.MY_NODE.connect()
        while True:
            print("Alive")
            time.sleep(60)
    except Exception as e:
        print(e)
