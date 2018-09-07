# Tuneable config

Some config elements can be globally tuned via pow messages from a control private contract.

This allows for live tuning depending of the network size, without requiring manual config nor update from the users.

No critical config items are there, only parameters that have to be globally synced for the net to behave in an optimum way.

## How?

Via "rainbow" color list.  
list of "key=value" strings. 

## List and defaults

### Current posnet version

No "," char in the values
> POSNET_ALLOW=posnet0001;posnet0002

### Bootstrap files

None yet
> BOOTSTRAP_URLS=

Upcoming format:
> BOOTSTRAP_URLS=url1;url2

### Network size and connectivity

How many peers at most to try to connect to?  
> MAX_CONNECT_TO=25

How many blocks - at most - to send in a single message when syncing catching up nodes.    
> BLOCK_SYNC_COUNT=20

### Network load related

For the whole net  
> TESTS_PER_SLOT=10

Seconds between pings  
> PING_DELAY=30

## Default data
POSNET_ALLOW=posnet0001;posnet0002,MAX_CONNECT_TO=25,BLOCK_SYNC_COUNT=20,TESTS_PER_SLOT=10,PING_DELAY=30,BOOTSTRAP_URLS=


## Possible future params

PLUGIN_VERSION
