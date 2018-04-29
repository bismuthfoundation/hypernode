"""
Pos Masternode class for Bismuth
Tornado based
"""

# import threading
import time
from enum import Enum
import os
import sys
import json
import struct
import asyncio
import aioprocessing
import logging
# pip install ConcurrentLogHandler
from cloghandler import ConcurrentRotatingFileHandler
# Tornado
from tornado.ioloop import IOLoop
from tornado.options import define, options
from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.tcpclient import TCPClient
from tornado.tcpserver import TCPServer

import tornado.log

# Our modules
import commands_pb2
# import comhandler
import common
import determine
import poschain
import posmempool
import posblock
import poscrypto

__version__ = '0.0.3'

"""
I use a global object to keep the state and route data between the servers and threads.
This looks not clean to me.
Will have to refactor if possible all in a single object, but looks hard enough, so postponing. 
"""
MY_NODE = None

app_log = None
access_log = None

# Logical timeout (s) for socket client
LTIMEOUT = 45

# Memo : tornado.process.task_id()


"""
Generic async stream com 
# TODO: move into a module of its own?
"""


async def async_receive(stream, ip):
    """
    Get a command, async version
    :param stream:
    :param ip:
    :return:
    """
    global MY_NODE
    protomsg = commands_pb2.Command()
    header = await stream.read_bytes(4)
    if len(header) < 4:
        raise RuntimeError("Socket EOF")
    data_len = struct.unpack('>i', header[:4])[0]
    data = await stream.read_bytes(data_len)
    MY_NODE.clients[ip][STATS_LASTACT] = time.time()
    MY_NODE.clients[ip][STATS_MSGRECV] += 1
    MY_NODE.clients[ip][STATS_BYTRECV] += 4 + data_len
    protomsg.ParseFromString(data)
    return protomsg


async def async_send(cmd, stream, ip):
    """
    Sends a protobuf command to the stream, async.
    :param cmd:
    :param stream:
    :param ip:
    :return:
    """
    global app_log
    global MY_NODE
    # TODO : stats and time, ping
    try:
        data = cmd.SerializeToString()
        data_len = len(data)
        await stream.write(struct.pack('>i', data_len) + data)
        # print(MY_NODE.clients)
        MY_NODE.clients[ip][STATS_LASTACT] = time.time()
        MY_NODE.clients[ip][STATS_MSGSENT] += 1
        MY_NODE.clients[ip][STATS_BYTSENT] += 4 + data_len
    except Exception as e:
        app_log.error("_send ip {}: {}".format(ip, e))
        """
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        """
        raise


async def async_send_string(cmd, value, stream, ip):
    """
    Sends a command with string param to the stream, async.
    :param cmd:
    :param value:
    :param stream:
    :param ip:
    :return:
    """
    global app_log
    protocmd = commands_pb2.Command()
    protocmd.Clear()
    protocmd.command = cmd
    protocmd.string_value = value
    await async_send(protocmd, stream, ip)


async def async_send_int32(cmd, value, stream, ip):
    """
    Sends a command with int32 param to the stream, async.
    :param cmd:
    :param value:
    :param stream:
    :param ip:
    :return:
    """
    global app_log
    protocmd = commands_pb2.Command()
    protocmd.Clear()
    protocmd.command = cmd
    protocmd.int32_value = value
    await async_send(protocmd, stream, ip)


async def async_send_void(cmd, stream, ip):
    """
    Sends a command to the stream, async.
    :param cmd:
    :param stream:
    :param ip:
    :return:
    """
    global app_log
    protocmd = commands_pb2.Command()
    protocmd.Clear()
    protocmd.command = cmd
    await async_send(protocmd, stream, ip)


async def async_send_txs(cmd, txs, stream, ip):
    """
    Sends a list of tx to the stream, async.
    :param cmd:
    :param txs: a list of tx
    :param stream:
    :param ip:
    :return:
    """
    global app_log
    protocmd = commands_pb2.Command()
    protocmd.Clear()
    protocmd.command = cmd
    for tx in txs:
        tx.add_to_proto(protocmd)
    await async_send(protocmd, stream, ip)


"""
TCP Server Classes
"""


class MnServer(TCPServer):
    """Tornado asynchronous TCP server."""

    async def handle_stream(self, stream, address):
        global MY_NODE
        global access_log
        global app_log
        peer_ip, fileno = address
        error_shown = False
        if MY_NODE.verbose:
            access_log.info("Incoming connection from {}".format(peer_ip))
        # TODO: here, use tiered system to reserve safe slots for jurors,
        # some slots for non juror mns, and some others for other clients (non mn clients)
        try:
            """
            # cmd : from us to peer
            self.protocmd = commands_pb2.Command()
            # msg : from peer to us
            self.protomsg = commands_pb2.Command()
            """
            msg = await async_receive(stream, peer_ip)
            if MY_NODE.verbose:
                access_log.info("Got msg >{}< from {}".format(msg.__str__().strip(), peer_ip))
            if msg.command == commands_pb2.Command.hello:
                access_log.info("Got Hello {} from {}".format(msg.string_value, peer_ip))
                if not await determine.connect_ok_from(msg.string_value, access_log):
                    await async_send(commands_pb2.Command.ko, stream, peer_ip)
                    return
                await async_send_string(commands_pb2.Command.hello, common.POSNET + MY_NODE.address, stream, peer_ip)
                MY_NODE.add_inbound(peer_ip, {'hello': msg.string_value})
            else:
                access_log.info("{} did not say hello".format(peer_ip))
                # TODO: Should we send back a proper ko message in that case?
                return
            # Here the peer said Hello and we accepted its version, we can have a date.
            while not Posmn.stop_event.is_set():
                try:
                    msg = await async_receive(stream, peer_ip)
                    await self._handle_msg(msg, stream, peer_ip)
                except StreamClosedError:
                    # This is a disconnect event, not an error
                    if MY_NODE.verbose:
                        access_log.info("Peer {} left.".format(peer_ip))
                    error_shown = True
                    return
                except Exception as e:
                    if not error_shown:
                        what = str(e)
                        if 'OK' not in what:
                            app_log.error("handle_stream {} for ip {}".format(what, peer_ip))
                    return
        except Exception as e:
            app_log.error("TCP Server init {}: Error {}".format(peer_ip, e))
            """
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            """
            return
        finally:
            MY_NODE.remove_inbound(peer_ip)

    async def _handle_msg(self, msg, stream, peer_ip):
        global access_log
        global MY_NODE
        if MY_NODE.verbose:
            access_log.info("Got msg >{}< from {}".format(msg.__str__().strip(), peer_ip))


"""
PoS MN Class
"""


class MNState(Enum):
    """
    Current State of the MN
    """
    START = 0
    SYNCING = 1
    TESTING = 2
    STRONG_CONSENSUS = 3
    MINIMAL_CONSENSUS = 4
    FORGING = 5
    SENDING = 6


# Index for clients stats
STATS_ACTIVEP = 0
STATS_COSINCE = 1
STATS_LASTACT = 2
STATS_MSGSENT = 3
STATS_MSGRECV = 4
STATS_BYTSENT = 5
STATS_BYTRECV = 6
STATS_LASTMPL = 7


class Posmn:
    """The PoS Masternode object"""
    # List of client routines
    # Each item (key=ip) is [active, last_active, sent_msg, sent_bytes, recv_msg, recv_bytes]
    clients = {}
    # list of inbound server connections
    inbound = {}

    stop_event = aioprocessing.AioEvent()

    def __init__(self, ip, port, address='', peers=None, verbose=False, wallet="poswallet.json"):
        self.ip = ip
        self.port = port
        self.address = address
        self.peers = peers
        self.verbose = verbose
        self.server_thread = None
        self.server = None
        self.state = MNState.START
        # list of peers I should stay connected to for a given round
        self.connect_to = []
        # Does the node try to connect to others?
        self.connecting = False
        self.init_log()
        # Time sensitive props
        self.poschain = poschain.SqlitePosChain(verbose=verbose)
        self.mempool = posmempool.SqliteMempool(verbose=verbose)
        self.is_delegate = False
        self.round = -1
        self.sir = -1
        self.previous_round = 0
        self.previous_sir = 0
        self.forger = None
        # Locks - Are they needed?
        self.round_lock = aioprocessing.Lock()
        self.clients_lock = aioprocessing.Lock()
        self.inbound_lock = aioprocessing.Lock()
        poscrypto.load_keys(wallet)

    def init_log(self):
        global app_log
        global access_log
        app_log = logging.getLogger("tornado.application")
        tornado.log.enable_pretty_logging()
        logfile = os.path.abspath("pos_app.log")
        # Rotate log after reaching 512K, keep 5 old copies.
        rotate_handler = ConcurrentRotatingFileHandler(logfile, "a", 512 * 1024, 5)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        rotate_handler.setFormatter(formatter)
        app_log.addHandler(rotate_handler)
        #
        access_log = logging.getLogger("tornado.access")
        tornado.log.enable_pretty_logging()
        logfile2 = os.path.abspath("pos_access.log")
        rotate_handler2 = ConcurrentRotatingFileHandler(logfile2, "a", 512 * 1024, 5)
        formatter2 = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        rotate_handler2.setFormatter(formatter2)
        access_log.addHandler(rotate_handler2)
        app_log.info("PoS MN {} Starting with pool address {}.".format(__version__, self.address))

    def add_inbound(self, ip, properties=None):
        """
        Safely add a distant peer from server coroutine.
        This is called only after initial exchange and approval
        :param ip:
        :param properties:
        :return:
        """
        with self.inbound_lock:
            self.inbound[ip] = properties

    def remove_inbound(self, ip):
        """
        Safely remove a distant peer from server coroutine
        :param ip:
        :return:
        """
        try:
            with self.inbound_lock:
                del self.inbound[ip]
        except:
            pass

    def update_inbound(self, ip, properties):
        """
        Safely update info for a connected peer
        :param ip:
        :param properties:
        :return:
        """
        with self.inbound_lock:
            self.inbound[ip] = properties

    def stop(self):
        """
        Signal to stop cleanly
        :return:
        """
        global app_log
        app_log.info("Trying to close nicely...")
        self.stop_event.set()
        # TODO: wait for potential threads to finish
        try:
            pass
            # A long sleep time will make nice close longer if we wait for the thread to finish
            # Since it's a daemon thread, we can leave it alone
            # self.whatever_thread.join()
        except Exception as e:
            app_log.error("Closing {}".format(e))

    @property
    def connected_count(self):
        """
        True if at least one client or server connection is active.
        Returns inbound + outbound count
        :return:
        """
        inbound_count = len(self.inbound)
        clients_count = 0
        # TODO: use another list to avoid counting one by one?
        for client in self.clients:
            if client[STATS_ACTIVEP]:
                clients_count += 1
        return inbound_count + clients_count

    async def manager(self):
        """
        Manager thread. Responsible for managing inner state of the node.
        :return:
        """
        global app_log
        if self.verbose:
            app_log.info("Started MN Manager")
        # Initialise round/sir data
        await self._check_round()
        while not self.stop_event.is_set():
            # Adjust state depending of the connection state
            if self.connected_count > 0:
                if self.state == MNState.START:
                    self.state = MNState.SYNCING
            elif self.state == MNState.SYNCING:
                self.state = MNState.START
            # TODO: We have 2 different status, this one , and status() function ????
            status = {'chain': self.poschain.status(),
                      'mempool': self.mempool.status(),
                      'outbound': list(self.clients.keys()),
                      'inbound': list(self.inbound.keys()),
                      'state': {'state': self.state.name,
                                'round': self.round,
                                'sir': self.sir,
                                'forger': self.forger}}
            app_log.info("Status: {}".format(json.dumps(status)))
            if self.connecting:
                if len(self.clients) < len(self.connect_to):
                    # Try to connect to our missing pre-selected peers
                    for peer in self.connect_to:
                        # [('aa012345678901aa', '127.0.0.1', 6969, 1)]
                        # tuples (address, ip, port, ?)
                        # ip_port = "{}:{}".format(peer[1], peer[2])
                        if peer[1] not in self.clients:
                            io_loop = IOLoop.instance()
                            with self.clients_lock:
                                # first index is active or not
                                self.clients[peer[1]] = [False, 0, 0, 0, 0, 0, 0]
                            io_loop.spawn_callback(self.client_worker, peer)
            # TODO: variable sleep time depending on the elapsed loop time - or use timeout?
            await asyncio.sleep(10)
            await self._check_round()

    async def client_worker(self, peer):
        """
        Client worker, running in a coroutine.
        Tries to connect to the given peer, terminates on error and deletes itself on close.
        :param peer: ('aa012345678901aa', '127.0.0.1', 6969, 1)
        :return:
        """
        global app_log
        global LTIMEOUT
        ip = peer[1]
        try:
            if self.verbose:
                access_log.info("Initiating client co-routine for {}:{}".format(peer[1], peer[2]))
            tcp_client = TCPClient()
            # ip_port = "{}:{}".format(peer[1], peer[2])
            stream = await tcp_client.connect(peer[1], peer[2], timeout=LTIMEOUT)
            connect_time = time.time()
            await async_send_string(commands_pb2.Command.hello, common.POSNET+self.address, stream, ip)
            msg = await async_receive(stream, peer[1])
            if self.verbose:
                access_log.info("Worker got {}".format(msg.__str__().strip()))
            if msg.command == commands_pb2.Command.hello:
                # decompose posnet/address and check.
                access_log.info("Worker got Hello {} from {}".format(msg.string_value, ip))
                if not await determine.connect_ok_from(msg.string_value, access_log):
                    await async_send(commands_pb2.Command.ko, stream, ip)
                    return
            if msg.command == commands_pb2.Command.ko:
                access_log.info("Worker got Ko {}".format(msg.string_value))
                return
            # now we can enter a long term relationship with this node.
            with self.clients_lock:
                # Set connected status
                self.clients[ip][STATS_ACTIVEP] = True
                self.clients[ip][STATS_COSINCE] = connect_time
            while not self.stop_event.is_set():
                await asyncio.sleep(common.WAIT)
                now = time.time()
                # Only send ping if time is due.
                # TODO: more than 30 sec? Config
                if self.clients[ip][STATS_LASTACT] < now - 30:
                    if self.verbose:
                        app_log.info("Sending ping to {}".format(ip))
                    # keeps connection active, or raise error if connection lost
                    await async_send_void(commands_pb2.Command.ping, stream, ip)
            if self.clients[ip][STATS_LASTACT] < now - 10:
                # TODO: get mempool (or empty)
                if self.verbose:
                    app_log.info("Sending mempool to {}".format(ip))
                mempool = self.mempool.since(self.clients[ip][STATS_LASTACT])
                await async_send_txs(commands_pb2.Command.txs, mempool, stream, ip)
            raise ValueError("Closing")
        except Exception as e:
            if self.verbose:
                app_log.warning("Connection lost to {} because {}. Retry in 30 sec.".format(peer[1], e))
            """
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            """
            #  Wait here so we don't retry immediately
            await asyncio.sleep(30)
        finally:
            try:
                with self.clients_lock:
                    # We could keep it and set to inactive, but is it useful? could grow too much
                    del self.clients[ip]
            except:
                pass

    async def _check_round(self):
        """
        Adjust round/slots depending properties.
        Always called from the manager co-routine only.
        Should not be called too often (1-10sec should be plenty)
        :return:
        """
        global app_log
        self.round, self.sir = determine.timestamp_to_round_slot(time.time())
        if (self.sir != self.previous_sir) or (self.round != self.previous_round):
            with self.round_lock:
                # Update all sir related info
                if self.verbose:
                    app_log.warning("New Slot {} in Round {}".format(self.sir, self.round))
                self.previous_sir = self.sir
                if self.round != self.previous_round:
                    # Update all round related info, we get here only once at the beginning of a new round
                    if self.verbose:
                        app_log.warning("New Round {}".format(self.round))
                    self.previous_round = self.round
                    # TODO : if we have connections, drop them.
                    # wait for new list, so we keep cnx if we already are. or drop anyway?
                    # no, would add general network load at each round start.
                    # use async here for every lenghty op - won't that lead to partial sync info?
                    self.connect_to = await determine.get_connect_to(self.peers, self.round, self.address)
                    tickets = await determine.mn_list_to_tickets(self.peers)
                    # TODO: real hash
                    self.slots = await determine.tickets_to_delegates(tickets, common.POC_LAST_BROADHASH)
                    if self.verbose:
                        app_log.info("Slots {}".format(json.dumps(self.slots)))
                    self.test_slots = await determine.mn_list_to_test_slots(self.peers, self.slots)
                    # TODO: disconnect from non partners peers
                    # TODO: save this round info to db
                if self.sir < len(self.slots):
                    self.forger = self.slots[self.sir][0]
                    if self.verbose:
                        app_log.info("Forger is {}".format(self.forger))
                else:
                    self.forger = None

    def serve(self):
        """
        Run the socker server.
        Once we called that, the calling thread is stopped until the server closes.
        :return:
        """
        global app_log
        if self.verbose:
            app_log.info("Status: "+json.dumps(self.status()))
        try:
            server = MnServer()
            # server.listen(port)
            server.bind(self.port, backlog=128, reuse_port=True)
            server.start(1)  # Forks multiple sub-processes
            if self.verbose:
                app_log.info("Starting server on tcp://localhost:" + str(self.port))
            io_loop = IOLoop.instance()
            io_loop.spawn_callback(self.manager)
            self.connect()
            try:
                io_loop.start()
            except KeyboardInterrupt:
                self.stop_event.set()
                io_loop.stop()
                app_log.info("Serve: exited cleanly")
        except Exception as e:
            app_log.error("Serve: {}".format(str(e)))

    def connect(self, connect=True):
        """
        Initiate outgoing connections
        :return:
        """
        self.connecting = connect
        # Will be handled by the manager.

    def status(self):
        """
        :return: MN Status info
        """
        return {'config': {'ip': self.ip, 'port': self.port, 'verbose': self.verbose},
                'peers': self.peers,
                'round': {'ts': time.time(), 'round': self.round, 'sir': self.sir}}
