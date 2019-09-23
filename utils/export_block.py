import sys
sys.path.append("../modules")

import poscrypto
import sqlite3

import argparse
from posblock import PosBlock, PosMessage


DB = None


SQL_TXS_FOR_HEIGHT = "SELECT * FROM pos_messages WHERE block_height = ? ORDER BY timestamp ASC"


def get_local_block(block_height):
    sql = "SELECT * FROM pos_chain WHERE height=?"
    res = DB.execute(sql, (block_height, ))
    return dict(res.fetchone())


def check_block_hash(block):
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


def export_block(block_height: int) -> str:
    """
    export block height to json
    :param peer:
    :param port:
    :param block_height:
    :param an optional logger
    :return:
    """
    try:
        block = get_local_block(block_height)
        block = PosBlock().from_dict(dict(block))
        # Add the block txs
        res = DB.execute(SQL_TXS_FOR_HEIGHT, (block_height,))
        txs = res.fetchall()
        for tx in txs:
            tx = PosMessage().from_dict(dict(tx))
            block.txs.append(tx)

        # tests
        if block.uniques_sources < 2:
            print("block unique sources seems incorrect")
            return
            # TODO: halt on these errors? Will lead to db corruption. No, because should have been tested by digest?
        if block.msg_count != len(txs):
            print("block msg_count seems incorrect")
            return
        check_block_hash(block)

        return block.to_json()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Helper")
    parser.add_argument(
        "-H", "--height", type=int, default=1, help="Block height to export"
    )
    args = parser.parse_args()

    DB = sqlite3.connect("../main/data/poc_pos_chain.db", timeout=10)
    DB.row_factory = sqlite3.Row  # So it can convert into dict

    json = export_block(args.height)
    with open("block_{}.json".format(args.height), "w") as f:
        f.write(json)
