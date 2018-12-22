# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json file

Week 16:
`python3 convert.py --action=week --param=16`

```
Week 16
-------------
TS   1545465600
UTC  2018-12-22T08:00:00Z
Round 2986
Slot  0
Last PoS Round 2985
PoW Height 962173
Real TS 1545465538.13
Next TS 1545465629.83
Balance 8048.763063839622
Balance (int) 8048

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

Week 11:
Warning: PoW address ced79e572f6bddde238baa5f3fe493b59fc764b5eff4174b9cc6c594, weight 1 instead of 2 - removing from list. (will be auto unreg)
Week 12:
Warning: PoW address 857f1193e311f6eacfdb0b75623c978b55839dd4a1d24138594d590d, weight 0 instead of 3 - removing from list.

Week 13:
getting round  2484
Warning: Balance check required for PoW height 931980
Warning: PoW address ced79e572f6bddde238baa5f3fe493b59fc764b5eff4174b9cc6c594, weight 1 instead of 2 - removing from list.
Warning: PoW address 857f1193e311f6eacfdb0b75623c978b55839dd4a1d24138594d590d, weight 0 instead of 3 - removing from list.
Warning: PoW address e812188c631c044d7baf01f5935cbec3402bde36ca32dad13ad6d407, weight 0 instead of 1 - removing from list.
Warning: PoW address dea8a5df9129dc9182ee17eddfda3eb91e3af79742636bff149bfc71, weight 0 instead of 1 - removing from list.

Week 14:
Warning: PoW address 9383a6dc2866c59e8639b61fac4b2ad81250ce3b341fe2fc504665a8, weight 0 instead of 3 - removing from list.
Warning: PoW address ced79e572f6bddde238baa5f3fe493b59fc764b5eff4174b9cc6c594, weight 1 instead of 2 - removing from list.
Warning: PoW address e981d2fb519edb74a72f0349e2185e8a19cab08e82c02df25c543d39, weight 0 instead of 1 - removing from list.
Warning: PoW address 857f1193e311f6eacfdb0b75623c978b55839dd4a1d24138594d590d, weight 0 instead of 3 - removing from list.
Warning: PoW address e812188c631c044d7baf01f5935cbec3402bde36ca32dad13ad6d407, weight 0 instead of 1 - removing from list.
Warning: PoW address dea8a5df9129dc9182ee17eddfda3eb91e3af79742636bff149bfc71, weight 0 instead of 1 - removing from list.


Auto unreg does not work as intended. Will need some fix. No incidence on earnings.
(Fixed with week 15)


## Fill_stats

`time python3 fill_stats.py`  
Took 27m9.083s

# Rewards extraction

`python3 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 to 0.1 this week as a test.

The script exports:
 
## Rewards, per reward address  
exported as rewards/week16_per_reward_address.csv

## Rewards, per HN
exported as rewards/week16_per_hn_address.csv
