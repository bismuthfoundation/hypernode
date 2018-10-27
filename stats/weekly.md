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

Sept 29 2018, 08:00 UTC - End of Week 4
> TS = 1537603200 + 604800
> TS = 1538208000

Oct 06 2018, 08:00 UTC - End of Week 5
> TS = 1538208000 + 604800
> TS = 1538812800

Oct 13 2018, 08:00 UTC - End of Week 6
> TS = 1538812800 + 604800
> TS = 1539417600

Oct 20 2018, 08:00 UTC - End of Week 7
> TS = 1539417600 + 604800
> TS = 1540022400

Oct 27 2018, 08:00 UTC - End of Week 8
> TS = 1540022400 + 604800
> TS = 1540627200

7*86400 = 604800 seconds increments between each week

From this timestamp, we can get the end PoS round. For week 8:

`python3 convert.py --action=ts2posround --param=1540627200`  
gives 
```
TS 1540627200
-------------
UTC   2018-10-27T08:00:00Z
Round 1642
Slot  0
```
This is the first round of week 8. So **the last PoS round of week7 is 1641**  
Last PoS round of week 7 was 1473.  
Each week adds 7*24 = 168 rounds.

## Check the HN port at that time

Get the PoW block at the end of week time :

`python3 convert.py --action=ts2powheight --param=1540627200`  
Gives
```
TS 1540627200
-------------
UTC 2018-10-27T08:00:00Z
PoW Height 881888
Real TS 1540629054.34
Next TS 1540629081.51
```

So matching PoW block is 881888

## Get balance of hn pot at given pow block

`python3 convert.py --action=hnbalance --param=881888`  
Gives
```
Balance 8145.7630638499
```

So Balance=8145  
(addr  3e08b5538a4509d9daa99e01ca5912cda3e98a7f79ca01248c2bde16)


## Fill_rounds

To go faster, edit fill_rounds.py , line 81, set previous_round to last round of previous week.   
On week 8:  
previous_round = 1473 

`python3 fill_rounds.py`  
1m27.726s

Verifies again the registered and active HNs for each round of the period.    
This will tell if any HN cheated on its balance (balance dropped below the registered collateral)


Week 8:
21469f889f1725a1682b80fe6f76ed59caf5d3f8c1111edc7680caf2 had his balance dropped from 10K to 0 since round 1552
9affc41b1656f604e2b0a915302c7f69440d410b04cc43916aa62a86 had his balance dropped from 10K to 0 since round 1608


## Fill_stats

Edit fill_stats with current week START_ROUND and END_ROUND  
Note: just edit the WEEK param from now on.

`time python3 fill_stats.py`  
Took 27m9.083s

# Rewards extraction

These SQL requests are to be run on hndb.db , table reward_stats  
I use SQLiteStudio but command line (sqlite3) works also.

0.2 is the score trigger.

Get total valid weights:  
`select  sum(weight) as weight from reward_stats where score >= 0.2;`  
43537  

We can compare without any filter:  
`select  sum(weight) as weight from reward_stats;`  
56342  


hn pot at 881888: we said 8145

We have to replace valid weights and pot in the following queries:

## Rewards, per reward address  
`select reward_address, cast(sum(weight) as double)*8145.0/43537.0 as reward, sum(weight) as weight from reward_stats where score >= 0.2 group by reward_address order by reward desc;`  
exported as week8_per_reward_address.csv

## Rewards, per HN
`select address, reward_address, cast(sum(weight) as double)*8145.0/43537.0 as reward, sum(weight) as weight from reward_stats where score >= 0.2 group by address order by reward desc;`
exported as week8_per_hn_address.csv
