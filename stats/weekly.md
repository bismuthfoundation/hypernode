# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json fi6e

Week 257  
`python3 convert.py --action=week --param=257`

```
Week 257
-------------
TS   1691222400
UTC  2023-08-05T08:00:00Z
Round 43474
Slot  0
Last PoS Round 43473
PoW Height 3383353
Real TS 1691222369.83
Next TS 1691222500.65
Balance 17203.59387799
Balance (int) 17203

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

Week 257:  no loss  

## Fill_stats

`time python3 fill_stats.py`  

# Rewards extraction

`python3 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 (initial setting) to 0.1 (current setting, to account for more HNs), now temporary to 0.

```
Calc Rewards for Week 257
Total Weights at 0.0: 54960
Full Weights: 59738
Loss: 8.00%
Max Reward 139.92 BIS, Token unit 23.32
Total token rewards 398
```

The script exports:
 
## Rewards, per reward address  
Exported as rewards/week257per_reward_address.csv

## Rewards, per HN
Exported as rewards/week257per_hn_address.csv
