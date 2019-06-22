# Stats collection Flow


convert.py --action=week --param=42

writes week.json with 
`{"week": 42, "ts": 1561190400, "UTC": "2019-06-22T08:00:00Z", "last_pos_round": 7353, "pow_height": 1222504, "balance": 23558}`

Used by the following scripts

`python3 fill_rounds.py`  
Verifies again the registered and active HNs for each round of the period.     
This will tell if any HN cheated on its balance (balance dropped below the registered collateral)

Saves via hn_db.save_hn_from_regs, round by round

ok until then.

`time python3 fill_stats.py`  


