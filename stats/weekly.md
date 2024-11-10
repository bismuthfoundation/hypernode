# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json fi6e

Week 323  
`python3 convert.py --action=week --param=323`

```
Week 323
-------------
TS   1731139200
UTC  2024-11-09T08:00:00Z
Round 54562
Slot  0
Last PoS Round 54561
PoW Height 4019747
Real TS 1731139166.87
Next TS 1731139224.49
Balance 36424.4626812
Balance (int) 20863

```

week.json (week 10):
```
{
  "week": 10,
  "ts": 1541836800,
  "UTC": "2018-11-10T08:00:00Z",
  "last_pos_round": 1977,
  "pow_height": 901872,
  "balance": 8024
}
```
 
ts is the timestamp for the end of the weekly reward. It's always saturday 08:00 UTC.  
The next scripts take the values from this json.

## Fill_rounds

`python3 fill_rounds.py`  

Verifies again the registered and active HNs for each round of the period.   
This will tell if any HN cheated on its balance (balance dropped below the registered collateral)

...


Week 242:  20k loss  
Warning: PoW address 7e356ae49ffeb45cfee0bc4c635b74a5762ba7a316a5a6df468101ad, weight 0 instead of 2 - removing from list.

... 

Week 259:  90k loss  
Warning: PoW address a847eb256fd52fc052cc88369a6f8ef1e138a296256587edeb700534, weight 0 instead of 3 - removing from list.  
Warning: PoW address f3ea769a1162e447cc7e54dab0a11fe7ba31f7461a8db6fe03400dfb, weight 0 instead of 3 - removing from list.  
Warning: PoW address 65a24b0213499622a1e9729231a0a86de5f2bff95fa6c67465136067, weight 0 instead of 3 - removing from list.  

Week 276: 10K loss  
Warning: PoW address 98855f9b7054f4763a2a754976b26bf2d504105402743cb706c79961, weight 0 instead of 1 - removing from list.  

Week 317: no loss  

Week 323: 30k loss  
Warning: PoW address 8bd3e1dbe966e4d7c067e9aad257b2e3dfd7444736aba8d84cbbb73a, weight 0 instead of 3 - removing from list.

## Fill_stats

`time python3 fill_stats.py`  

# Rewards extraction

`python3 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 (initial setting) to 0.1 (current setting, to account for more HNs), now temporary to 0.

```
Calc Rewards for Week 323
Total Weights at 0.0: 17460
Full Weights: 18206
Loss: 4.10%
Max Reward 225.84 BIS, Token unit 37.64
Total token rewards 312

```

The script exports:
 
## Rewards, per reward address  
Exported as rewards/week323per_reward_address.csv

## Rewards, per HN
Exported as rewards/week323per_hn_address.csv
