"""
Temp.

Fills reward_stats with real metrics
for a range of rounds (reward period)

"""


import argparse
import asyncio
import logging
import sys

# custom modules
sys.path.append('../modules')
import config
import hn_db
import poschain


__version__ = '0.0.2'


"""
block 800k, timestamp = 2018/08/31,12:11:25 
1535717485.55

Following POS round: 279, timestamp 1535720421
height 3921
"""

BLOCK_800K_TS = 1535717485

# Start and end rounds, inclusive
START_ROUND = 279

# Sept 8 2018, 08:00 UTC - End of Week 1
# TS = 1536393600
# PoS Round = 466 (begins at that date, therefore use 465)
END_ROUND = 465
# END_ROUND = 280

# 0.2 is nice.
MIN_SCORE = 0.2

# Paste here the real total reward to dispatch
# This formula is just an approx for on going estimates, use the real pot balance at END_ROUND end time.
REWARDS = (END_ROUND - START_ROUND + 1) * 60 * 0.8


def get_score(pos, weight, detail):
    """

    :param pos:
    :param weight:
    :param detail:
    :return:
    """
    score = 0
    # Real txs, proof of activity
    nb_txs = (detail.get('sources', 0)-detail.get('start_count', 0))
    # no incentive in tx spamming: 3 txs = 1 point, up to 3 points max for 9 tx and above
    if nb_txs >= 3:
        score += min(nb_txs, 9) / 3
    # too much = spam
    if nb_txs > 80:
        score -= 1
    forged = detail.get('forged', 0)
    # proof of forge
    if forged >= 1:
        score += 1
    # The more the weight, the more it has to be stable
    score -= detail.get('start_count', 0)/3 * weight
    # No weight here, tests are not weighted
    tests_sent = (detail.get('no_tests_sent', 0) + detail.get('ok_tests_sent', 0) + detail.get('ko_tests_sent', 0))
    # 10 tests = 1 point, 1 moint max.
    score += min(tests_sent/10, 1)
    # Needs 5 ok actions to counter one ko. non weighted. cap max number of ok?
    score += detail.get('ok_actions_received', 0) / 5
    score -= detail.get('ko_actions_received', 0)
    return score


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bismuth HyperNode reward stats filler')
    parser.add_argument("-v", "--verbose", action="count", default=False, help='Be verbose.')
    args = parser.parse_args()
    distinct = True
    verbose = True if args.verbose else False
    config.load('../main/')
    config.COMPUTING_REWARD = True

    datadir = '../main/data/'
    app_log = logging.getLogger('foo')  # FakeLog()

    print("Rewards from round {} to {}, Rewards={}".format(START_ROUND, END_ROUND, REWARDS))

    poschain = poschain.SqlitePosChain(verbose=verbose, app_log=app_log, db_path=datadir, mempool=None)
    hn_db = hn_db.SqliteHNDB(verbose=verbose, app_log=app_log, db_path=datadir)

    loop = asyncio.get_event_loop()

    # height = loop.run_until_complete(poschain.async_height())

    all_hns = {}
    all_round = {}

    loop.run_until_complete(hn_db.async_execute("DELETE FROM reward_stats WHERE 1", commit=True))
    loop.run_until_complete(hn_db.async_execute("VACUUM", commit=True))

    for round in range(START_ROUND, END_ROUND +1):
        print("Computing round {}".format(round))
        # get active HN for that round, from hypernodes table

        hns = loop.run_until_complete(hn_db.async_fetchall("SELECT address, weight, reward FROM hypernodes WHERE round = ? and active = 1", (round,)))
        hns = {hn[0]:{'weight': hn[1], 'reward': hn[2]} for hn in hns}
        # print(hns)

        details = loop.run_until_complete(poschain.async_active_hns_details(round))
        """
        dict of 
         'BSZM7PcWevqhG5T3PfF94PdcWeW6hH3DUk': {'sources': 12, 'forged': 0, 'ok_tests_sent': 8, 'ko_tests_sent': 2, 'ok_actions_received': 2}
        """
        #hn = loop.run_until_complete(hn_db.async_fetchall("SELECT address, weight FROM hypernodes WHERE active=1 AND round= ?", (round,)))
        # print(hn)
        # print(details)
        for pos, detail in details.items():
            # print(pos, detail)
            if pos in hns:
                weight = hns[pos]['weight']
                reward_address = hns[pos]['reward']
                score = get_score(pos, weight, detail)
                loop.run_until_complete(hn_db.async_execute("INSERT INTO reward_stats (round, address, weight, nblocks, "
                                                            "ntxs, nstarts, nnotests, noktests, nkotests, nokactions, "
                                                            "nkoactions, score, reward_address) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                                            (round, pos, weight, detail.get('forged', 0),
                                                            detail.get('sources', 0), detail.get('start_count', 0), detail.get('no_tests_sent', 0), detail.get('ok_tests_sent', 0), detail.get('ko_tests_sent', 0),
                                                            detail.get('ok_actions_received', 0), detail.get('ko_actions_received', 0), score, reward_address
                                                            )
                                                            ))
        loop.run_until_complete(hn_db.async_commit())

        # 0.2 : 29573 -
        # Rewards from round 279 to 440, Rewards = 7776.0



        # select address, cast(sum(weight) as double)*6672.0/25128.0 as reward from reward_stats where score >= 0.05 group by address
        # select reward_address, cast(sum(weight) as double)*6672.0/25128.0 as reward from reward_stats where score >= 0.05 group by reward_address



        # select reward_address, cast(sum(weight) as double)*7776.0/29573.0 as reward from reward_stats where score >= 0.2 group by reward_address
        # select address, cast(sum(weight) as double)*7776.0/29573.0 as reward from reward_stats where score >= 0.2 group by address

        # shn : 1134 / 7776 = 14.58%
        # 300K sur 2M = 15%
        # select address, reward_address, cast(sum(weight) as double)*7776.0/29573.0 as reward, sum(weight) as weight from reward_stats where score >= 0.2 group by address order by reward desc
        # select address, reward_address, cast(sum(weight) as double)*7776.0/29573.0 as reward, sum(weight) as weight from reward_stats where score >= 0.2 group by address order by reward desc
"""
select  sum(weight) as weight from reward_stats where score >= 0.2;
34711
select  sum(weight) as weight from reward_stats;
36612
hn pot at 811159: say 8900

select address, reward_address, cast(sum(weight) as double)*8900.0/34711.0 as reward, sum(weight) as weight from reward_stats where score >= 0.2 group by address order by reward desc;
select reward_address, cast(sum(weight) as double)*8900.0/34711.0 as reward, sum(weight) as weight from reward_stats where score >= 0.2 group by reward_address order by reward desc;

select  sum(weight) as weight from reward_stats where score >= 0;
35935
select reward_address, cast(sum(weight) as double)*8900.0/35935.0 as reward, sum(weight) as weight from reward_stats where score >= 0 group by reward_address order by reward desc;

select  sum(weight) as weight from reward_stats where score >= 0.1;
35477
select reward_address, cast(sum(weight) as double)*8900.0/35477.0 as reward, sum(weight) as weight from reward_stats where score >= 0.1 group by reward_address order by reward desc;



"""
