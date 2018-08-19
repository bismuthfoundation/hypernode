#!/bin/bash

# Run several local hn_instance in screens for dev/debug

# 4 to .... (0 to 3 are run in regular terminals)
for i in {21..30}
do
    screen -d -S "hn${i}" -m bash -c "cd ../main;python3 hn_instance.py -i ${i} " -X quit
    sleep 2
done
