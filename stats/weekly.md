# Weekly data collection

To be automated.

To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion

Get the timestamp for the end of the weekly reward. It's always saturday 08:00 UTC.

Sept 8 2018, 08:00 UTC - End of Week 1
> TS = 1536393600

Sept 15 2018, 08:00 UTC - End of Week 2
> TS = 1536998400

Sept 22 2018, 08:00 UTC - End of Week 3
> TS = 1537603200

7*86400 = 604800 seconds increments between each week

From this timestamp, we can get the end PoS round. For week3:

`python3 convert.py --action=ts2posround --param=1536998400`  
gives 
```
UTC   2018-09-22T08:00:00Z
Round 802
Slot  0
```
This is the first round of week 4. So **the last PoS round of week 3 is 801**  
Last PoS round of week 2 was 633.  
Each week adds 7*24 = 168 rounds.

## Check the HN port at that time

Get the PoW block at the end of week time :

`python3 convert.py --action=ts2powheight --param=1537603200`  
Gives
```
UTC 2018-09-22T08:00:00Z
PoW Height 831272
Real TS 1537603197.97
Next TS 1537603205.14
```

So matching PoW block is 831272

## Get balance of hn pot at given pow block

`python3 convert.py --action=hnbalance --param=831272`  
Gives
```
Balance 8256.99999999001
```

So Balance=8256  
(addr  3e08b5538a4509d9daa99e01ca5912cda3e98a7f79ca01248c2bde16)


## Fill_rounds

To go faster, edit fill_rounds.py , line 81, set previous_round to last round of previous week.   
On week3:  
previous_round = 633 

`python3 fill_rounds.py`  
1m27.726s

Verifies again the registered and active HNs for each round of the period.    
This will tell if any HN cheated on its balance (balance dropped below the registered collateral)


## Fill_stats

Edit fill_stats with current week START_ROUND and END_ROUND

`time python3 fill_stats.py`  
Took 27m9.083s

# Rewards extraction

These SQL requests are to be run on hndb.db , table reward_stats  
I use SQLiteStudio but command line (sqlite3) works also.

0.2 is the score trigger.

Get total valid weights:  
`select  sum(weight) as weight from reward_stats where score >= 0.2;`  
39311  

We can compare without any filter:  
`select  sum(weight) as weight from reward_stats;`
44346  

Means 11.35% of lines (one line = 1 HN, 1 round) have been ignored.  
It's more than week 2, probably because of delayed node updates.

hn pot at 831272: we said 8256

We have to replace valid weights and pot in the following queries:

## Rewards, per reward address  
`select reward_address, cast(sum(weight) as double)*8256.0/39311.0 as reward, sum(weight) as weight from reward_stats where score >= 0.2 group by reward_address order by reward desc;`  
exported as week3_per_reward_address.csv

## Rewards, per HN
`select address, reward_address, cast(sum(weight) as double)*8256.0/39311.0 as reward, sum(weight) as weight from reward_stats where score >= 0.2 group by address order by reward desc;`
exported as week3_per_hn_address.csv
