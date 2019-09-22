import sys
sys.path.append("../modules")

import com_helpers
import poshelpers
import poscrypto
import asyncio
import json
import sqlite3

from logging import getLogger
from tornado.iostream import StreamClosedError
from tornado.tcpclient import TCPClient
import argparse
import commands_pb2
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


def insert_block(block):
    """
    Saves block object to file db - mostly copy from poschain

    :param block: a native PosBlock object
    :return:
    """
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
        # Delete the existing block
        sql1 = "DELETE from pos_messages WHERE block_height=?"
        DB.execute(sql1, (block.height,))
        DB.commit()
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

            try:
                for batch in str_txs:
                    # TODO: there is some mess here, some batches do not go through.
                    values = SQL_INSERT_INTO_VALUES + ",".join(batch)
                    DB.execute(values)
                    DB.commit()
            except Exception as e:
                print(e)
                return

    sql2 = "DELETE from pos_chain WHERE height=?"
    DB.execute(sql2, (block.height,))
    DB.commit()
    # Then the block and commit
    DB.execute(SQL_INSERT_BLOCK, block.to_db())
    DB.commit()
    return True


async def get_block(peer, port, block_height, logger=None):
    """
    Get block from a peer
    :param peer:
    :param port:
    :param block_height:
    :param an optional logger
    :return:
    """
    logger = logger if logger else getLogger("tornado.application")
    try:
        logger.info("Asking {} for missing block {}...".format(peer, block_height))
        previous_block = PosBlock()
        previous = get_local_block(block_height - 1)
        previous_block.from_dict(previous)
        # print(previous)
        stream = await TCPClient().connect(peer, port, timeout=LTIMEOUT)
        hello_string = poshelpers.hello_string(port=6969, address=ADDRESS)
        full_peer = "{}:{}".format(peer, port)
        await com_helpers.async_send_string(
            commands_pb2.Command.hello,
            hello_string,
            stream,
            full_peer,
        )
        msg = await com_helpers.async_receive(stream, full_peer)
        """
        print(
            "Client got {}".format(com_helpers.cmd_to_text(msg.command))
        )
        """
        if msg.command == commands_pb2.Command.hello:
            # decompose posnet/address and check.
            """print(
                "Client got Hello {} from {}".format(msg.string_value, full_peer)
            )
            """
            # self.clients[full_peer]['hello'] = msg.string_value  # nott here, it's out of the client biz
        if msg.command == commands_pb2.Command.ko:
            logger.warning("Client got Ko {}".format(msg.string_value))
            return
        # now we can enter a long term relationship with this node.
        await com_helpers.async_send_int32(
            commands_pb2.Command.getblock,
            block_height,
            stream,
            full_peer,
        )
        # TODO: Add some timeout not to be stuck if the peer does not answer.
        # TODO: or at least, go out of this sync mode if the sync peer closes.
        msg = await com_helpers.async_receive(stream, full_peer)
        block = PosBlock()
        block.from_proto(msg.block_value[0])
        # print(block.to_dict(as_hex=True))
        if block_height == 76171:  # Broken block
            ok = True
        else:
            ok = check_block_hash(block)
        if not ok:
            logger.warning("Block {} KO".format(block_height))
            return False
        if block.previous_hash != previous_block.block_hash:
            logger.warning("Block {} does not fit previous block".format(block_height))
            return False
        # Ok, insert
        try:
            insert_block(block)
        except:
            pass
        return True
    except StreamClosedError as e:
        logger.warning("Error {} fetching missing block".format(str(e)))
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Helper")
    parser.add_argument(
        "-H", "--height", type=int, default=1, help="Block height to request"
    )
    parser.add_argument(
        "-I",
        "--ip",
        type=str,
        default="192.99.248.44",
        help="IP to query",
    )
    args = parser.parse_args()

    with open("../main/poswallet.json") as f:
        wallet = json.load(f)
    ADDRESS = wallet['address']

    DB = sqlite3.connect("../main/data/poc_pos_chain.db", timeout=10)
    DB.row_factory = sqlite3.Row  # So it can convert into dict

    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_block(args.ip, 6969, args.height))

    # return
