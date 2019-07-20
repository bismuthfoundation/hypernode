"""
Test HyperNode Update
Run from the command line, sends an "update" command to the clients listed in data/mns.txt
"""

import sys
import os
import argparse
# import time
import asyncio

# custom modules
sys.path.append('../modules')
# import common
import posclient
import com_helpers


__version__ = '0.0.11'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bismuth Proof of concept PoS updater client')
    parser.add_argument("-u", "--url", type=str, default = 'http://eggpool.net/hnd_zip/', help='Update URL')
    parser.add_argument("-v", "--verbose", action="count", default=False, help='Be verbose.')
    parser.add_argument("-f", "--file", type=str, default = 'data/mns.txt', help='txt file of ip:port to connect to')

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit()
    try:
        with open(args.file, 'r') as fp:
            nodes = [line.strip().split(':') for line in fp]
        loop = asyncio.get_event_loop()
        for node in nodes:
            if args.verbose:
                print("Trying {}:{}".format(node[0], node[1]))
            com_helpers.MY_NODE = posclient.Posclient(node[0], node[1])
            loop.run_until_complete(com_helpers.MY_NODE.action('update', args.url))

    except Exception as e:
        print("Error:", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
