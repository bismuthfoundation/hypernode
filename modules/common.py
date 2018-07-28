"""
Bismuth
Common variables and helpers for PoS

Also serves as config file for POC and tests
"""

import os
import shutil
import requests
import tarfile
# from collections import OrderedDict
from hashlib import blake2b

__version__ = '0.0.17'

# POC - Will be taken from config - Always 10 chars
# TODO: enforce 10 chars
POSNET = 'posnet0001'
POSNET_ALLOW = 'posnet0001,posnet0002'

# Network Byte ID - 0x19 = Main PoS Net 'B' - 0x55 Test PoS Net 'b'
NETWORK_ID = b'\x19'
# NETWORK_ID = b'\x55'

VERBOSE = True

# How long to wait in the main client loop
WAIT = 10

# Wait time when catching up, to speed things up.
SHORT_WAIT = 0.001

# How long to wait before retrying a failed peer?
PEER_RETRY_SECONDS = 20

# Seconds between pings
PING_DELAY = 30

# limit, so nodes won't want to play with that.
FUTURE_ALLOWED = 5

# How many blocks - at most - to send in a single message when syncing catching up nodes
# TODO: Estimate block size depending on the HN count
BLOCK_SYNC_COUNT = 10

# Debug/Dev only - Never forge if True
DO_NOT_FORGE = False

# Dev only - break nice color
DEBUG = False

# The reference list of active Hypernodes for the round
# address, ip, port, weight
POC_HYPER_NODES_LIST = [
    ('BLYkQwGZmwjsh7DY6HmuNBpTbqoRqX14ne', '127.0.0.1', 6969, 1),  # hn 0
    ('BHbbLpbTAVKrJ1XDLMM48Qa6xJuCGofCuH', '127.0.0.1', 6970, 2),
    ('B8stX39s5NBFx746ZX5dcqzpuUGjQPJViC', '127.0.0.1', 6971, 1),
    ('BMSMNNzB9qdDp1vudRZoge4BUZ1gCUC3CV', '127.0.0.1', 6972, 1),
    ('BNJp77d1BdoaQu9HEpGjKCsGcKqsxkJ7FD', '127.0.0.1', 6973, 1)
    ]

# The broadhash of the previous round determines the shuffle.
# block hashes and broad hashes are 20 bytes
POC_LAST_BROADHASH = b"123456789abcdef12345"

"""
Here comes tuneable algorithm variables 
"""

# Duration of a PoS slot in minute - each slot can be filled by a block (or stay empty)
POS_SLOT_TIME_MIN = 5
POS_SLOT_TIME_SEC = POS_SLOT_TIME_MIN * 60

# How many slots in a round? Better keep them an odd number.
MAX_ROUND_SLOTS = 3

# How many block times to wait at the end of a round to reach consensus?
END_ROUND_SLOTS = 1

# How many tests should the whole Net perform per slot?
# each test will issue 2 messages, one from the tester, the other from the testee
TESTS_PER_SLOT = 5

# We can run several type of tests. They are indexed by a byte. This can evolve with time.
TESTS_TYPE = [0, 1, 2, 3, 4]

# Block validation Criteria

# Should be less than TESTS_PER_SLOT*2
REQUIRED_MESSAGES_PER_BLOCK = 4
REQUIRED_SOURCES_PER_BLOCK = 3

# This is a constant. Time for block 0, slot 0 of the PoS chain. Can't change once launched.
ORIGIN_OF_TIME = 1522419000


# Round time in seconds
ROUND_TIME_SEC = POS_SLOT_TIME_SEC * (MAX_ROUND_SLOTS + END_ROUND_SLOTS)


GENESIS_SEED = 'BIG_BANG_HASH'
GENESIS_HASH = blake2b(GENESIS_SEED.encode('utf-8'), digest_size=20)
GENESIS_ADDRESS = 'BLYkQwGZmwjsh7DY6HmuNBpTbqoRqX14ne'
GENESIS_SIGNATURE = ''

# GENERIC HELPERS


def download_file(url, filename):
    """
    Fetch a file from an URL with progress indicator

    :param url:
    :param filename:
    :return:
    """
    r = requests.get(url, stream=True)
    total_size = int(r.headers.get('content-length')) / 1024
    with open(filename, 'wb') as filename:
        chunkno = 0
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                chunkno = chunkno + 1
                if chunkno % 10000 == 0:  # every x chunks
                    print("Downloaded {} %".format(int(100 * (chunkno / total_size))))
                filename.write(chunk)
                filename.flush()
        print("Downloaded 100 %")


def update_source(url, app_log=None):
    """
    Update source file from an url

    :param url: url of the tgz archive
    :param app_log: optional log handler
    :return:
    """
    try:
        archive_path = "./hnd.tgz"
        download_file(url, archive_path)
        tar = tarfile.open(archive_path)
        tar.extractall("./")
        tar.close()
        # move to current dir
        from_dir = "./hnd_zip/"
        files = os.listdir(from_dir)
        for f in files:
            shutil.move(from_dir + f, './' + f)
    except Exception as e:
        if app_log:
            app_log.warning("Something went wrong in update_source: {}, aborted".format(e))
        raise


def same_height(peer_status, our_status):
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


def first_height_is_better(height_a, height_b):
    """
    Compares properties of the heights to tell which one is to keep in case of forks.
    Uses 'forgers', 'forgers_round', 'uniques', 'uniques_round', 'round', 'height'

    :param height_a:
    :param height_b:
    :return: Boolean, True if a is > b
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
    """if height_a['uniques'] > height_b['uniques']:
        return True
    """
    return False


def heights_match(height_a, height_b):
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


def peer_to_fullpeer(peer):
    """
    converts a tuple (address, ip, port, active) to a string ip:0port

    :param peer:
    :return:
    """
    return peer[1] + ':' + str(peer[2]).zfill(5)


def ipport_to_fullpeer(ip, port):
    return ip + ':' + str(port).zfill(5)


if __name__ == "__main__":
    print("I'm a module, can't run!")
