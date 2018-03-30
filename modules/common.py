"""
Bismuth
Common variables and helpers for PoS

Serves as config file for POC and tests
"""
import poscrypto

__version__ = '0.0.1'

# POC prefix is for POC only, will use real data later.

# The reference list of active Masternodes for the round
# hex pubkey, ip, port, weight
POC_MASTER_NODES_LIST = [
    ('aa012345678901aa', '127.0.0.1', 6969, 1),
    ('bb123456789012bb', '127.0.0.1', 6970, 2),
    ('cc234567890123cc', '127.0.0.1', 6971, 1),
    ('dd345678901234dd', '127.0.0.1', 6972, 1),
    ('ee456789012345ee', '127.0.0.1', 6973, 1)
    ]

# The broadhash of the previous round determines the shuffle.
POC_LAST_BROADHASH = poscrypto.blake('POC')

"""
Here comes tuneable algorithm variables 
"""

# Duration of a PoS slot in minute - each slot can be filled by a block (or stay empty)
POS_SLOT_TIME = 5

# How many slots in a round? Better keep them an odd number.
MAX_ROUND_SLOTS = 3

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




if __name__ == "__main__":
    print("I'm a module, can't run!")