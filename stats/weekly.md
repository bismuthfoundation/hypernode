# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json file

Week 105  
`python3.7 convert.py --action=week --param=105`

```
Week 105
-------------
TS   1599292800
UTC  2020-09-05T08:00:00Z
Round 17938
Slot  0
Last PoS Round 17937
PoW Height 1855229
Real TS 1599292776.45
Next TS 1599292993.38
Balance 22554.32932072063
Balance (int) 22554
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

Week 60: No change

Week 61: No change

Week 62: 20 K loss  
Warning: PoW address 870527d6dbf70a6d08463224397c5c5bffa103afb4751784172057f0, weight 2 instead of 3 - removing from list.  *  
Warning: PoW address eec86c3a830b32bd426420142cd28672f0d7f90c8c387949ec986ae8, weight 0 instead of 1 - removing from list.  *

Week 63:  40K loss  
Warning: PoW address 85d74c77e31c00b0ebd75c8a63b23ded0d7e7cff2b884f80b44612b2, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address 89febb810bea2307263cd03be80c6a0f154b5a4db91a28d5d0771d69, weight 2 instead of 3 - removing from list.  *  

Week 64: 90K loss  
Warning: PoW address ea11ecd1a1bd3fa74fb90f27db06a802c361b1ad6275d386bed26d2e, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 5633db9f22fd804d3e73aa0dd5380161444b653b6fb1adf633ed3f10, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 4a39fbb81625b80104226153d0e7bd006ba7cb946daf6b3a9d6a0c0d, weight 0 instead of 3 - removing from list.  *  

Week 65:  30k loss 
Warning: PoW address d47a5f37159a837274bfaf01e51fe5609742ba0690fb32629582833f, weight 1 instead of 3 - removing from list.  *  

Week66: No change  
Warning: PoW address d47a5f37159a837274bfaf01e51fe5609742ba0690fb32629582833f, weight 1 instead of 3 - removing from list.  

Week 67: 10k loss  
Warning: PoW address 563a256cc30e5882fde17edff3b6d5e2d20a91a71fb11f7eaa3fa6f4, weight 0 instead of 1 - removing from list.  *  

Week 68: 30k loss  
Warning: PoW address 727dc68d941dad9e824dfe940237ecf46accaf5cbf7c9216ef02a705, weight 0 instead of 3 - removing from list. *  

Week 69: 30k loss  
Warning: PoW address c900d360dd21a8026ac56c96287d9280fafa6562983972b63c8a1870, weight 0 instead of 3 - removing from list.  *  

Week 70: 10k loss  
Warning: PoW address a152c277477ff8cd1545292e31925810b8abb812b1a913c698db57a7, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address c900d360dd21a8026ac56c96287d9280fafa6562983972b63c8a1870, weight 0 instead of 3 - removing from list.

Week 71: No loss 

Week 72: 60K loss  
Warning: PoW address 040f19212e885c7b590ca1bee851d757276a3e91170cb6e92dade4c7, weight 0 instead of 3 - removing from list.  *  
Warning: PoW address 963ab874d41d41d5c49b5695ff5b10d1f9a1e761ff3b937a54106653, weight -1 instead of 3 - removing from list  *  

Week 73:  50K loss  
Warning: PoW address c374b40e3f60fed2dd3a8004f4caf4e2fc60e203d3fcab088ad0e6df, weight -1 instead of 1 - removing from list.  *  
Warning: PoW address 1f115e642055b06806b52545466cbcc0bc540362bfb46cd313762499, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address 8b1ca22f2fc53d13187589085bc6c5076937d1c1ddae170d64392f6d, weight 0 instead of 3 - removing from list.  *  

Week 74: No loss

Week 75: 30K loss  
Warning: PoW address 980f8c00a4711838fb9002db0846012892cae8548c67a1d2d40e0ec0, weight 0 instead of 3 - removing from list.  * 
Week 76: No loss

Week 77: 40k loss  
Warning: PoW address e30026ad9a9c9060e661fab691555c5f6144b9180a59ed099731c24a, weight 0 instead of 1 - removing from list.  *  
Warning: PoW address 17dabf2990a00a9fc1221db779c3a752113c8966b64537eb6b164937, weight -1 instead of 3 - removing from list.  *  

Week 78: No loss

Week 79: 90K loss
Warning: PoW address 905dff2233842c886f600a4777348e5df85c36211d1c86f39cd26e03, weight 0 instead of 3 - removing from list. *  
Warning: PoW address 50e2ebb1375803ad5a319eeb94f907da5c78b9953b49ee8a669c8ddd, weight 0 instead of 3 - removing from list. *  
Warning: PoW address bda1951e0591d5f4cd95daab212cdedbf4cfdd4f498197fc0f4d0d17, weight 0 instead of 3 - removing from list *  


Week 80: 30K loss  
Warning: PoW address fe6c23eae26ef3113b452faa73ea31d86c1eb0a7254ea9cb57e2db10, weight 0 instead of 3 - removing from list.  * 

Week 81: No loss

Week 82: No loss

Week 83: No loss

Week 84: No loss

Week 85: 60K loss  
Warning: PoW address d28bbda8a752bd6d011501504bcb781d13c035240981fdea0c11bdfd, weight -1 instead of 3 - removing from list.  *  
Warning: PoW address 5846042bb12f2bca54ec945bfbcd635ce5a35e6ec0f1d9c91a561c2e, weight 0 instead of 3 - removing from list.  *  

Week 86:  110K loss 
Warning: PoW address 7d5c2999f9a2e44c23e7b2b73b4c0edae308e9d39482bf44da481edc, weight 0 instead of 2 - removing from list. *  
Warning: PoW address c0c1e37d2a6c18e7977109520c39d5c13a82dc90a3d6852ea2179ec1, weight 0 instead of 3 - removing from list. *  
Warning: PoW address cd293727e742a91472d3193229a5d7cae43bb8fe460e640de74b703f, weight -1 instead of 3 - removing from list. *  
Warning: PoW address 9f6f1a0168ef1d140d3d4dd57c2122a0ee2645ecbfd98f03e0e071fc, weight -1 instead of 3 - removing from list. *  

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


## Fill_stats

`time python3.7 fill_stats.py`  
(about 11 min => 11 sec now)

# Rewards extraction

`python3.7 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 (initial setting) to 0.1 (current setting, to account for more HNs), now temporary to 0.

```
Calc Rewards for Week 105
Total Weights at 0.0: 89422
Full Weights: 98596
Loss: 9.30%
```

The script exports:
 
## Rewards, per reward address  
Exported as rewards/week105.per_reward_address.csv

## Rewards, per HN
Exported as rewards/week105.per_hn_address.csv
