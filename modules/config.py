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
# Copy the ones you want in LOG
LOG = []
AVAILABLE_LOGS = ['connections']

"""
Here comes temp. PoC variables
"""

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
Here comes tuneable algorithm variables - Do not change those or you will fork
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

# Genesis block
GENESIS_SEED = 'BIG_BANG_HASH'
GENESIS_HASH = blake2b(GENESIS_SEED.encode('utf-8'), digest_size=20)
GENESIS_ADDRESS = 'BLYkQwGZmwjsh7DY6HmuNBpTbqoRqX14ne'
GENESIS_SIGNATURE = ''
# TODO: check chain: verify that fits.


if __name__ == "__main__":
    print("I'm a module, can't run!")