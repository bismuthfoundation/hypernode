"""
Check db for missing txns and report. Very crude.
Run with HN stopped.
"""

import sqlite3
import json

if __name__ == "__main__":
    db = sqlite3.connect("../main/data/poc_pos_chain.db", timeout=10)
    SQL = "SELECT MAX(height) FROM pos_chain"
    res = db.execute(SQL)
    height = res.fetchone()[0]
    print("Height {}".format(height))
    SQL1 = "SELECT msg_count FROM pos_chain WHERE height=?"
    SQL2 = "SELECT count(*) FROM pos_messages WHERE block_height=?"
    missings = []
    for height in range(height - 1):
        # get txn count from header
        res = db.execute(SQL1, (height,))
        temp = res.fetchone()
        if temp is None:
            print("Height {} is None".format(height))
            missings.append(height)
        msg_count1 = temp[0] if temp else 0
        # get txn count from pos_messages
        res = db.execute(SQL2, (height,))
        temp = res.fetchone()
        msg_count2 = temp[0] if temp else 0
        if msg_count1 != msg_count2:
            print("{}: {} - {}".format(height, msg_count1, msg_count2))
            missings.append(height)
    with open("missing.json", "w") as fp:
        json.dump(missings, fp)
    print("Dumped as missing.json")
