# Chain coupling

What I'll need:

## 1. A way to get active MNs for a round.

Input: a timestamp

Condition: The pow ledger must have at least (X) blocks after that timestamp

Output: list of MN addresses (PoS pubkeys), id addresses, locked collateral

* can be an extra API_ command
* can be a set of direct sql requests

### V1 - Only registered MNs

PoW only

### V2 - V1 + having a recorded activity (PoS side) the previous round

PoW + PoS 

### V3 - V2 + quality criterions from PoS

PoW + PoS 


## 2. PoS Payouts

### Private contract

### No single point of failure

### Criterions from PoS