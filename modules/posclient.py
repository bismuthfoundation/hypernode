"""
Demo Pos client class for Bismuth
Tornado based
"""

from tornado.tcpclient import TCPClient
# import asyncio

import common
import com_helpers
import poscrypto
import posblock
import commands_pb2

__version__ = '0.0.1'


class Posclient:

    def __init__(self, ip, port, verbose=False, wallet="poswallet.json"):
        self.ip = ip
        self.port = port
        self.verbose = verbose
        poscrypto.load_keys(wallet)

    async def action(self, action='hello'):
        """
        test action
        :param action:
        :return:
        """
        if action not in ('hello', 'ping', 'status', 'tx', 'mempool'):
            raise ValueError("Unknown action: {}".format(action))
        tcp_client = TCPClient()
        stream = await tcp_client.connect(self.ip, self.port)
        await com_helpers.async_send_string(commands_pb2.Command.hello, common.POSNET + poscrypto.ADDRESS,
                                            stream, self.ip)
        msg = await com_helpers.async_receive(stream, self.ip)
        if self.verbose:
            print("Client got {}".format(msg.__str__().strip()))
        if msg.command == commands_pb2.Command.hello:
            # decompose posnet/address and check.
            print("Client got Hello {} from {}".format(msg.string_value, self.ip))
        if msg.command == commands_pb2.Command.ko:
            print("Client got Ko {}".format(msg.string_value))
            return
        if 'ping' == action:
            return
        if 'hello' == action:
            return
        if 'tx' == action:
            tx = posblock.PosMessage().from_values(recipient='BHbbLpbTAVKrJ1XDLMM48Qa6xJuCGofCuH', value='1')
            try:
                tx.sign()
                # tx.value = 5  # uncomment to trigger invalid signature
                print(tx.to_json())
                await com_helpers.async_send_txs(commands_pb2.Command.tx, [tx], stream, self.ip)
            except Exception as e:
                print(e)
        if 'mempool' == action:
            try:
                # mempool with an "1" int value means send full mempool, unfiltered
                await com_helpers.async_send_int32(commands_pb2.Command.mempool, 1, stream, self.ip)
            except Exception as e:
                print(e)

        msg = await com_helpers.async_receive(stream, self.ip)
        print("Client got {}".format(msg.__str__().strip()))
