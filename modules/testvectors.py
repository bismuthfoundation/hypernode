"""
Test constants to be used at different places.
Dev only.
"""

import config

POW_HN_CURSOR = [
    (0, 'bis1', 'hypernode:register', 'ip1:port:pos1', 0),  # first valid HN
    (1, 'bis2', 'hypernode:register', 'ip2:port:pos2,reward=bis2a', 0),  # second valid HN wit opt reward
    (2, 'bis1', 'hypernode:register', 'ip3:port:pos1', 0),  # same address tries to register with a new ip (ko)
    (2, 'bis1', 'hypernode:register', 'ip1c:port:pos1c', 0),  # same pow address tries to register again(ko)
    (2, 'bis1', 'hypernode:register', 'ip1:port:pos1', 0),
    # same address tries to register with same params (ok, after auto unreg?)
    (3, 'bis2', 'hypernode:register', 'ip2:port:pos2b', 0),  # hn2 tries to change pos address, ko
    (4, 'bis3', 'hypernode:register', 'ip1:port:pos1b', 0),  # someone tries to register an existing HN (same ip)
    (5, 'bis4', 'hypernode:register', 'ip4:port:pos4', 0),  # valid HN
    (6, 'bis4', 'hypernode:unregister', 'ip4:port:pos4', 0),  # valid unreg HN
    (7, 'bis4', 'hypernode:register', 'ip4:port:pos4', 0),  # valid HN
    (8, 'bis4', 'hypernode:unregister', 'ip4:port:pos4b', 0),  # invalid unreg HN
    (8, config.POS_CONTROL_ADDRESS, 'hypernode:unregister', 'ip4:port:pos4', 0),  # valid pos controlled unreg HN
    ]
