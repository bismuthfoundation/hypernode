"""
Pos Masternode class for Bismuth
Tornado based
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

__version__ = '0.0.6'

"""
I use a global object to keep the state and route data between the servers and threads.
This looks not clean to me.
Will have to refactor if possible all in a single object, but looks hard enough, so postponing. 
"""

app_log = None
access_log = None

# Logical timeout (s) for socket client
LTIMEOUT = 45

# Minimum required connectivity before we are able to operate
# TODO: could depend on the jurors count.
MINIMUM_CONNECTIVITY = 2


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
        peer_port = '00000'
        error_shown = False
        access_log.info("SRV: Incoming connection from {}".format(peer_ip))
        # TODO: here, use tiered system to reserve safe slots for jurors,
        # some slots for non juror mns, and some others for other clients (non mn clients)
        try:
            # Get first message, we expect an hello with version number and address
            msg = await async_receive(stream, peer_ip)
            if self.verbose:
                access_log.info("SRV: Got msg >{}< from {}".format(com_helpers.cmd_to_text(msg.command), peer_ip))
            if msg.command == commands_pb2.Command.hello:
                access_log.info("SRV: Got Hello {} from {}".format(msg.string_value, peer_ip))
                reason, ok = await determine.connect_ok_from(msg.string_value, access_log)
                peer_port = msg.string_value[10:15]
                full_peer = common.ipport_to_fullpeer(peer_ip, peer_port)
                if not ok:
                    # TODO: send reason of deny?
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
            while not Posmn.stop_event.is_set():
                try:
                    # Loop over the requests until disconnect or end of server.
                    msg = await async_receive(stream, full_peer)
                    await self._handle_msg(msg, stream, peer_ip, peer_port)
                except StreamClosedError:
                    # This is a disconnect event, not an error
                    access_log.info("SRV: Peer {} left.".format(full_peer))
                    error_shown = True
                    return
                except Exception as e:
                    if not error_shown:
                        what = str(e)
                        if 'OK' not in what:
                            app_log.error("SRV: handle_stream {} for ip {}".format(what, full_peer))
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        print(exc_type, fname, exc_tb.tb_lineno)

                    return
        except Exception as e:
            app_log.error("SRV: TCP Server init {}: Error {}".format(peer_ip, e))

            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

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
        try:
            if self.verbose:
                # access_log.info("SRV: Got msg >{}< from {}:{}".format(msg.__str__().strip(), peer_ip, peer_port))
                access_log.info("SRV: Got msg >{}< from {}:{}".format(com_helpers.cmd_to_text(msg.command), peer_ip, peer_port))
            full_peer = common.ipport_to_fullpeer(peer_ip, peer_port)
            # Don't do a thing.
            # if msg.command == commands_pb2.Command.ping:
            #    await com_helpers.async_send(commands_pb2.Command.ok, stream, peer_ip)
            # TODO: rights management
            if msg.command == commands_pb2.Command.tx:
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
                print(msg)
                blocks = await self.node.poschain.async_blocksync(msg.int32_value)
                await async_send_block(blocks, stream, full_peer)

            elif msg.command == commands_pb2.Command.update:
                # TODO: rights/auth and config management
                await self.update(msg.string_value, stream, full_peer)

        except Exception as e:
            app_log.error("SRV: _handle_msg {}: Error {}".format(full_peer, e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
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
    CATCHING_UP_CONNECT1 = 7
    CATCHING_UP_CONNECT2 = 8
    CATCHING_UP_ELECT = 9
    CATCHING_UP_PRESYNC = 10
    CATCHING_UP_SYNC = 11


class Posmn:
    """The PoS Masternode object"""
    # List of client routines
    # Each item (key=ip) is [active, last_active, sent_msg, sent_bytes, recv_msg, recv_bytes]
    clients = {}
    # list of inbound server connections
    inbound = {}

    stop_event = aioprocessing.AioEvent()

    def __init__(self, ip, port, address='', peers=None, verbose=False, wallet="poswallet.json", datadir="data"):
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
        self.datadir = datadir
        # list of peers I should stay connected to for a given round
        self.connect_to = []
        # Does the node try to connect to others?
        self.connecting = False
        try:
            self.init_log()
            poscrypto.load_keys(wallet)
            # Time sensitive props
            self.poschain = poschain.SqlitePosChain(verbose=verbose, app_log=app_log, db_path=datadir+'/')
            self.mempool = posmempool.SqliteMempool(verbose=verbose, app_log=app_log, db_path=datadir+'/')
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
            # Locks - Are they needed?
            self.round_lock = aioprocessing.Lock()
            self.clients_lock = aioprocessing.Lock()
            self.inbound_lock = aioprocessing.Lock()
        except Exception as e:
            print("Error creating posmn: {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

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
        app_log.info("PoS MN {} Starting with pool address {}, data dir '{}'.".format(__version__, self.address, self.datadir))
        if not os.path.isdir(self.datadir):
            os.makedirs(self.datadir)

    def add_inbound(self, ip, port, properties=None):
        """
        Safely add a distant peer from server coroutine.
        This is called only after initial exchange and approval
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
        Safely remove a distant peer from server coroutine
        :param ip:
        :param port:
        :return:
        """
        try:
            with self.inbound_lock:
                ip = '{}:{}'.format(ip, port)
                del self.inbound[ip]
        except:
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
        # TODO: wait for potential threads to finish
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
            app_log.info("Started MN Manager")
        # Initialise round/sir data
        await self.refresh_last_block()
        # TODO: _check_round should get consensus and network current height/round
        await self._check_round()
        while not self.stop_event.is_set():
            # updates our current view of the peers we are connected to and net global status/consensus
            await self._update_network()
            # Adjust state depending of the connection state
            if self.connected_count >= MINIMUM_CONNECTIVITY:
                if self.state == MNState.START:
                    await self.change_state_to(MNState.SYNCING)
            # elif self.state == MNState.SYNCING:
            else:
                await self.change_state_to(MNState.START)
            # If we should sync, but we are late compared to the net, then go in to "catching up state"
            try:
                # can throw if net_height not known yet.
                if self.state == MNState.SYNCING and self.net_height['round'] > self.poschain.height_status.round:
                    app_log.warning("We are late, catching up!")
                    # TODO: set time to trigger CATCHING_UP_CONNECT2
                    await self.change_state_to(MNState.CATCHING_UP_CONNECT1)
                    # on "connect 1 phase, we wait to be connect to at least .. peers
                    # on connect2 phase, we add random peers other than our round peers to get enough
                    await self.change_state_to(MNState.CATCHING_UP_ELECT)
                    # TODO: more magic here to be sure we got a good one - here, just pick a random one from the top chain.
                    self.sync_from = random.choice(self.net_height['peers'])
                    app_log.warning("Sync From {}".format(self.sync_from))
                    await self.change_state_to(MNState.CATCHING_UP_PRESYNC)

            except:
                pass
            if self.state == MNState.CATCHING_UP_PRESYNC:
                # If we have no client worker, add one
                if self.sync_from not in self.clients:
                    io_loop = IOLoop.instance()
                    with self.clients_lock:
                        # first index is active or not
                        self.clients[self.sync_from] = {'stats': [False, 0, 0, 0, 0, 0, 0, 0, 0]}
                    ip, port = self.sync_from.split(':')
                    io_loop.spawn_callback(self.client_worker, ('N/A', ip, port, 1))
                # TODO: add some timeout so we can retry another one if this one fails.
                # TODO: The given worker will be responsible for changing state on ok or failed status

            if self.state == MNState.SYNCING and self.forger == poscrypto.ADDRESS and not self.forged:
                await self.change_state_to(MNState.STRONG_CONSENSUS)

            if self.state == MNState.STRONG_CONSENSUS:
                if self.consensus_pc > 50 and not common.DO_NOT_FORGE:
                    await self.change_state_to(MNState.FORGING)
                    # Forge will send also
                    await self.forge()
                    # await asyncio.sleep(10)
                    self.forged = True
                    await self.change_state_to(MNState.SYNCING)
                else:
                    if self.verbose:
                        app_log.info("My slot, but too low a consensus to forge now.")

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
                        full_peer = common.peer_to_fullpeer(peer)
                        if full_peer not in self.clients:
                            io_loop = IOLoop.instance()
                            with self.clients_lock:
                                # first index is active or not
                                self.clients[full_peer] = {'stats': [False, 0, 0, 0, 0, 0, 0, 0, 0]}
                            io_loop.spawn_callback(self.client_worker, peer)
            # TODO: variable sleep time depending on the elapsed loop time - or use timeout?
            await asyncio.sleep(common.WAIT)
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

    async def _consensus(self):
        """
        Returns the % of jurors we agree with
        :return:
        """
        # TODO
        our_status = await self.poschain.async_height()
        our_status = our_status.to_dict(as_hex=True)
        # in self.clients we should have the latest blocks of every peer we are connected to
        """
        # TEMP - DEBUG - DEV
        app_log.info('Clients {}'.format(json.dumps(self.clients)))
        app_log.info('Inbound {}'.format(json.dumps(self.inbound)))
        """
        nb = 0
        # global status of known peers
        peers_status = {}
        for ip, peer in self.clients.items():
            # print(peer)
            """
            'height_status': {'height': 94, 'round': 3361, 'sir': 0,
                              'block_hash': '796748324623f516639d71850ea3397d08a301ba', 'uniques': 0, 'uniques10': 0,
                              'forgers': 4, 'forgers10': 3}
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
                    # TODO: only count if in our common.POC_MASTER_NODES_LIST list?
                    nb += 1
                else:
                    app_log.warning('Peer {} disagrees'.format(ip))
            except:
                pass
        for ip, peer in self.inbound.items():
            if ip not in self.clients:
                # print(peer)
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
                        nb += 1
                    else:
                        app_log.warning('Peer {} disagrees'.format(ip))
                except:
                    pass
        # print("clients", self.clients)
        total = len(common.POC_MASTER_NODES_LIST)
        pc = round(nb * 100 / total)
        app_log.info('{} Peers do agree with us, {}%'.format(nb, pc))
        peers_status = peers_status.values()
        # print('> peers status', peers_status)
        peers_status = sorted(peers_status, key=itemgetter('forgers', 'uniques', 'height', 'round'), reverse=True)
        print('> sorted peers status')
        # TEMP
        for h in peers_status:
            print(' ', h)
        # print("inbound", self.inbound)
        self.consensus_nb = nb
        self.consensus_pc = pc
        try:
            # TODO: move precise checks, here we just take the most valued chain. We should take number of peers at this height, too.
            # If too weak, use the next one.
            self.net_height = peers_status[0]
        except:
            self.net_height = None
        return pc

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
        height = posblock.PosHeight().from_proto(height_proto)
        if server:
            self.inbound[full_peer]['height_status'] = height.to_dict(as_hex=True)
        else:
            # Client
            self.clients[full_peer]['height_status'] = height.to_dict(as_hex=True)

    async def post_block(self, proto_block, peer_ip, peer_port):
        """
        Co routine to send the block we forged to a given peer
        Should we use threads instead and a simpler tcp client? Perfs to be tested.
        :param proto_block:
        :param peer_ip:
        :param peer_port:
        :return:
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
            # TODO: Send the block to our peers (unless we were unable to insert it in our db)
            block = block.to_proto()
            app_log.error("Block Forged, I should send it")
            # build the list of jurors to send to. Exclude ourselves.
            to_send = [self.post_block(block, peer[1], peer[2]) for peer in common.POC_MASTER_NODES_LIST if not (peer[1] == self.ip and peer[2] == self.port)]
            try:
                await asyncio.wait(to_send, timeout=30)
            except Exception as e:
                app_log.error("Timeout sending block: {}".format(e))
            # print(block.__str__())
            return True
        except Exception as e:
            app_log.error("Error forging: {}".format(e))
            return False

    def hello_string(self):
        """
        Builds up the hello string
        :return:
        """
        return common.POSNET + str(self.port).zfill(5) + self.address

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
        full_peer = common.peer_to_fullpeer(peer)
        try:
            if self.verbose:
                access_log.info("Initiating client co-routine for {}".format(full_peer))
            tcp_client = TCPClient()
            # ip_port = "{}:{}".format(peer[1], peer[2])
            stream = await tcp_client.connect(peer[1], peer[2], timeout=LTIMEOUT)
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
                if self.state in (MNState.CATCHING_UP_PRESYNC, MNState.CATCHING_UP_SYNC) and self.sync_from == full_peer:
                    # Faster sync
                    app_log.warning("Entering presync with {}".format(full_peer))
                    await asyncio.sleep(common.SHORT_WAIT)
                    if self.state == MNState.CATCHING_UP_PRESYNC:
                        # Here, we check if our last block matches the peer's one.
                        # If not, we rollback one block at a time until we agree.
                        await com_helpers.async_send_int32(commands_pb2.Command.blockinfo,
                                                            self.poschain.height_status.height, stream,full_peer)
                        msg = await com_helpers.async_receive(stream, full_peer)
                        # TODO: check message is blockinfo
                        info = posblock.PosHeight().from_proto(msg.height_value)
                        # print('self', self.poschain.height_status.to_dict(as_hex=True))
                        # print('peer', info.to_dict(as_hex=True))
                        if self.poschain.height_status.block_hash == info.block_hash and self.poschain.height_status.round == info.round:
                            # we are ok, move to next state
                            await self.change_state_to(MNState.CATCHING_UP_SYNC)
                            app_log.warning("Common ancestor OK with {}, CATCHING MISSED BLOCKS".format(full_peer))
                        else:
                            # todo
                            app_log.error("Block mismatch but Rollback is not implemented yet.")
                            print('self', self.poschain.height_status.to_dict(as_hex=True))
                            print('peer', info.to_dict(as_hex=True))
                            await asyncio.sleep(10)
                            self.stop_event.set()

                    if self.state == MNState.CATCHING_UP_SYNC:
                        # We are on a compatible branch, lets get the missing blocks until we are sync.
                        # The peer will send as many blocks as he wants, and sends empty when it's over.

                        # warning: we use a property that can be None instead of the method.
                        while self.net_height['height'] > self.poschain.height_status.height:
                            await com_helpers.async_send_int32(commands_pb2.Command.blocksync,
                                                               self.poschain.height_status.height + 1, stream, full_peer)
                            msg = await com_helpers.async_receive(stream, full_peer)
                            # print(msg)
                            if not msg.block_value:
                                app_log.warning("No more blocks from {}".format(full_peer))
                            else:
                                blocks_count = 0
                                for block in msg.block_value:
                                    if await self.poschain.digest_block(block, from_miner=False):
                                        blocks_count += 1
                                app_log.info("Saved {} blocks from {}".format(blocks_count, full_peer))

                        app_log.warning("Net Synced via {}".format(full_peer))
                        await self.change_state_to(MNState.SYNCING)
                else:
                    await asyncio.sleep(common.WAIT)
                    now = time.time()
                    if self.state not in (MNState.STRONG_CONSENSUS, MNState.MINIMAL_CONSENSUS, MNState.CATCHING_UP_PRESYNC, MNState.CATCHING_UP_SYNC):
                        # If we are trying to reach consensus, don't ask for mempool sync. Peers may send anyway.
                        height_delay = 10
                        if self.clients[full_peer]['stats'][com_helpers.STATS_LASTMPL] < now - 10:
                            # Send our new tx from mempool if any, will get the new from peer.
                            await self._exchange_mempool(stream, full_peer)
                    else:
                        # Not looking for consensus, but send our height every now and then to stay sync
                        height_delay = 30
                    if self.state not in (MNState.CATCHING_UP_PRESYNC, MNState.CATCHING_UP_SYNC):
                        if self.clients[full_peer]['stats'][com_helpers.STATS_LASTHGT] < now - height_delay:
                            # Time to send our last block info to the peer, he will answer back with his
                            await self._exchange_height(stream, full_peer)

                    # Only send ping if time is due.
                    # TODO: more than 30 sec? Config
                    if self.clients[full_peer]['stats'][com_helpers.STATS_LASTACT] < now - 30:
                        if self.verbose:
                            app_log.info("Sending ping to {}".format(full_peer))
                        # keeps connection active, or raise error if connection lost
                        await com_helpers.async_send_void(commands_pb2.Command.ping, stream, full_peer)

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
                    del self.clients[full_peer]
            except:
                pass

    async def _exchange_height(self, stream, full_peer):
        global app_log
        # TODO: do not send if our height did not change since the last time. Will spare net resources.
        if self.verbose:
            app_log.info("Sending height to {}".format(full_peer))
        height = await self.poschain.async_height()
        self.clients[full_peer]['stats'][com_helpers.STATS_LASTHGT] = time.time()
        await async_send_height(commands_pb2.Command.height, height, stream, full_peer)
        # Peer will answer with its height
        # TODO: have some watchdog to close connection if peer does not answer after a while (but does not disconnect)
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
        return status

