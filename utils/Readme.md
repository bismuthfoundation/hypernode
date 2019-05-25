# Hypernode utils

User and admin utils for Bismuth HyperNodes.

## hn_node_update.py

Automatic node update for standard HN setups, for 4.3.0.0 Fork.  
To be run from the Bismuth node directory (should be ~/Bismuth or /root/bistmuth).  
One liner once in the Bismuth dir: `curl https://github.com/bismuthfoundation/hypernode/raw/master/utils/hn_node_update.py|python3`

## gen_address.py

Creates a new PoS wallet like the Hypernode does.

## reserved_hn_update.py

To be used by a certified address only.  
Sends a message that triggers an automatic update on all the hypernodes with automatic update enabled.
