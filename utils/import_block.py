import sys
sys.path.append("../modules")

import poscrypto
import json
import os
import sqlite3

import argparse
from posblock import PosBlock


LTIMEOUT = 45
ADDRESS = ''

DB = None


SQL_INSERT_BLOCK = "INSERT INTO pos_chain VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

# Partial sql for batch insert.
SQL_INSERT_INTO_VALUES = (
    "INSERT INTO pos_messages (txid, block_height, timestamp, sender, recipient, what, "
    "params, value, pubkey, received) VALUES "
)


def get_local_block(block_height):
    sql = "SELECT * FROM pos_chain WHERE height=?"
    res = DB.execute(sql, (block_height, ))
    return dict(res.fetchone())


def check_block_hash(block):
    try:
        raw = block.to_raw()
        msg_count = len(block.txs)
        # set removes duplicates.
        block.uniques_sources = len(set([tx.sender for tx in block.txs]))
        # TODO: verify sig signature = poscrypto.sign(raw, verify=True)
        block_hash = poscrypto.blake(raw).digest()
        if msg_count != block.msg_count:
            print("Bad Tnx count")
            return False
        return block_hash == block.block_hash
    except Exception as e:
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))


def insert_block(block, simulate=False):
    """
    Saves block object to file db - mostly copy from poschain

    :param block: a native PosBlock object
    :return:
    """
    if simulate:
        print("Simulation only")
    try:
        # Save the txs
        # TODO: if error inserting block, delete the txs... transaction?
        tx_ids = []
        # this is now an array of array. batch store the txs.
        str_txs = []
        batch = []
        batch_count = 0
        if block.height in [76171]:
            # Delete the existing block
            sql1 = "DELETE from pos_messages WHERE block_height=?"
            if not simulate:
                DB.execute(sql1, (block.height,))
                DB.commit()
        else:
            for tx in block.txs:
                if tx.block_height != block.height:
                    print(
                        "TX had bad height {} instead of {}, fixed. - TODO: do not digest?".format(
                            tx.block_height, block.height
                        )
                    )
                    return
                    # tx.block_height = block.height
                # print(tx)
                temp = tx.to_str_list()
                if temp[0] in tx_ids:
                    print(temp[0], "Double!!")
                else:
                    tx_ids.append(temp[0])

                    batch.append(" (" + ", ".join(temp) + ") ")
                    batch_count += 1
                    if batch_count >= 100:
                        str_txs.append(batch)
                        batch_count = 0
                        batch = []
                # optimize push in a batch and do a single sql with all tx in a row
                # await self.async_execute(SQL_INSERT_TX, tx.to_db(), commit=False)
            # print(tx_ids)
            if len(batch):
                str_txs.append(batch)
            if len(tx_ids):

                if block.uniques_sources < 2:
                    print("block unique sources seems incorrect")
                    return
                # TODO: halt on these errors? Will lead to db corruption. No, because should have been tested by digest?
                if block.msg_count != len(tx_ids):
                    print("block msg_count seems incorrect")
                    return
                check_block_hash(block)

                try:
                    for batch in str_txs:
                        # TODO: there is some mess here, some batches do not go through.
                        values = SQL_INSERT_INTO_VALUES + ",".join(batch)
                        if not simulate:
                            DB.execute(values)
                            DB.commit()
                except Exception as e:
                    print(e)
                    return
                # TODO: recheck all was inserted, if not error and end.
        # Delete the existing block
        sql1 = "DELETE from pos_messages WHERE block_height=?"
        if not simulate:
            DB.execute(sql1, (block.height,))
            DB.commit()

        sql2 = "DELETE from pos_chain WHERE height=?"
        if not simulate:
            DB.execute(sql2, (block.height,))
            DB.commit()
            # Then the block and commit
            DB.execute(SQL_INSERT_BLOCK, block.to_db())
            DB.commit()
        return True
    except Exception as e:
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))


def import_block(block_height: int, simulate:bool=False):
    try:
        with open("block_{}.json".format(block_height)) as f:
            data = json.load(f)
        block = PosBlock().from_hex_dict(data)
        """for tx in block.txs:
            print(tx.to_list())
        """
        insert_block(block, simulate=simulate)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Helper")
    parser.add_argument(
        "-H", "--height", type=int, default=1, help="Block height to import"
    )
    args = parser.parse_args()


    DB = sqlite3.connect("../main/data/poc_pos_chain.db", timeout=10)
    DB.row_factory = sqlite3.Row  # So it can convert into dict

    import_block(args.height, simulate=True)

    # return
