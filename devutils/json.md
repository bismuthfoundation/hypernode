# Json memo

hn_client.py sends back json strings.

How to prettify that output?

## Pure python

pipe through python:

`python3 hn_client.py --action=round | python -mjsontool`

will indent properly

## jq

jq is a useful json utility that can do way more.

`sudo apt install jq`

pipe through jq:

`python3 hn_client.py --action=round | jq '.'`

will indent properly and color the output.

