# Bismuth POS Node Commands

In complete rewrite for PoS

commands_pb2.Command.*



## Hello
id 0
string_value : the peer version (10 char) plus the sender pubkey   

ex:
posnet0016aa012345678901aa 

## ok
id 1
no param

## ko
id 2
string
returns reason of error: version mismatch, bad ip, bad pubkey, bad block, bad slot, no resources, no reason

## ping
id 3
TX: one tx (ping params)

## peers
id 4
IPS : list of ip and ports. commands_pb2.Command.IP
List of peers, with default port.
* maintain a bin version of that, in memory, within a protobuf, no need to convert each time


## tx
id 5
TX : list of commands_pb2.Command.TX
One or several tx from the node mempool


