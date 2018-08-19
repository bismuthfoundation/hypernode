#!/bin/bash

# Empty data0 to data50

# 4 to .... (0 to 3 are run in regular terminals)
for i in {0..50}
do
    rm "../main/data${i}/posmempool.db"
    rm "../main/data${i}/poc_pos_chain.db"
    rm "../main/data${i}/hndb.db"
done
