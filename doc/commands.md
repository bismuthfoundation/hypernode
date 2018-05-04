# Bismuth POS Node Commands

In complete rewrite for PoS

commands_pb2.Command.*



## Hello
id 0 - ok
string_value : the peer version (10 char) plus the sender pubkey (34 chars)   

ex:
posnet0001BMSMNNzB9qdDp1vudRZoge4BUZ1gCUC3CV 

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
One or several tx from the a node client

## block
id 7
block : a commands_pb2.Block
A forged block from a juror.

## mempool
id 8 - WIP
TX : list of commands_pb2.Command.TX
One or several tx from the peer mempool


# Command flow

Each node has a server, responding to requests, and some clients, initiating requests.  
Clients send commands and wait for an answer.  
Servers wait for an event, and answer.  

## Communication starter

* Client sends "Hello" with its POSNET version and PoS address
* Server may answer "ko" with a reason, or
* Server may answer "Hello" its own POSNET version and PoS address

## Keep alive

* Client can send some "ping" command to keep the socket (and check it is) alive. Only needed if no command was issued for ( < timeout) time.

## Mempool Sync
* Every (time) the client sends its mempool (new tx only) to the server it's connected to, and gets the peer new tx as well to digest.
TODO: continue to "sync" when it's our turn to forge? 


