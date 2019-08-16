"""
Simple Async TCP Client for Bismuth Wallet

Eggdrasyl
Bismuth Foundation

July 2018 - July 2019

Adapted from bismuthClient, to be merged into bismuthclient in the end

"""

import json
from asyncio import sleep as async_sleep
from asyncio import wait_for, run_coroutine_threadsafe, get_event_loop
from logging import getLogger

from tornado.tcpclient import TCPClient

__version__ = '0.0.3'


class PoWAsyncClient:

    def __init__(self, server, port, app_log=None, loop=None, address='', verbose=False):
        # print("async init", server_list)
        self.server = server
        self.port = port
        self.app_log = app_log if app_log else getLogger()
        if loop is None:
            loop = get_event_loop()
        self.loop = loop
        self.address = address
        self.connected = False
        self.stream = None
        self.client = None
        self.verbose = verbose
        self._status = {"connected": False, "address": self.address}
        self.ip_port = 'N/A'

    async def connect(self, timeout=10):
        self.connected = False
        self.stream = None
        self.client = TCPClient()
        self.stream = await self.client.connect(self.server, self.port, timeout=timeout, )
        if self.stream:
            self.connected = True
            if self.verbose:
                self.app_log.info("connected to {}:{}".format(self.server, self.port))
        else:
            raise RuntimeError("Unable to connect to {}:{}".format(self.server, self.port))

    def close(self):
        self.client.close()
        """
        if self.stream:
            try:
                self.stream.close()
            except:
                pass
        """
        self.client = None
        self.stream = None
        self.connected = False

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            self.close()
        except Exception as e:
            self.app_log.warning("PoWAsyncClient exception {}".format(e))

    def status(self, address):
        self.address = address
        return self._status

    async def _receive(self):
        """
        Get a command, async version
        :param stream:
        :param ip:
        :return:
        """
        if self.stream:
            header = await self.stream.read_bytes(10)
            data_len = int(header)
            data = await self.stream.read_bytes(data_len)
            data = json.loads(data.decode("utf-8"))
            return data
        else:
            self.app_log.warning('receive: not connected')

    def receive(self, timeout=None):
        future = run_coroutine_threadsafe(self._receive(), self.loop)
        return future.result(timeout)

    def send(self, data, timeout=None):
        future = run_coroutine_threadsafe(self._send(data), self.loop)
        return future.result(timeout)

    def command(self, data,  param=None, timeout=None):
        """Sync interface to command."""
        if not self.connected:
            # print("connecting")
            self.loop.run_until_complete(self.connect(timeout=timeout))
        # print("command")
        res = self.loop.run_until_complete(self._command(data, param))
        # future = run_coroutine_threadsafe(self._command(data, param), self.loop)
        # return future.result(timeout)
        return res

    async def async_command(self, data: str,  param=None, timeout=None, retry: int=3, retry_pause: int=2):
        if retry <= 0:
            retry = 1
        while retry > 0:
            retry -= 1
            try:
                if not self.connected:
                    await self.connect(timeout=timeout)
                result = await wait_for(self._command(data, param), timeout=timeout)
                return result
            except Exception as e:
                self.app_log.warning("async_command: {} connected {}".format(e, self.connected))
                self.close()
                await async_sleep(retry_pause)
        raise RuntimeError("Unable to process command")


    async def _send(self, data):
        """
        sends an object to the stream, async.
        :param data:
        :param stream:
        :param ip:
        :return:
        """
        if self.stream:
            try:
                data = str(json.dumps(data))
                header = str(len(data)).encode("utf-8").zfill(10)
                full = header + data.encode('utf-8')
                await self.stream.write(full)
            except Exception as e:
                self.app_log.error("send_to_stream {} for ip {}".format(str(e), self.ip_port))
                self.stream = None
                self.connected = False
                raise
        else:
            self.app_log.warning('send: not connected')

    async def _command(self, data, param=None):
        if self.stream:
            await self._send(data)
            if param:
                await self._send(param)
            return await self._receive()
        else:
            self.app_log.warning('command: not connected')
            return None

    def convert_ip_port(self, ip, some_port):
        """
        Get ip and port, but extract port from ip if ip was as ip:port
        :param ip:
        :param some_port: default port
        :return: (ip, port)
        """
        if ':' in ip:
            ip, some_port = ip.split(':')
        return ip, some_port


if __name__ == "__main__":
    print("I'm a module, can't run")
