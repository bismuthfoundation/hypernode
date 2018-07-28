"""
Pos Hypernode class for Bismuth Cryptocurrency
Tornado based

Note:
    TODO: are prioritary actions TBD
    FR: are features request. Think of them as second class
    TODO items that are less urgent
    FR: will go into TODO: as TODO: is cleared.
"""

import time
import random
from enum import Enum
import os
import sys
import json
from distutils.version import LooseVersion
import requests
import asyncio
import aioprocessing
import logging
# pip install ConcurrentLogHandler
from cloghandler import ConcurrentRotatingFileHandler
from operator import itemgetter
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
import common
import determine
import poschain
import posmempool
import posblock
import poscrypto
import com_helpers
from com_helpers import async_receive, async_send_string, async_send_block
from com_helpers import async_send_void, async_send_txs, async_send_height

__version__ = '0.0.75'

"""
# FR: I use a global object to keep the state and route data between the servers and threads.
This looks not clean to me.
Will have to refactor if possible all in a single object, but looks hard enough, therefore postponing. 
"""

app_log = None
access_log = None

# The following is here rather than in common, because I don't consider that a param, but a constant for every node.
# FR: More extensive sort (constants vs params) TBD later when we have more perspective.

# Logical timeout (s) for socket client
LTIMEOUT = 45

# Minimum required connectivity before we are able to operate
# FR: Could depend on the jurors count.
MINIMUM_CONNECTIVITY = 2


"""
TCP Server Classe
"""


class HnServer(TCPServer):
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
        peer_port = '00000'
        access_log.info("SRV: Incoming connection from {}".format(peer_ip))
        # TODO: here, use tiered system to reserve safe slots for jurors,
        # some slots for non juror hns, and some others for other clients (non hn clients)
        try:
            # Get first message, we expect an hello with version number and address
            msg = await async_receive(stream, peer_ip)
            if self.verbose:
                access_log.info("SRV: Got msg >{}< from {}".format(com_helpers.cmd_to_text(msg.command), peer_ip))
            if msg.command == commands_pb2.Command.hello:
                reason, ok = await determine.connect_ok_from(msg.string_value, access_log)
                peer_port = msg.string_value[10:15]
                full_peer = common.ipport_to_fullpeer(peer_ip, peer_port)
                access_log.info("SRV: Got Hello {} from {}".format(msg.string_value, full_peer))
                if not ok:
                    # FR: send reason of deny?
                    # Should we send back a proper ko message in that case? - remove later if used as a DoS attack
                    await async_send_string(commands_pb2.Command.ko, reason, stream, peer_ip)
                    return
                # Right version, we send our hello as well.
                await async_send_string(commands_pb2.Command.hello, self.node.hello_string(), stream, peer_ip)
                # Add the peer to inbound list
                self.node.add_inbound(peer_ip, peer_port, {'hello': msg.string_value})

            elif msg.command == commands_pb2.Command.block:
                # block sending does not require hello
                access_log.info("SRV: Got forged block from {}".format(peer_ip))
                # TODO: check that this ip is in the current forging round, or add to anomalies buffer
                for block in msg.block_value:
                    await self.node.poschain.digest_block(block, from_miner=True)
                return
            else:
                access_log.info("SRV: {} did not say hello".format(peer_ip))
                # Should we send back a proper ko message in that case? - remove later if used as a DoS attack
                await async_send_string(commands_pb2.Command.ko, "Did not say hello", stream, peer_ip)
                return
            # Here the peer said Hello and we accepted its version, we can have a date.
            while not Poshn.stop_event.is_set():
                try:
                    # Loop over the requests until disconnect or end of server.
                    msg = await async_receive(stream, full_peer)
                    await self._handle_msg(msg, stream, peer_ip, peer_port)
                except StreamClosedError:
                    # This is a disconnect event, not an error
                    access_log.info("SRV: Peer {} left.".format(full_peer))
                    return
                except Exception as e:
                    what = str(e)
                    # FR: Would be cleaner with a custom exception
                    if 'OK' not in what:
                        app_log.error("SRV: handle_stream {} for ip {}".format(what, full_peer))
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
                    return

        except Exception as e:
            app_log.error("SRV: TCP Server init {}: Error {}".format(peer_ip, e))
            # FR: the following code logs extra info for debug.
            # factorize in a single function with common.EXTRA_LOG switch to activate.
            # Maybe also log in a distinct file since these are supposed to be unexpected exceptions
            # Used also in other files.
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
            return

        finally:
            self.node.remove_inbound(peer_ip, peer_port)

    async def _handle_msg(self, msg, stream, peer_ip, peer_port):
        """
        Handles a single command received by the server.

        :param msg:
        :param stream:
        :param peer_ip:
        :return:
        """
        global access_log
        if self.verbose:
            access_log.info("SRV: Got msg >{}< from {}:{}"
                            .format(com_helpers.cmd_to_text(msg.command), peer_ip, peer_port))
        full_peer = common.ipport_to_fullpeer(peer_ip, peer_port)
        try:
            # Don't do a thing.
            # if msg.command == commands_pb2.Command.ping:
            #    await com_helpers.async_send(commands_pb2.Command.ok, stream, peer_ip)
            # TODO: rights management
            if msg.command == commands_pb2.Command.status:
                status = json.dumps(self.node.my_status)
                await async_send_string(commands_pb2.Command.status, status, stream, full_peer)

            elif msg.command == commands_pb2.Command.tx:
                # We got one or more tx from a peer. This is NOT as part of the mempool sync, but as a way to inject
                # external txs from a "controller / wallet or such
                try:
                    await self.node.digest_txs(msg.tx_values, full_peer)
                    await async_send_void(commands_pb2.Command.ok, stream, full_peer)
                except Exception as e:
                    app_log.warning("SRV: Error {} digesting tx from {}:{}".format(e, peer_ip, peer_port))
                    await async_send_void(commands_pb2.Command.ko, stream, full_peer)

            elif msg.command == commands_pb2.Command.mempool:
                # peer mempool extract
                try:
                    await self.node.digest_txs(msg.tx_values, full_peer)
                except Exception as e:
                    app_log.warning("SRV: Error {} digesting tx from {}:{}".format(e, peer_ip, peer_port))
                # TODO: use clients stats to get real since
                txs = await self.mempool.async_since(0)
                # TODO: filter out the tx we got from the peer also.
                if self.verbose:
                    app_log.info("SRV Sending back txs {}".format([tx.to_json() for tx in txs]))
                # This is a list of PosMessage objects
                await async_send_txs(commands_pb2.Command.mempool, txs, stream, full_peer)

            elif msg.command == commands_pb2.Command.height:
                await self.node.digest_height(msg.height_value, full_peer, server=True)
                height = await self.node.poschain.async_height()
                await async_send_height(commands_pb2.Command.height, height, stream, full_peer)

            elif msg.command == commands_pb2.Command.blockinfo:
                height = await self.node.poschain.async_blockinfo(msg.int32_value)
                await async_send_height(commands_pb2.Command.blockinfo, height, stream, full_peer)

            elif msg.command == commands_pb2.Command.blocksync:
                blocks = await self.node.poschain.async_blocksync(msg.int32_value)
                await async_send_block(blocks, stream, full_peer)

            elif msg.command == commands_pb2.Command.roundblocks:
                blocks = await self.node.poschain.async_roundblocks(msg.int32_value)
                await async_send_block(blocks, stream, full_peer)

            elif msg.command == commands_pb2.Command.getblock:
                block = await self.node.poschain.async_getblock(msg.int32_value)
                await async_send_block(block, stream, full_peer)

            elif msg.command == commands_pb2.Command.getaddtxs:
                txs = await self.node.poschain.async_getaddtxs(msg.string_value)
                await async_send_block(txs, stream, full_peer)

            elif msg.command == commands_pb2.Command.update:
                # TODO: rights/auth and config management
                await self.update(msg.string_value, stream, full_peer)

            else:
                # if self.verbose:
                #    app_log.warning("SRV unknown message {}, closing.".format(com_helpers.cmd_to_text(msg.command)))
                raise ValueError("Unknown message {}".format(com_helpers.cmd_to_text(msg.command)))

        except ValueError as e:
            app_log.warning("SRV: Error {} for peer {}.".format(e, full_peer))
            # FR: can we just ignore, or should we raise to close the connection?

        except Exception as e:
            app_log.error("SRV: _handle_msg {}: Error {}".format(full_peer, e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
            raise

    async def update(self, url, stream, peer_ip):
            app_log.info('Checking version from {}'.format(url))
            version_url = url + 'version.txt'
            try:
                version = requests.get(version_url).text.strip()
                # compare to our version
                if LooseVersion(__version__) < LooseVersion(version):
                    app_log.info("Newer {} version, updating.".format(version))
                    # fetch archive and extract
                    common.update_source(url + "hnd.tgz", app_log)
                    # FR: bootstrap db on condition or other message ?
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
                app_log.error("Error {} updating from {}".format(e, url))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))


"""
PoS HN Class
"""


class HNState(Enum):
    """
    Current State of the HN
    """
    START = 0
    SYNCING = 1
    TESTING = 2
    STRONG_CONSENSUS = 3
    MINIMAL_CONSENSUS = 4
    FORGING = 5
    SENDING = 6
    CATCHING_UP_CONNECT1 = 7
    CATCHING_UP_CONNECT2 = 8
    CATCHING_UP_ELECT = 9
    CATCHING_UP_PRESYNC = 10
    CATCHING_UP_SYNC = 11
    ROUND_SYNC = 12


class Poshn:
    """The PoS Hypernode object"""
    # There is only one instance of this class per node.
    # List of client routines
    # Each item (key=ip) is [active, last_active, sent_msg, sent_bytes, recv_msg, recv_bytes]
    clients = {}
    # list of inbound server connections
    inbound = {}

    stop_event = aioprocessing.AioEvent()  # FR: Move these to instance prop?

    def __init__(self, ip, port, address='', peers=None, verbose=False,
                 wallet="poswallet.json", datadir="data", suffix=''):
        global app_log
        global access_log
        self.ip = ip
        self.port = port
        self.address = address
        self.peers = peers
        self.verbose = verbose
        self.server_thread = None
        self.server = None
        self.state = HNState.START
        self.datadir = datadir
        # Helps id the instance for multi-instances dev and unique log files.
        self.suffix = suffix
        # Used when round syncing, to save previous state and our expectations about the end result.
        self.saved_state = {"state": self.state, "height_target": None}
        # list of peers I should stay connected to for a given round
        self.connect_to = []
        # Does the node try to connect to others?
        self.connecting = False
        self.my_status = None
        try:
            self.init_log()
            poscrypto.load_keys(wallet)
            # Time sensitive props
            self.mempool = posmempool.SqliteMempool(verbose=verbose, app_log=app_log, db_path=datadir+'/')
            self.poschain = poschain.SqlitePosChain(verbose=verbose, app_log=app_log,
                                                    db_path=datadir+'/', mempool=self.mempool)
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
            self.connected_count = 0
            self.consensus_nb = 0
            self.consensus_pc = 0
            self.net_height = None
            self.sync_from = None
            # Locks - Are they needed? - not if one process is enough
            self.round_lock = aioprocessing.Lock()
            self.clients_lock = aioprocessing.Lock()
            self.inbound_lock = aioprocessing.Lock()
        except Exception as e:
            app_log.error("Error creating poshn: {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))

    def init_log(self):
        global app_log
        global access_log
        if common.DEBUG:
            logging.basicConfig(level=logging.DEBUG)
        app_log = logging.getLogger("tornado.application")
        tornado.log.enable_pretty_logging()
        logfile = os.path.abspath("logs/pos_app{}.log".format(self.suffix))
        # Rotate log after reaching 512K, keep 5 old copies.
        rotate_handler = ConcurrentRotatingFileHandler(logfile, "a", 512 * 1024, 5)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        rotate_handler.setFormatter(formatter)
        app_log.addHandler(rotate_handler)
        #
        access_log = logging.getLogger("tornado.access")
        tornado.log.enable_pretty_logging()
        logfile2 = os.path.abspath("logs/pos_access{}.log".format(self.suffix))
        rotate_handler2 = ConcurrentRotatingFileHandler(logfile2, "a", 512 * 1024, 5)
        formatter2 = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        rotate_handler2.setFormatter(formatter2)
        access_log.addHandler(rotate_handler2)
        app_log.info("PoS HN {} Starting with pool address {}, data dir '{}' suffix {}."
                     .format(__version__, self.address, self.datadir, self.suffix))
        if not os.path.isdir(self.datadir):
            os.makedirs(self.datadir)

    def add_inbound(self, ip, port, properties=None):
        """
        Safely add a distant peer from server co-routine.
        This is called only after initial exchange and approval.

        :param ip:
        :param port:
        :param properties:
        :return:
        """
        ip = '{}:{}'.format(ip, port)
        with self.inbound_lock:
            self.inbound[ip] = properties

    def remove_inbound(self, ip, port):
        """
        Safely remove a distant peer from server co-routine

        :param ip:
        :param port:
        :return:
        """
        try:
            with self.inbound_lock:
                ip = '{}:{}'.format(ip, port)
                del self.inbound[ip]
        except KeyError:
            pass
        except Exception as e:
            app_log.error(">> remove_inbound")
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
            pass

    def update_inbound(self, ip, port, properties):
        """
        Safely update info for a connected peer

        :param ip:
        :param port:
        :param properties:
        :return:
        """
        ip = '{}:{}'.format(ip, port)
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
        # wait for potential threads to finish
        try:
            pass
            # A long sleep time will make nice close longer if we wait for the thread to finish
            # Since it's a daemon thread, we can leave it alone
            # self.whatever_thread.join()
        except Exception as e:
            app_log.error("Closing {}".format(e))

    async def manager(self):
        """
        Manager thread. Responsible for managing inner state of the node.

        :return:
        """
        global app_log
        global MINIMUM_CONNECTIVITY
        if self.verbose:
            app_log.info("Started HN Manager")
        # Initialise round/sir data
        await self.refresh_last_block()
        await self._check_round()
        while not self.stop_event.is_set():
            try:
                # updates our current view of the peers we are connected to and net global status/consensus
                await self._update_network()
                if self.state == HNState.SYNCING and self.forger == poscrypto.ADDRESS and not self.forged:
                    await self.change_state_to(HNState.STRONG_CONSENSUS)

                if self.state in (HNState.STRONG_CONSENSUS, HNState.MINIMAL_CONSENSUS) and self.forger != poscrypto.ADDRESS:
                    # We did not reach consensus in time, and we passed our turn.
                    app_log.warning("Too late to forge, back to Sync")
                    await self.change_state_to(HNState.SYNCING)
                # Adjust state depending of the connection state
                if self.connected_count >= MINIMUM_CONNECTIVITY:
                    if self.state == HNState.START:
                        await self.change_state_to(HNState.SYNCING)
                # elif self.state == HNState.SYNCING:
                else:
                    await self.change_state_to(HNState.START)

                """
                # Done in _consensus - replace here? would be more logic.
                if self.net_height:
                    # TODO: replace this lengthy condition by a readable function of its own -
                    if self.state == HNState.SYNCING and self.net_height['round'] == self.poschain.height_status.round and \
                            (self.net_height['forgers_round'] > self.poschain.height_status.forgers_round or \
                            self.net_height['uniques_round'] > self.poschain.height_status.uniques_round ) and \
                            self.net_height['count'] >= 2 :
                        # We are in the right round, but a most valuable chain is there.
                        app_log.warning("Better net chain, will analyse - TODO")
                        self.sync_from = random.choice(self.net_height['peers'])
                        # TODO: get whole round in one message, fast analyse without storing to check it's true,
                        # digest if ok.
                        # This is temp only, recycle late sync for now.
                        app_log.warning("Round Sync From {}".format(self.sync_from))
                        await self.change_state_to(HNState.CATCHING_UP_PRESYNC)
                """

                # If we should sync, but we are late compared to the net, then go in to "catching up state"
                if self.state == HNState.SYNCING and self.net_height \
                        and self.net_height['round'] > self.poschain.height_status.round:
                    app_log.warning("We are late, catching up!")
                    # FR: set time to trigger CATCHING_UP_CONNECT2
                    await self.change_state_to(HNState.CATCHING_UP_CONNECT1)
                    # on "connect 1 phase, we wait to be connect to at least .. peers
                    # on connect2 phase, we add random peers other than our round peers to get enough
                    await self.change_state_to(HNState.CATCHING_UP_ELECT)
                    # FR: more magic here to be sure we got a good one - here, just pick one from the top chain.
                    self.sync_from = random.choice(self.net_height['peers'])
                    app_log.warning("Sync From {}".format(self.sync_from))
                    await self.change_state_to(HNState.CATCHING_UP_PRESYNC)
                if self.state == HNState.CATCHING_UP_PRESYNC:
                    # If we have no client worker, add one
                    if self.sync_from not in self.clients:
                        io_loop = IOLoop.instance()
                        with self.clients_lock:
                            # first index is active or not
                            self.clients[self.sync_from] = {'stats': [False, 0, 0, 0, 0, 0, 0, 0, 0]}
                        ip, port = self.sync_from.split(':')
                        io_loop.spawn_callback(self.client_worker, ('N/A', ip, port, 1))
                    # FR: add some timeout so we can retry another one if this one fails.
                    # FR: The given worker will be responsible for changing state on ok or failed status

                if self.state == HNState.STRONG_CONSENSUS:
                    if self.consensus_pc > 50 and not common.DO_NOT_FORGE:
                        await self.change_state_to(HNState.FORGING)
                        # Forge will send also
                        await self.forge()
                        # await asyncio.sleep(10)
                        self.forged = True
                        await self.change_state_to(HNState.SYNCING)
                    else:
                        if self.verbose:
                            app_log.info("My slot, but too low a consensus to forge now.")

                # FR: Maybe don't display each time
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
                            full_peer = common.peer_to_fullpeer(peer)
                            if full_peer not in self.clients:
                                io_loop = IOLoop.instance()
                                with self.clients_lock:
                                    # first index is active or not
                                    self.clients[full_peer] = {'stats': [False, 0, 0, 0, 0, 0, 0, 0, 0]}
                                io_loop.spawn_callback(self.client_worker, peer)
                # FR: variable sleep time depending on the elapsed loop time - or use timeout?
                await asyncio.sleep(common.WAIT)
                await self._check_round()

            except Exception as e:
                app_log.error("Error in manager {}".format(e))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))

    async def change_state_to(self, new_state):
        """
        Sets new status and logs change.

        :param new_state:
        :return:
        """
        self.state = new_state
        if self.verbose:
            await self.status(log=True)

    async def _consensus(self):
        """
        Returns the % of jurors we agree with

        :return: double
        """
        peers_status = {}
        our_status = await self.poschain.async_height()
        our_status = our_status.to_dict(as_hex=True)
        our_status['count'] = 1
        our_status['peers'] = []
        if self.verbose:
            print("Our status", our_status)
        # peers_status = {'WE': our_status}
        # in self.clients we should have the latest blocks of every peer we are connected to
        nb = 0  # Nb of peers with same height as ours.
        # global status of known peers
        for ip, peer in self.clients.items():
            """
            'height_status': {'height': 94, 'round': 3361, 'sir': 0,
                              'block_hash': '796748324623f516639d71850ea3397d08a301ba', 'uniques': 0, 'uniques_round':0,
                              'forgers': 4, 'forgers_round': 3}
            """
            try:
                if peer['height_status']['block_hash'] in peers_status:
                    peers_status[peer['height_status']['block_hash']]['count'] += 1
                    peers_status[peer['height_status']['block_hash']]['peers'].append(ip)
                else:
                    peers_status[peer['height_status']['block_hash']] = peer['height_status'].copy()
                    peers_status[peer['height_status']['block_hash']]['count'] = 1
                    peers_status[peer['height_status']['block_hash']]['peers'] = [ip]
                if common.same_height(peer['height_status'], our_status):
                    app_log.info('Peer {} agrees'.format(ip))
                    # TODO: only count if in our common.POC_HYPER_NODES_LIST list?
                    nb += 1
                else:
                    app_log.warning('Peer {} disagrees'.format(ip))
            except:
                pass
        for ip, peer in self.inbound.items():
            if ip not in self.clients:
                try:
                    if peer['height_status']['block_hash'] in peers_status:
                        peers_status[peer['height_status']['block_hash']]['count'] += 1
                        peers_status[peer['height_status']['block_hash']]['peers'].append(ip)
                    else:
                        peers_status[peer['height_status']['block_hash']] = peer['height_status'].copy()
                        peers_status[peer['height_status']['block_hash']]['count'] = 1
                        peers_status[peer['height_status']['block_hash']]['peers'] = [ip]
                    if common.same_height(peer['height_status'], our_status):
                        nb += 1
                        if self.verbose:
                            app_log.info('Peer {} agrees'.format(ip))
                    else:
                        if self.verbose:
                            app_log.warning('Peer {} disagrees'.format(ip))
                except:
                    pass
        total = len(common.POC_HYPER_NODES_LIST)
        pc = round(nb * 100 / total)
        app_log.info('{} Peers do agree with us, {}%'.format(nb, pc))
        peers_status = peers_status.values()
        peers_status = sorted(peers_status,
                              key=itemgetter('forgers', 'forgers_round', 'uniques', 'uniques_round', 'round', 'height'),
                              reverse=True)
        # TEMP
        if self.verbose:
            print('> sorted peers status')
            for h in peers_status:
                print(' ', h)
        self.consensus_nb = nb
        self.consensus_pc = pc
        try:
            if len(peers_status):
                # FR: more precise checks? Here we just take the most valued chain.
                # We should take number of peers at this height, too.
                # If too weak, use the next one.
                self.net_height = peers_status[0]
                if common.first_height_is_better(self.net_height, our_status):
                    if self.net_height["round"] == our_status["round"]:
                        best_peers = self.net_height['peers']
                        app_log.warning('There is a better chain for our round on the net: "{}"'
                                        .format(','.join(best_peers)))
                        if self.state in [HNState.STRONG_CONSENSUS, HNState.MINIMAL_CONSENSUS, HNState.SYNCING]:
                            app_log.info('State {} force round sync and check'.format(self.state))
                            await self._round_sync(our_status["round"], self.net_height)
                        else:
                            app_log.warning('State is {}, ignoring for now.'.format(self.state))
            else:
                self.net_height = None
        except Exception as e:
            app_log.error('Consensus error {}'.format(e))
            self.net_height = None
        return pc

    async def _round_sync(self, a_round, promised_height):
        """
        Tries to sync from a peer advertising a better chain than ours.
        BEWARE: this is only ok if the peer is a juror for the current round.

        :param a_round: Round # to fetch
        :param promised_height: dict of the supposedly best available height
        :return: Boolean (success)
        """
        res = False
        # Store the current state
        self.saved_state = self.state
        await self.change_state_to(HNState.ROUND_SYNC)
        # pick a peer - if sync fails, we will try another random one next time
        peer = random.choice(promised_height['peers'])
        try:
            # Get the whole round data from that peer - We suppose it fits in memory
            the_blocks = await self._get_round_blocks(peer, a_round)
            if not the_blocks:
                raise ValueError("Did not get blocks from {}".format(peer))
            # check the data fits and count sources/forgers
            simulated_target = await self.poschain.check_round(a_round, the_blocks, fast_check=True)
            # print("expected", promised_height)
            # print("simulated", simulated_target)
            # Check it matches the target,
            if common.heights_match(promised_height, simulated_target):
                if self.verbose:
                    app_log.info('Distant Round {} Data from {} fits expectations.'.format(a_round, peer))
                # Delete the round to replace
                await self.poschain.delete_round(a_round)
                await self.poschain.status()
                # digest the blocks
                for block in the_blocks.block_value:
                    await self.poschain.digest_block(block, from_miner=False)
                await self.status(log=False)
                # TODO: emit tx or add to buffer
            else:
                app_log.warning('Distant Round {} Data from {} fails its promise.'.format(a_round, peer))
                # TODO: emit tx or add to buffer
        except ValueError as e:  # innocuous error, will retry.
            app_log.warning('_round_sync error "{}"'.format(e))
        except Exception as e:
            app_log.error('_round_sync error "{}"'.format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
        finally:
            # Set previous state again
            await self.change_state_to(self.saved_state)
            return res

    async def _get_round_blocks(self, peer, a_round):
        """
        Request full blocks from a full (or partial) round from a given peer

        :param peer:
        :param a_round:
        :return: list of blocks
        """
        try:
            # FR: Do we have a stream to this peer? if yes, use it instead of creating a new one ?
            # means add to self.clients
            if self.verbose:
                app_log.info('get_round_blocks({}, {})'.format(peer, a_round))
            ip, port = peer.split(':')
            stream = await self._get_peer_stream(ip, int(port), temp=True)
            # request the info
            if stream:
                await com_helpers.async_send_int32(commands_pb2.Command.roundblocks, a_round, stream, peer)
                blocks = await com_helpers.async_receive(stream, peer)
                try:
                    stream.close()
                except Exception as e:
                    app_log.error('_get_round_blocks error closing stream "{}"'.format(e))
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
                return blocks
            else:
                app_log.warning("Couldn't get temp stream from {}'.format(peer))")
                return None
        except Exception as e:
            app_log.error('_get_round_blocks error "{}"'.format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
            return None

    async def refresh_last_block(self):
        """
        Fetch fresh info from the PoS chain

        :return:
        """
        last_block = await self.poschain.last_block()
        self.last_height, self.previous_hash = last_block['height'], last_block['block_hash']
        self.last_round, self.last_sir = last_block['round'], last_block['sir']

    async def digest_txs(self, txs, peer_ip):
        """
        Checks tx and digest if they are new
        :param txs:
        :param peer_ip:
        :return:
        """
        try:
            nb = 0
            total = 0
            for tx in txs:
                # Will raise if error digesting, return false if already present in mempool or chain
                if await self.mempool.digest_tx(tx, poschain=self.poschain):
                    nb += 1
                total += 1
            app_log.info("Digested {}/{} tx(s) from {}".format(nb, total, peer_ip))
        except Exception as e:
            app_log.warning("Error {} digesting tx".format(e))

    async def digest_height(self, height_proto, full_peer, server=False):
        """

        :param height_proto: protobuff structure
        :param full_peer:
        :param server: comes from the server (inbound) or client (outbound) side?
        :return:
        """
        try:
            height = posblock.PosHeight().from_proto(height_proto)
            if server:
                self.inbound[full_peer]['height_status'] = height.to_dict(as_hex=True)
            else:
                # Client
                self.clients[full_peer]['height_status'] = height.to_dict(as_hex=True)
        except KeyError as e:
            app_log.error("Key Error {} digest_height".format(e))
        except Exception as e:
            app_log.error("Error {} digest_height".format(e))

    async def post_block(self, proto_block, peer_ip, peer_port):
        """
        Co routine to send the block we forged to a given peer
        Should we use threads instead and a simpler tcp client? Perfs to be tested.

        :param proto_block: a protobuf block
        :param peer_ip: the peer ip
        :param peer_port: the peer port
        :return: None
        """
        global app_log
        if self.verbose:
            app_log.info("Sending block to {}:{}".format(peer_ip, peer_port))
        try:
            full_peer = common.ipport_to_fullpeer(peer_ip, peer_port)
            tcp_client = TCPClient()
            stream = await tcp_client.connect(peer_ip, peer_port, timeout=5)
            await async_send_block(proto_block, stream, full_peer)
        except Exception as e:
            app_log.warning("Error '{}' sending block to {}:{}".format(e, peer_ip, peer_port))

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
            block.txs = await self.mempool.async_all(self.last_height + 1)
            if not len(block.txs):
                # not enough TX, won't pass in prod
                # raise ValueError("No TX to embed, block won't be valid.")
                app_log.warning("No TX to embed, block won't be valid.")
            # Remove from mempool
            await self.mempool.clear()
            # print(block.to_dict())
            block.sign()
            # print(block.to_dict())
            # FR: Shall we pass that one through "digest" to make sure?
            await self.poschain.insert_block(block)
            await self.change_state_to(HNState.SENDING)
            # Send the block to our peers (unless we were unable to insert it in our db)
            block = block.to_proto()
            if self.verbose:
                print("proto", block)
            app_log.info("Block Forged, I will send it")
            # build the list of jurors to send to. Exclude ourselves.
            to_send = [self.post_block(block, peer[1], peer[2])
                       for peer in common.POC_HYPER_NODES_LIST
                       if not (peer[1] == self.ip and peer[2] == self.port)]
            try:
                await asyncio.wait(to_send, timeout=30)
            except Exception as e:
                app_log.error("Timeout sending block: {}".format(e))
            # print(block.__str__())
            return True
        except Exception as e:
            app_log.error("Error forging: {}".format(e))
            return False

    def hello_string(self, temp=False):
        """
        Builds up the hello string

        :param temp: True - For one shot commands, from an already connected ip, uses a fake 00000 port as self id.
        :return:
        """
        if temp:
            port = 0
        else:
            port = self.port
        return common.POSNET + str(port).zfill(5) + self.address

    async def _get_peer_stream(self, ip, port, temp=True):
        """
        Returns a stream with communication already established.
        stream has to be closed after use.

        :param ip: 127.0.0.1
        :param port: 6969
        :param temp: True - For temps commands, uses a fake 00000 port as self id.
        :return: IOStream
        """
        global LTIMEOUT
        full_peer = common.ipport_to_fullpeer(ip, port)
        try:
            # FR: dup code, use that in the client_worker co-routine?
            if self.verbose:
                access_log.info("Initiating client connection to {}".format(full_peer))
            # ip_port = "{}:{}".format(peer[1], peer[2])
            stream = await TCPClient().connect(ip, port, timeout=LTIMEOUT)
            # connect_time = time.time()
            await com_helpers.async_send_string(commands_pb2.Command.hello, self.hello_string(temp=temp),
                                                stream, full_peer)
            msg = await com_helpers.async_receive(stream, full_peer)
            if self.verbose:
                access_log.info("Client got {}".format(com_helpers.cmd_to_text(msg.command)))
            if msg.command == commands_pb2.Command.hello:
                # decompose posnet/address and check.
                access_log.info("Client got Hello {} from {}".format(msg.string_value, full_peer))
                # self.clients[full_peer]['hello'] = msg.string_value  # nott here, it's out of the client biz
            if msg.command == commands_pb2.Command.ko:
                access_log.info("Client got Ko {}".format(msg.string_value))
                return
            # now we can enter a long term relationship with this node.
            return stream
        except tornado.iostream.StreamClosedError as e:
            if self.verbose:
                app_log.warning("Connection lost to {} because {}. No retry.".format(full_peer, e))
        except Exception as e:
            app_log.error("Connection lost to {} because {}. No Retry.".format(full_peer, e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))

    async def client_worker(self, peer):
        """
        Client worker, running in a coroutine.
        Tries to connect to the given peer, terminates on error and deletes itself on close.

        :param peer: ('aa012345678901aa', '127.0.0.1', 6969, 1)
        :return:
        """
        global app_log
        global LTIMEOUT
        # ip = peer[1]
        full_peer = common.peer_to_fullpeer(peer)
        stream = None
        try:
            if self.verbose:
                access_log.info("Initiating client co-routine for {}".format(full_peer))
            # ip_port = "{}:{}".format(peer[1], peer[2])
            stream = await TCPClient().connect(peer[1], peer[2], timeout=LTIMEOUT)
            connect_time = time.time()
            await com_helpers.async_send_string(commands_pb2.Command.hello, self.hello_string(), stream, full_peer)
            msg = await com_helpers.async_receive(stream, full_peer)
            if self.verbose:
                access_log.info("Worker got {}".format(com_helpers.cmd_to_text(msg.command)))
            if msg.command == commands_pb2.Command.hello:
                # decompose posnet/address and check.
                access_log.info("Worker got Hello {} from {}".format(msg.string_value, full_peer))
                self.clients[full_peer]['hello'] = msg.string_value
            if msg.command == commands_pb2.Command.ko:
                access_log.info("Worker got Ko {}".format(msg.string_value))
                return
            # now we can enter a long term relationship with this node.
            with self.clients_lock:
                # Set connected status
                self.clients[full_peer]['stats'][com_helpers.STATS_ACTIVEP] = True
                self.clients[full_peer]['stats'][com_helpers.STATS_COSINCE] = connect_time
            while not self.stop_event.is_set():
                if self.state in (HNState.CATCHING_UP_PRESYNC, HNState.CATCHING_UP_SYNC) \
                        and self.sync_from == full_peer:
                    # Faster sync
                    app_log.info(">> Entering presync with {}".format(full_peer))
                    await asyncio.sleep(common.SHORT_WAIT)
                    if self.state == HNState.CATCHING_UP_PRESYNC:
                        # Here, we check if our last block matches the peer's one.
                        # If not, we rollback one block at a time until we agree.
                        await com_helpers.async_send_int32(commands_pb2.Command.blockinfo,
                                                           self.poschain.height_status.height, stream, full_peer)
                        msg = await com_helpers.async_receive(stream, full_peer)
                        # TODO: check message is blockinfo
                        info = posblock.PosHeight().from_proto(msg.height_value)
                        if self.verbose:  # FR: to remove later on
                            print('self', self.poschain.height_status.to_dict(as_hex=True))
                            print('peer', info.to_dict(as_hex=True))
                        if self.poschain.height_status.block_hash == info.block_hash \
                                and self.poschain.height_status.round == info.round:
                            # we are ok, move to next state
                            await self.change_state_to(HNState.CATCHING_UP_SYNC)
                            app_log.info(">> Common ancestor OK with {}, CATCHING MISSED BLOCKS".format(full_peer))
                        else:
                            app_log.info(">> Block mismatch, will rollback")
                            # FR: find the common ancestor faster via height/hash list
                            while self.poschain.height_status.block_hash != info.block_hash:
                                if self.verbose:  # FR: remove later on
                                    print('self', self.poschain.height_status.to_dict(as_hex=True))
                                    print('peer', info.to_dict(as_hex=True))
                                await self.poschain.rollback()
                                await com_helpers.async_send_int32(commands_pb2.Command.blockinfo,
                                                                   self.poschain.height_status.height, stream,
                                                                   full_peer)
                                msg = await com_helpers.async_receive(stream, full_peer)
                                #  TODO: check message is blockinfo
                                info = posblock.PosHeight().from_proto(msg.height_value)
                                # await asyncio.sleep(5)
                            app_log.info(">> Should have rolled back to {} level.".format(full_peer))
                            # self.stop_event.set()
                            # sys.exit()

                    if self.state == HNState.CATCHING_UP_SYNC:
                        # We are on a compatible branch, lets get the missing blocks until we are sync.
                        # The peer will send as many blocks as he wants, and sends empty when it's over.

                        # warning: we use a property that can be None instead of the method.
                        while self.net_height['height'] > self.poschain.height_status.height:
                            await com_helpers.async_send_int32(
                                commands_pb2.Command.blocksync, self.poschain.height_status.height + 1,
                                stream, full_peer)
                            msg = await com_helpers.async_receive(stream, full_peer)
                            if not msg.block_value:
                                app_log.info("No more blocks from {}".format(full_peer))
                            else:
                                blocks_count = 0
                                for block in msg.block_value:
                                    if await self.poschain.digest_block(block, from_miner=False):
                                        blocks_count += 1
                                app_log.info("Saved {} blocks from {}".format(blocks_count, full_peer))

                        app_log.info(">> Net Synced via {}".format(full_peer))
                        await self.change_state_to(HNState.SYNCING)
                else:
                    await asyncio.sleep(common.WAIT)
                    now = time.time()
                    if self.state not in (HNState.STRONG_CONSENSUS, HNState.MINIMAL_CONSENSUS,
                                          HNState.CATCHING_UP_PRESYNC, HNState.CATCHING_UP_SYNC):
                        # If we are trying to reach consensus, don't ask for mempool sync so often.
                        # Peers may send anyway.
                        height_delay = 10
                        mempool_delay = 30
                    else:
                        # Not looking for consensus, but send our height every now and then to stay sync
                        height_delay = 30
                        mempool_delay = 20
                    if self.clients[full_peer]['stats'][com_helpers.STATS_LASTMPL] < now - mempool_delay:
                        # Send our new tx from mempool if any, will get the new from peers.
                        if await self.mempool.tx_count():
                            #  Just don't waste bandwith if our mempool is empty.
                            await self._exchange_mempool(stream, full_peer)
                    if self.state not in (HNState.CATCHING_UP_PRESYNC, HNState.CATCHING_UP_SYNC):
                        if self.clients[full_peer]['stats'][com_helpers.STATS_LASTHGT] < now - height_delay:
                            # Time to send our last block info to the peer, he will answer back with his
                            await self._exchange_height(stream, full_peer)

                    # Only send ping if time is due.
                    if self.clients[full_peer]['stats'][com_helpers.STATS_LASTACT] < now - common.PING_DELAY:
                        if self.verbose:
                            app_log.info("Sending ping to {}".format(full_peer))
                        # keeps connection active, or raise error if connection lost
                        await com_helpers.async_send_void(commands_pb2.Command.ping, stream, full_peer)
            try:
                stream.close()
            except:
                pass
            raise ValueError("Closing")
        except tornado.iostream.StreamClosedError as e:
            if self.verbose:
                app_log.warning("Connection lost to {} because {}. Retry in {} sec."
                                .format(peer[1], e, common.PEER_RETRY_SECONDS))
        except Exception as e:
            if self.verbose:
                app_log.error("Connection lost to {} because {}. Retry in {} sec."
                              .format(peer[1], e, common.PEER_RETRY_SECONDS))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
            try:
                stream.close()
            except:
                pass
            #  Wait here so we don't retry immediately
            await asyncio.sleep(common.PEER_RETRY_SECONDS)
        finally:
            try:
                with self.clients_lock:
                    # We could keep it and set to inactive, but is it useful? could grow too much
                    del self.clients[full_peer]
            except:
                pass

    async def _exchange_height(self, stream, full_peer):
        global app_log
        # FR: do not send if our height did not change since the last time. Will spare net resources.
        if self.verbose:
            app_log.info("Sending height to {}".format(full_peer))
        height = await self.poschain.async_height()
        self.clients[full_peer]['stats'][com_helpers.STATS_LASTHGT] = time.time()
        await async_send_height(commands_pb2.Command.height, height, stream, full_peer)
        # Peer will answer with its height
        # FR: have some watchdog to close connection if peer does not answer after a while (but does not disconnect)
        msg = await com_helpers.async_receive(stream, full_peer)
        if msg.command != commands_pb2.Command.height:
            raise ValueError("Bad answer to height command from {}".format(full_peer))
        try:
            await self.digest_height(msg.height_value, full_peer)
        except Exception as e:
            app_log.warning("Error {} digesting height from {}".format(e, full_peer))

    async def _exchange_mempool(self, stream, full_peer):
        global app_log
        if self.verbose:
            app_log.info("Sending mempool to {}".format(full_peer))
        txs = await self.mempool.async_since(self.clients[full_peer]['stats'][com_helpers.STATS_LASTMPL])
        self.clients[full_peer]['stats'][com_helpers.STATS_LASTMPL] = time.time()
        await com_helpers.async_send_txs(commands_pb2.Command.mempool, txs, stream, full_peer)
        # Peer will answer with its mempool
        msg = await com_helpers.async_receive(stream, full_peer)
        if msg.command != commands_pb2.Command.mempool:
            raise ValueError("Bad answer to mempool command from {}".format(full_peer))
        # if self.verbose:
        #    access_log.info("Worker got mempool answer {}".format(msg.__str__().strip()))
        try:
            await self.digest_txs(msg.tx_values, full_peer)
        except Exception as e:
            app_log.warning("Error {} digesting tx from {}".format(e, full_peer))

    async def _update_network(self):
        """
        Adjust peers and network properties.
        Always called from the manager co-routine only.

        :return:
        """
        inbound_count = len(self.inbound)
        clients_count = 0
        # Improve: use another list to avoid counting one by one?
        for who, client in self.clients.items():
            # Don't count the same peer twice
            if who not in self.inbound:
                # Only count the ones we are effectively connected to
                if client['stats'][com_helpers.STATS_ACTIVEP]:
                    clients_count += 1
        self.connected_count = inbound_count + clients_count
        # update our view of the network state
        await self._consensus()

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
                    app_log.info(">> New Slot {} in Round {}".format(self.sir, self.round))
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
                    tickets = await determine.hn_list_to_tickets(self.peers)
                    # TODO: real hash
                    self.slots = await determine.tickets_to_delegates(tickets, self.previous_hash)
                    if self.verbose:
                        app_log.info("Slots {}".format(json.dumps(self.slots)))
                    self.test_slots = await determine.hn_list_to_test_slots(self.peers, self.slots)
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
        Run the socket server.
        Once we called that, the calling thread is stopped until the server closes.

        :return:
        """
        global app_log
        loop = asyncio.get_event_loop()
        if common.DEBUG:
            loop.set_debug(True)
        if self.verbose:
            loop.run_until_complete(self.status(log=True))
        try:
            loop.run_until_complete(self.init_check())
        except Exception as e:
            app_log.error("Serve Init: {}".format(str(e)))
            return
        try:
            server = HnServer()
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

    async def init_check(self):
        """
        Initial coherence check
        # FR: more checks

        :return:
        """
        app_log.info("Initial coherence check")
        try:
            # Now test coherence and mempool
            await self.mempool.async_purge()
            mem_txs = await self.mempool.async_alltxids()
            txs = []
            for tx in mem_txs:
                if await self.poschain.tx_exists(tx):
                    app_log.info("Tx {} in our chain, removing from mempool".format(tx))
                    txs.append(tx)
            if len(txs):
                self.mempool.async_del_txids(txs)
        except Exception as e:
            app_log.error("Coherence Check: {}".format(str(e)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
            raise

    async def status(self, log=True):
        """
        Assemble and store the node status as a dict.

        :return: HN Status info
        """
        global app_log
        poschain_status = await self.poschain.status()
        mempool_status = await self.mempool.status()
        status = {'config': {'address': self.address, 'ip': self.ip, 'port': self.port, 'verbose': self.verbose},
                  'chain': poschain_status,
                  'mempool': mempool_status,
                  'peers': {
                    'connected_count': self.connected_count,
                    'outbound': list(self.clients.keys()),
                    'inbound': list(self.inbound.keys()),
                    'net_height': self.net_height
                  },
                  'state': {'state': self.state.name,
                            'round': self.round,
                            'sir': self.sir,
                            'forger': self.forger}}
        # 'peers': self.peers
        if log:
            app_log.info("Status: {}".format(json.dumps(status)))
        self.my_status = status
        return self.status
