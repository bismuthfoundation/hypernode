"""
Test MN Client
Run from the command line with the instance index from common .py
"""

import sys
import argparse
import time
import asyncio

# custom modules
sys.path.append('../modules')
import common
import posclient
import com_helpers


__version__ = '0.0.1'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bismuth Proof of concept PoS client')
    parser.add_argument("-i", "--index", type=int, default = 0, help='Demo address index [0-4]')
    parser.add_argument("-I", "--ip", type=str, default = '127.0.0.1', help='MN Host to connect to (127.0.0.1)')
    parser.add_argument("-p", "--port", type=str, default = 6969, help='MN port (6969)')
    parser.add_argument("-v", "--verbose", action="count", default=False, help='Be verbose.')

    parser.add_argument("--action", type=str, default=None, help='Specific action. hello, ping, status, tx, mempool')
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit()
    try:
        com_helpers.MY_NODE = posclient.Posclient(args.ip, args.port, wallet="mn_temp/mn{}.json".format(args.index))
        # asyncio.Task(com_helpers.MY_NODE.action(args.action))
        loop = asyncio.get_event_loop()
        loop.run_until_complete(com_helpers.MY_NODE.action(args.action))

    except Exception as e:
        print(e)
