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

Nov 3 2018, 08:00 UTC - End of Week 9
> TS = 1540627200 + 604800
> TS = 1541232000

7*86400 = 604800 seconds increments between each week

From this timestamp, we can get the end PoS round. For week 9:

`python3 convert.py --action=ts2posround --param=1541232000`  
gives 
```
TS 1541232000
-------------
UTC   2018-11-03T08:00:00Z
Round 1810
Slot  0
```
This is the first round of week 10. So **the last PoS round of week9 is 1809**  
Last PoS round of week 8 was 1641.  
Each week adds 7*24 = 168 rounds.

## Check the HN port at that time

Get the PoW block at the end of week time :

`python3 convert.py --action=ts2powheight --param=1541232000`  
Gives
```
TS 1541232000
-------------
UTC 2018-11-03T08:00:00Z
PoW Height 891847
Real TS 1541231948.98
Next TS 1541232016.52
```

So matching PoW block is 891847

## Get balance of hn pot at given pow block

`python3 convert.py --action=hnbalance --param=891847`  
Gives
```
Balance 7968.763063830003
```

So Balance=7968  
(addr  3e08b5538a4509d9daa99e01ca5912cda3e98a7f79ca01248c2bde16)


## Fill_rounds

To go faster, edit fill_rounds.py , line 81, set previous_round to last round of previous week.   
On week 9:  
previous_round = 1641 

`python3 fill_rounds.py`  
1m27.726s

Verifies again the registered and active HNs for each round of the period.    
This will tell if any HN cheated on its balance (balance dropped below the registered collateral)


Week 9:
Warning: PoW address ced79e572f6bddde238baa5f3fe493b59fc764b5eff4174b9cc6c594, weight 1 instead of 2 - removing from list.
Warning: PoW address 58df82e6159b00f5323521a4a60cfbea24f74a414cccf7bc802c2fa4, weight 0 instead of 2 - removing from list.

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
2437  

We can compare without any filter:  
`select  sum(weight) as weight from reward_stats;`  
3381  


hn pot at 891847: we said 7968

We have to replace valid weights and pot in the following queries:

## Rewards, per reward address  
`select reward_address, cast(sum(weight) as double)*7968.0/2437.0 as reward, sum(weight) as weight from reward_stats where score >= 0.2 group by reward_address order by reward desc;`  
exported as week9_per_reward_address.csv

## Rewards, per HN
`select address, reward_address, cast(sum(weight) as double)*7968.0/2437.0 as reward, sum(weight) as weight from reward_stats where score >= 0.2 group by address order by reward desc;`
exported as week9_per_hn_address.csv
