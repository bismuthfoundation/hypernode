# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json fi6e

Week 223  
`python3 convert.py --action=week --param=223`

```
Week 223
-------------
TS   1670659200
UTC  2022-12-10T08:00:00Z
Round 37762
Slot  0
Last PoS Round 37761
PoW Height 3041941
Real TS 1670659162.84
Next TS 1670659257.45
Balance 18429.7391462
Balance (int) 18429

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

Week 150: 30K Loss  
Warning: PoW address c2ddaa3a6233fdae122eab931333f867af6174350a2c1a33ba090670, weight 0 instead of 3 - removing from list.  *

Week 151: No Loss  
Warning: PoW address c2ddaa3a6233fdae122eab931333f867af6174350a2c1a33ba090670, weight 0 instead of 3 - removing from list.  * 

Week 152: No Loss  

Week 153: No Loss  

Week 154: No Loss  

Week 155: No Loss  

Week 156: 30K Loss  

Warning: PoW address 4b1a0476ced360ff390dde816860f5ebfd06ae81cb2a3ef19af9b43e, weight 0 instead of 3 - removing from list.  * 

Week 157: No Loss  

Week 158: No Loss  

Week 159: No Loss  

Week 160: No Loss  

Week 161: No Loss  

Week 162: No Loss  

Week 163: No Loss  

Week 164: No Loss  

Week 165: 30K loss  
Warning: PoW address f5cdaf364cd448ca90ca8bbc636af25f019cc2ad21c04cc007eeaea7, weight 0 instead of 3 - removing from list.

Week 166: 40K Loss  

Week 167: 10K Loss   
Warning: PoW address d2a5bc9f3ba1b2eb66a98ca0262cb8a5785e5048cdcfed26c73c8924, weight 0 instead of 1 - removing from list. *  

Week 168: 150K Loss  
Warning: PoW address 1af8f10f2ab8564953992a98c13364369569910c65be7f2c2a2bc442, weight 0 instead of 3 - removing from list. *  
Warning: PoW address 8a3e0d2d3eb34b29e5a9c22564b9d9012c0ffb1c67b164a33a5c9a34, weight 0 instead of 3 - removing from list. *  
Warning: PoW address 1df67f53550e408574295aef40a7e579c38d4c38f8ad2a429e8470d6, weight 0 instead of 3 - removing from list. *  
Warning: PoW address d2a5bc9f3ba1b2eb66a98ca0262cb8a5785e5048cdcfed26c73c8924, weight 0 instead of 1 - removing from list. *  
Warning: PoW address c5943d3bf6dc1bda8f138b5de0d0ab3dcd0a36c863552d04e0d46f98, weight 0 instead of 3 - removing from list. *  
Warning: PoW address Bis1Q6YkN5f8mPVaSam7ZNg9qAwRodPhH936q, weight 0 instead of 2 - removing from list. *  

Week 169: 10k loss  
Warning: PoW address 0bf461aeed5b62836b21450e9af8554406dc0d80d8c4d9ae0a0089e0, weight 0 instead of 1 - removing from list. *  

Week 170: no loss  

Week 171: no loss  

Week 172: no loss 

Week 173: no loss 

Week 174: no loss 

Week 175: 60k loss  
Warning: PoW address 8d571a1297c3c8304a432821ed59074eff2d3314e955919a7721a42c, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 343d9e4e65691a88dfae298c9272440886d1492930445b6f64971598, weight 0 instead of 3 - removing from list.  *  

Week 176:  20k loss  
Warning: PoW address 3c4e412ea0e5d89b19b7d226912223fa870321494ba5b1444c404762, weight 0 instead of 2 - removing from list.  *  

Week 177:  30k loss  
Warning: PoW address fd024338b26d474baefc5c5caec420ff3f9fd1a4535a723281d84ee0, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address 3c4e412ea0e5d89b19b7d226912223fa870321494ba5b1444c404762, weight 0 instead of 2 - removing from list.  *  

Week 178:  no loss  

Week 179:  no loss  

Week 180:  no loss  

Week 181:  30k loss  
Warning: PoW address a404a1b836a2cdc99b3054b693a3756b1414ff0ab8f4832ebea02938, weight 0 instead of 1 - removing from list.  * 
Warning: PoW address c647a72b6b4435852d31ca2b66ca6a3769dfa3aefd53feb1919ec1f4, weight 0 instead of 1 - removing from list.  * 
Warning: PoW address 7dc8ea3baee06cdc1bbebba8ab50ef34636264901da424939c769615, weight 0 instead of 1 - removing from list.  * 


Week 182:  30k loss  
Warning: PoW address 616cf46dec5e292034a3b9e88315a2161ec3f927f279e922e55a770f, weight 0 instead of 3 - removing from list.  * 

Week 183:  No loss  

Week 184:  No loss  

Week 185:  No loss  

Week 186:  No loss  

Week 187:  No loss  

Week 188:  No loss  

Week 189: 30K loss  
Warning: PoW address d7cd5dbacc85174cdbe3525ed92d9b1c6cd6b7af33a3cf31689ef5c9, weight 0 instead of 3 - removing from list.  *  

Week 190:  No loss  

Week 191:  No loss  

Week 192:  No loss  

Week 193:  No loss  

Week 194:  No loss  

Week 195:  No loss  

Week 196:  No loss  

Week 197:  20K loss  
Warning: PoW address 44d2dda5e771a2a2999a08f6c0d24d142042b47b1bda6297470ec752, weight 0 instead of 2 - removing from list.  *  

Week 198:  30K loss  
Warning: PoW address ba50c90230ddc99cfba6ccea881f5e91b3145aedbfd51c1fff84adeb, weight 0 instead of 3 - removing from list.  * 


Week 199:  No loss  

Week 200:  No loss  

Week 201:  No loss  

Week 202:  No loss  

Week 203:  No loss  

Week 204:  No loss  

Week 205:  No loss  

Week 206:  No loss  

Week 207:  No loss  

Week 208:  No loss  

Week 209:  No loss  

Week 210:  No loss  

Week 211:  No loss  

Week 212:  90K loss  
Warning: PoW address 3bc3202c5b7d0c76b81f2d2b40e9e464d90153d6a3dad85eb9625052, weight 0 instead of 3 - removing from list. *  
Warning: PoW address 17c02bbbdaa844ab5f5b3cd21227b3ff8494ac5c16cd9cf58cd93834, weight 0 instead of 3 - removing from list. *  
Warning: PoW address a958b32c1c3822149ff4db7042ef56aaf5af0622b5f74fffcdc00174, weight 0 instead of 3 - removing from list. *  

Week 213:  no loss  

Week 214:  10K loss  
Warning: PoW address f44e1adb0d5407d4ae483b13a587bb66eccb7bb9850c57a695903f1e, weight 0 instead of 1 - removing from list.  *

Week 215:  30K loss  
Warning: PoW address a16ec4a1194c03e13fd24641577184d497d9ca5ddd8697476494e80b, weight 0 instead of 3 - removing from list.  *  

Week 216:  no loss  

Week 217:  no loss  

Week 218:  no loss  

Week 219:  no loss  

Week 220:  10k loss  
Warning: PoW address c50fb7c1b763c2bff1daf1d678941ba8e61066a1feba27660a120033, weight 1 instead of 3 - removing from list.

Week 221:  no loss  

Week 222:  no loss  

Week 223:  no loss  


## Fill_stats

`time python3 fill_stats.py`  

# Rewards extraction

`python3 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 (initial setting) to 0.1 (current setting, to account for more HNs), now temporary to 0.

```
Calc Rewards for Week 223
Total Weights at 0.0: 74312
Full Weights: 83677
Loss: 11.19%
Max Reward 122.76 BIS, Token unit 20.46
Total token rewards 486

```

The script exports:
 
## Rewards, per reward address  
Exported as rewards/week223per_reward_address.csv

## Rewards, per HN
Exported as rewards/week223per_hn_address.csv
