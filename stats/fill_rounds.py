#!/usr/bin/env python3
"""
Temp.

Fills unused pos_rounds with info
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from os import path

# custom modules
sys.path.append('../modules')
import config
import hn_db
import pow_interface
import poschain
from os import path


__version__ = '0.0.2'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bismuth HyperNode Round filler')
    parser.add_argument("-v", "--verbose", action="count", default=False, help='Be verbose.')
    parser.add_argument("-d", "--distinct", action="count", default=False, help='Use the distinct process (debug)')
    # parser.add_argument("-j", "--json", action="count", default=False, help='Return json content')
    args = parser.parse_args()
    distinct = True if args.distinct else False
    verbose = True if args.verbose else False
    config.load('../main/')
    config.COMPUTING_REWARD = True
    # check if db exists
    if not path.isfile(config.POW_LEDGER_DB):
        raise ValueError("Bismuth Full ledger not found at {}".format(config.POW_LEDGER_DB))
    pow = pow_interface.PowInterface(verbose=verbose)

    datadir = '../main/data/'

    app_log = logging.getLogger('foo')  # FakeLog()

    poschain = poschain.SqlitePosChain(verbose=verbose, app_log=app_log,
                                            db_path=datadir, mempool=None)
    hn_db = hn_db.SqliteHNDB(verbose=verbose, app_log=app_log, db_path=datadir)

    loop = asyncio.get_event_loop()

    height = loop.run_until_complete(poschain.async_height())
    height = height.to_dict()
    print(height)


    # get latest round
    last_round = int(height['round'])

    # TODO: store last round at the end and restart from here.

    """
    res = loop.run_until_complete(pow.load_hn_pow(datadir='../main/data', a_round=400, inactive_last_round=None,
                                                  force_all=False, no_cache=True, ignore_config=True,
                                                  distinct_process=distinct, ip='', balance_check=True))

    sys.exit()
    """
    # ok just hn regs
    # ok check balances for each round, screen alerts
    # ok check inactive last round, update
    # check slots, see if forgers bad slot
    # extract status per round, compare with status per day and % tx
    # csv export, forged round / day and total, tx / day and total

    # TODO: insert round 0?

    all_peers = []

    # get latest one from the current db, so we don't have to rebuilt all when bootstrapping

    # previous_round = 1641  # last from week 8
    if not path.isfile('week.json'):
        print("No week.json, run convert.py")
        sys.exit()
    with open('week.json', 'r') as f:
        datas = json.load(f)
    previous_round = datas['last_pos_round'] - 168
    if last_round <= datas['last_pos_round']:
        print("Error: Last round is {}, should be strictly more than {}".format(last_round, datas['last_pos_round']))
        sys.exit()
    last_round = datas['last_pos_round'] + 1
    print("Last PoS round Week n-1 ", previous_round)
    print("Last PoS round Week n ", last_round)


    for round in range(previous_round, last_round):
        # for round in range(200, 300):
        print("getting round ", round + 1)

        # This should be done on hn start, if some rounds are not filled up (old hns)

        # who was inactive last round?
        #active_hns = loop.run_until_complete(poschain.async_active_hns(round))  # sends back pos address
        # print("actives", active_hns)
        # print(all_peers)
        #inactive_hns = set(all_peers) - set(active_hns)
        #print("inactive", inactive_hns)
        # Fail safe to avoid disabling everyone on edge cases or attack scenarios
        # This does not apply to stats collection. Inactive HNs have been inactive.
        """
        if len(active_hns) < config.MIN_ACTIVE_HNS:
            # Also covers for recovering if previous round had no block because of low consensus.
            inactive_hns = []
            app_log.warning("Ignoring inactive HNs since there are not enough active ones.")
        """
        #
        inactive_hns = []
        pow.regs = {}  # reset previous regs
        # No need to consider a HN inactive. if it was inactive that round, its metrics will tell anyway.
        res = loop.run_until_complete(pow.load_hn_pow(datadir='../main/data', a_round=int(round + 1), inactive_last_round=inactive_hns,
                                                  force_all=False, no_cache=True, ignore_config=True,
                                                  distinct_process=distinct, ip='', balance_check=True))

        """if '014f78b703d3a1dd92671ee81252b7a382dadfffad9d9a1a66f1184c' in res:
            print(json.dumps(res['014f78b703d3a1dd92671ee81252b7a382dadfffad9d9a1a66f1184c']))
        else:
            print('no 014f78b703d3a1dd92671ee81252b7a382dadfffad9d9a1a66f1184c')
        """
        """
        {"01cfe422b2f1b672b0dbc0e0fe2614f59cfaf9d26459bae089e76aab": {"ip": "51.15.95.155", "port": "6969",
                                                                      "pos": "BLYkQwGZmwjsh7DY6HmuNBpTbqoRqX14ne",
                                                                      "reward": "8f2d03c817c3d36a864c99a27f6b6179eb1898a631bc007a7e0ffa39",
                                                                      "weight": 3, "timestamp": 1534711530.06,
                                                                      "active": true}}
        """
        all_peers = [item['pos'] for item in res.values()]

        # todo: do only if not exists ?
        count, hash = loop.run_until_complete(hn_db.save_hn_from_regs(res, round))
        print(count, hash)
        # time.sleep(2)
