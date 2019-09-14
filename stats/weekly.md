# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json file

Week 54:  
`python3.7 convert.py --action=week --param=54`

```
Week 54
-------------
TS   1568448000
UTC  2019-09-14T08:00:00Z
Round 9370
Slot  0
Last PoS Round 9369
PoW Height 1342859
Real TS 1568447979.65
Next TS 1568448093.18
Balance 24216.232016698108
Balance (int) 24216
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

`python3.7 fill_rounds.py`  

Verifies again the registered and active HNs for each round of the period.   
This will tell if any HN cheated on its balance (balance dropped below the registered collateral)

Week 40:  50K loss  
Warning: PoW address 46d70c334c277b77ef5a2bb6e545ed0f6c33c9b4f412d6dec3bc3aba, weight 0 instead of 2 - removing from list.  *  
Warning: PoW address 419fab8e3a09b22b8ddb5e768527c4c871616d59040ebeeb7c26db71, weight -1 instead of 1 - removing from list.  *  
Warning: PoW address e1ed085e11ad4fc3d39e1e2d8525b28cb707dc76f637bb2951f0f14d, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address c0c057f4c2d6ed6b1f50540b9a05a38398df0223b36c51b05fd2b509, weight 0 instead of 1 - removing from list.  *  

Week 41:  20K loss  
Warning: PoW address 2e172a00dec25f9278e98d2f0b7f107eede77e541d957499681ddb70, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address e576adfa21b92cfb25e46bcfd7fedd7d3c63b4397c6cd646d4446601, weight 0 instead of 1 - removing from list.  *  

Week 43:  150K loss  
Warning: PoW address eb8712d7664ff57ed6287c09843c396c72732701c6279219815253e5, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address eed4ce8c41701615d37324def12c4f10855f39a3869c269cfac6c19e, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address a95063a7c405378769d07765eae9da96afa876e6ade42e88cb4bf551, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address c8acfba2d08020c0cf18d045ba02754e9e3ad17fb693ad4b07fe222a, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address d0037df391b6a52e0e560f85b9031ab651d18825ae4b611bdca472c1, weight 0 instead of 3 - removing from list.  *  

Week 44  : 10K loss  
Warning: PoW address f82ed723a9679a66095edb10478d3ebb900436f59792b56b07cdad7b, weight 0 instead of 1 - removing from list.  * 

Week 45: 220K loss  
Warning: PoW address 9b2cf63335a7cf67f095a51104dce03c5bcf3f18588623a63d67a11c, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 90a924b489f6f8a94017c9ad3488506352def52d3576497e4f3b9a6e, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address eae88c011a155b9b7edca6092eca5d986aa2bd08c5e936d170cf245b, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 952f2f5a9d82fddd2c2dff54cb652879fb882638d9770bf0b08a1d4b, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 9ab49f66492ebeb91397bd574e84658c7c3f88ab476bab61abac427c, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 74b07b11968849f0e7661a8d5bf638afb0526f8d7efdb8a13278d743, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 27c4b8eefbc8451e53c0cf30fb807813502227ba66b0019dc691a253, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address e480811089c7e4c7e93ee67591053bb8317ccaff788caf3ef6fb8ce6, weight 0 instead of 1 - removing from list.  *  

Week 46: 40K loss    
Warning: PoW address 9d1d55bdad0b0f09152a603b73bbb03a951f376a3bae474ca98fe3da, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address 9463995e455116ed5e4969aac36e8f315eb1c4714ae076eaff6cded8, weight 0 instead of 3 - removing from list.  *  

Week 47:  50K loss  
Warning: PoW address 9d1d55bdad0b0f09152a603b73bbb03a951f376a3bae474ca98fe3da, weight 0 instead of 1 - removing from list.  
Warning: PoW address 57736590c5a519bb03a8404d8d02fca60389983bbc41fb1b18b4a6ea, weight 0 instead of 2 - removing from list.  *  
Warning: PoW address 9463995e455116ed5e4969aac36e8f315eb1c4714ae076eaff6cded8, weight 0 instead of 3 - removing from list.  
Warning: PoW address 30bff062bc5cd277d2d2d4e203b8eaf159b179210f992573af91b67d, weight 0 instead of 3 - removing from list.  *  

Week 48: 110K loss  
Warning: PoW address 9d1d55bdad0b0f09152a603b73bbb03a951f376a3bae474ca98fe3da, weight 0 instead of 1 - removing from list.  
Warning: PoW address 57736590c5a519bb03a8404d8d02fca60389983bbc41fb1b18b4a6ea, weight 0 instead of 2 - removing from list.  
Warning: PoW address 9463995e455116ed5e4969aac36e8f315eb1c4714ae076eaff6cded8, weight 0 instead of 3 - removing from list.  
Warning: PoW address ecf667adadf3af8f70c2091d9285d93e3ac5ad4e9c71b28d74e7c707, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 30bff062bc5cd277d2d2d4e203b8eaf159b179210f992573af91b67d, weight 0 instead of 3 - removing from list.  
Warning: PoW address 861b525e33947fb2302b728c1b9512938ac7043c3113c2e6fa176ec4, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 6a144d1bdc04709d41f6d85a38c5a20fa711749d2a3bede54a848bf7, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 4a6df7ab7071f82717e1f63aee106eff858e624582dc4f0ad10a0470, weight 0 instead of 2 - removing from list.  *  

Week 49: 30K loss    
Warning: PoW address 9d1d55bdad0b0f09152a603b73bbb03a951f376a3bae474ca98fe3da, weight 0 instead of 1 - removing from list.  
Warning: PoW address 27f6fc4609a49968b0ca742cf02ef82f256aaeea7d2faae71d2de064, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 57736590c5a519bb03a8404d8d02fca60389983bbc41fb1b18b4a6ea, weight 0 instead of 2 - removing from list.  
Warning: PoW address 9463995e455116ed5e4969aac36e8f315eb1c4714ae076eaff6cded8, weight 0 instead of 3 - removing from list.  
Warning: PoW address ecf667adadf3af8f70c2091d9285d93e3ac5ad4e9c71b28d74e7c707, weight 0 instead of 3 - removing from list.  
Warning: PoW address 30bff062bc5cd277d2d2d4e203b8eaf159b179210f992573af91b67d, weight 0 instead of 3 - removing from list.  
Warning: PoW address 861b525e33947fb2302b728c1b9512938ac7043c3113c2e6fa176ec4, weight 0 instead of 3 - removing from list.  
Warning: PoW address 6a144d1bdc04709d41f6d85a38c5a20fa711749d2a3bede54a848bf7, weight 0 instead of 3 - removing from list.  
Warning: PoW address 4a6df7ab7071f82717e1f63aee106eff858e624582dc4f0ad10a0470, weight 0 instead of 2 - removing from list.  

Week 50:  30K loss  
Warning: PoW address da857e60f755d7ea8a9c2cc03bdb70a7725c42717b5a841232744577, weight -1 instead of 3 - removing from list.  *  
Warning: PoW address f438216c183d6e38d0725aa536d7a68a9f333a66392537d9b7f098a5, weight 1 instead of 3 - removing from list.  *  

Week 51:  70K loss  
Warning: PoW address 9fa7bd5bba29dd48362cd2f39bedc4f81be10b1646a14e5fff9b091d, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address d4d69ddce86794a325e307b7bcc8fd78f7aa4a6076dc76011300a5f8, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address f61cd144852d280e1aa3b66a7120d39c655ca6c21244693b1fd0dc34, weight -1 instead of 3 - removing from list.  *

Week 52:  0 loss  
Warning: PoW address d4d69ddce86794a325e307b7bcc8fd78f7aa4a6076dc76011300a5f8, weight 0 instead of 1 - removing from list.  
Warning: PoW address f61cd144852d280e1aa3b66a7120d39c655ca6c21244693b1fd0dc34, weight -1 instead of 3 - removing from list.

Week 53:   10K loss  
Warning: PoW address 1525994bfd12be2a6a0e8ee80460d57ed3fa9638e589437c93754c81, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address d4d69ddce86794a325e307b7bcc8fd78f7aa4a6076dc76011300a5f8, weight 0 instead of 1 - removing from list.  
Warning: PoW address f61cd144852d280e1aa3b66a7120d39c655ca6c21244693b1fd0dc34, weight -1 instead of 3 - removing from list.  

Week 54:  20K loss  
Warning: PoW address 82ac6b778ac48da686736819e0dc06c739332e5c5903b3167b64e5de, weight 0 instead of 2 - removing from list.  *  


## Fill_stats

`time python3.7 fill_stats.py`  
(about 11 min => 11 sec now)

# Rewards extraction

`python3.7 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 (initial setting) to 0.1 (current setting, to account for more HNs), now temporary to 0.

```
Calc Rewards for Week 54
Total Weights at 0.0: 53603
Full Weights: 63521
Loss: 15.61%
```

The script exports:
 
## Rewards, per reward address  
exported as rewards/week54_per_reward_address.csv

## Rewards, per HN
exported as rewards/week54_per_hn_address.csv
