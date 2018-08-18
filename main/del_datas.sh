#!/bin/bash

# Empty data0 to data50

# 4 to .... (0 to 3 are run in regular terminals)
for i in {0..50}
do
    rm "./data${i}/posmempool.db"
    rm "./data${i}/poc_pos_chain.db"
    rm "./data${i}/hndb.db"
done
