# Bismuth POS Node Commands

In complete rewrite for PoS

commands_pb2.Command.*



## Hello
id 0 - ok
string_value : the peer version (10 char) plus the node port (5 chars, left padded with 0) plus the sender pubkey (34 chars)   

ex:
posnet000106969BMSMNNzB9qdDp1vudRZoge4BUZ1gCUC3CV 

## ok
id 1 - ok
no param

## ko
id 2 - ok
string
returns reason of error: version mismatch, bad ip, bad pubkey, bad block, bad slot, no resources, no reason
As enum or string? balance between command len and ease of use => string for now.

## ping
id 3 - ok
TX: one tx (ping params)
*temp for poc*: ping is an empty command for now, just used for keep alive.

## peers
id 4
IPS : list of ip and ports. commands_pb2.Command.IP
List of peers, with default port.
* maintain a bin version of that, in memory, within a protobuf, no need to convert each time

## status
id 5
no param
returns a json status as string

## tx
id 6 - ok
TX : list of commands_pb2.Command.TX
One or several tx from the a node client. Server sends back "ok" or "ko"

## block
id 7
block : a commands_pb2.Block
A forged block from a juror.

## mempool
id 8 - WIP
TX : list of commands_pb2.Command.TX
One or several tx from the peer mempool
Almost similar to tx. Difference is TX does not require the mempool back, 
whereas this mempool message asks for the peer mempool in return.

## height
id 10 - wip
The current height status of a chain.  
Embeds current height as well as metrics about the variety of the chain (number of uniques sources and forgers)

## blockinfo
id 11 - wip
Ask info for a specific block height. Question comes with an int32, answer with a height

## blocksync
id 12 - wip 
Ask info for a list of blocks starting with the given one. Question comes with an int32, answer with block(s)

## roundblocks
id 13 - wip
Ask the full block data for a given round. Question comes with an int32, answer with block(s)






# Command flow

Each node has a server, responding to requests, and some clients, initiating requests.  
Clients send commands and wait for an answer.  
Servers wait for an event, and answer.  

## Communication starter

* Client sends "Hello" with its POSNET version, port and PoS address
* Server may answer "ko" with a reason, or
* Server may answer "Hello" with its own POSNET version, port and PoS address

## Keep alive

* Client can send some "ping" command to keep the socket (and check it is) alive. Only needed if no command was issued for ( < timeout) time.

## Mempool Sync
* Every (time) the client sends its mempool (new tx only) to the server it's connected to, and gets the peer new tx as well to digest.
 


