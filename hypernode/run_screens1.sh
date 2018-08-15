#!/bin/bash

# Run several local hn_instance in screens for dev/debug

# 4 to .... (0 to 3 are run in regular terminals)
for i in {4..20}
do
    screen -d -S "hn${i}" -m bash -c "python hn_instance.py -i ${i} " -X quit
    sleep 2
done
