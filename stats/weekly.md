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

7*86400 = 604800 seconds increments between each week

From this timestamp, we can get the end PoS round. For week2:

`python3 convert.py --action=ts2posround --param=1536998400`  
gives 
```
UTC   2018-09-15T08:00:00Z
Round 634
Slot  0
```
This is the first round of week 2. So **the last PoS round of week 2 is 633**  
Last PoS round of week 1 was 465.  
Each week adds 7*24 = 168 rounds.

## Check the HN port at that time

Get the PoW block at the end of week time :

`python3 convert.py --action=ts2powheight --param=1536998400`  
Gives
```
UTC 2018-09-15T08:00:00Z
PoW Height 820954
Real TS 1536998381.26
Next TS 1536998583.04
```

So matching PoW block is 820954

## Get balance of hn pot at given pow block

`python3 convert.py --action=hnbalance --param=820954`  
Gives
```
Balance 7867.99999998
```

So Balance=7867  
(addr  3e08b5538a4509d9daa99e01ca5912cda3e98a7f79ca01248c2bde16)


## Fill_rounds

To go faster, edit fill_rounds.py , line 81, set previous_round to last round of previous week.   
On week2:  
previous_round = 465 

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
I use SQLiteStudio but command line works also.

0.2 is the score trigger.

Get total valid weights:  
`select  sum(weight) as weight from reward_stats where score >= 0.2;`  
36763  

We can compare without any filter:  
`select  sum(weight) as weight from reward_stats;`
40558  

Means 9.35% of lines (one line = 1 HN, 1 round) have been ignored.  
It's way more than week 1, and because of the required upgrade about 30 HNs did not do.

hn pot at 820954: we said 7867

We have to replace valid weights and pot in the following queries:

## Rewards, per reward address  
`select reward_address, cast(sum(weight) as double)*7867.0/36763.0 as reward, sum(weight) as weight from reward_stats where score >= 0.2 group by reward_address order by reward desc;`  
exported as week2_per_reward_address.csv

## Rewards, per HN
`select address, reward_address, cast(sum(weight) as double)*7867.0/36763.0 as reward, sum(weight) as weight from reward_stats where score >= 0.2 group by address order by reward desc;`
exported as week2_per_hn_address.csv


