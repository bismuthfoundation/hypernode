# Test Goals

* Ensures the node is alive
* Ensure it is properly working and has up to date data / settings
* Complicated challenges to ensure it has enough resources to do its job

# Notes 

* Tests are bi-directional:  
  When A tests B, it also gives B info, and both A and B report the test result.
  
* Tests are random but predictable:
  At each round start, all tests for the round are being decided, so a node can't do random tests.   
  This is to avoid denial of services attacks and such. 
  
* Tests params consist of:  
  Who test, Test Type, Tested MN, test params
  
* Tests results then become a tx/message:  
  timestamp, Who test, Test Type, Tested MN, test params  
  and :  
  raw test results, test note  
  raw test result is what was send by the tested node, test note is note (0-10) given by the tester.


# Test types for PoS

## 0 - Ping

Ping is the most basic test. It does in fact check several things:
* node availability
* node version (like all commands)
* node timestamp (so drift with ours)


## 1 - Last 10 blocks abstract

* check hash and height.
* allow for 1 block difference.
* gives some "sync" note.

## 2 - Random pow blocks series hash

TODO

## 3 - Bandwith test

* bandwith test from real data or not

# Random Notes

## Test ideas

* seed => huge buffer, hash, result (one half published by A, other Half published by B, both halfs calculated by both)

* seed => list , or list of past blocks (PoW and/or PoS) => hash of blocks, to check presence and validity



## Various
 
* anti tx flood : cap tx per node (ip and address) per block and round

* When do MN send round status, with connected peers, connexions attemps, so they can decide for active mn next round?  
 avoid everyone at the same time. but not evenly either, or some will report old data.