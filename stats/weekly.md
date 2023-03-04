# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json fi6e

Week 235  
`python3 convert.py --action=week --param=235`

```
Week 235
-------------
TS   1677916800
UTC  2023-03-04T08:00:00Z
Round 39778
Slot  0
Last PoS Round 39777
PoW Height 3162604
Real TS 1677916799.04
Next TS 1677916818.34
Balance 18455.09950622
Balance (int) 18455

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


## Fill_stats

`time python3 fill_stats.py`  

# Rewards extraction

`python3 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 (initial setting) to 0.1 (current setting, to account for more HNs), now temporary to 0.

```
Calc Rewards for Week 235
Total Weights at 0.0: 75960
Full Weights: 82423
Loss: 7.84%
Max Reward 122.45 BIS, Token unit 20.41
Total token rewards 489

```

The script exports:
 
## Rewards, per reward address  
Exported as rewards/week235per_reward_address.csv

## Rewards, per HN
Exported as rewards/week235per_hn_address.csv
