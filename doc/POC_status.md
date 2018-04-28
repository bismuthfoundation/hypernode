# Status of the POC Code

# 1 Start of Round

(To be updated with new addresses of MN)

See round_start.py, based upon fake data  
aa012345678901aa  
bb123456789012bb  
cc234567890123cc  
dd345678901234dd  
ee456789012345ee  
are 5 madeup MN privkey, short and easy to recognize.

## 1.1 Define Jury for a round

Done

Commented round_start.py output:
(To be updated with new addresses of MN)

```
# This is the hash of the 5 or 10 last blocks from last round (constant here for poc)
# It's used to determine the next round 
Last Round broadhash b3a1e0b050bb7f593cf394798ed671e3

# These are variables to tune. I choose small ones for debug/poc.
# candidates will be #of MN, slots will be like 51 or 101 max
5 candidates, 3 slots

# Each candidate gets one or more ticket depending of its weight (can be collateral/ 10k or more evolved metric)
# Here, all weight 1 except bb, weight 2: he got 2 tickets
# a ticket# was added to each address, so that the resulting hash is unique and all tickets are well shuffled.
Tickets
 [('aa012345678901aa', 0), ('bb123456789012bb', 1), ('bb123456789012bb', 2), ('cc234567890123cc', 3), ('dd345678901234dd', 4), ('ee456789012345ee', 5)]

# Tickets are then sorted by hash distance from the broadhash  
# (Address, ticket#) -  ticket# is no more useful here
Sorted Tickets:
 [('cc234567890123cc', 3), ('ee456789012345ee', 5), ('bb123456789012bb', 2), ('dd345678901234dd', 4), ('aa012345678901aa', 0), ('bb123456789012bb', 1)]
```

## 1.2 Fill round slots with Jury tickets

Done

```
#and we keep the first 3 (slots #) 
Slots
 [('cc234567890123cc', 3), ('ee456789012345ee', 5), ('bb123456789012bb', 2)]
```


## 1.3 Fill test slots

Done.

For each slot, we also define TESTS_PER_SLOT tests to be run.  
There are different test type.
The forging masternode is never testing nor tested for that slot.
The tests concern every MN, not just the jury.

```
Tests Slots
 [
 [('bb123456789012bb', 'dd345678901234dd', 3), ('aa012345678901aa', 'ee456789012345ee', 0), ('dd345678901234dd', 'bb123456789012bb', 4), ('aa012345678901aa', 'ee456789012345ee', 0), ('dd345678901234dd', 'ee456789012345ee', 2)], 
 [('bb123456789012bb', 'cc234567890123cc', 0), ('bb123456789012bb', 'cc234567890123cc', 3), ('aa012345678901aa', 'cc234567890123cc', 1), ('bb123456789012bb', 'aa012345678901aa', 0), ('bb123456789012bb', 'cc234567890123cc', 1)], 
 [('aa012345678901aa', 'cc234567890123cc', 3), ('cc234567890123cc', 'aa012345678901aa', 3), ('cc234567890123cc', 'ee456789012345ee', 0), ('dd345678901234dd', 'aa012345678901aa', 0), ('aa012345678901aa', 'ee456789012345ee', 1)]
 ]
```
Here we have 3 slots, 5 tests per slot.  
Each test, like `('aa012345678901aa', 'cc234567890123cc', 3)` is a tuple (tester, tested, test_type)

  

# 2 Round Process

## 2.1 Timeslots and helpers

Ok.

Given a timestamp (usually the current time) we deduce the Round and slot#, hence the current forger and test to be run.

In the current POC, the MN list and previous hash does not change, so the same "round" plays again and again.

Sample output during a round

```
Current Time 1522441470: Round 18 - Slot 2
Forger is bb123456789012bb
Tests: [('aa012345678901aa', 'cc234567890123cc', 3), ('cc234567890123cc', 'aa012345678901aa', 3), ('cc234567890123cc', 'ee456789012345ee', 0), ('dd345678901234dd', 'aa012345678901aa', 0), ('aa012345678901aa', 'ee456789012345ee', 1)]
```

When at the end of a round, we have an empty slot (see common.END_ROUND_SLOTS) that is used to make sure we reach consensus. 

```
Current Time 1522441530: Round 18 - Slot 3
End of round...
```


## 2.2 Forging

TBD

## 2.3 Block sending

TBD

## 2.4 Late Sync

TBD


## [...]

# End of round

TBD

# 3 Inter node communication

## 3.1 Node server

Base ok, Tornado converted.

## 3.2 Node client

Base ok, Tornado and async/await, too.

## 3.3 Base node commands

wip

- Hello and ping ok

## 3.4 resources management

Tiers for keeping enough open slots for selected peers. tbd.

## 3.5 communication security

Various checks tbd 

# 4 PoS Chain object

## 4.1 Base

Done.

## 4.2 In Memory prototype

Dropped. Would take longer than going straight with SQLite

## 4.3 SQLite prototype

DB Definition ok
TODO: Add schema

## 4.4 Basic validity checks

TBD

## 4.5 Extended checks

TBD

# 5 PoS Addresses

Done, Doc to be written.
- 1 byte prefix, network id
- 20 byte blake2b hash of pubkey
- 4 bytes checksum
- b58 encoded

Hash size: 20 byte
Address size: 32 bytes text format (25 bytes in raw format)
