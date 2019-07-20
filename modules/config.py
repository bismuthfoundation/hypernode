"""
Bismuth
Common variables for PoS

Also serves as config file for POC and tests
"""

import json
from hashlib import blake2b
from os import path

__version__ = "0.0.39"

"""
User config - You can change these ones, but **See doc**
Please use config.txt instead of editing here.  
It's important this config.py is the one for the current release or you will end up unsynced.

This file is only to be edited by dev or for debug purposes.
"""

VERBOSE = True

# Debug/Dev only - Never forge if True
DO_NOT_FORGE = False

# Dev only - break nice color
DEBUG = False

# Dev only, dumps sql insert params in data dir
DUMP_INSERTS = False

# FR: default log level? or just as a command line switch?

# optional log details we may want. AVAILABLE_LOGS lists all possible extra details.
# Copy the ones you want in LOG
LOG = []

AVAILABLE_LOGS = [
    "determine",
    "connections",
    "mempool",
    "srvmsg",
    "workermsg",
    "txdigest",
    "blockdigest"
    "timing",
]

# Path to the Bismuth chain
POW_LEDGER_DB = "../../Bismuth-master/static/ledger.db"

PYTHON_EXECUTABLE = "python3"

AUTO_UPDATE = True

# List of safe IPs we accept auto update requests from.
# Do not change unless you know what you're doing
ALLOW_UPDATES_FROM = "127.0.0.1;192.99.34.19;163.172.222.163;51.15.56.70"

# Some calls may be CPU intensive. limit them to some hosts (local host and official API servers)
ALLOW_QUERIES_FROM = "127.0.0.1;192.99.34.19;163.172.222.163;51.15.56.70"
"""
Here comes temp. PoC variables
"""

# The reference list of active Hypernodes for the round
# address, ip, port, weight, bis_registrar, bis_recipient
POC_HYPER_NODES_LIST_0 = [
    (
        "BLYkQwGZmwjsh7DY6HmuNBpTbqoRqX14ne",
        "127.0.0.1",
        6969,
        1,
        "bis_addr_0",
        "bis_addr_0",
    ),  # hn 0
    (
        "BHbbLpbTAVKrJ1XDLMM48Qa6xJuCGofCuH",
        "127.0.0.1",
        6970,
        2,
        "bis_addr_1",
        "bis_addr_1",
    ),
    (
        "B8stX39s5NBFx746ZX5dcqzpuUGjQPJViC",
        "127.0.0.1",
        6971,
        1,
        "bis_addr_2",
        "bis_addr_2",
    ),
    (
        "BMSMNNzB9qdDp1vudRZoge4BUZ1gCUC3CV",
        "127.0.0.1",
        6972,
        1,
        "bis_addr_3",
        "bis_addr_3",
    ),
    (
        "BNJp77d1BdoaQu9HEpGjKCsGcKqsxkJ7FD",
        "127.0.0.1",
        6973,
        1,
        "bis_addr_4",
        "bis_addr_3",
    )
    # on purpose, 3 and 4 have same recipient address
]

POC_HYPER_NODES_LIST = []

# Leave True for Real world use.
# if False - DEV ONLY - hn_instance will load from hn_temp dir.
LOAD_HN_FROM_POW = True
# DEV only - number of test HN to consider. 49 max. - Unused for real world.
MAX_DEBUG_HN = 20

# The broadhash of the previous round determines the shuffle.
# block hashes and broad hashes are 20 bytes
# Not used except for tests.
POC_LAST_BROADHASH = b"123456789abcdef12345"

# Local node
POW_IP = '127.0.0.1'
# Local pow port
POW_PORT = 5658

"""
Here comes tuneable algorithm variables - Do not change those or you will fork or be unable to sync
"""

# Wednesday Sept 12, 08:00 UTC + 1Day
#  TS = 1536739200 + 1day
# Round = 562 => 586
# NEXT_HF_AT_ROUND = 586

# required version of the plugin version
PLUGIN_VERSION = "0.1.0"

# required minimal version of the node
REQUIRED_NODE_VERSION = "4.3.0.6"

# POC - Will be taken from config - Always 10 chars
# TODO: enforce 10 chars when assembling chain
POSNET = "posnet0002"
# I messed up with previous config, why we still need to support posnet0001.
# Will be gone with next update.
POSNET_ALLOW = "posnet0001;posnet0002;posnet0003"

# Default hard coded url.
BOOTSTRAP_URLS = ["http://bp12.eggpool.net/hn_bs.tar.gz"]

# Network Byte ID - 0x19 = Main PoS Net 'B' - 0x55 Test PoS Net 'b'
NETWORK_ID = b"\x19"
# NETWORK_ID = b'\x55'

# Default Hypernodes port
DEFAULT_PORT = 6969

# How many peers at most to try to connect to?
MAX_CONNECT_TO = 40

# If too few HNs are marked as active, ignore inactive ones.
MIN_ACTIVE_HNS = 10

# How many blocks - at most - to send in a single message when syncing catching up nodes
# TODO: Estimate block size depending on the HN count
BLOCK_SYNC_COUNT = 20

# How long to wait in the main client loop
WAIT = 10

# How long between status reports - status are intensive to build, 30 sec min, 5 min max (300 sec) - 1 min default.
STATUS_EVERY = 60

# Wait time when catching up, to speed things up.
SHORT_WAIT = 0.001

# How long to wait before retrying a failed peer?
PEER_RETRY_SECONDS = 20

# Seconds between pings
PING_DELAY = 30

# limit, so nodes won't want to play with that.
FUTURE_ALLOWED = 5

# Duration of a PoS slot in minute - each slot can be filled by a block (or stay empty)
# POS_SLOT_TIME_MIN = 5  # POC test
POS_SLOT_TIME_MIN = 3  # Real world setting?
POS_SLOT_TIME_SEC = POS_SLOT_TIME_MIN * 60

# How many slots in a round? Better keep them an odd number.
# MAX_ROUND_SLOTS = 3  # POC test
# MAX_ROUND_SLOTS = 3  # POC test
MAX_ROUND_SLOTS = 19  # Real world. 19+1 = 20 , 3x20 = 60 (round time)

# To be adjusted depending on connectivity and HNs number.
MIN_FORGE_CONSENSUS = 18
MIN_FORGE_CONSENSUS_LOW = 11

# How many block times to wait at the end of a round to reach consensus?
END_ROUND_SLOTS = 1

# How many tests should the whole Net perform per slot?
# each test will issue 2 messages, one from the tester, the other from the testee
# 19 slots per round. 10 tests per slots, check
TESTS_PER_SLOT = 10

# We can run several type of tests. They are indexed by a byte. This can evolve with time.
TESTS_TYPE = [0, 1, 2, 3, 4]

# Block validation Criteria

# Should be less than TESTS_PER_SLOT*2
REQUIRED_MESSAGES_PER_BLOCK = 4
REQUIRED_SOURCES_PER_BLOCK = 3

# This is a constant. Time for block 0, slot 0 of the PoS chain. Can't change once launched.
# ORIGIN_OF_TIME = 1522419000  # Legacy tests
# ORIGIN_OF_TIME = 1533980000  # First tests with 1 hour round time, 3 min slot time.
ORIGIN_OF_TIME = 1534716000  # Real Origin: August 20


# Do not change these - Private contract controller.
POS_CONTROL_ADDRESS = "BKYnuT4Pt8xfZrSKrY3mUyf9Cd9qJmTgBn"
POW_CONTROL_ADDRESS = "cf2562488992997dff3658e455701589678d0e966a79e2a037cbb2ff"
# Round time in seconds
ROUND_TIME_SEC = POS_SLOT_TIME_SEC * (MAX_ROUND_SLOTS + END_ROUND_SLOTS)

# Genesis block
GENESIS_SEED = "BIG_BANG_HASH"
GENESIS_HASH = blake2b(GENESIS_SEED.encode("utf-8"), digest_size=20)
GENESIS_ADDRESS = "BKYnuT4Pt8xfZrSKrY3mUyf9Cd9qJmTgBn"
GENESIS_SIGNATURE = ""
# TODO: check chain: verify that fits.


"""
DEBUG VARS
"""

POW_DISTINCT_PROCESS = False
PROCESS_TIMEOUT = 25
POW_ALTERNATE_URL = ""

"""
Global Variables
"""

COMPUTING_REWARD = False

STOP_EVENT = None

# --------------------------------------------------- #

# The potential variables and their type
VARS = {
    "POW_LEDGER_DB": "str",
    "LOG": "list",
    "MAX_CONNECT_TO": "int",
    "BLOCK_SYNC_COUNT": "int",
    "WAIT": "int",
    "STATUS_EVERY": "int",
    "SHORT_WAIT": "float",
    "PEER_RETRY_SECONDS": "int",
    "PYTHON_EXECUTABLE": "str",
    "POW_DISTINCT_PROCESS": "bool",
    "POW_ALTERNATE_URL": "str",
    "AUTO_UPDATE": "bool",
    "ALLOW_UPDATES_FROM": "str",
    "ALLOW_QUERIES_FROM": "str",
    "POW_IP": "str",
    "POW_PORT": "int",
}
# These two have been removed from config - POSNET depends on code, not config, and POSNET_WALLOW comes from the PoW.
# "POSNET": "str",
# "POSNET_ALLOW": "list",

COLORED_VARS = {
    # "POW_LEDGER_DB": "str",
    # "LOG": "list",
    # "POSNET": "str",
    "POSNET_ALLOW": "list",
    "MAX_CONNECT_TO": "int",
    "BLOCK_SYNC_COUNT": "int",
    # "WAIT": "int",
    # "SHORT_WAIT": "float",
    # "PEER_RETRY_SECONDS": "int",
    # "PYTHON_EXECUTABLE": "str",
    # "POW_DISTINCT_PROCESS": "bool",
    # "AUTO_UPDATE": "bool",
    "ALLOW_UPDATES_FROM": "str",
    "TESTS_PER_SLOT": "int",
    "PING_DELAY": "int",
    "MIN_FORGE_CONSENSUS": "int",
}


def get_left_right(line, var_list):
    left, right = map(str.strip, line.rstrip("\n").split("="))
    if left not in var_list:
        return None, None
    param = var_list[left]
    if param == "int":
        right = int(right)
    elif param == "float":
        right = float(right)
    elif param == "list":
        # Separator may be ; or ,
        right = [str(item.strip()) for item in right.replace(";", ",").split(",")]
    elif param == "bool":
        if right.lower() in ["false", "0", "", "no"]:
            right = False
        else:
            right = True
    else:
        # treat as "str"
        pass
    return left, right


def overload(file_name: str):
    for line in open(file_name):
        if line and line[0] == "#":
            continue
        if "=" in line:
            left, right = get_left_right(line, VARS)
            if left:
                globals().update({left: right})


def update_colored():
    # Check colored from plugin - if exists - and overload again
    colored_file_name = POW_LEDGER_DB.replace("static/ledger.db", "colored.json")
    if path.isfile(colored_file_name):
        with open(colored_file_name) as f:
            colored = json.load(f)
            rainbow = colored.get("rainbow")
            for key_value in rainbow:
                left, right = get_left_right(key_value, COLORED_VARS)
                if left:
                    # print("Set {}={} from rainbow".format(left, right))
                    globals().update({left: right})
            bootstrap = colored.get("bootstrap")
            if bootstrap:
                globals().update({"BOOTSTRAP_URLS": bootstrap})


def load(prefix: str = ""):
    """
    Overload info with config.default.txt and config.txt
    :return:
    """
    overload(prefix + "config.default.txt")
    if path.exists(prefix + "config.txt"):
        overload(prefix + "config.txt")
    update_colored()

    return {var: globals()[var] for var in VARS}


if __name__ == "__main__":
    print("I'm a module, can't run!")
