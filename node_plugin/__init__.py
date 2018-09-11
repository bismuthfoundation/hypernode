"""
Plugin

Hypernode plugin

This plugin is intended to extend the node with features specifically needed by the HN companion.
"""


import json
import math
import os
import sqlite3
# import sys
import time
from ipwhois import IPWhois
from warnings import filterwarnings
# from warnings import resetwarnings


__version__ = '0.0.6'


MANAGER = None


# Has to be sync with matching params from HN - Do not edit
ORIGIN_OF_TIME = 1534716000  # Real Origin: August 20
POS_SLOT_TIME_MIN = 3
POS_SLOT_TIME_SEC = POS_SLOT_TIME_MIN * 60
MAX_ROUND_SLOTS = 19
END_ROUND_SLOTS = 1
ROUND_TIME_SEC = POS_SLOT_TIME_SEC * (MAX_ROUND_SLOTS + END_ROUND_SLOTS)

SQL_BLOCK_HEIGHT_PRECEDING_TS = "SELECT max(block_height) FROM transactions WHERE timestamp <= ?"

SQL_GET_COLOR_LIST = "SELECT openfield FROM transactions WHERE address = ? and operation = ? " \
                     "ORDER BY block_height DESC LIMIT 1"

COLORED = dict()
COLORS = ['white', 'cloud', 'brown', 'bismuth', 'gray', 'blue', 'red', 'orange', 'black', 'rainbow', 'bootstrap']
"""
Some colors are just reserved, not used yet.
white: whitelist for specific ips that could be catched by global blacklists
cloud: large cloud operators been seen to operate large number of fake or malicious nodes
brown: nodes - non miners - been seen to ask for exagerated rollbacks. Either malicious or badly configured.
bismuth: known miners ip
gray: outdated nodes, unmaintained...
blue:
red:
orange:
black: blacklist for real evil nodes
rainbow: no ip list, but some global config params that can be globally tuned without asking for posnet or code update.
bootstrap: urls of HN bootstrap file
"""

POW_CONTROL_ADDRESS = 'cf2562488992997dff3658e455701589678d0e966a79e2a037cbb2ff'

UPDATED = False

HNROUNDS_DIR = 'hnrounds/'
HNCOLORED = 'colored.json'

# TODO: from config
LEDGER_PATH = 'static/ledger.db'


filterwarnings(action="ignore")


def init_colored():
    global COLORED
    with sqlite3.connect(LEDGER_PATH, timeout=5) as db:
        try:
            for color in COLORS:
                res = db.execute(SQL_GET_COLOR_LIST, (POW_CONTROL_ADDRESS, 'color:{}'.format(color)))
                result = res.fetchone()
                if result:
                    result = result[0].strip().split(',')
                else:
                    result = []
                COLORED[color] = result
            with open(HNCOLORED, 'w') as f:
                json.dump(COLORED, f)
        except Exception as e:
            print(e)


def action_init(params):
    global MANAGER
    global DESC
    try:
        MANAGER = params['manager']
        MANAGER.app_log.warning("Init Hypernode Plugin")
    except:
        pass
    DESC = {'127.0.0.1': 'localhost'}
    try:
        os.mkdir(HNROUNDS_DIR)
    except:
        pass
    # Init colored lists while we are in solo mode
    init_colored()
    # sys.exit()
    try:
        with open("ipresolv.json", 'r') as f:
            DESC = json.load(f)
    except:
        pass


def filter_colored(colored):
    for color in COLORS:
        colored[color] = COLORED[color]
    return colored


def action_fullblock(full_block):
    """
    Update colored list on new tw
    """
    global COLORED
    for tx in full_block['transactions']:
        if tx[3] == POW_CONTROL_ADDRESS:
            # This is ours
            operation = str(tx[10])
            if operation.startswith('color:'):
                # and it's a color payload
                _, color = operation.split(':')
                items = tx[11].strip().split(',')
                COLORED[color] = items
                with open(HNCOLORED, 'w') as f:
                    json.dump(COLORED, f)


def get_desc(ip):
    global DESC
    global UPDATED
    if ip in DESC:
        desc = DESC[ip]
    else:
        # filterwarnings(action="ignore")
        obj = IPWhois(ip)
        res = obj.lookup_whois()
        desc = res.get('asn_description')
        # resetwarnings()
        if desc:
            UPDATED = True
            DESC[ip] = desc.lower()
    return desc


def filter_peer_ip(peer_ip):
    desc = get_desc(peer_ip['ip'])
    if desc:
        for cloud in COLORED['cloud']:
            if cloud in desc and (peer_ip['ip'] not in COLORED['white']):
                MANAGER.app_log.warning("Spam Filter: Blocked IP {}".format(peer_ip['ip']))
                peer_ip['ip'] = 'banned'
    return peer_ip


def filter_rollback_ip(peer_ip):
    if peer_ip['ip'] in COLORED['brown']:
        MANAGER.app_log.warning("Spam Filter: No rollback from {}".format(peer_ip['ip']))
        peer_ip['ip'] = 'no'
    return peer_ip


def timestamp_to_round_slot(ts=0):
    """
    Given a timestamp, returns the specific round and slot# that fits.

    :param ts: timestamp to use. If 0, will use current time
    :return: tuple (round, slot in round)
    """
    if ts == 0:
        ts = time.time()
    the_round = math.floor((ts - ORIGIN_OF_TIME) / ROUND_TIME_SEC)
    round_start = ORIGIN_OF_TIME + the_round * ROUND_TIME_SEC
    the_slot = math.floor((ts - round_start) / POS_SLOT_TIME_SEC)
    return the_round, the_slot


def round_to_timestamp(a_round):
    """
    Returns timestamp of the exact start of that round

    :param a_round:
    :return: int (timestamp)
    """
    round_ts = ORIGIN_OF_TIME + a_round * ROUND_TIME_SEC
    return round_ts


def test_ledger():
    with sqlite3.connect(LEDGER_PATH, timeout=5) as db:
        try:
            res = db.execute("PRAGMA table_info(transactions)")
            result = res.fetchall()
            print(result)
        except Exception as e:
            print(e)


def action_status(status):
    global UPDATED
    if UPDATED:
        # save new descriptions on status
        with open("ipresolv.json", 'w') as f:
            json.dump(DESC, f)
        UPDATED = False
