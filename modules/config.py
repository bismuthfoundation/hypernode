"""
Bismuth
Common variables for PoS

Also serves as config file for POC and tests
"""

from hashlib import blake2b

__version__ = '0.0.18'

"""
User config - You can change these one - See doc
"""

VERBOSE = True

# Debug/Dev only - Never forge if True
DO_NOT_FORGE = False

# Dev only - break nice color
DEBUG = False

# FR: default log level? or just as a command line switch?

# optional log details we may want. AVAILABLE_LOGS lists all possible extra details.
# Copy the ones you want in LOG
LOG = []
AVAILABLE_LOGS = ['connections']

# Path to the Bismuth chain
# TODO: override by config.json, see notes.md
POW_LEDGER_DB = "../../Bismuth-master/static/ledger.db"


"""
Here comes temp. PoC variables
"""

# The reference list of active Hypernodes for the round
# address, ip, port, weight, bis_registrar, bis_recipient
POC_HYPER_NODES_LIST_0 = [
    ('BLYkQwGZmwjsh7DY6HmuNBpTbqoRqX14ne', '127.0.0.1', 6969, 1, "bis_addr_0", "bis_addr_0"),  # hn 0
    ('BHbbLpbTAVKrJ1XDLMM48Qa6xJuCGofCuH', '127.0.0.1', 6970, 2, "bis_addr_1", "bis_addr_1"),
    ('B8stX39s5NBFx746ZX5dcqzpuUGjQPJViC', '127.0.0.1', 6971, 1, "bis_addr_2", "bis_addr_2"),
    ('BMSMNNzB9qdDp1vudRZoge4BUZ1gCUC3CV', '127.0.0.1', 6972, 1, "bis_addr_3", "bis_addr_3"),
    ('BNJp77d1BdoaQu9HEpGjKCsGcKqsxkJ7FD', '127.0.0.1', 6973, 1, "bis_addr_4", "bis_addr_3")
    # on purpose, 3 and 4 have same recipient address
    ]

POC_HYPER_NODES_LIST = []

# Leave True for Real world use.
# if False - DEV ONLY - hn_instance will load from hn_temp dir.
LOAD_HN_FROM_POW = False

# The broadhash of the previous round determines the shuffle.
# block hashes and broad hashes are 20 bytes
POC_LAST_BROADHASH = b"123456789abcdef12345"


"""
Here comes tuneable algorithm variables - Do not change those or you will fork or be unable to sync
"""

# POC - Will be taken from config - Always 10 chars
# TODO: enforce 10 chars when assembling chain
POSNET = 'posnet0001'
POSNET_ALLOW = 'posnet0001,posnet0002'

# Network Byte ID - 0x19 = Main PoS Net 'B' - 0x55 Test PoS Net 'b'
NETWORK_ID = b'\x19'
# NETWORK_ID = b'\x55'

# Default Hypernodes port
DEFAULT_PORT = 6960

# How many peers at most to try to connect to?
MAX_CONNECT_TO = 25

# If too few HNs are marked as active, ignore inactive ones.
MIN_ACTIVE_HNS = 10

# How many blocks - at most - to send in a single message when syncing catching up nodes
# TODO: Estimate block size depending on the HN count

BLOCK_SYNC_COUNT = 20
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

# Duration of a PoS slot in minute - each slot can be filled by a block (or stay empty)
POS_SLOT_TIME_MIN = 5  # POC test
POS_SLOT_TIME_MIN = 3  # Real world setting?
POS_SLOT_TIME_SEC = POS_SLOT_TIME_MIN * 60

# How many slots in a round? Better keep them an odd number.
MAX_ROUND_SLOTS = 3  # POC test
MAX_ROUND_SLOTS = 19  # Real world. 19+1 = 20 , 3x20 = 60 (round time)

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
ORIGIN_OF_TIME = 1522419000  # Legacy tests
ORIGIN_OF_TIME = 1533980000  # Firsts tests with 1 hour round time, 3 min slot time.

# Do not change this.
POS_CONTROL_ADDRESS = '3e08b5538a4509d9daa99e01ca5912cda3e98a7f79ca01248c2bde16'

# Round time in seconds
ROUND_TIME_SEC = POS_SLOT_TIME_SEC * (MAX_ROUND_SLOTS + END_ROUND_SLOTS)

# Genesis block
GENESIS_SEED = 'BIG_BANG_HASH'
GENESIS_HASH = blake2b(GENESIS_SEED.encode('utf-8'), digest_size=20)
GENESIS_ADDRESS = 'BLYkQwGZmwjsh7DY6HmuNBpTbqoRqX14ne'
GENESIS_SIGNATURE = ''
# TODO: check chain: verify that fits.


if __name__ == "__main__":
    print("I'm a module, can't run!")
