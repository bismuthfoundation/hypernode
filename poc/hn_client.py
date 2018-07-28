"""
****************
HyperNode Client
****************

Run from the command line with the instance index from common .py

Example:

.. code-block:: text

  python3 hn_client.py -i 0 --action status

Basic Command line arguments
============================

-i , --index (optional, default=0)
----------------------------------
Instance index to connect to.

-I , --ip (optional, default=127.0.0.1)
---------------------------------------
Hypernode Host to connect to.

-p , --port (optional, default=6969)
------------------------------------
Hypernode port to connect to.

-v , --verbose (optional, default=False)
----------------------------------------
Be verbose.

Commands
========

Commands are issued via ``--action`` and ``--param`` command line switches.

``--param`` is an optional input parameter to the action command

--action=hello
---------------

--action=ping
--------------

--action=status
----------------
Returns full Hypernode status as a Json string

--action=block --param=block_height
------------------------------------
WIP -
Returns block info and list of transactions for given height

--action=tx --param=tx_signature
---------------------------------
WIP - Returns detail of the given transaction


--action=mempool
-----------------
Returns current mempool content as json.


--action=txtest
---------------
Emits a test transaction


"""

import sys
import argparse
import time
import asyncio

# custom modules
sys.path.append('../modules')
# import common
import posclient
import com_helpers


__version__ = '0.0.4'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bismuth Proof of concept PoS client')
    parser.add_argument("-i", "--index", type=int, default = 0, help='Demo address index [0-4]')
    parser.add_argument("-I", "--ip", type=str, default = '127.0.0.1', help='HN Host to connect to (127.0.0.1)')
    parser.add_argument("-p", "--port", type=str, default = 6969, help='HN port (6969)')
    parser.add_argument("-v", "--verbose", action="count", default=False, help='Be verbose.')

    parser.add_argument("--action", type=str, default=None,
                        help='Specific action. hello, ping, status, block, tx, mempool, txtest.')
    parser.add_argument("--param", type=str, default=None, help='Input param from block and tx command.')
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit()
    try:
        com_helpers.MY_NODE = posclient.Posclient(args.ip, args.port, wallet="mn_temp/mn{}.json".format(args.index),
                                                  verbose=args.verbose)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(com_helpers.MY_NODE.action(args.action))

    except Exception as e:
        print(e)
