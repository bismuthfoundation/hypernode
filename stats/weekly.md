# Weekly data collection

To be automated.  
To be done only after Saturday, 08:00 UTC


## Get the bounds

convert.py allows to deal with timestamp and block conversion.  
The new "week" action gives all the required info from the Week Number and saves them to a week.json file

Week 96  
`python3.7 convert.py --action=week --param=96`

```
Week 96
-------------
TS   1593849600
UTC  2020-07-04T08:00:00Z
Round 16426
Slot  0
Last PoS Round 16425
PoW Height 1764702
Real TS 1593849489.33
Next TS 1593849603.11
Balance 23151.626054081367
Balance (int) 23151
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

Week 87: No loss

Week 88: No loss

Week 89: No loss

Week 90: No loss

Week 91: 30K loss

Week 92: No loss

Week 93: No loss

Week 94: 30k loss

Week 95: No loss

Week 96: No loss

## Fill_stats

`time python3.7 fill_stats.py`  
(about 11 min => 11 sec now)

# Rewards extraction

`python3.7 calc_rewards.py`

Now does all the requests. Check SCORE_TRIGGER inside this script.  
Trigger was lowered from 0.2 (initial setting) to 0.1 (current setting, to account for more HNs), now temporary to 0.

```
Calc Rewards for Week 96
Total Weights at 0.0: 84307
Full Weights: 102457
Loss: 17.71%
```

The script exports:
 
## Rewards, per reward address  
Exported as rewards/week96.per_reward_address.csv

## Rewards, per HN
Exported as rewards/week96.per_hn_address.csv
