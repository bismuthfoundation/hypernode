"""
Bismuth
Common helpers for PoS
"""

import json
import logging
import os
import random
import sys
import tarfile
from operator import itemgetter

import requests
from logging import getLogger

import config
import poscrypto

__version__ = '0.0.7'


# GENERIC HELPERS ##############################################################


def download_file(url: str, filename: str):
    """
    Fetch a file from an URL with progress indicator

    :param url:
    :param filename:
    :return:
    """
    app_log = getLogger("tornado.application")
    r = requests.get(url, stream=True)
    total_size = int(r.headers.get('content-length')) / 1024
    with open(filename, 'wb') as filename:
        chunkno = 0
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                chunkno = chunkno + 1
                if chunkno % 10000 == 0:  # every x chunks
                    app_log.info("Downloaded {} %".format(int(100 * (chunkno / total_size))))
                filename.write(chunk)
                filename.flush()
        app_log.info("Downloaded 100 %")


def bootstrap(datadir):
    """
    Get the bootstrap archive and extract to the given datadir

    :param datadir:
    """
    # print("Udating {} from {}".format(datadir, config.BOOTSTRAP_URLS))
    if not len(config.BOOTSTRAP_URLS):
        return False
    url = random.choice(config.BOOTSTRAP_URLS)
    archive_path = "{}/hn_bs.tar.gz".format(datadir)
    download_file(url, archive_path)
    with tarfile.open(archive_path) as tar:
        tar.extractall(datadir)
    return True


def update_source(url: str, app_log: logging.log=None):
    """
    Update source file from an url

    :param url: url of the tgz archive
    :param app_log: optional log handler
    :return:
    """
    try:
        archive_path = "../../hypernode.tar.tgz"
        download_file(url, archive_path)
        tar = tarfile.open(archive_path)
        tar.extractall("../../")
        tar.close()
        """
        # move to current dir
        from_dir = "./hypernode/"
        files = os.listdir(from_dir)
        print("Files", files)
        sys.exit()
        for f in files:
            shutil.move(from_dir + f, './' + f)
        """
    except Exception as e:
        if app_log:
            app_log.warning("Something went wrong in update_source: {}, aborted".format(e))
        raise

# DB #####################################################################


def bool_to_dbstr(a_bool:bool):
    return '1' if a_bool else '0'


# Height Helpers #####################################################################


def same_height(peer_status: dict, our_status: dict):
    """
    Compares not only the height but the whole properties, including Round, Slot In Round and block hash.

    :param peer_status:
    :param our_status:
    :return: Boolean
    """
    for key in ("height", "round", "sir", "block_hash"):
        if peer_status[key] != our_status[key]:
            return False
    return True


def first_height_is_better(height_a: dict, height_b: dict):
    """
    Compares properties of the heights to tell which one is to keep in case of forks.
    Uses 'forgers', 'forgers_round', 'uniques', 'uniques_round', 'round', 'height'

    :param height_a:
    :param height_b:
    :return: Boolean, True if a is > b
    """
    """
    if height_a['forgers'] > height_b['forgers']:
        return True
    if height_a['forgers_round'] > height_b['forgers_round']:
        return True
    if height_a['uniques_round'] > height_b['uniques_round']:
        return True
    if height_a['round'] > height_b['round']:
        return True
    if height_a['height'] > height_b['height']:
        return True
    # TODO: use timestamp instead?
    if height_a['block_hash'] > height_b['block_hash']:
        return True
    return False
    """
    if height_a['block_hash'] == height_b['block_hash']:
        return False
    sorted_heights = sorted([height_a, height_b],
                          key=itemgetter('forgers', 'uniques', 'round', 'height', 'forgers_round',
                                         'uniques_round', 'block_hash'),
                          reverse=True)
    return sorted_heights[0]['block_hash'] == height_a['block_hash']


def heights_match(height_a: dict, height_b: dict):
    """
    Checks if simulated height_b fits the predicate height_a
    only checks the current round info, not the whole chain.

    :param height_a: a height dict
    :param height_b: a height dict
    :return: boolean
    """
    for key in ('height', 'round', 'sir', 'block_hash', 'uniques_round', 'forgers_round'):
        if height_a.get(key) != height_b.get(key):
            return False
    return True


# Peer format helpers ###########################################################################

def peer_to_fullpeer(peer: tuple):
    """
    converts a tuple (address, ip, port, active) to a string ip:0port

    :param peer:
    :return:
    """
    return peer[1] + ':' + str(peer[2]).zfill(5)


def ipport_to_fullpeer(ip: str, port: int):
    return ip + ':' + str(port).zfill(5)


# Various helpers ###########################################################################

def hello_string(port: int=101, posnet: str=None, address: str=None):
    """
    Build hello string from params.

    :param port: port number
    :param posnet: posnet version
    :param address: pos address
    :return:
    """
    posnet = config.POSNET if not posnet else posnet
    if len(posnet) != 10:
        raise ValueError("posnet len is wrong: ''".format(posnet))
    address = poscrypto.ADDRESS if not address else address
    poscrypto.validate_address(address)  # Will raise if invalid
    return posnet + str(port).zfill(5) + address


def hello_to_params(hello:str, as_dict=False):
    posnet, port, peer_address = hello[:10], hello[10:15], hello[15:]
    if as_dict:
        return {'posnet': posnet, 'port':int(port), 'address': peer_address}
    return posnet, port, peer_address


def load_hn_temp():
    """
    fill list of HNs from our local repo, for dev at scale.

    Do NOT use in prod ever.

    :return: None
    """
    config.POC_HYPER_NODES_LIST = []
    try:
        i = 0
        random.seed('my_fixed_seed')
        weight_profile = [1, 1, 1, 1, 1, 1, 2, 2, 2, 3, 3]
        while os.path.isfile("hn_temp/mn{}.json".format(i)):
            with open("hn_temp/mn{}.json".format(i)) as f:
                hn = json.load(f)
                #  ('B8stX39s5NBFx746ZX5dcqzpuUGjQPJViC', '127.0.0.1', 6971, 1, "bis_addr_2", "bis_addr_2"),
                # Weight distribution
                weight = random.choice(weight_profile)
                hn_tuple = (hn['address'], '127.0.0.1', 6969 + i, weight, "bis_addr_{}".format(i), "bis_addr_{}".format(i))
                config.POC_HYPER_NODES_LIST.append(hn_tuple)
            i += 1
        # print(config.POC_HYPER_NODES_LIST)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
        sys.exit()


def fake_hn_dict(inactive_last_round, app_log):
    """
    Simulates getting HN info from the Pow, but takes from the hn_temp instead. DEV/Debug only

    Do NOT use in prod ever.

    Indexed by bis_addr, sub dict keys: ['ip', 'port', 'pos', 'reward', 'weight', 'timestamp', 'active']

    :return: dict of dict.
    """
    try:
        i = 0
        regs = {}
        random.seed('my_fixed_seed')
        weight_profile = [1, 1, 1, 1, 1, 1, 2, 2, 2, 3, 3]
        while os.path.isfile("hn_temp/mn{}.json".format(i)):
            with open("hn_temp/mn{}.json".format(i)) as f:
                hn = json.load(f)
                # Weight distribution
                weight = random.choice(weight_profile)
                regs["bis{}".format(i)] = dict(zip(['ip', 'port', 'pos', 'reward', 'weight', 'timestamp', 'active'],
                                              ['127.0.0.1', 6969 + i, hn['address'], "bis{}".format(i), weight, 0, True]))
            i += 1
            if i > config.MAX_DEBUG_HN:
                break
        for address, items in regs.items():
            if items['pos'] in inactive_last_round:
                regs[address]['active'] = False
        return regs
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
        sys.exit()


if __name__ == "__main__":
    print("I'm a module, can't run!")
