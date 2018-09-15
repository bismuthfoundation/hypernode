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


__version__ = '0.0.1'


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

    previous_round = 465  # last from week 1

    for round in range(previous_round, last_round):
        # for round in range(200, 300):
        print("getting round ", round + 1)

        # This should be done on hn start, if some rounds are not filled up (old hns)

        # who was inactive last round?
        active_hns = loop.run_until_complete(poschain.async_active_hns(round))  # sends back pos address
        # print(all_peers)
        inactive_hns = set(all_peers) - set(active_hns)
        # print(inactive_hns)
        # Fail safe to avoid disabling everyone on edge cases or attack scenarios
        if len(active_hns) < config.MIN_ACTIVE_HNS:
            # Also covers for recovering if previous round had no block because of low consensus.
            inactive_hns = []
            app_log.warning("Ignoring inactive HNs since there are not enough active ones.")

        res = loop.run_until_complete(pow.load_hn_pow(datadir='../main/data', a_round=int(round + 1), inactive_last_round=inactive_hns,
                                                  force_all=False, no_cache=True, ignore_config=True,
                                                  distinct_process=distinct, ip='', balance_check=True))
        # print(json.dumps(res))
        """
        {"01cfe422b2f1b672b0dbc0e0fe2614f59cfaf9d26459bae089e76aab": {"ip": "51.15.95.155", "port": "6969",
                                                                      "pos": "BLYkQwGZmwjsh7DY6HmuNBpTbqoRqX14ne",
                                                                      "reward": "8f2d03c817c3d36a864c99a27f6b6179eb1898a631bc007a7e0ffa39",
                                                                      "weight": 3, "timestamp": 1534711530.06,
                                                                      "active": true}}
        """
        all_peers = [item['pos'] for item in res.values()]



        # todo: do only if not exists ?
        loop.run_until_complete(hn_db.save_hn_from_regs(res, round))

        # time.sleep(2)
