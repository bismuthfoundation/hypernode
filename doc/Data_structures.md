# Data structures

## Block Hashes

Hash and block_hashes are blake2b 20 byte long hashes.

## Addresses

Raw address is derived from pub key.  
blake2b(pubkey, len=20)

A network id byte is prefixed.

Main PoS network:  
NETWORK_ID = b'\x19'  
This will make an address beginning with a "B" char.

Test PoS net:  
NETWORK_ID = b'\x55'  
This will make an address beginning with a "b" char.

Then a 4 bytes checksum is appended
checksum = blake2b(v, digest_size=4).digest()

The raw address is then a (1 + 20 + 4) = 25 bytes long bytearray.

It's converted to ascii using b58 encoding, and makes for a 34 byte len ascii string.

This 34 byte ascii is what is stored. 

TODO: drawing

## Signatures, pubkeys

Signatures and pubkeys are 64 byte long binary buffers.  
They are stored as such. 

## PoS messages

Messages are PoS transactions.

Here is the sql definition:

CREATE TABLE pos_messages (
    txid         BLOB (64)    PRIMARY KEY,
    block_height INTEGER,
    timestamp    INTEGER,
    sender       VARCHAR (34),
    recipient    VARCHAR (34),
    what         INTEGER,
    params       STRING,
    value        INTEGER,
    pubkey       BLOB (64),
    received     INTEGER
);

pos_mempool has the very same structure, with a 'block_height' field fixed to 0. 

## PoS Blocks

CREATE TABLE pos_chain (
    height          INTEGER      PRIMARY KEY,
    round           INTEGER,
    sir             INTEGER,
    timestamp       INTEGER,
    previous_hash   BLOB (20),
    msg_count       INTEGER,
    uniques_sources INTEGER,
    signature       BLOB (64),
    block_hash      BLOB (20),
    received_by     STRING,
    forger          VARCHAR (34) 
);

A block is composed of the pos_chain entry + the list of the pos_messages for the same block_height.

The hash of a block is the blake2b hash(len=20) of the following binary block buffer.  
in that order:  
    * height          INTEGER
    * round           INTEGER
    * sir             INTEGER
    * timestamp       INTEGER
(each as a 4 byte buffer, big endian)
then 
    * list of tx id : in ts order, only the txid (64 byte each
    * previous_hash (20 bytes)
    
The signature of a block is the signature of the same raw binary buffer, signed by the forger of that block.

## PoS rounds

Stores the delegates and tickets for each round

CREATE TABLE pos_rounds (
    round      INTEGER PRIMARY KEY,
    active_mns TEXT,
    slots      STRING,
    test_slots STRING
);

## Addresses

Index table to store addresses related data

CREATE TABLE addresses (
    address VARCHAR (34) PRIMARY KEY,
    pubkey  BLOB (64),
    ip      VARCHAR (32),
    alias   VARCHAR (32),
    extra   STRING
);

