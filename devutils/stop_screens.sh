#!/bin/bash

# Run several local hn_instance in screens for dev/debug

# 4 to .... (0 to 3 are run in regular terminals)
for i in {4..49}
do
    screen -S "hn${i}" -X at "#" stuff $'\003'
    sleep 0.2
done

screen -ls |grep hn
