https://stackoverflow.com/questions/3379292/is-an-index-needed-for-a-primary-key-in-sqlite
https://www.slideshare.net/charsbar/dbdsqlite

https://www.sqlite.org/lang_createtable.html#rowid

EXPLAIN QUERY PLAN SELECT recipient, count(*) as messages FROM pos_messages WHERE block_height >= 87060 AND block_height <= 87062 AND what=200 GROUP BY recipient
0	0	0	SEARCH TABLE pos_messages USING INDEX what_params (what=?)
0	0	0	USE TEMP B-TREE FOR GROUP BY


 SELECT sender, count(distinct(recipient)) as messages FROM pos_messages WHERE block_height >= 87060 AND block_height <= 87062 AND what=101 GROUP BY sender
0	0	0	SEARCH TABLE pos_messages USING INDEX what_params (what=?)
0	0	0	USE TEMP B-TREE FOR GROUP BY

SELECT sender, count(*) as messages FROM pos_messages WHERE block_height >= 87060 AND block_height <= 87062 AND what=202 and params != 'START' GROUP BY sender
0	0	0	SEARCH TABLE pos_messages USING INDEX what_params (what=?)
0	0	0	USE TEMP B-TREE FOR GROUP BY


EXPLAIN QUERY PLAN SELECT COUNT(DISTINCT(sender)) AS uniques FROM pos_messages
0	0	0	SCAN TABLE pos_messages USING COVERING INDEX sender
=> use checkpoint at previous round to limit with block_height >=
but would mean return all distinct (367 atm) and merge with new ones.
keep a dict (sender, count) and update on new round only.


EXPLAIN QUERY PLAN SELECT txid FROM pos_messages WHERE txid = "\xc1q\xd7\xaf\xb0\xbb\xe6\x96\xdb\xe1\xc5\x83\x80\xe1\xc0.*\xdd\x7fb(\x8e\x8d\x8f\xce'\x05 \xc7y2,!9Zr\xff\x9a\x06\xaa\xbd\x1c\x14E\xfb3\xff\x10M\x01\x00<\x87=\xc9Y\x92\xb9}h\x9953a"
0	0	0	SEARCH TABLE pos_messages USING COVERING INDEX sqlite_autoindex_pos_messages_1 (txid=?)
Still is slow on pos_message
SELECT count(*) FROM...
add tx4 like index? 


EXPLAIN QUERY PLAN SELECT COUNT(DISTINCT(sender)) AS uniques_round FROM pos_messages WHERE block_height >= 87842
0	0	0	SEARCH TABLE pos_messages USING INDEX height_ts (block_height>?)


EXPLAIN QUERY PLAN SELECT COUNT(DISTINCT(forger)) AS forgers_round FROM pos_chain WHERE round = 7211
0	0	0	SEARCH TABLE pos_chain USING INDEX round (round=?)
(no forger index, adding the index does not help)


EXPLAIN QUERY PLAN SELECT height, round, sir, block_hash FROM pos_chain ORDER BY height DESC LIMIT 1
0	0	0	SCAN TABLE pos_chain
EXPLAIN QUERY PLAN SELECT height, round, sir, block_hash FROM pos_chain where height=(select max(height) from pos_chain)
0	0	0	SEARCH TABLE pos_chain USING INTEGER PRIMARY KEY (rowid=?)
0	0	0	EXECUTE SCALAR SUBQUERY 1
1	0	0	SEARCH TABLE pos_chain
uses index, but time seems similar: bench


poc_pos_chain.db : 
EXPLAIN QUERY PLAN SELECT COUNT(DISTINCT(sender)) AS uniques FROM pos_messages WHERE block_height <= 87841
0	0	0	SEARCH TABLE pos_messages USING INDEX height_ts (block_height<?)

poc_pos_chain.db : DELETE FROM pos_messages WHERE block_height IN (SELECT height FROM pos_chain WHERE round = ?)  (7212,)
EXPLAIN QUERY PLAN SELECT * FROM pos_messages WHERE block_height IN (SELECT height FROM pos_chain WHERE round = 7212)
0	0	0	SEARCH TABLE pos_messages USING INDEX height_ts (block_height=?)
0	0	0	EXECUTE LIST SUBQUERY 1
1	0	0	SEARCH TABLE pos_chain USING COVERING INDEX round (round=?)

posmempool.db : DELETE FROM pos_messages WHERE timestamp <= strftime('%s', 'now', '-30 minute')


TODO also: factorize/index pubkey
