# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json fi6e

Week 186  
`python3 convert.py --action=week --param=186`

```
Week 186
-------------
TS   1648281600
UTC  2022-03-26T08:00:00Z
Round 31546
Slot  0
Last PoS Round 31545
PoW Height 2669604
Real TS 1648281589.44
Next TS 1648281659.59
Balance 20151.69043539
Balance (int) 20151

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

Week 87 to 100: No loss

Week 101: 30K loss  
Warning: PoW address 0510f82deb1adfbe44bc54e4ae44c3504b1a37b2ab94be3685b64ddb, weight 0 instead of 2 - removing from list. *   
Warning: PoW address b2b9802bc5f589a8c0638034df546814dbe48132d9ee54ae48da8934, weight 0 instead of 1 - removing from list. *  

Week 102: 50K loss  
Warning: PoW address 3daa7cb20e7c0af52cbf43ed7505474f320ed0c5bdadb7d69e7e7d5d, weight 0 instead of 2 - removing from list.  *  
Warning: PoW address be8355d581e7ba5775fc970bb60fee831a47ddc4ef92a28d07027adf, weight 0 instead of 3 - removing from list.  *  

Week 103: No Loss

Week 104: Significant losses

Warning: PoW address a8219e34ef35721d92a7e0ce54586169f56fb27939170d6e2258e599, weight 0 instead of 2 - removing from list.  
Warning: PoW address 4e93a3551b2198b358b623fdbf4b65da35367d836d4e65ce0b7f2c63, weight 0 instead of 3 - removing from list.  
Warning: PoW address d128451327015225626801e8bff43e2d4e787c02ea7b07562edc4286, weight 0 instead of 3 - removing from list.  
Warning: PoW address 557e6d2e72e01fb40fabe4c1abdd010b0e0cba4f6ddbbb4c351aa8f1, weight 0 instead of 3 - removing from list.  
Warning: PoW address e30394f77025d0d7b81f4665a38a755be7a7dc0e682eb3850951507a, weight 0 instead of 3 - removing from list.  
Warning: PoW address 14b9738c24bed22f381ceaecb2a36318bab655a348fe23addeb895ec, weight 0 instead of 3 - removing from list.  
Warning: PoW address 6d30876e15bec32452ea8ba0eed1a1f2a98d9e62163e51665e86c707, weight 0 instead of 3 - removing from list.  
Warning: PoW address 6b3613873476d87f2b2a3185350d888ac9797e625c827b4fbc4931c4, weight 0 instead of 3 - removing from list.  
Warning: PoW address 8d54db36d08ba7a8339bc3bd388a000114a54f2e6f63c18be1f22a9a, weight 0 instead of 3 - removing from list.  
Warning: PoW address f3edd32e2bb14a0df57c440b2d1f7be000523122f5f99e90d5d38075, weight 0 instead of 3 - removing from list.  
Warning: PoW address 28f9abdeac50fa12a043c54f05ed3c3aabfa777a366a53b6aa8a4b22, weight 0 instead of 3 - removing from list.  
Warning: PoW address 80a0af8361186b5bb72a623364d9530ed91ec19b2ba00b95d2457bae, weight 0 instead of 3 - removing from list.  
Warning: PoW address a982dbb1582285b47b1bf6e84b61b5ded99963c347c5b1a5716ff9c8, weight 0 instead of 3 - removing from list.  
Warning: PoW address e99fbb5ada450e19191f0876e01ef5966e1e83e70d94f38999afb317, weight 0 instead of 3 - removing from list.  
Warning: PoW address 07042d4da79f461b235114bf3a32f247d6c8e21b461cc872cbf75d21, weight 0 instead of 3 - removing from list.  
Warning: PoW address 3a930e2ab1495a8017fa0bebe1ebfc8ed9bdb5ed137d90a04d2d8e9f, weight 0 instead of 3 - removing from list.  
Warning: PoW address 7f49850362a8e24ffeddc2d42a065eacda453963a1073951062e8c07, weight 0 instead of 3 - removing from list.  
Warning: PoW address 3b971e2bcfc40724cd6f269380f9aa1b0fe701e873f945522f827a06, weight 0 instead of 3 - removing from list.  
Warning: PoW address 0449c37bbfe53ee2df5b401d09d115f9b2f0bcf6da90f6842d04fcc0, weight 0 instead of 3 - removing from list.  
Warning: PoW address 19b3c49980b2501dd0f1fac6ef1b9bc5bc1eb7cf16a2edb6b1ff9438, weight 0 instead of 3 - removing from list.  
Warning: PoW address 171766928868ea7501dff2f6265b614b35bc233abf99f3c3e848f871, weight 0 instead of 3 - removing from list.  
Warning: PoW address bbec3c115e02524816d22f6f1eb184f22cabc1dd40327c4a87cb6c56, weight 0 instead of 3 - removing from list.  
Warning: PoW address 07ec3503073011a41bc46a701f202025b36ac7abd486b3f0125ff734, weight 0 instead of 3 - removing from list.  
Warning: PoW address c88f12fa811e76c11dffda4160fdd5f447e7811b00a4ecafd5f1f872, weight 0 instead of 3 - removing from list.  
Warning: PoW address 1c294edf9ad339d4c612a8a92ec0ddd032028c33b40aa1aeae52ee14, weight 0 instead of 3 - removing from list.  
Warning: PoW address cee7104163d2a73a42eab38ceca6259012687b4001faf2a1a3bf900b, weight 0 instead of 3 - removing from list.  
Warning: PoW address 9da9123767efd974a2b4f8d01c5c255b08b8d60f9dbbdd7f4352a5eb, weight 0 instead of 3 - removing from list.  
Warning: PoW address 99aa727f2eda1f461450bc185eb0ad37e299ec5fa81922b73b9beaf0, weight 0 instead of 3 - removing from list.  
Warning: PoW address e9fb56a8050d17bde01c9b63fd716dffd5d60a3804290e37d844cbbc, weight 0 instead of 1 - removing from list.  

Week 105: 50k loss  
Warning: PoW address 645ce206924e84fa1e3a15afdedc4b6efc979fbf79eb57f8e65f708c, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 3b4152271b9d93e0a4c4a43ab524c227eeb1073c3067bafb7ca89d42, weight 1 instead of 3 - removing from list.  *  

Week 106: 30k loss  
Warning: PoW address d9d8b6ed0f25c9d78faa02124e5a4c62e1a050805c8155f8f84dbfba, weight 0 instead of 3 - removing from list.  * 

Week 107: 10K loss  
Warning: PoW address 809a58bfd52ca0f8befdeb46a334c37a8ad60fc5153aeefe0f8d63d5, weight 0 instead of 1 - removing from list.  * 

Week 108: 10K loss  
Warning: PoW address 6f55192a32140932898c1f069ae70e10bbb8e0f849f1bf9bbfe1133e, weight 0 instead of 1 - removing from list.  * 

Week 109: 10K loss  
Warning: PoW address 60f98bda0238815643f0a985a111208f26e77edd228c2405ef245dc5, weight 0 instead of 1 - removing from list.  *  

Week 110: 20K loss  
Warning: PoW address 0b9bef177bca2f4213012e1b9e8eb5a3cca5ef1a96624e4c97720ae9, weight 0 instead of 2 - removing from list.  *  

Week 111: 20K loss  
Warning: PoW address 0b9bef177bca2f4213012e1b9e8eb5a3cca5ef1a96624e4c97720ae9, weight 0 instead of 2 - removing from list.

Week 112: No loss  

Week 113: No loss   

Week 114: 30K loss  
Warning: PoW address 5c7fdf67d6753de9f26460da56c1379a1ec26c6e1e4a79eb69912451, weight 2 instead of 3 - removing from list.  *  

Week 115: 30K loss  
Warning: PoW address 8d57af5dc042b824c62baecffb64ce6eabb74a0027a434617a10f8cd, weight 2 instead of 3 - removing from list.  *

Week 116: 80K loss  
Warning: PoW address 003b2b143949241801c9003702b446d5abb37496cad025514ccce55b, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 080965db6930a2fdce8413033b3d3365597585d78dd1a0d565999d8d, weight 0 instead of 2 - removing from list.  *  
Warning: PoW address 7c7032c155a2c71ad8dc18fdb0c8a544e771e8a5ab2ec03a358dd67f, weight 0 instead of 3 - removing from list.  *  

Week 117: 20K loss  
Warning: PoW address ca12d5a70decbbe6caa1d7ca644bc029080186039df19d3747073093, weight 0 instead of 2 - removing from list.  *

Week 118: 30K loss  
Warning: PoW address 18e0fac56218ee2b5239ddc4fee5cfdddf57b95e20a854acfb7f5cc9, weight 0 instead of 3 - removing from list.  *  

Week 119: 10k Loss  
Warning: PoW address f438216c183d6e38d0725aa536d7a68a9f333a66392537d9b7f098a5, weight 0 instead of 1 - removing from list.  *  

Week 120:  20k loss
Warning: PoW address 90ce1ecab243e722a6981b603c443e87571499a9ca261e3bb2b87f8f, weight 1 instead of 2 - removing from list.  * 

Week 121:  No loss  

Week 122:  30K Loss  
Warning: PoW address 095d7aaa85650ea54c2b9d83d957c14e082c214d565a248ef5694868, weight 0 instead of 3 - removing from list.  * 

Week 123:  50K Loss  
Warning: PoW address c1f5ca2761fc8ae72989ca59288840543997ebd18f43ea85e700eb8f, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address be426ec5d42e5e7a3744cf92c650cfec53c1bea7809b9243028de915, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 90ce1ecab243e722a6981b603c443e87571499a9ca261e3bb2b87f8f, weight 0 instead of 1 - removing from list.  *  

Week 124:  No loss

Week 125:  20K Loss  
Warning: PoW address b55b25d2937abead6249340449aa354c2264a7d867861463544253d6, weight 1 instead of 2 - removing from list.  *  
Warning: PoW address e1bf97a8163c818110a3c265a52601e87f6fec838bf48c36dac5bdf9, weight 0 instead of 1 - removing from list.  *  

Week 126: 10k loss  
Warning: PoW address 2b63a62a0f655fc50a79baf95b25373560202e95032a281e4b7824c3, weight 0 instead of 1 - removing from list.  *  

Week 127: 10k loss  
Warning: PoW address 6939922fac47ba8d9a5f0234b1af93856eac52f693eb55f4ab9de79a,, weight 0 instead of 1 - removing from list.  *  

Week 128:  
No loss

Week 129:  11K loss  
Warning: PoW address a5c51c73b7b97fdfd97b0b86a3f809d09102249007b292e4fc67230a, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 5e47f571c6c084f37ed727455d54f0c7f3fca8eb0b795aec72e1e9a4, weight 0 instead of 2 - removing from list.  *  
Warning: PoW address 8e5a86002bd2e0c4c2cc29c808f51a9e8b2442c25f72a1cfe8f17f3b, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 07042d4da79f461b235114bf3a32f247d6c8e21b461cc872cbf75d21, weight 0 instead of 3 - removing from list.  *  

Week 130:  2K loss  
Warning: PoW address 825cff1cb0599788a336f30518943080dc9f9fb7f2e9ed42c50e0324, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address 6d064a93ad0c570bdff008fed5728299e5ffb553f888d32098edd69c, weight 0 instead of 1 - removing from list.  *  


Week 131:  
No loss

Week 132: 70K loss  
Warning: PoW address 7c90e9de3ca408c9e5be374962a61a4f3c73b4a958443db20947040c, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 040db50686489d23e9fd53656188697ef3102e7a811cca8cac5ff9cb, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address ef9c5ae3de1e6cb168100c5328281a38c686ad44b75f27f954dfb430, weight 0 instead of 1 - removing from list.  *  

Week 133: 10K loss  
Warning: PoW address 7c189c8a10f86436e55ef2c70a25e234329931df3612ca12b1573062, weight 0 instead of 1 - removing from list.  * 

Week 134: 30k loss  
Warning: PoW address bfc237fc1cca0aed09438b8c87cc6311402eab942179a115d8647ae7, weight 0 instead of 3 - removing from list.  *   

Week 135: No loss  

Week 136: 360K loss  
Warning: PoW address 557e6d2e72e01fb40fabe4c1abdd010b0e0cba4f6ddbbb4c351aa8f1, weight 0 instead of 3 - removing from list.  *   
Warning: PoW address d128451327015225626801e8bff43e2d4e787c02ea7b07562edc4286, weight 0 instead of 3 - removing from list.  *   
Warning: PoW address e30394f77025d0d7b81f4665a38a755be7a7dc0e682eb3850951507a, weight 0 instead of 3 - removing from list.  *   
Warning: PoW address 14b9738c24bed22f381ceaecb2a36318bab655a348fe23addeb895ec, weight 0 instead of 3 - removing from list.  *   
Warning: PoW address 6d30876e15bec32452ea8ba0eed1a1f2a98d9e62163e51665e86c707, weight 0 instead of 3 - removing from list.  *   
Warning: PoW address 6b3613873476d87f2b2a3185350d888ac9797e625c827b4fbc4931c4, weight 0 instead of 3 - removing from list.  *   
Warning: PoW address 8d54db36d08ba7a8339bc3bd388a000114a54f2e6f63c18be1f22a9a, weight 0 instead of 3 - removing from list.  *   
Warning: PoW address f3edd32e2bb14a0df57c440b2d1f7be000523122f5f99e90d5d38075, weight 0 instead of 3 - removing from list.  *   
Warning: PoW address 28f9abdeac50fa12a043c54f05ed3c3aabfa777a366a53b6aa8a4b22, weight 0 instead of 3 - removing from list.  *   
Warning: PoW address 80a0af8361186b5bb72a623364d9530ed91ec19b2ba00b95d2457bae, weight 0 instead of 3 - removing from list.  *   
Warning: PoW address a982dbb1582285b47b1bf6e84b61b5ded99963c347c5b1a5716ff9c8, weight 0 instead of 3 - removing from list.  *   
Warning: PoW address e99fbb5ada450e19191f0876e01ef5966e1e83e70d94f38999afb317, weight 0 instead of 3 - removing from list.  *   

Week 137: No loss  

Week 138: 30K loss  
Warning: PoW address 27d1176553d19d28126d5af6020bbcbf98402a2c6dbd61b36f2ebc0c, weight 0 instead of 3 - removing from list.  *  

Week 139: 180K loss  
Warning: PoW address 67122597f2918316c6ea326c7531e774678ea4d7fdf58edfd3925946, weight 1 instead of 3 - removing from list.  *  
Warning: PoW address 3568feaef017e395e9a854fb4f13dd389d8bb55b3afdcad3c8790e48, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 3b13e6916cafb2787be375725e8c8fe87f5e3381b5e6ffd3c31091e9, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address d588e025050dcaed277dea61d11d61eaf0176f82b6b858d877c90dbd, weight 0 instead of 2 - removing from list.  *  
Warning: PoW address 9f5a8f080854b061f892379fd4e12c8abc4332784cd796c1387eb1e0, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 91b3daa33f733a0a94b2a1ed5bf95c51c4b3af26a5dae928a310c38a, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address 3a3ce4220e7fb1748426b8b3b292e0e9b69193484e1c6d5c79b39942, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address f5ab1e0435f80485e6d3513967a2bdb4e0122af6ef765be6de97d654, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address 67786f1507a9818b55e1c8a4036b3dacc21ca19477b24b3f48a88dbd, weight 0 instead of 2 - removing from list.  *  

Week 140: No Loss  

Week 141: No Loss  

Week 142: No Loss  

Week 143: 20K Loss   
Warning: PoW address e7cafb25c34de2a0a2ab2758ad2164bcfe67ab8b23a76f69854596a6, weight 0 instead of 2 - removing from list.  * 

Week 144: No Loss  

Week 145: 60k Loss  
Warning: PoW address e9aa9decc30e969678be62ea3a8762b9aef906e0362d2d3e691ce3c7, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 44ba9acf1e4252b40e920742f0e0d5cd7913f192635d96bfc036e47d, weight 0 instead of 3 - removing from list.  *  

Week 146: No Loss  

Week 147: 20K loss  
Warning: PoW address 7d8a3308942a4bebc451bbd909f4612091084d1403925cd1d1cf87ad, weight 0 instead of 2 - removing from list.  * 
  
Week 148: No Loss  

Week 149: No Loss  

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


## Fill_stats

`time python3 fill_stats.py`  

# Rewards extraction

`python3 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 (initial setting) to 0.1 (current setting, to account for more HNs), now temporary to 0.

```
Calc Rewards for Week 186
Total Weights at 0.0: 78101
Full Weights: 103001
Loss: 24.17%
Max Reward 130.04 BIS, Token unit 21.67
Total token rewards 605
```

The script exports:
 
## Rewards, per reward address  
Exported as rewards/week186per_reward_address.csv

## Rewards, per HN
Exported as rewards/week186per_hn_address.csv
