# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json file

Week 43:
`python3 convert.py --action=week --param=43`

```
Week 43
-------------
TS   1561795200
UTC  2019-06-29T08:00:00Z
Round 7522
Slot  0
Last PoS Round 7521
PoW Height 1232398
Real TS 1561795198.15
Next TS 1561795232.58
Balance 23738.831175248546
Balance (int) 23738
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

Week 26 and 27  
Warning: PoW address fd385f7152bb649a71c404ff3a8163e84c24c083f3281df827ad69d8, weight 0 instead of 1 - removing from list.  
Warning: PoW address 6ab07aec4f68b3f4f1671da81f4cbe3287037e9041d3325fbdf5b46b, weight 0 instead of 1 - removing from list.

Week 28  
Warning: PoW address 6191730b866836430df215651a2f97d4a3e8a526aacb95b27ebe3041, weight 2 instead of 3 - removing from list.  
Warning: PoW address e5e7452326fdd2bafbae55bc3acf32a635b4b9203d1bd56849393102, weight 0 instead of 3 - removing from list.

Week 35  
Warning: PoW address 0e63ce3259dfd5b1928e0edd85880b557fad0f66635fdd9899d36233, weight -1 instead of 1 - removing from list.  
Warning: PoW address eeec69543f6236e296e8a4293e4129207d621e4107730ede28bbaf80, weight 2 instead of 3 - removing from list.

Week 36  
Warning: PoW address 7f416973869f8f655a11deafdf1291b34269e5e43f28ac915ee6d98a, weight 0 instead of 1 - removing from list.  
Warning: PoW address 0e63ce3259dfd5b1928e0edd85880b557fad0f66635fdd9899d36233, weight -1 instead of 1 - removing from list.  
Warning: PoW address eeec69543f6236e296e8a4293e4129207d621e4107730ede28bbaf80, weight 0 instead of 3 - removing from list.  
Warning: PoW address 03e1e5ac5616a4925cece0f315a8482b2a87f9d9ee3dbff46667fe42, weight 0 instead of 3 - removing from list.  
Warning: PoW address 6b746e6cec45bb42dc9a27c1f682c6622b4f3ba81864d6aee2fb0a27, weight 0 instead of 3 - removing from list.

Week 37  
Warning: PoW address 7f416973869f8f655a11deafdf1291b34269e5e43f28ac915ee6d98a, weight 0 instead of 1 - removing from list.  
Warning: PoW address 0e63ce3259dfd5b1928e0edd85880b557fad0f66635fdd9899d36233, weight 0 instead of 1 - removing from list.  
Warning: PoW address eeec69543f6236e296e8a4293e4129207d621e4107730ede28bbaf80, weight 0 instead of 3 - removing from list.  
Warning: PoW address 03e1e5ac5616a4925cece0f315a8482b2a87f9d9ee3dbff46667fe42, weight 0 instead of 3 - removing from list.  
Warning: PoW address 6b746e6cec45bb42dc9a27c1f682c6622b4f3ba81864d6aee2fb0a27, weight 0 instead of 3 - removing from list.  

Week 40  
Warning: PoW address 46d70c334c277b77ef5a2bb6e545ed0f6c33c9b4f412d6dec3bc3aba, weight 0 instead of 2 - removing from list.  
Warning: PoW address 419fab8e3a09b22b8ddb5e768527c4c871616d59040ebeeb7c26db71, weight -1 instead of 1 - removing from list.  
Warning: PoW address e1ed085e11ad4fc3d39e1e2d8525b28cb707dc76f637bb2951f0f14d, weight 0 instead of 1 - removing from list.  
Warning: PoW address c0c057f4c2d6ed6b1f50540b9a05a38398df0223b36c51b05fd2b509, weight 0 instead of 1 - removing from list.  

Week 41  
Warning: PoW address 2e172a00dec25f9278e98d2f0b7f107eede77e541d957499681ddb70, weight 0 instead of 1 - removing from list.  
Warning: PoW address e576adfa21b92cfb25e46bcfd7fedd7d3c63b4397c6cd646d4446601, weight 0 instead of 1 - removing from list.

Week43  
Warning: PoW address eb8712d7664ff57ed6287c09843c396c72732701c6279219815253e5, weight 0 instead of 3 - removing from list.  
Warning: PoW address eed4ce8c41701615d37324def12c4f10855f39a3869c269cfac6c19e, weight 0 instead of 3 - removing from list.  
Warning: PoW address a95063a7c405378769d07765eae9da96afa876e6ade42e88cb4bf551, weight 0 instead of 3 - removing from list.  
Warning: PoW address c8acfba2d08020c0cf18d045ba02754e9e3ad17fb693ad4b07fe222a, weight 0 instead of 3 - removing from list.  
Warning: PoW address d0037df391b6a52e0e560f85b9031ab651d18825ae4b611bdca472c1, weight 0 instead of 3 - removing from list.  

## Fill_stats

`time python3 fill_stats.py`  
(about 11 min => 11 sec now)

# Rewards extraction

`python3 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 (initial setting) to 0.1 (current setting, to account for more HNs), now temporary to 0.

```
Calc Rewards for Week 43
Total Weights at 0.0: 57877
Full Weights: 61239
Loss: 5.49%
```

The script exports:
 
## Rewards, per reward address  
exported as rewards/week43_per_reward_address.csv

## Rewards, per HN
exported as rewards/week43_per_hn_address.csv
