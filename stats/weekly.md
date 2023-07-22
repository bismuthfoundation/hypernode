# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json fi6e

Week 255  
`python3 convert.py --action=week --param=255`

```
Week 255
-------------
TS   1690012800
UTC  2023-07-22T08:00:00Z
Round 43138
Slot  0
Last PoS Round 43137
PoW Height 3363656
Real TS 1690012799.85
Next TS 1690012818.75
Balance 17549.63727801
Balance (int) 17549
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

Week 255:  no loss  

## Fill_stats

`time python3 fill_stats.py`  

# Rewards extraction

`python3 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 (initial setting) to 0.1 (current setting, to account for more HNs), now temporary to 0.

```
Calc Rewards for Week 255
Total Weights at 0.0: 61101
Full Weights: 65786
Loss: 7.12%
Max Reward 142.17 BIS, Token unit 23.70
Total token rewards 386
```

The script exports:
 
## Rewards, per reward address  
Exported as rewards/week255per_reward_address.csv

## Rewards, per HN
Exported as rewards/week255per_hn_address.csv
