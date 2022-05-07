#!/usr/bin/env python3
"""
Calc and exports HN rewards for a week, from stats.
"""


import argparse
import asyncio
import logging
import sys

# custom modules
sys.path.append('../modules')
import config
import hn_db
import json
import poschain
from os import path


__version__ = '0.0.3'

SCORE_TRIGGER = 0.0

if __name__ == "__main__":
    verbose = False

    datadir = '../main/data/'
    app_log = logging.getLogger('foo')  # FakeLog()

    if not path.isfile('week.json'):
        print("No week.json, run convert.py")
        sys.exit()
    with open('week.json', 'r') as f:
        datas = json.load(f)
    WEEK = datas['week']
    BALANCE = datas['balance']

    print("Calc Rewards for Week {}".format(WEEK))

    hn_db = hn_db.SqliteHNDB(verbose=verbose, app_log=app_log, db_path=datadir)
    loop = asyncio.get_event_loop()

    total_weights = loop.run_until_complete(hn_db.async_fetchone('select sum(weight) as weight from reward_stats where score >= ?', (SCORE_TRIGGER,)))[0]
    print("Total Weights at {}: {}".format(SCORE_TRIGGER, total_weights))
    full_weights = loop.run_until_complete(hn_db.async_fetchone('select sum(weight) as weight from reward_stats'))[0]
    print("Full Weights: {}".format(full_weights))
    loss_pc = (full_weights - total_weights) / full_weights * 100
    print("Loss: {:.2f}%".format(loss_pc))

    if path.isfile('rewards/week{}_per_reward_address.csv'.format(WEEK)):
        print("csv file already there, *not* overwriting")
        #sys.exit()
    if path.isfile('rewards/week{}_per_hn_address.csv'.format(WEEK)):
        print("csv file already there, *not* overwriting")
        #sys.exit()

    sql = "select address, reward_address, cast(sum(weight) as double)*?/? as reward, sum(weight) as weight , max(weight) as collateral from reward_stats where score >= ? group by address order by reward desc"
    per_reward = loop.run_until_complete(hn_db.async_fetchall(sql, (float(BALANCE), float(total_weights), SCORE_TRIGGER)))
    max_reward = per_reward[0][2]
    token_unit = max_reward * 0.5 / per_reward[0][4]
    print(f"Max Reward {max_reward:0.2f} BIS, Token unit {token_unit:0.2f}")
    tokens_rewards = {}
    total_tokens_rewards = 0
    with open('rewards/week{}_per_hn_address.csv'.format(WEEK), 'w') as f:
        f.write("address,reward_address,reward,total_weight,weight\n")
        for row in per_reward:
            f.write("{},{},{},{}, {}\n".format(row[0], row[1], row[2], row[3], row[4]))
            reward_address = row[1]
            reward = row[2]
            weight = row[4]
            token_reward = weight if (reward / weight) >= token_unit else 0
            total_tokens_rewards += token_reward
            # token_reward *= weight
            tokens_rewards[reward_address] = tokens_rewards.get(reward_address, 0) + token_reward
    print(f"Total token rewards {total_tokens_rewards}")

    sql = "select reward_address, cast(sum(weight) as double)*?/? as reward, sum(weight) as weight from reward_stats where score >= ? group by reward_address order by reward desc"
    per_reward = loop.run_until_complete(hn_db.async_fetchall(sql, (float(BALANCE), float(total_weights), SCORE_TRIGGER)))
    with open('rewards/week{}_per_reward_address.csv'.format(WEEK), 'w') as f:
        f.write("reward_address,reward,total_weights,total_tokens\n")
        for row in per_reward:
            # print(list(row))
            try:
                f.write("{},{},{},{}\n".format(row[0], row[1], row[2], tokens_rewards[row[0]]))
            except Exception as e:
                print(e)
