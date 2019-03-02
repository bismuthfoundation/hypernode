# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json file

Week 26:
`python3 convert.py --action=week --param=26`

```
Week 26
-------------
TS   1551513600
UTC  2019-03-02T08:00:00Z
Round 4666
Slot  0
Last PoS Round 4665
PoW Height 1062577
Real TS 1551513513.06
Next TS 1551513694.14
Balance 8224.753063899232
Balance (int) 8224
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

Week 19:
Warning: PoW address 8d57af5dc042b824c62baecffb64ce6eabb74a0027a434617a10f8cd, weight 2 instead of 3 - removing from list.
Warning: PoW address 9a92218d6682e4f2a01722dff41d1d3e9654c4807b4c29cdc7a95e47, weight 0 instead of 1 - removing from list.
Warning: PoW address b4c32ab1e27a991dfee8f5460c1796a40e9e944c14a006e5e291e8a0, weight 1 instead of 3 - removing from list.

Week 20:
Warning: PoW address 7c35fc4f1cd74e886dab73d4fe6ee8e798301c3a7720529c4a7eb03b, weight 2 instead of 3 - removing from list.
Warning: PoW address 8d57af5dc042b824c62baecffb64ce6eabb74a0027a434617a10f8cd, weight 2 instead of 3 - removing from list.
Warning: PoW address 9a92218d6682e4f2a01722dff41d1d3e9654c4807b4c29cdc7a95e47, weight 0 instead of 1 - removing from list.
Warning: PoW address b4c32ab1e27a991dfee8f5460c1796a40e9e944c14a006e5e291e8a0, weight 2 instead of 3 - removing from list.
Warning: PoW address 74f45adf91d0f0116cc3b61652822551dcfb19b7b02101cd5c86685d, weight 0 instead of 3 - removing from list.
Warning: PoW address da06e77a08f9b07e4a7f6a4788ab269d3df0e09c38d8fa64f321374e, weight 0 instead of 3 - removing from list.

6 HNs to be deactivated. Reminder: If you want to lower your collateral, you have to unreg, wait for the transaction to be mined, then rereg.

Week 21:  
Warning: PoW address 5841e2d6473c8b2d1285bf07bf8893738a34fc240f80122bae36c81c, weight 0 instead of 3 - removing from list.

Week23:
Warning: PoW address ea00b8991c6f76c2922f522c6d135df5dfcbe800e58cb78507c4caeb, weight 0 instead of 1 - removing from list.

Week24 and 25
Warning: PoW address fd385f7152bb649a71c404ff3a8163e84c24c083f3281df827ad69d8, weight 0 instead of 1 - removing from list.


## Fill_stats

`time python3 fill_stats.py`  
Took 27m9.083s

# Rewards extraction

`python3 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 (initial setting) to 0.1 (current setting, to account for more HNs), now temporary to 0.

The script exports:
 
## Rewards, per reward address  
exported as rewards/week26_per_reward_address.csv

## Rewards, per HN
exported as rewards/week26_per_hn_address.csv
