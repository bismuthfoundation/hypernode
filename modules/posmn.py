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
from distutils.version import LooseVersion
import requests
# import struct
import asyncio
import aioprocessing
import logging
# pip install ConcurrentLogHandler
from cloghandler import ConcurrentRotatingFileHandler
# Tornado
from tornado.ioloop import IOLoop
# from tornado.options import define, options
# from tornado import gen
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
import com_helpers
from com_helpers import async_receive, async_send_string, async_send_int32
from com_helpers import async_send_void, async_send_txs

__version__ = '0.0.4'

"""
I use a global object to keep the state and route data between the servers and threads.
This looks not clean to me.
Will have to refactor if possible all in a single object, but looks hard enough, so postponing. 
"""

app_log = None
access_log = None

# Logical timeout (s) for socket client
LTIMEOUT = 45

# Memo : tornado.process.task_id()


"""
TCP Server Classes
"""


class MnServer(TCPServer):
    """Tornado asynchronous TCP server."""

    def __init__(self):
        self.verbose = False
        self.node = None
        self.mempool = None
        super().__init__()

    async def handle_stream(self, stream, address):
        """
        Handles the lifespan of a client, from connection to end of stream
        :param stream:
        :param address:
        :return:
        """
        global access_log
        global app_log
        peer_ip, fileno = address
        error_shown = False
        access_log.info("Incoming connection from {}".format(peer_ip))
        # TODO: here, use tiered system to reserve safe slots for jurors,
        # some slots for non juror mns, and some others for other clients (non mn clients)
        try:
            # Get first message, we expect an hello with version number and address
            msg = await async_receive(stream, peer_ip)
            if self.verbose:
                access_log.info("Got msg >{}< from {}".format(msg.__str__().strip(), peer_ip))
            if msg.command == commands_pb2.Command.hello:
                access_log.info("Got Hello {} from {}".format(msg.string_value, peer_ip))
                reason, ok = await determine.connect_ok_from(msg.string_value, access_log)
                if not ok:
                    # TODO: send reason of deny?
                    # Should we send back a proper ko message in that case? - remove later if used as a DoS attack
                    await async_send_string(commands_pb2.Command.ko, reason, stream, peer_ip)
                    return
                # Right version, we send our hello as well.
                await async_send_string(commands_pb2.Command.hello, common.POSNET
                                        + com_helpers.MY_NODE.address, stream, peer_ip)
                # Add the peer to inbound list
                self.node.add_inbound(peer_ip, {'hello': msg.string_value})
            else:
                access_log.info("{} did not say hello".format(peer_ip))
                # Should we send back a proper ko message in that case? - remove later if used as a DoS attack
                await async_send_string(commands_pb2.Command.ko, "Did not say hello", stream, peer_ip)
                return
            # Here the peer said Hello and we accepted its version, we can have a date.
            while not Posmn.stop_event.is_set():
                try:
                    # Loop over the requests until disconnect or end of server.
                    msg = await async_receive(stream, peer_ip)
                    await self._handle_msg(msg, stream, peer_ip)
                except StreamClosedError:
                    # This is a disconnect event, not an error
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
            self.node.remove_inbound(peer_ip)

    async def _handle_msg(self, msg, stream, peer_ip):
        """
        Handles a single command received by the server.
        :param msg:
        :param stream:
        :param peer_ip:
        :return:
        """
        global access_log
        if self.verbose:
            access_log.info("Got msg >{}< from {}".format(msg.__str__().strip(), peer_ip))
        # Don't do a thing.
        # if msg.command == commands_pb2.Command.ping:
        #    await com_helpers.async_send(commands_pb2.Command.ok, stream, peer_ip)
        # TODO: rights management
        if msg.command == commands_pb2.Command.tx:
            # We got one or more tx from a peer. This is NOT as part of the mempool sync, but as a way to inject
            # external txs from a "controller / wallet or such
            for tx in msg.tx_values:
                try:
                    # Will raise if error
                    await self.mempool.digest_tx(tx)
                    app_log.info("Digested tx from {}".format(peer_ip))
                    await async_send_void(commands_pb2.Command.ok, stream, peer_ip)
                except Exception as e:
                    app_log.warning("Error {} digesting tx from {}".format(e, peer_ip))
                    await async_send_void(commands_pb2.Command.ko, stream, peer_ip)
        elif msg.command == commands_pb2.Command.mempool:
            # TODO: digest the received txs
            # TODO: use clients stats to get real since
            txs = await self.mempool.async_since(0)
            # This is a list of PosMessage objects
            await async_send_txs(commands_pb2.Command.mempool, txs, stream, peer_ip)
        elif msg.command == commands_pb2.Command.update:
            # TODO: rights/auth and config management
            await self.update(msg.string_value, stream, peer_ip)

    async def update(self, url, stream, peer_ip):
            app_log.info('Checking version from {}'.format(url))
            version_url = url + 'version.txt'
            try:
                version = requests.get(version_url).text.strip()
                # compare to our version
                if LooseVersion(__version__) < LooseVersion(version):
                    app_log.info("Newer {} version, updating.".format(version))
                    # fetch archive and extract
                    common.update_source(url + "mnd.tgz", app_log)
                    # Todo: bootstrap db on condition or other message ?
                    await async_send_void(commands_pb2.Command.ok, stream, peer_ip)
                    # restart
                    args = sys.argv[:]
                    app_log.warning('Re-spawning {}'.format(' '.join(args)))
                    args.insert(0, sys.executable)
                    if sys.platform == 'win32':
                        args = ['"%s"' % arg for arg in args]
                    os.execv(sys.executable, args)
                    self.node.stop()
                else:
                    msg = "Keeping our {} version vs distant {}".format(__version__, version)
                    app_log.info(msg)
                    await async_send_string(commands_pb2.Command.ko, msg, stream, peer_ip)
            except Exception as e:
                app_log.warning("Error {} updating from {}".format(e, url))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)


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


class Posmn:
    """The PoS Masternode object"""
    # List of client routines
    # Each item (key=ip) is [active, last_active, sent_msg, sent_bytes, recv_msg, recv_bytes]
    clients = {}
    # list of inbound server connections
    inbound = {}

    stop_event = aioprocessing.AioEvent()

    def __init__(self, ip, port, address='', peers=None, verbose=False, wallet="poswallet.json"):
        global app_log
        global access_log
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
        poscrypto.load_keys(wallet)
        # Time sensitive props
        self.poschain = poschain.SqlitePosChain(verbose=verbose, app_log=app_log)
        self.mempool = posmempool.SqliteMempool(verbose=verbose, app_log=app_log)
        self.is_delegate = False
        self.round = -1
        self.sir = -1
        self.previous_round = 0
        self.previous_sir = 0
        self.forger = None
        self.forged = False
        #
        self.last_height = 0
        self.previous_hash = ''
        self.last_round = 0
        self.last_sir = 0
        # Locks - Are they needed?
        self.round_lock = aioprocessing.Lock()
        self.clients_lock = aioprocessing.Lock()
        self.inbound_lock = aioprocessing.Lock()

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
            if client[com_helpers.STATS_ACTIVEP]:
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
        await self.refresh_last_block()
        await self._check_round()
        while not self.stop_event.is_set():
            # Adjust state depending of the connection state
            if self.connected_count > 0:
                if self.state == MNState.START:
                    await self.change_state_to(MNState.SYNCING)
            elif self.state == MNState.SYNCING:
                await self.change_state_to(MNState.START)
            if self.state == MNState.SYNCING and self.forger == poscrypto.ADDRESS and not self.forged:
                await self.change_state_to(MNState.STRONG_CONSENSUS)

            if self.state == MNState.STRONG_CONSENSUS:
                if await self.consensus() > 50 :
                    await self.change_state_to(MNState.FORGING)
                    # Forge will send also
                    await self.forge()
                    # await asyncio.sleep(10)
                    self.forged = True
                    await self.change_state_to(MNState.SYNCING)

            # TODO: don't display each time
            await self.status(log=True)
            if self.connecting:
                # TODO: if we are looking for consensus, then we will connect to
                # every juror, not just our round peers, then disconnect once block submitted
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
                                self.clients[peer[1]] = [False, 0, 0, 0, 0, 0, 0, 0]
                            io_loop.spawn_callback(self.client_worker, peer)
            # TODO: variable sleep time depending on the elapsed loop time - or use timeout?
            await asyncio.sleep(10)
            await self._check_round()

    async def change_state_to(self, new_state):
        """
        Sets new status and logs change.
        :param new_state:
        :return:
        """
        self.state = new_state
        if self.verbose:
            await self.status(log=True)

    async def consensus(self):
        """
        Returns the % of jurors we agree with
        :return:
        """
        # TODO
        # in self.clients we should have the latest blocks of every peer we are connected to
        return 80

    async def refresh_last_block(self):
        """
        Fetch fresh info from the PoS chain
        :return:
        """
        last_block = await self.poschain.last_block()
        self.last_height, self.previous_hash = last_block['height'], last_block['block_hash']
        self.last_round, self.last_sir = last_block['round'], last_block['sir']

    async def forge(self):
        """
        Consensus has been reached, we are forger, forge and send block
        :return:
        """
        global app_log
        try:
            await self.refresh_last_block()
            # check last round and SIR, make sure they are >
            if self.round <= self.last_round and self.sir <= self.last_sir:
                raise ValueError("We already have this round/SIR in our chain.")
            if not self.forger == poscrypto.ADDRESS:
                # Should never pass here.
                raise ValueError("We are not the forger for current round!!!")
            block_dict = {"height": self.last_height + 1, "round": self.round, "sir": self.sir,
                          "timestamp": int(time.time()), "previous_hash": self.previous_hash,
                          "forger": self.address, 'received_by': ''}
            if self.verbose:
                app_log.info("Forging block {} Round {} SIR {}".format(self.last_height + 1, self.round, self.sir))
            block = posblock.PosBlock().from_dict(block_dict)
            # txs are native objects
            block.txs = await self.mempool.async_all()
            if not len(block.txs):
                # not enough TX, won't pass in prod
                # raise ValueError("No TX to embed, block won't be valid.")
                app_log.error("No TX to embed, block won't be valid.")
            # Remove from mempool
            await self.mempool.clear()
            block.sign()
            # TODO: Shall we pass that one through "digest" to make sure?
            await self.poschain.insert_block(block)
            await self.change_state_to(MNState.SENDING)
            # TODO: Send the block to our peers (unless we were unable to insert it in our db
            block = block.to_proto()
            app_log.error("Block Forged, I should send it")
            # print(block.__str__())
            return True
        except Exception as e:
            app_log.error("Error forging: {}".format(e))
            return False

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
            await com_helpers.async_send_string(commands_pb2.Command.hello, common.POSNET+self.address, stream, ip)
            msg = await com_helpers.async_receive(stream, peer[1])
            if self.verbose:
                access_log.info("Worker got {}".format(msg.__str__().strip()))
            if msg.command == commands_pb2.Command.hello:
                # decompose posnet/address and check.
                access_log.info("Worker got Hello {} from {}".format(msg.string_value, ip))
            if msg.command == commands_pb2.Command.ko:
                access_log.info("Worker got Ko {}".format(msg.string_value))
                return
            # now we can enter a long term relationship with this node.
            with self.clients_lock:
                # Set connected status
                self.clients[ip][com_helpers.STATS_ACTIVEP] = True
                self.clients[ip][com_helpers.STATS_COSINCE] = connect_time
            while not self.stop_event.is_set():
                await asyncio.sleep(common.WAIT)
                now = time.time()
                # Only send ping if time is due.
                # TODO: more than 30 sec? Config
                if self.clients[ip][com_helpers.STATS_LASTACT] < now - 30:
                    if self.verbose:
                        app_log.info("Sending ping to {}".format(ip))
                    # keeps connection active, or raise error if connection lost
                    await com_helpers.async_send_void(commands_pb2.Command.ping, stream, ip)
                if self.state not in (MNState.STRONG_CONSENSUS, MNState.MINIMAL_CONSENSUS):
                    # If we are trying to reach consensus, don't ask for mempool sync. Peers may send anyway.
                    if self.clients[ip][com_helpers.STATS_LASTMPL] < now - 10:
                        # Send our new tx from mempool if any, will get the new from peer.
                        if self.verbose:
                            app_log.info("Sending mempool to {}".format(ip))
                        txs = await self.mempool.async_since(self.clients[ip][com_helpers.STATS_LASTMPL])
                        self.clients[ip][com_helpers.STATS_LASTMPL] = time.time()
                        await com_helpers.async_send_txs(commands_pb2.Command.mempool, txs, stream, ip)
            raise ValueError("Closing")
        except Exception as e:
            if self.verbose:
                app_log.warning("Connection lost to {} because {}. Retry in 20 sec.".format(peer[1], e))
            """
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            """
            #  Wait here so we don't retry immediately
            await asyncio.sleep(20)
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
                # If we forged the last block, forget.
                self.forged = False
                # Update all sir related info
                if self.verbose:
                    app_log.warning("New Slot {} in Round {}".format(self.sir, self.round))
                self.previous_sir = self.sir
                if self.round != self.previous_round:
                    # Update all round related info, we get here only once at the beginning of a new round
                    await self.refresh_last_block()
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
                    self.slots = await determine.tickets_to_delegates(tickets, self.previous_hash)
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
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.status(log=True))
        try:
            server = MnServer()
            server.verbose = self.verbose
            server.mempool = self.mempool
            server.node = self
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
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.mempool.async_close())
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

    async def status(self, log=True):
        """
        :return: MN Status info
        """
        global app_log
        mempool_status = await self.mempool.status()
        status = {'config': {'address': self.address, 'ip': self.ip, 'port': self.port, 'verbose': self.verbose},
                  'chain': self.poschain.status(),
                  'mempool': mempool_status,
                  'outbound': list(self.clients.keys()),
                  'inbound': list(self.inbound.keys()),
                  'state': {'state': self.state.name,
                            'round': self.round,
                            'sir': self.sir,
                            'forger': self.forger}}
        # 'peers': self.peers
        if log:
            app_log.info("Status: {}".format(json.dumps(status)))
        return status

