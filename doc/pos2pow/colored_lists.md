# Colored lists

The Hypernodes produce several lists that should be used by regular nodes to filter out bad or suspicious actors.  
This document details the various lists and their meaning.

Each node can - or not - rely on these lists.
Filtering with these is on by default since that ensure network resilience and stability, and avoid DDOS and spam attacks on the network.

## ? : Miners lists

Since the miners are the ones to produce blocks and mining requires hash power, miner nodes can be handled in a prefered way, and avoid some counter measures.  
For instance, bad provider blacklist does not apply to a miner. 

- List of miners from last week, with blocks #

## ? : Active last month

This 

## ? : Good provider

Nodes that send a good new block during the past week.  
Prefered nodes for connection.

- list of ip: number of blocks

## Black : Banned

How to go in:
- trigger enough automatic metrics
- being added manually by a core dev, with a public reason and log.

How to go out:

## ? : Smooth Operator

The operator of this node is known by the Bismuth team - or is a team member. He can be reached easily, and has a history of good behaviour.  
His nodes are up to date and taken care of. He uses the colored lists.
This is a very restrictive list that acts as a "trusted seed".

## ? : No rollback allowed

This node has shown a more than average rollback rate.  
This can be due to low perf, bad config, or deliberate messing with the network.  
Rollback requests from these nodes will be ignored or require more confirmations.

- list of ip: rollback req (also include total rollback) 

## ? : Bad provider

Some providers are largely used to run spammy nodes at scale.  
They can be banned after automatic detection.