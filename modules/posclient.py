"""
Pos client class for Bismuth HyperNodes
=======================================
Tornado based
"""

import os
import sys
from tornado.tcpclient import TCPClient
# import asyncio
import json
import time

import common
import com_helpers
import poscrypto
import posblock
import commands_pb2

__version__ = '0.0.34'


class Posclient:

    def __init__(self, ip, port, verbose=False, wallet="poswallet.json", version=''):
        self.ip = ip
        self.port = port
        self.verbose = verbose
        self.client_version = version
        poscrypto.load_keys(wallet, verbose=self.verbose)

    async def action(self, action='hello', param=''):
        """
        Action Handler

        :param action:
        :param param:
        :return: The command result
        """
        try:
            if action not in ('hello', 'ping', 'status', 'tx', 'address_txs', 'mempool', 'update', 'txtest', 'block'):
                raise ValueError("Unknown action: {}".format(action))
            tcp_client = TCPClient()
            # FR: if self.verbose, print time to connect, time to hello, time end to end. Use a finally: section
            stream = await tcp_client.connect(self.ip, self.port)
            # Clients identifies itself as port 00101. ports < 1000 won't be used as peers.
            await com_helpers.async_send_string(commands_pb2.Command.hello, common.POSNET + '00101' + poscrypto.ADDRESS,
                                                stream, self.ip)
            msg = await com_helpers.async_receive(stream, self.ip)
            if self.verbose:
                print("Client got {}".format(msg.__str__().strip()))

            if msg.command == commands_pb2.Command.hello:
                # decompose posnet/address and check.
                if self.verbose:
                    print("Client got Hello {} from {}".format(msg.string_value, self.ip))

            if msg.command == commands_pb2.Command.ko:
                print("Client got Ko {}".format(msg.string_value))
                return

            if 'ping' == action:
                # TODO - useful for client?
                return

            if 'hello' == action:
                # TODO - return version infos: posnet000106969BMSMNNzB9qdDp1vudRZoge4BUZ1gCUC3CV
                return

            if 'status' == action:
                await com_helpers.async_send_void(commands_pb2.Command.status, stream, self.ip)
                msg = await com_helpers.async_receive(stream, self.ip)
                if msg.command == commands_pb2.Command.status:
                    status = json.loads(msg.string_value)
                    status['client'] = {"version": self.client_version, "lib_version": __version__, "localtime":time.time()}
                    # FR: could add times to connect, hello and end to end in  here too.
                    print(json.dumps(status))
                    return

            if 'tx' == action:
                await com_helpers.async_send_string(commands_pb2.Command.gettx, str(param), stream, self.ip)
                msg = await com_helpers.async_receive(stream, self.ip)
                if msg.command == commands_pb2.Command.gettx:
                    if msg.tx_values:
                        txs = [json.loads(posblock.PosMessage().from_proto(tx).to_json()) for tx in msg.tx_values]
                        print(json.dumps(txs))
                        return
                    else:
                        print('false')
                    return

            if 'address_txs' == action:
                await com_helpers.async_send_string(commands_pb2.Command.getaddtxs, str(param), stream, self.ip)
                msg = await com_helpers.async_receive(stream, self.ip)
                # print(msg)
                if msg.command == commands_pb2.Command.getaddtxs:
                    # FR: deal with that conversion more efficiently in poschain
                    txs = [json.loads(posblock.PosMessage().from_proto(tx).to_json()) for tx in msg.tx_values]
                    print(json.dumps(txs))
                    return

            if 'mempool' == action:
                try:
                    # mempool with an "1" int value means send full mempool, unfiltered
                    await com_helpers.async_send_int32(commands_pb2.Command.mempool, 1, stream, self.ip)
                except Exception as e:
                    print(e)

            if 'update' == action:
                try:
                    print("Sending update ", param)
                    await com_helpers.async_send_string(commands_pb2.Command.update, param, stream, self.ip)
                except Exception as e:
                    print("update", e)

            if 'txtest' == action:
                tx = posblock.PosMessage().from_values(recipient='BHbbLpbTAVKrJ1XDLMM48Qa6xJuCGofCuH', value='1')
                try:
                    tx.sign()
                    # tx.value = 5  # uncomment to trigger invalid signature
                    print(tx.to_json())
                    await com_helpers.async_send_txs(commands_pb2.Command.tx, [tx], stream, self.ip)
                except Exception as e:
                    print(e)

            if 'block' == action:
                await com_helpers.async_send_int32(commands_pb2.Command.getblock, int(param), stream, self.ip)
                msg = await com_helpers.async_receive(stream, self.ip)
                if msg.command == commands_pb2.Command.getblock:
                    if msg.block_value:
                        block = posblock.PosBlock().from_proto(msg.block_value[0])
                        print(block.to_json())
                    else:
                        print('false')
                    return

            msg = await com_helpers.async_receive(stream, self.ip)
            print("Client got {}".format(msg.__str__().strip()))

        except ValueError as e:
            print("Client:", e)

        except Exception as e:
            print("Client:", e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
