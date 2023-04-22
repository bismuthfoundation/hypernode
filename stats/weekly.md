# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json fi6e

Week 242  
`python3 convert.py --action=week --param=242`

```
Week 242
-------------
TS   1682150400
UTC  2023-04-22T08:00:00Z
Round 40954
Slot  0
Last PoS Round 40953
PoW Height 3232675
Real TS 1682150372.44
Next TS 1682150511.04
Balance 18476.96607959
Balance (int) 18476
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

Week 222:  no loss  

Week 223:  no loss  

Week 224:  no loss  

Week 225:  no loss  

Week 226:  no loss  

Week 227:  no loss  

Week 228:  no loss  

Week 229:  no loss  

Week 230:  no loss  

Week 231:  no loss  

Week 232:  no loss  

Week 233:  no loss  

Week 234:  no loss  

Week 235:  no loss  

Week 236:  no loss  

Week 237:  no loss  

Week 238:  no loss  

Week 239:  no loss  

Week 240:  no loss  

Week 241:  no loss  

Week 242:  20k loss  
Warning: PoW address 7e356ae49ffeb45cfee0bc4c635b74a5762ba7a316a5a6df468101ad, weight 0 instead of 2 - removing from list.

## Fill_stats

`time python3 fill_stats.py`  

# Rewards extraction

`python3 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 (initial setting) to 0.1 (current setting, to account for more HNs), now temporary to 0.

```
Calc Rewards for Week 242
Total Weights at 0.0: 78828
Full Weights: 87724
Loss: 10.14%
Max Reward 118.13 BIS, Token unit 19.69
Total token rewards 504

```

The script exports:
 
## Rewards, per reward address  
Exported as rewards/week242per_reward_address.csv

## Rewards, per HN
Exported as rewards/week242per_hn_address.csv
