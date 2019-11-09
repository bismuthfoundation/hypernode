# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json file

Week 62:  
`python3.7 convert.py --action=week --param=62`

```
Week 62
-------------
TS   1573286400
UTC  2019-11-09T08:00:00Z
Round 10714
Slot  0
Last PoS Round 10713
PoW Height 1423388
Real TS 1573286391.42
Next TS 1573286574.62
Balance 24072.232016550144
Balance (int) 24072
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

Week 55:  10K loss  
Warning: PoW address a50e4ff9ebd2bf4d843f4797d8ee6de43db9445c6b9fbf9ada169ca9, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address 82ac6b778ac48da686736819e0dc06c739332e5c5903b3167b64e5de, weight 0 instead of 2 - removing from list.

Week 56:  550K loss (The 30ks being moved to another HN address, not lost)  
Warning: PoW address 175a01ae07f53546f2988f369b4e3f72e4e4af5c03a8b764993f515e, weight 1 instead of 3 - removing from list.  *  
Warning: PoW address 23a8199566c7bd418e0d8531d937545e68e2db78674fce68a886d34f, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 24a71fc4a31cd95bbb8e95b1d185491c79bba207961168cfc0946194, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address be7c151eab50142ab30ff29da83d917b4495179a3f0384d04414bb16, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 7ee4dbe6c350a731d59c942aeb20911b2526706606140b8cdf1b3b06, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address b7116d5e94dd09f1ca182e1d92761194fbc1c7262e37e0d8152375fd, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 9e295d7c47150a7e1a195a3e453b5af95650e3db1d5a581e13868eb5, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 4ab193b4a2bdf6ebf2175710603d589f307b718968233b4613370b76, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address c9ca8284ab78d845f0dc61386081d6fa9cab1034e7115d796b729978, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 9eb83a2e932cfa102b65b9e891837c46170b2f1fa269f9a1d9e901e7, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address ddb503da0fb09739e1d8c976252912e43eb3c4420d940396f383bf90, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 27fa5b107eae73b66a1ccbc35b8620685a92513dbe7290c2a80646fd, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 8e6294ba5b84d17730a5cc8b2fe87c2ef5752d39c9fa4021378a5aae, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address c01499718c955379834b0e3d8a4af14b3e444395219a25926e4ffdd7, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 039815dd485a766bc590c610ae509b97bffd88cb41ee24f17c744a89, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address d8e92d42bfe387a2bc0d01a9192653f2cd91761e2e76612ea6150689, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 36783c65fa60cdb8a40954468d206c39f65fb1a726c831462ab032ef, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 63dcd18823c7b3f85446a13059a0e26f639666637ace58c7bd0f34dc, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 81292078ccefdf41768416497d6c7ec4c5e310ba50e051a66d91df16, weight 0 instead of 3 - removing from list.  *  

WeeK 57:  40K loss  
Warning: PoW address e556274d92f6b3d035c6ae6e35e8620af8e0df9833d8040f51a22c04, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address b2c0f4ae6f9a2068aac6287bf8f3f0008e29c6156092d6efdb179b95, weight 0 instead of 1 - removing from list.  *  

WeeK 58: 10K loss  
Warning: PoW address d6591aef0d618b7c3abb2770dee41d3f0e58aebdc55426bb264497fe, weight 2 instead of 3 - removing from list.  *

WeeK 59:  20K loss  
Warning: PoW address 3703518b080fc56b783a15cb6fe5452d8acb4c6a5958b8a2d50e25fb, weight 1 instead of 3 - removing from list.  *
Warning: PoW address d6591aef0d618b7c3abb2770dee41d3f0e58aebdc55426bb264497fe, weight 2 instead of 3 - removing from list.

Week 60: No change

Week 61: No change

Week 62: 20 K loss  
Warning: PoW address 870527d6dbf70a6d08463224397c5c5bffa103afb4751784172057f0, weight 2 instead of 3 - removing from list.  *  
Warning: PoW address eec86c3a830b32bd426420142cd28672f0d7f90c8c387949ec986ae8, weight 0 instead of 1 - removing from list.  *


## Fill_stats

`time python3.7 fill_stats.py`  
(about 11 min => 11 sec now)

# Rewards extraction

`python3.7 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 (initial setting) to 0.1 (current setting, to account for more HNs), now temporary to 0.

```
Calc Rewards for Week 62
Total Weights at 0.0: 81343
Full Weights: 94072
Loss: 13.53%
```

The script exports:
 
## Rewards, per reward address  
Exported as rewards/week62_per_reward_address.csv

## Rewards, per HN
Exported as rewards/week62_per_hn_address.csv
