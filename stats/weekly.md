# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json fi6e

Week 241  
`python3 convert.py --action=week --param=241`

```
Week 241
-------------
TS   1681545600
UTC  2023-04-15T08:00:00Z
Round 40786
Slot  0
Last PoS Round 40785
PoW Height 3222806
Real TS 1681545594.75
Next TS 1681545601.11
Balance 18542.7427796
Balance (int) 18542
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

## Fill_stats

`time python3 fill_stats.py`  

# Rewards extraction

`python3 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 (initial setting) to 0.1 (current setting, to account for more HNs), now temporary to 0.

```
Calc Rewards for Week 241
Total Weights at 0.0: 80807
Full Weights: 89181
Loss: 9.39%
Max Reward 115.65 BIS, Token unit 19.27
Total token rewards 521
```

The script exports:
 
## Rewards, per reward address  
Exported as rewards/week241per_reward_address.csv

## Rewards, per HN
Exported as rewards/week241per_hn_address.csv
