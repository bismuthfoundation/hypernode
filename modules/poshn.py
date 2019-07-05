"""
Pos Hypernode class for Bismuth Cryptocurrency
Tornado based

Note:
    TODO: are prioritary actions TBD
    FR: are features request. Think of them as second class TO DO items that are less urgent
    FR: will go into TODO: as TODO: is cleared.
"""

import json
import logging
import os
import random
import resource
import socket
import sys
from asyncio import get_event_loop, TimeoutError, wait_for, Task
from asyncio import sleep as async_sleep
from asyncio import wait as asyncio_wait
from distutils.version import LooseVersion
from enum import Enum
from operator import itemgetter
from os import path
from time import time
from hashlib import sha256

import aioprocessing
import psutil
import requests
import tornado.log

# pip install ConcurrentLogHandler
from cloghandler import ConcurrentRotatingFileHandler

# Tornado
from tornado.ioloop import IOLoop

# from tornado.options import define, options
# from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.tcpclient import TCPClient
from tornado.tcpserver import TCPServer
from tornado.util import TimeoutError

# Our modules
import com_helpers
import commands_pb2
import config
import determine
import hn_db
import posblock
import poschain
import poscrypto
import poshelpers
from com_helpers import async_receive, async_send_string, async_send_block
from com_helpers import async_send_void, async_send_txs, async_send_height
from naivemempool import NaiveMempool
from pow_interface import PowInterface
from pow_interface import get_pow_status

__version__ = "0.0.98p"

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
MINIMUM_CONNECTIVITY = 3  # let 1 for growth phase.

# Some systems do not support reuse_port
REUSE_PORT = hasattr(socket, "SO_REUSEPORT")


"""
TCP Server Class
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
        Async. Handles the lifespan of a client, from connection to end of stream

        :param stream:
        :param address:
        :return:
        """
        global access_log
        global app_log
        peer_ip, fileno = address
        peer_port = "00000"
        access_log.info("SRV: Incoming connection from {}".format(peer_ip))
        remove = False  # So we do not remove inbound info for temp "block" command.
        # TODO: here, use tiered system to reserve safe slots for jurors,
        # some slots for non juror hns, and some others for other clients (non hn clients)
        try:
            # Get first message, we expect an hello with version number and address
            msg = await async_receive(stream, peer_ip)
            if self.verbose and "srvmsg" in config.LOG:
                access_log.info(
                    "SRV: Got msg >{}< from {}".format(
                        com_helpers.cmd_to_text(msg.command), peer_ip
                    )
                )
            if msg.command == commands_pb2.Command.hello:
                reason, ok = await determine.connect_ok_from(
                    msg.string_value, access_log
                )
                peer_port = msg.string_value[10:15]
                full_peer = poshelpers.ipport_to_fullpeer(peer_ip, peer_port)
                access_log.info(
                    "SRV: Got Hello {} from {}".format(msg.string_value, full_peer)
                )
                if not ok:
                    # FR: send reason of deny?
                    # Should we send back a proper ko message in that case? - remove later if used as a DoS attack
                    await async_send_string(
                        commands_pb2.Command.ko, reason, stream, peer_ip
                    )
                    return
                # Right version, we send our hello as well.
                await async_send_string(
                    commands_pb2.Command.hello,
                    self.node.hello_string(),
                    stream,
                    peer_ip,
                )
                # Add the peer to inbound list
                self.node.add_inbound(
                    peer_ip, peer_port, {"hello": msg.string_value, "stats": [0] * 9}
                )
                remove = True

            elif msg.command == commands_pb2.Command.block:
                while self.node.state in [HNState.NEWROUND]:
                    # Do not run block processing while in new round computation
                    await async_sleep(1)
                # block sending does not require hello
                access_log.info("SRV: Got forged block from {}".format(peer_ip))
                if peer_ip not in self.node.registered_ips:
                    # TODO: add to anomalies buffer
                    access_log.warning(
                        "Got block from {} but not a registered ip".format(peer_ip)
                    )
                    return
                await self.node.check_round()  # Make sure our round info is up to date
                if not self.node.forger:
                    access_log.warning(
                        "Got block from {} but no current forger".format(peer_ip)
                    )
                    return
                hn = await self.node.hn_db.hn_from_address(
                    self.node.forger, self.node.round
                )
                if (
                    self.node.state in [HNState.SYNCING, HNState.ROUND_SYNC]
                    and hn["ip"] != peer_ip
                ):
                    # We can only be sure it's a fake if we are synced up to current round
                    access_log.warning(
                        "Got block from {} but forger {} ip is {}".format(
                            peer_ip, self.node.forger, hn["ip"]
                        )
                    )
                    # TODO: add to anomalies buffer
                    return
                for block in msg.block_value:
                    await self.node.poschain.digest_block(block, from_miner=True)
                return
            elif msg.command == commands_pb2.Command.test:
                # block sending does not require hello
                if peer_ip not in self.node.registered_ips:
                    # TODO: add to anomalies buffer
                    access_log.warning(
                        "Got block from {} but not a registered ip".format(peer_ip)
                    )
                    return
                access_log.error("SRV: Got test block from {}".format(peer_ip))
                # TODO: check that this ip is in the current test round, or add to anomalies buffer
                # await self.node.check_round()  # Make sure our round info is up to date
                await self.node._new_tx(
                    msg.tx_values[0].sender, 203, msg.tx_values[0].params, int(time())
                )
                await async_send_block(msg, stream, peer_ip)
                return
            else:
                access_log.warning("SRV: {} did not say hello".format(peer_ip))
                # Should we send back a proper ko message in that case? - remove later if used as a DoS attack
                await async_send_string(
                    commands_pb2.Command.ko, "Did not say hello", stream, peer_ip
                )
                return
            # Here the peer said Hello and we accepted its version, we can have a date.
            while not config.STOP_EVENT.is_set():
                try:
                    # Loop over the requests until disconnect or end of server.
                    msg = await async_receive(stream, full_peer)
                    await self._handle_msg(msg, stream, peer_ip, peer_port)
                except StreamClosedError:
                    # This is a disconnect event, not an error
                    if "connections" in config.LOG:
                        access_log.info("SRV: Peer {} left.".format(full_peer))
                    return
                except Exception as e:
                    what = str(e)
                    # FR: Would be cleaner with a custom exception
                    if "OK" not in what:
                        app_log.error(
                            "SRV: handle_stream {} for ip {}".format(what, full_peer)
                        )
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    app_log.error(
                        "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
                    )
                    return

        except Exception as e:
            app_log.error("SRV: TCP Server init {}: Error {}".format(peer_ip, e))
            # FR: the following code logs extra info for debug.
            # factorize in a single function with common.EXTRA_LOG switch to activate.
            # Maybe also log in a distinct file since these are supposed to be unexpected exceptions
            # Used also in other files.
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))
            return

        finally:
            if remove:
                self.node.remove_inbound(peer_ip, peer_port)
            try:
                # Is this done a level higher?
                stream.close()
            except:
                pass

    async def _handle_msg(self, msg, stream, peer_ip, peer_port):
        """
        Async. Handles a single command received by the server.

        :param msg:
        :param stream:
        :param peer_ip:
        """
        if self.verbose and "srvmsg" in config.LOG:
            access_log.info(
                "SRV: Got msg >{}< from {}:{}".format(
                    com_helpers.cmd_to_text(msg.command), peer_ip, peer_port
                )
            )
        full_peer = poshelpers.ipport_to_fullpeer(peer_ip, peer_port)
        while self.node.state in [HNState.NEWROUND]:
            # Do not run incoming actions while in new round computation
            await async_sleep(1)
        try:
            # Don't do a thing.
            # if msg.command == commands_pb2.Command.ping:
            #    await com_helpers.async_send(commands_pb2.Command.ok, stream, peer_ip)
            # TODO: rights management
            if msg.command == commands_pb2.Command.status:
                self.node.my_status["instance"]["localtime"] = time()
                status = json.dumps(self.node.my_status)
                del self.node.my_status["instance"]["localtime"]
                await async_send_string(
                    commands_pb2.Command.status, status, stream, full_peer
                )

            elif msg.command == commands_pb2.Command.getround:
                round_status = json.dumps(await self.node.round_status())
                await async_send_string(
                    commands_pb2.Command.getround, round_status, stream, full_peer
                )

            elif (
                msg.command == commands_pb2.Command.gethypernodes
                and peer_ip in config.ALLOW_QUERIES_FROM
            ):
                hypernodes = await self.node.get_hypernodes(msg.string_value)
                await async_send_string(
                    commands_pb2.Command.gethypernodes,
                    json.dumps(hypernodes),
                    stream,
                    full_peer,
                )

            elif msg.command == commands_pb2.Command.getheights:
                heights = await self.node.get_heights()
                await async_send_string(
                    commands_pb2.Command.getheights,
                    json.dumps(heights),
                    stream,
                    full_peer,
                )

            elif msg.command == commands_pb2.Command.tx:
                # We got one or more tx from a peer. This is NOT as part of the mempool sync, but as a way to inject
                # external txs from a "controller / wallet or such
                # TODO: check that the sender address is a registered HN address (anti spam)
                try:
                    await self.node.digest_txs(msg.tx_values, full_peer)
                    await async_send_void(commands_pb2.Command.ok, stream, full_peer)
                except Exception as e:
                    app_log.warning(
                        "SRV: Error {} digesting tx from {}:{}".format(
                            e, peer_ip, peer_port
                        )
                    )
                    await async_send_void(commands_pb2.Command.ko, stream, full_peer)

            elif msg.command == commands_pb2.Command.mempool:
                if peer_ip not in self.node.registered_ips:
                    access_log.warning(
                        "Got mempool from {} but not a registered ip".format(peer_ip)
                    )
                    # just don't digest?
                else:
                    # peer mempool extract
                    try:
                        await self.node.digest_txs(msg.tx_values, full_peer)
                    except Exception as e:
                        app_log.warning(
                            "SRV: Error {} digesting tx from {}:{}".format(
                                e, peer_ip, peer_port
                            )
                        )
                # Use clients stats to get real since - beware of one shot clients, send full (int_value=1)
                # sys.exit()
                stats = self.node.inbound[full_peer]["stats"]
                last = int(stats[com_helpers.STATS_LASTMPL]) if len(stats) else 0
                txs = await self.mempool.async_since(last)
                self.node.inbound[full_peer]["stats"][
                    com_helpers.STATS_LASTMPL
                ] = time()
                # Filter out the tx we got from the peer
                # app_log.info("{} txs before filtering".format(len(txs)))
                peer_txids = [tx.txid for tx in msg.tx_values]
                txs = [tx for tx in txs if tx.txid not in peer_txids]
                # app_log.info("{} txs after filtering".format(len(txs)))
                if "mempool" in config.LOG:
                    if self.verbose and "txdigest" in config.LOG:
                        app_log.info(
                            "SRV Sending back txs {} to {}, ts={}".format(
                                [tx.to_json() for tx in txs], full_peer, last
                            )
                        )
                    else:
                        app_log.info(
                            "SRV Sending back {} txs to {}, ts={}".format(
                                len(txs), full_peer, last
                            )
                        )
                # This is a list of PosMessage objects
                await async_send_txs(
                    commands_pb2.Command.mempool, txs, stream, full_peer
                )

            elif msg.command == commands_pb2.Command.height:
                if peer_ip in self.node.registered_ips:
                    await self.node.digest_height(
                        msg.height_value, full_peer, server=True
                    )
                else:
                    # just don't digest
                    access_log.warning(
                        "Got Height request from {} but not a registered ip.".format(
                            peer_ip
                        )
                    )
                height = await self.node.poschain.async_height()
                await async_send_height(
                    commands_pb2.Command.height, height, stream, full_peer
                )

            elif msg.command == commands_pb2.Command.blockinfo:
                height = await self.node.poschain.async_blockinfo(msg.int32_value)
                await async_send_height(
                    commands_pb2.Command.blockinfo, height, stream, full_peer
                )

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

            elif msg.command == commands_pb2.Command.gettx:
                tx = await self.node.poschain.async_gettx(msg.string_value)
                await async_send_block(tx, stream, full_peer)

            elif msg.command == commands_pb2.Command.getheaders:
                blocks = await self.node.poschain.async_getheaders(msg.string_value)
                await async_send_block(blocks, stream, full_peer)

            elif msg.command == commands_pb2.Command.update:
                if not config.AUTO_UPDATE:
                    access_log.warning(
                        "Got Update from {} but not allowed by config.".format(peer_ip)
                    )
                    return
                if peer_ip not in config.ALLOW_UPDATES_FROM:
                    access_log.warning(
                        "Got Update from {} but not an allowed ip.".format(peer_ip)
                    )
                    return
                await self.update(msg.string_value, stream, full_peer)

            else:
                # if self.verbose:
                #    app_log.warning("SRV unknown message {}, closing.".format(com_helpers.cmd_to_text(msg.command)))
                raise ValueError(
                    "Unknown message {}".format(com_helpers.cmd_to_text(msg.command))
                )

        except ValueError as e:
            app_log.warning("SRV: Error {} for peer {}.".format(e, full_peer))
            # FR: can we just ignore, or should we raise to close the connection?

        except Exception as e:
            app_log.error("SRV: _handle_msg {}: Error {}".format(full_peer, e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))
            raise

    async def update(self, url, stream, peer_ip):
        """
        Update process when an 'update' message
        from an authorized source is received.

        :param url:
        :param stream:
        :param peer_ip:
        """
        app_log.info("Checking version from {}".format(url))
        version_url = url + "version.txt"
        try:
            version = requests.get(version_url).text.strip()
            if not version or "html" in version:
                app_log.warning("Version info not found")
                return
            # compare to our version
            if LooseVersion(__version__) < LooseVersion(version):
                app_log.info(
                    "Newer {} version than our {}, updating.".format(
                        version, __version__
                    )
                )
                # fetch archive and extract
                poshelpers.update_source(url + "hypernode.tar.gz", app_log)
                # FR: bootstrap db on condition or other message ?
                await async_send_void(commands_pb2.Command.ok, stream, peer_ip)
                # restart
                """
                args = sys.argv[:]
                app_log.warning('Re-spawning {}'.format(' '.join(args)))
                args.insert(0, sys.executable)
                if sys.platform == 'win32':
                    args = ['"%s"' % arg for arg in args]
                os.execv(sys.executable, args)
                """
                app_log.info("Updated, will now clean stop, cronjob will restart.")
                # Just close, the cronjob will do a clean relaunch
                self.node.stop()
            else:
                msg = "Keeping our {} version vs distant {}".format(
                    __version__, version
                )
                app_log.info(msg)
                await async_send_string(commands_pb2.Command.ko, msg, stream, peer_ip)
        except Exception as e:
            app_log.error("Error {} updating from {}".format(e, url))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))


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
    NEWROUND = 13
    POW_NOT_SYNC = 14


class Poshn:
    """The PoS Hypernode object"""

    # There is only one instance of this class per node.
    # List of client routines
    # Each item (key=ip) is [active, last_active, sent_msg, sent_bytes, recv_msg, recv_bytes]
    clients = {}
    # list of inbound server connections
    inbound = {}

    def __init__(
        self,
        ip,
        port,
        address="",
        peers=None,
        verbose=False,
        outip="127.0.0.1",
        interface="",
        wallet="poswallet.json",
        datadir="data",
        suffix="",
        version="",
    ):
        """
        TODO

        :param ip:
        :param port:
        :param address:
        :param peers:
        :param verbose:
        :param wallet:
        :param datadir:
        :param suffix:
        :param version:
        """
        global app_log
        global access_log
        config.STOP_EVENT = aioprocessing.AioEvent()
        self.ip = ip
        self.outip = outip
        self.interface = interface
        self.port = port
        self.address = address
        self.all_peers = peers
        self.registered_ips = []
        self.active_peers = list(peers)
        self.round_meta = (
            {}
        )  #  control hashes for current round info, to be embedded in status.
        self.verbose = verbose
        self.server_thread = None
        self.server = None
        self.state = HNState.START
        self.datadir = datadir
        # The version of the instance runner, hn_instance
        self.client_version = version
        # Helps id the instance for multi-instances dev and unique log files.
        self.suffix = suffix
        # Used when round syncing, to save previous state and our expectations about the end result.
        self.saved_state = {"state": self.state, "height_target": None}
        # list of peers I should stay connected to for a given round
        self.connect_to = []
        # Does the node try to connect to others?
        self.connecting = False
        self.my_status = None
        self.process = None
        self.forged_count = 0  # How many blocks forged since start of the HN
        self.slots = None
        self.test_slots = None
        self.tests_to_run = []  # Holds the tests to run this slot
        self.tests_to_answer = []  # and the tests others will ask us this slot.
        self.no_test_this_round = False
        self.no_test_sent = 0
        self.testing = False  # Flag: we are currently running a test.
        self.being_tested = False
        self.not_reg = False  # Suppose we are reg by default
        # From whom are we digesting mempool?
        self.mempool_digesting = ""
        try:
            self.init_log()
            self.check_os()
            poscrypto.load_keys(wallet)
            self.address = poscrypto.ADDRESS
            # Try to bootstrap if empty
            if not os.path.isfile(
                "{}/poc_pos_chain.db".format(datadir)
            ) or not os.path.isfile("{}/hndb.db".format(datadir)):
                app_log.warning("No chain found, Bootstrapping.")
                if not poshelpers.bootstrap(datadir):
                    app_log.warning("Bootstrap failed, will catch slowly over the net.")
                    time.sleep(10)
            # Make sure node version is ok and node plugin runs.
            self.check_node()
            self.check_pow_status()
            # Time sensitive props
            """
            self.mempool = posmempool.SqliteMempool(
                verbose=verbose, app_log=app_log, db_path=datadir + "/", ram=True
            )
            """
            self.mempool = NaiveMempool(verbose=verbose, app_log=app_log)
            self.poschain = poschain.SqlitePosChain(
                verbose=verbose,
                app_log=app_log,
                db_path=datadir + "/",
                mempool=self.mempool,
            )
            self.powchain = PowInterface(app_log=app_log)
            self.hn_db = hn_db.SqliteHNDB(
                verbose=verbose, app_log=app_log, db_path=datadir + "/"
            )
            loop = get_event_loop()
            loop.run_until_complete(self.powchain.wait_synced())

            # that part is better handled as "initial round check"
            """
            loop.run_until_complete(self.powchain.load_hn_pow(datadir=self.datadir))
            # print(self.powchain.regs)
            if not self.powchain.regs:
                app_log.error("No registered HN found, closing. Try restarting.")
                sys.exit()
            self.active_regs = [
                items for items in self.powchain.regs.values() if items["active"]
            ]
            self.registered_ips = [items["ip"] for items in self.powchain.regs.values()]
            app_log.info(
                "Status: At launch, {} registered HN, among which {} are active".format(
                    len(self.powchain.regs), len(self.active_regs)
                )
            )
            """
            self.is_delegate = False
            self.round = -1
            self.sir = -1
            self.previous_round = 0
            self.previous_sir = 0
            self.forger = None
            self.forged = False
            #
            self.last_height = 0
            self.previous_hash = ""
            self.last_round = 0
            self.last_sir = 0
            self.connected_count = 0
            self.consensus_nb = 0
            self.consensus_pc = 0
            self.peers_status = {}
            self.net_height = None
            self.sync_from = None
            self.current_round_start = 0
            # Locks - Are they needed? - not if one process is enough
            self.round_lock = aioprocessing.Lock()
            self.clients_lock = aioprocessing.Lock()
            self.inbound_lock = aioprocessing.Lock()

        except Exception as e:
            app_log.error("Error creating poshn: {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))

    def init_log(self):
        """
        Initialize the log related objects.
        """
        global app_log
        global access_log
        if config.DEBUG:
            logging.basicConfig(level=logging.DEBUG)
        app_log = logging.getLogger("tornado.application")
        tornado.log.enable_pretty_logging()
        logfile = os.path.abspath("logs/pos_app{}.log".format(self.suffix))
        # Rotate log after reaching 512K, keep 5 old copies.
        rotate_handler = ConcurrentRotatingFileHandler(logfile, "a", 512 * 1024, 5)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        rotate_handler.setFormatter(formatter)
        app_log.addHandler(rotate_handler)
        #
        access_log = logging.getLogger("tornado.access")
        tornado.log.enable_pretty_logging()
        logfile2 = os.path.abspath("logs/pos_access{}.log".format(self.suffix))
        rotate_handler2 = ConcurrentRotatingFileHandler(logfile2, "a", 512 * 1024, 5)
        formatter2 = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        rotate_handler2.setFormatter(formatter2)
        access_log.addHandler(rotate_handler2)
        app_log.info(
            "PoS HN {} Starting on ip address '{}:{}', data dir '{}' suffix {}.".format(
                __version__, self.ip, self.port, self.datadir, self.suffix
            )
        )
        if not os.path.isdir(self.datadir):
            os.makedirs(self.datadir)

    def check_os(self):
        if os.name == "posix":
            self.process = psutil.Process()
            limit = resource.getrlimit(resource.RLIMIT_NOFILE)
            app_log.info("OS File limits {}, {}".format(limit[0], limit[1]))
            if limit[0] < 1024:
                app_log.error("Too small ulimit, please tune your system.")
                sys.exit()
            if limit[0] < 65000:
                app_log.warning(
                    "ulimit shows non optimum value, consider tuning your system."
                )
        else:
            app_log.error(
                "Non Posix system, requirements are not satisfied. Use at your own risks."
            )

    def check_node(self):
        # TODO: dup code with hn_check, factorize in helpers.
        node_filename = path.abspath(
            config.POW_LEDGER_DB.replace("static/", "").replace("ledger.db", "node.py")
        )
        node_version = None
        for line in open(node_filename):
            if "VERSION" in line:
                node_version = (
                    line.split("=")[-1]
                    .split("#")[0]
                    .replace("'", "")
                    .replace('"', "")
                    .strip()
                )
                break
        ok = LooseVersion(node_version) >= LooseVersion(config.REQUIRED_NODE_VERSION)
        app_log.info(
            "Companion node Version {}, required {}, {}".format(
                node_version, config.REQUIRED_NODE_VERSION, ok
            )
        )
        if not ok:
            app_log.error("Insufficient companion node version")
            # kill outdated nodes
            try:
                for proc in psutil.process_iter():
                    if "node.py" in proc.cmdline():
                        proc.kill()
            finally:
                sys.exit()

    def check_pow_status(self):
        # TODO: dup code with hn_check, factorize in helpers.
        # FR: rule of 3: 3 times we do that hack to get a filename, use a helper.
        status_filename = path.abspath(
            config.POW_LEDGER_DB.replace("static/", "").replace(
                "ledger.db", "powstatus.json"
            )
        )
        ok = False
        while not ok:
            if not path.isfile(status_filename):
                app_log.warning(
                    "No powstatus.json. Make sure the node runs. Waiting 30 sec"
                )
                time.sleep(30)
            elif os.path.getmtime(status_filename) < time() - 6 * 60:
                app_log.warning(
                    "powstatus.json seems too old. Make sure the node runs. Waiting 30 sec."
                )
                time.sleep(30)
            else:
                app_log.info("powstatus.json ok.")
                ok = True

    def add_inbound(self, ip, port, properties=None):
        """
        Safely add a distant peer from server co-routine.
        This is called only after initial exchange and approval.

        :param ip:
        :param port:
        :param properties:
        """
        ip = "{}:{}".format(ip, port)
        with self.inbound_lock:
            self.inbound[ip] = properties

    def remove_inbound(self, ip, port):
        """
        Safely remove a distant peer from server co-routine.

        :param ip:
        :param port:
        """
        try:
            with self.inbound_lock:
                ip = "{}:{}".format(ip, port)
                del self.inbound[ip]
        except KeyError:
            pass
        except Exception as e:
            app_log.error(">> remove_inbound")
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))

    def update_inbound(self, ip, port, properties):
        """
        Safely update info for a connected peer.

        :param ip:
        :param port:
        :param properties:
        """
        ip = "{}:{}".format(ip, port)
        with self.inbound_lock:
            self.inbound[ip] = properties

    def stop(self):
        """
        Signal to stop as cleanly as possible.
        """
        global app_log
        app_log.info("Trying to close nicely...")
        config.STOP_EVENT.set()
        loop = get_event_loop()
        loop.create_task(self.poschain.async_commit())
        loop.create_task(self.poschain.async_close())
        loop.create_task(self.mempool.async_close())
        loop.create_task(self.hn_db.async_close())
        loop.create_task(async_sleep(2))
        # wait for potential threads to finish
        try:
            pass
            # A long sleep time will make nice close longer if we wait for the thread to finish
            # Since it's a daemon thread, we can leave it alone
            # self.whatever_thread.join()
        except Exception as e:
            app_log.error("Closing {}".format(e))
        app_log.info("Bye!")
        sys.exit()

    async def do_test_peer(self, proto_block, peer_ip, peer_port):
        """
        Async. Send the test block to a given peer

        :param proto_block: a protobuf block
        :param peer_ip: the peer ip
        :param peer_port: the peer port
        :return: the answer from the peer
        """
        stream = None
        if self.verbose:
            app_log.info("Sending test request to {}:{}".format(peer_ip, peer_port))
        try:
            full_peer = poshelpers.ipport_to_fullpeer(peer_ip, peer_port)
            if self.interface:
                # If we specified a custom interface, we want to force listen on the associated ip.
                stream = await TCPClient().connect(
                    peer_ip, peer_port, timeout=5, source_ip=self.outip
                )
            else:
                stream = await TCPClient().connect(peer_ip, peer_port, timeout=5)
            await async_send_block(proto_block, stream, full_peer)
            res = await async_receive(stream, full_peer)
            return res
        except StreamClosedError:
            return None
        except Exception as e:
            app_log.warning(
                "Error '{}' sending test block to {}:{}".format(e, peer_ip, peer_port)
            )
        finally:
            try:
                if stream:
                    stream.close()
            except:
                pass

    async def run_test_peer(self, test):
        """
        Run a single test of a given peer, and store the result in a new transaction.
        TODO: check (local cache or chain) that this test was not already done.
        Edge case of a node that is restarted then does the tests again because it's still the same slot.
        Like a temp dir, with json of this round tests only. Keep a version in ram, and save to disk, so we can reload on start.

        :param test: tuple (from, recipient, test id)
        :return:
        """
        # ('BMSMNNzB9qdDp1vudRZoge4BUZ1gCUC3CV', 'BDs2Lc78KuWSB7CQj7aNaxJZLVBZV6hsTC', 4)
        app_log.warning("Running test {}".format(json.dumps(test)))
        # construct block
        protocmd = commands_pb2.Command()
        protocmd.Clear()
        protocmd.command = commands_pb2.Command.test
        # tx_values[0].txid, tx_values[0].block_height, tx_values[0].pubkey
        tx = protocmd.tx_values.add()
        tx.timestamp, tx.sender, tx.recipient = int(time()), test[0], test[1]
        tx.txid, tx.block_height, tx.pubkey = b"", 0, b""
        # 202 = A tests B - 203 = B reports being tested by A - 204 = failed test
        tx.what, tx.params, tx.value = 202, "TEST:{}".format(test[2]), 0
        # print(protocmd)
        # get ip, port from address
        peer = await self.hn_db.hn_from_address(test[1], self.round)
        # TODO: deal with NONE result
        future = self.do_test_peer(protocmd, peer["ip"], peer["port"])
        # send block
        try:
            result = await wait_for(future, 30)
        except TimeoutError as e:
            app_log.warning("Test Timeout")
            result = None
        except Exception as e:
            app_log.warning("Test Timeout")
            result = None
        if result:
            app_log.warning("Good test from {}".format(test[1]))
            await self._new_tx(test[1], 202, tx.params, result.tx_values[0].value)
        else:
            app_log.warning("Failed test from {}".format(test[1]))
            await self._new_tx(test[1], 204, tx.params, tx.timestamp)
        # print(result)
        # self.stop()
        # write result

    async def manager(self):
        """
        Async Manager co-routine. Responsible for managing inner state of the node.
        """
        global app_log
        global MINIMUM_CONNECTIVITY
        if self.verbose:
            app_log.info("Started HN Manager")
        # Initialise round/sir data
        await self.refresh_last_block()
        await self.check_round()
        await self._new_tx(
            recipient=self.address, what=202, params="START", value=self.round
        )
        next_status = time() + 30  # Force first status to be short after start.
        while not config.STOP_EVENT.is_set():
            try:
                # app_log.warning("loop 1")
                # updates our current view of the peers we are connected to and net global status/consensus
                await self._update_network()  # some runs showed quite some time in here for chain swaps.
                # app_log.warning("loop 2")
                if (
                    self.state == HNState.SYNCING
                    and self.forger == poscrypto.ADDRESS
                    and not self.forged
                ):
                    await self.change_state_to(HNState.STRONG_CONSENSUS)

                if (
                    self.state in (HNState.STRONG_CONSENSUS, HNState.MINIMAL_CONSENSUS)
                    and self.forger != poscrypto.ADDRESS
                ):
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
                if (
                    self.state == HNState.SYNCING
                    and self.net_height
                    and self.net_height["round"] > self.poschain.height_status.round
                ):
                    app_log.warning("We are late, catching up!")
                    # FR: set time to trigger CATCHING_UP_CONNECT2
                    await self.change_state_to(HNState.CATCHING_UP_CONNECT1)
                    # on "connect 1 phase, we wait to be connect to at least .. peers
                    # on connect2 phase, we add random peers other than our round peers to get enough
                    await self.change_state_to(HNState.CATCHING_UP_ELECT)
                    # FR: more magic here to be sure we got a good one - here, just pick one from the top chain.
                    self.sync_from = random.choice(self.net_height["peers"])
                    app_log.warning("Sync From {}".format(self.sync_from))
                    await self.change_state_to(HNState.CATCHING_UP_PRESYNC)
                if self.state == HNState.CATCHING_UP_PRESYNC:
                    # If we have no client worker, add one
                    if self.sync_from not in self.clients:
                        io_loop = IOLoop.instance()
                        with self.clients_lock:
                            # first index is active or not
                            self.clients[self.sync_from] = {
                                "stats": [False, 0, 0, 0, 0, 0, 0, 0, 0]
                            }
                        ip, port = self.sync_from.split(":")
                        io_loop.spawn_callback(self.client_worker, ("N/A", ip, port, 1))
                    # FR: add some timeout so we can retry another one if this one fails.
                    # FR: The given worker will be responsible for changing state on ok or failed status

                if self.state == HNState.STRONG_CONSENSUS:
                    if (
                        (self.consensus_pc > config.MIN_FORGE_CONSENSUS)
                        or (
                            len(self.peers_status) == 1
                            and self.consensus_pc > config.MIN_FORGE_CONSENSUS_LOW
                        )
                    ) and (not config.DO_NOT_FORGE):
                        mempool_status = await self.mempool.status()
                        if mempool_status["NB"] >= config.REQUIRED_MESSAGES_PER_BLOCK:
                            # Make sure we are at least 15 sec after round start, to let other nodes be synced.
                            if time() - self.current_round_start > 15:
                                await self.change_state_to(HNState.FORGING)
                                # Forge will send also
                                await self.forge()
                                # await async_sleep(10)
                                self.forged = True
                                await self.change_state_to(HNState.SYNCING)
                            else:
                                if self.verbose:
                                    app_log.info("My slot, but too soon to forge now.")
                        else:
                            if self.verbose:
                                app_log.info(
                                    "My slot, but too few tx in mempool to forge now."
                                )
                    else:
                        if self.verbose:
                            app_log.info(
                                "My slot, but too low a consensus to forge now."
                            )

                if (
                    self.state == HNState.SYNCING
                    and self.net_height
                    and len(self.tests_to_run)
                    and not self.testing
                ):
                    # time to run a test!
                    self.testing = True
                    try:
                        test = self.tests_to_run.pop(0)
                        await self.run_test_peer(test)
                    finally:
                        self.testing = False
                # app_log.warning("loop 3")
                # Do not display every round, cpu intensive
                if time() > next_status:
                    # print("loop status")
                    await self.status(log=True)
                    next_status = time() + config.STATUS_EVERY
                if self.connecting:
                    # TODO: if we are looking for consensus, then we will connect to
                    # every juror, not just our round peers, then disconnect once block submitted
                    if len(self.clients) < len(self.connect_to):
                        # Try to connect to our missing pre-selected peers
                        for peer in self.connect_to:
                            # [('aa012345678901aa', '127.0.0.1', 6969, 1)]
                            # tuples (address, ip, port, ?)
                            # ip_port = "{}:{}".format(peer[1], peer[2])
                            full_peer = poshelpers.peer_to_fullpeer(peer)
                            if full_peer not in self.clients:
                                io_loop = IOLoop.instance()
                                with self.clients_lock:
                                    # first index is active or not
                                    self.clients[full_peer] = {
                                        "stats": [False, 0, 0, 0, 0, 0, 0, 0, 0]
                                    }
                                io_loop.spawn_callback(self.client_worker, peer)
                # FR: variable sleep time depending on the elapsed loop time - or use timeout?
                await async_sleep(config.WAIT)
                # app_log.warning("loop CR")
                await self.check_round()

            except Exception as e:
                app_log.error("Error in manager {}".format(e))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                app_log.error(
                    "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
                )
        if self.verbose:
            app_log.info("Closed HN Manager")

    async def change_state_to(self, new_state):
        """
        Async. Sets new status and logs change.

        :param new_state:
        """
        self.state = new_state
        """
        if self.verbose:
            # too heavy, do not do it.
            print("change state status")
            await self.status(log=True)
        """

    async def _consensus(self):
        """
        Async. Returns the % of jurors we agree with

        :return: double
        """
        try:
            peers_status = {}
            our_status = await self.poschain.async_height()
            our_status = our_status.to_dict(as_hex=True)
            our_status["count"] = 1
            our_status["peers"] = []
            if self.verbose:
                app_log.info("Our status: {}".format(json.dumps(our_status)))
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
                    if peer["height_status"]["block_hash"] in peers_status:
                        peers_status[peer["height_status"]["block_hash"]]["count"] += 1
                        peers_status[peer["height_status"]["block_hash"]][
                            "peers"
                        ].append(ip)
                    else:
                        if peer["height_status"]["block_hash"] in [
                            "466cbd256fc248fd87f9aadedd8469afc8b4efa2"
                        ]:
                            app_log.warning(
                                "Peer {} banned hash {}".format(
                                    ip, peer["height_status"]["block_hash"]
                                )
                            )
                        else:
                            peers_status[peer["height_status"]["block_hash"]] = peer[
                                "height_status"
                            ].copy()
                            peers_status[peer["height_status"]["block_hash"]][
                                "count"
                            ] = 1
                            peers_status[peer["height_status"]["block_hash"]][
                                "peers"
                            ] = [ip]
                    if poshelpers.same_height(peer["height_status"], our_status):
                        # TODO: only if more verbose or debug.
                        """
                        if self.verbose:
                            app_log.info("Peer {} agrees".format(ip))
                        """
                        # TODO: only count if in our common.POC_HYPER_NODES_LIST list?
                        nb += 1
                    else:
                        pass
                        """
                        if self.verbose:
                            app_log.warning("Peer {} disagrees".format(ip))
                        """
                except:
                    pass
            for ip, peer in self.inbound.items():
                if ip not in self.clients:
                    try:
                        if peer["height_status"]["block_hash"] in peers_status:
                            peers_status[peer["height_status"]["block_hash"]][
                                "count"
                            ] += 1
                            peers_status[peer["height_status"]["block_hash"]][
                                "peers"
                            ].append(ip)
                        else:
                            peers_status[peer["height_status"]["block_hash"]] = peer[
                                "height_status"
                            ].copy()
                            peers_status[peer["height_status"]["block_hash"]][
                                "count"
                            ] = 1
                            peers_status[peer["height_status"]["block_hash"]][
                                "peers"
                            ] = [ip]
                        if poshelpers.same_height(peer["height_status"], our_status):
                            nb += 1
                            """
                            # Add to debug instead
                            if self.verbose:
                                app_log.info("Peer {} agrees".format(ip))
                            """
                        else:
                            pass
                            """
                            if self.verbose:
                                app_log.warning("Peer {} disagrees".format(ip))
                            """
                    except:
                        pass
            total = len(self.all_peers)
            pc = round(nb * 100 / total)
            app_log.info("Status: {} Peers do agree with us, {}%".format(nb, pc))
            peers_status = peers_status.values()
            peers_status = sorted(
                peers_status,
                key=itemgetter(
                    "forgers",
                    "uniques",
                    "round",
                    "height",
                    "forgers_round",
                    "uniques_round",
                    "block_hash",
                ),
                reverse=True,
            )
            # TEMP
            app_log.info("Status: {} observable chain(s)".format(len(peers_status)))
            if self.verbose:
                # app_log.info("> sorted peers status")
                i = 0
                for h in peers_status:
                    i += 1
                    """
                    {'height': 90140, 'round': 7650, 'sir': 15,
                     'block_hash': '327087ddc8c2cf3919141610b030ec0572cb5ea4', 'uniques': 397, 'uniques_round': 156,
                     'forgers': 352, 'forgers_round': 8, 'count': 5,
                     'peers': ['155.138.215.140:06969', '149.28.53.219:06969', '149.28.20.99:06969',
                               '94.23.120.129:06969', '46.105.170.153:06969']}
                    """
                    # print(" ", h)
                    app_log.info(
                        "{}. Height {} Round {} Sir {} - u/ur/f: {}/{}/{} - Count {}".format(
                            i,
                            h["height"],
                            h["round"],
                            h["sir"],
                            h["uniques"],
                            h["uniques_round"],
                            h["forgers"],
                            h["count"],
                        )
                    )
            try:
                with open("chains.json", "w") as fp:
                    json.dump(peers_status, fp, indent=2)
            except Exception as e:
                app_log.info("Error {} saving chains.json".format(e))

            self.peers_status = peers_status
            self.consensus_nb = nb
            self.consensus_pc = pc

        except Exception as e:
            app_log.error("_consensus: {}".format(str(e)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))
            sys.exit()

        try:
            if len(peers_status):
                # FR: more precise checks? Here we just take the most valued chain.
                # We should take number of peers at this height, too.
                # If too weak, use the next one.
                self.net_height = peers_status[0]
                if poshelpers.first_height_is_better(self.net_height, our_status):
                    if self.net_height["round"] == our_status["round"]:
                        best_peers = self.net_height["peers"]
                        app_log.warning(
                            'There is a better chain for our round on the net: "{}"'.format(
                                ",".join(best_peers)
                            )
                        )
                        if self.state in [
                            HNState.STRONG_CONSENSUS,
                            HNState.MINIMAL_CONSENSUS,
                            HNState.SYNCING,
                        ]:
                            app_log.info(
                                "State {} force round sync and check".format(self.state)
                            )
                            # TODO: can be lenghty or stuck. add timeout.
                            await self._round_sync(our_status["round"], self.net_height)
                        else:
                            app_log.warning(
                                "State is {}, ignoring for now.".format(self.state)
                            )
            else:
                self.net_height = None
        except Exception as e:
            app_log.error("Consensus error {}".format(e))
            self.net_height = None
        return pc

    async def get_heights(self):
        """
        Return dict of known peers heights.
        """
        try:
            heights = {
                key: value["height_status"]
                for key, value in self.clients.items()
                if "height_status" in value
            }
            # add inbound
            # TEMP
            print(">> in", self.inbound)
            for key, value in self.inbound.items():
                if key not in heights:
                    if "height_status" in value:
                        heights[key] = value["height_status"]
            return heights
        except Exception as e:
            app_log.error('get_heights error "{}"'.format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))
            sys.exit()

    async def get_hypernodes(self, param):
        """
        Return list of registered and active Hypernodes with metrics.

        param is an optional string param "full,start_round,end_round" where full is "0", "1" or "2".

        If full is set to "1", a dict is return instead of a list, with full metrics of each Hypernode for the given period.

        If full is set to "2", no round info is needed. A dict is returned instead of a list, with weight and active status up to end_round.

        :param param:
        :return:
        """
        if not param:
            return self.all_peers
        if param == "1":
            full = "1"
            start_round = self.round
            end_round = self.round
        elif param == "2":
            full = "2"
            start_round = 0
            end_round = self.round
        else:
            full, start_round, end_round = map(str.strip, param.split(","))
        app_log.info(
            "Registered Hypernodes, full {}, round {} to {}".format(
                full, start_round, end_round
            )
        )
        if full == "2":
            # We should remove from this list the ones that were inactive the round before.
            active_hns = await self.poschain.async_active_hns(int(end_round) - 1)
            all_peers = [item[0] for item in self.all_peers]
            inactive_hns = set(all_peers) - set(active_hns)
            hypernodes = await self.powchain.load_hn_pow(
                int(end_round), datadir=self.datadir, inactive_last_round=inactive_hns
            )
            return hypernodes

        # Get all HN who were valid for at least a round
        # from local DB and powchain.regs: show also inactive
        # TODO: these are only the HNs still reg for latest round, we should maybe be more cool
        hypernodes = {
            item[0]: {
                "ip": item[1],
                "port": item[2],
                "weight": item[3],
                "registrar": item[4],
                "recipient": item[5],
                "kpis": {},
            }
            for item in self.all_peers
        }
        if full == "1":
            app_log.info(
                "Computing HN KPIs for Round {} to {}".format(start_round, end_round)
            )
            # Find all the HN who sent a tx (or forged a block) for those rounds, and update their props
            actives = await self.poschain.async_active_hns_details(
                start_round, end_round
            )
            # Avoiding dict comprehension here since more will come later on.
            for hypernode in hypernodes:
                # TODO: success: ok tests. errors: ko tests. warnings: strange behavior logued
                # (needs confirmation by several peers)
                # rounds : # of rounds with activity, sources : # of tx for the period
                hypernodes[hypernode]["kpis"] = {
                    "success": 0,
                    "errors": 0,
                    "failed_pings": 0,
                    "ok_pings": 0,
                    "warnings": 0,
                    "rounds": 0,
                    "sources": 0,
                }
                if hypernode in actives:
                    hypernodes[hypernode]["kpis"] = {
                        key: value for key, value in actives[hypernode].items()
                    }
                    hypernodes[hypernode]["kpis"]["active"] = True
                else:
                    hypernodes[hypernode]["kpis"]["active"] = False

            # forgers = await self.poschain.async_forger_hns(start_round, end_round)

        return hypernodes

    async def _round_sync(self, a_round, promised_height):
        """
        Async. Tries to sync from a peer advertising a better chain than ours.
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
        peer = random.choice(promised_height["peers"])
        if self.verbose:
            app_log.info("_round_sync, {} peers".format(len(promised_height["peers"])))
        try:
            # Get the whole round data from that peer - We suppose it fits in memory
            if self.verbose:
                app_log.info("_get_round_blocks({}, {})".format(peer, a_round))
            # needs a timeout there
            start = time()
            the_blocks = await wait_for(
                self._get_round_blocks(peer, a_round), timeout=60
            )
            if not the_blocks:
                raise ValueError("Did not get blocks from {}".format(peer))
            else:
                if self.verbose:
                    app_log.info(
                        "_get_round_blocks done in {:0.2f} sec.".format(time() - start)
                    )
            # check the data fits and count sources/forgers
            simulated_target = await wait_for(
                self.poschain.check_round(a_round, the_blocks, fast_check=True),
                timeout=200,
            )
            # print("expected", promised_height)
            # print("simulated", simulated_target)
            # Check it matches the target,
            if poshelpers.heights_match(promised_height, simulated_target):
                """ TODO
                [E 180815 09:09:42 poshn:902] _round_sync error "'bool' object has no attribute 'get'"
                [E 180815 09:09:42 poshn:905] detail <class 'AttributeError'> poshn.py 880
                """
                if self.verbose:
                    app_log.info(
                        "Distant Round {} Data from {} fits expectations.".format(
                            a_round, peer
                        )
                    )
                # Delete the round to replace
                if self.verbose:
                    app_log.info("delete_round({})".format(a_round))
                await self.poschain.delete_round(a_round)
                # Force status update
                if self.verbose:
                    app_log.info("round sync 1 status")
                await self.poschain.status()
                # digest the blocks
                for block in the_blocks.block_value:
                    await self.poschain.digest_block(block, from_miner=False)
                # Force update again at end of sync.
                if self.verbose:
                    app_log.info("round sync 2 status")
                await self.status(log=False)
                # get PoS address from peer (it's a ip:0port string)
                hn = await self.hn_db.hn_from_peer(peer, self.round)
                await self._new_tx(
                    hn["address"],
                    what=200,
                    params="R.SYNC:{}".format(peer),
                    value=a_round,
                )
            else:
                app_log.warning(
                    "Distant Round {} Data from {} fails its promise.".format(
                        a_round, peer
                    )
                )
                # get PoS address from peer (it's a ip:0port string)
                hn = await self.hn_db.hn_from_peer(peer, self.round)
                await self._new_tx(
                    hn["address"],
                    what=101,
                    params="P.FAIL:{}".format(peer),
                    value=a_round,
                )
                # FR: Add to buffer instead of sending right away (avoid tx spam)
        except TimeoutError:
            app_log.warning("_round_sync timeout")
        except ValueError as e:  # innocuous error, will retry.
            app_log.warning('_round_sync error "{}"'.format(e))
        except Exception as e:
            app_log.error('_round_sync error "{}"'.format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))
        finally:
            # Set previous state again
            await self.change_state_to(self.saved_state)
            return res

    async def _new_tx(self, recipient="", what=0, params="", value=0):
        """
        Insert a new TX (message) in the local mempool

        :param recipient:
        :param what:
        :param params:
        :param value:
        :return:
        """
        tx = posblock.PosMessage().from_values(
            recipient=recipient, what=what, params=params, value=value
        )
        # from_values(self, timestamp=0, sender='', recipient='', what=0, params='', value=0, pubkey=None):
        try:
            tx.sign()
            # print(tx.to_json())
            await self.mempool.digest_tx(tx, self.poschain)
        except Exception as e:
            app_log.error('_new_tx error "{}"'.format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))

    async def _get_round_blocks(self, peer, a_round):
        """
        Async. Request full blocks from a full (or partial) round from a given peer.

        :param peer:
        :param a_round:
        :return: list of blocks
        """
        try:
            # FR: Do we have a stream to this peer? if yes, use it instead of creating a new one ?
            # means add to self.clients
            """
            if self.verbose:  # already loggued 1 level above.
                app_log.info("get_round_blocks({}, {})".format(peer, a_round))
            """
            ip, port = peer.split(":")
            stream = await self._get_peer_stream(ip, int(port), temp=True)
            # request the info
            if stream:
                await com_helpers.async_send_int32(
                    commands_pb2.Command.roundblocks, a_round, stream, peer
                )
                blocks = await com_helpers.async_receive(stream, peer)
                try:
                    stream.close()
                except Exception as e:
                    app_log.error(
                        '_get_round_blocks error closing stream "{}"'.format(e)
                    )
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    app_log.error(
                        "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
                    )
                return blocks
            else:
                app_log.warning("Couldn't get temp stream from {}'.format(peer))")
                return None
        except Exception as e:
            app_log.error('_get_round_blocks error "{}"'.format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))
            return None

    async def refresh_last_block(self):
        """
        Async. Fetch fresh info from the PoS chain.
        Update the inner properties.
        """
        last_block = await self.poschain.last_block()
        self.last_height, self.previous_hash = (
            last_block["height"],
            last_block["block_hash"],
        )
        self.last_round, self.last_sir = last_block["round"], last_block["sir"]

    async def digest_txs(self, txs, peer_ip):
        """
        Async. Checks tx and digest if they are new.

        :param txs:
        :param peer_ip:
        :return:
        """
        # Takes some time digesting 100 tx. And can be digesting from several peers at the same time.
        # Hold digesting from a peer if we are already digesting from another one?
        # Also, can merge both from client and server side, same host!!!
        """
        # Commented out for testing, see if current naive mempool can handle.
        if self.state not in (HNState.SYNCING, HNState.ROUND_SYNC, HNState.STRONG_CONSENSUS, HNState.MINIMAL_CONSENSUS):
            # We are catching up or otherwise busy, do not digest txs?
            # TODO: we will miss txs, since nodes will not resend them. Add a command to tell "send them all" when going into sync state.
            app_log.info("Ignoring tx sync from {}".format(peer_ip))
            return
        """
        if not len(txs):
            return
        if len(txs) > 200:
            if self.verbose and "mempool" in config.LOG:
                app_log.info(
                    "Too many ({}) txs to sync from {}, ignoring ".format(
                        len(txs), peer_ip
                    )
                )
            return
        if peer_ip == self.mempool_digesting:
            if self.verbose and "mempool" in config.LOG:
                app_log.info("Ignoring redundant sync from {}".format(peer_ip))
            return
        while self.mempool_digesting:
            if self.verbose and "mempool" in config.LOG:
                app_log.info("Waiting to sync {} txs from {}".format(len(txs), peer_ip))
            await async_sleep(config.WAIT)
        try:
            start = time()
            self.mempool_digesting = peer_ip
            if self.verbose and "mempool" in config.LOG:
                app_log.info("Got {} tx(s) from {}".format(len(txs), peer_ip))
            nb = 0
            total = 0
            # TODO: batch-test and insert
            for tx in txs:
                # Will raise if error digesting, return false if already present in mempool or chain
                if await self.mempool.digest_tx(tx, poschain=self.poschain):
                    nb += 1
                total += 1
            if nb > 0:
                app_log.info("Digested {}/{} tx(s) from {} in {:0.2} sec.".format(nb, total, peer_ip, time() - start))
        except KeyboardInterrupt:
            raise
        except Exception as e:
            app_log.warning("Error {} digesting tx".format(e))
        finally:
            self.mempool_digesting = ""

    async def digest_height(self, height_proto, full_peer, server=False):
        """
        Async. Update inner properties with distant peer height info.

        :param height_proto: protobuff structure
        :param full_peer:
        :param server: comes from the server (inbound) or client (outbound) side?
        """
        try:
            height = posblock.PosHeight().from_proto(height_proto)
            if server:
                self.inbound[full_peer]["height_status"] = height.to_dict(as_hex=True)
            else:
                # Client
                self.clients[full_peer]["height_status"] = height.to_dict(as_hex=True)
        except KeyError as e:
            app_log.error("Key Error {} digest_height".format(e))
        except Exception as e:
            app_log.error("Error {} digest_height".format(e))

    async def post_block(self, proto_block, peer_ip, peer_port):
        """
        Async. Send the block we forged to a given peer
        Should we use threads instead and a simpler tcp client? Perfs to be tested.

        :param proto_block: a protobuf block
        :param peer_ip: the peer ip
        :param peer_port: the peer port
        """
        stream = None
        if self.verbose:
            app_log.info("Sending block to {}:{}".format(peer_ip, peer_port))
        try:
            full_peer = poshelpers.ipport_to_fullpeer(peer_ip, peer_port)
            # FR: Are context managers possible here? would lighten the finally step
            if self.interface:
                stream = await TCPClient().connect(
                    peer_ip, peer_port, timeout=5, source_ip=self.outip
                )
            else:
                stream = await TCPClient().connect(peer_ip, peer_port, timeout=5)
            await async_send_block(proto_block, stream, full_peer)
        except Exception as e:
            app_log.warning(
                "Error '{}' sending block to {}:{}".format(e, peer_ip, peer_port)
            )
        finally:
            if stream:
                stream.close()

    async def forge(self):
        """
        Async. Consensus has been reached, we are forger, forge and send block.
        """
        try:
            await self.refresh_last_block()
            # check last round and SIR, make sure they are >
            if self.round <= self.last_round and self.sir <= self.last_sir:
                raise ValueError("We already have this round/SIR in our chain.")
            if not self.forger == poscrypto.ADDRESS:
                # Should never pass here.
                raise ValueError("We are not the forger for current round!!!")
            block_dict = {
                "height": self.last_height + 1,
                "round": self.round,
                "sir": self.sir,
                "timestamp": int(time()),
                "previous_hash": self.previous_hash,
                "forger": self.address,
                "received_by": "",
            }
            if self.verbose:
                app_log.info(
                    "Forging block {} Round {} SIR {}".format(
                        self.last_height + 1, self.round, self.sir
                    )
                )
            block = posblock.PosBlock().from_dict(block_dict)
            # txs are native objects
            block.txs = await self.mempool.async_all(self.last_height + 1)
            if not len(block.txs):
                # not enough TX, won't pass in prod
                # raise ValueError("No TX to embed, block won't be valid.")
                app_log.error("No TX to embed, block won't be valid.")
            # TODO: count also uniques_sources
            # Remove from mempool
            await self.mempool.clear()
            # print(block.to_dict())
            block.sign()
            # print(block.to_dict())
            # FR: Shall we pass that one through "digest" to make sure?
            # await self.poschain._insert_block(block)
            block = block.to_proto()
            await self.poschain.digest_block(
                block, from_miner=True, relaxed_checks=True
            )
            await self.change_state_to(HNState.SENDING)
            # Send the block to our peers (unless we were unable to insert it in our db)
            """if self.verbose:
                print("proto", block)
            """
            app_log.info("Block Forged, I will send it")
            self.forged_count += 1
            # build the list of jurors to send to. Exclude ourselves.
            to_send = [
                self.post_block(block, peer[1], peer[2])
                for peer in self.all_peers
                if not (peer[1] == self.outip and int(peer[2]) == self.port)
            ]
            try:
                await asyncio_wait(to_send, timeout=45)
            except Exception as e:
                app_log.error("Timeout sending block: {}".format(e))
            # print(block.__str__())
            return True
        except Exception as e:
            app_log.error("Error forging: {}".format(e))
            return False

    def hello_string(self, temp=False):
        """
        Builds up the hello string.
        common.POSNET + str(port).zfill(5) + self.address

        :param temp: True - For one shot commands, from an already connected ip, uses a fake 00000 port as self id.
        :return: string
        """
        # FR: use lru cache decorator to cache both values of the string without re-validating the address each time.
        if temp:
            port = 0
        else:
            port = self.port
        return poshelpers.hello_string(port=port, address=self.address)
        # return config.POSNET + str(port).zfill(5) + self.address

    async def _get_peer_stream(self, ip, port, temp=True):
        """
        Async. Return a stream with communication already established.
        Stream has to be closed after use.

        :param ip: 127.0.0.1
        :param port: 6969
        :param temp: True - For temps commands, uses a fake 00000 port as self id.
        :return: IOStream
        """
        global LTIMEOUT
        full_peer = poshelpers.ipport_to_fullpeer(ip, port)
        try:
            # FR: dup code, use that in the client_worker co-routine?
            if self.verbose:
                access_log.info("Initiating client connection to {}".format(full_peer))
            # ip_port = "{}:{}".format(peer[1], peer[2])
            if self.interface:
                stream = await TCPClient().connect(
                    ip, port, timeout=LTIMEOUT, source_ip=self.outip
                )
            else:
                stream = await TCPClient().connect(ip, port, timeout=LTIMEOUT)
            # connect_time = time()
            await com_helpers.async_send_string(
                commands_pb2.Command.hello,
                self.hello_string(temp=temp),
                stream,
                full_peer,
            )
            msg = await com_helpers.async_receive(stream, full_peer)
            if self.verbose:
                access_log.info(
                    "Client got {}".format(com_helpers.cmd_to_text(msg.command))
                )
            if msg.command == commands_pb2.Command.hello:
                # decompose posnet/address and check.
                access_log.info(
                    "Client got Hello {} from {}".format(msg.string_value, full_peer)
                )
                # self.clients[full_peer]['hello'] = msg.string_value  # nott here, it's out of the client biz
            if msg.command == commands_pb2.Command.ko:
                access_log.info("Client got Ko {}".format(msg.string_value))
                return
            # now we can enter a long term relationship with this node.
            return stream
        except tornado.iostream.StreamClosedError as e:
            if self.verbose and "connections" in config.LOG:
                app_log.info(
                    "Connection lost to {} because {}. No retry.".format(full_peer, e)
                )
        except Exception as e:
            app_log.error(
                "Connection lost to {} because {}. No Retry.".format(full_peer, e)
            )
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))

    async def client_worker(self, peer):
        """
        Async. Client worker, running in a co-routine.
        Tries to connect to the given peer, terminates on error and deletes itself on close.

        :param peer: ('aa012345678901aa', '127.0.0.1', 6969, 1)
        """
        full_peer = poshelpers.peer_to_fullpeer(peer)
        stream = None
        retry = True
        try:
            if self.verbose and "connections" in config.LOG:
                access_log.info("Initiating client co-routine for {}".format(full_peer))
            # ip_port = "{}:{}".format(peer[1], peer[2])
            if self.interface:
                stream = await TCPClient().connect(
                    peer[1], peer[2], timeout=LTIMEOUT, source_ip=self.outip
                )
            else:
                stream = await TCPClient().connect(peer[1], peer[2], timeout=LTIMEOUT)
            connect_time = time()
            await com_helpers.async_send_string(
                commands_pb2.Command.hello, self.hello_string(), stream, full_peer
            )
            msg = await com_helpers.async_receive(stream, full_peer)
            if self.verbose and "workermsg" in config.LOG:
                access_log.info(
                    "Worker got {}".format(com_helpers.cmd_to_text(msg.command))
                )
            if msg.command == commands_pb2.Command.hello:
                # decompose posnet/address and check.
                access_log.info(
                    "Worker got Hello {} from {}".format(msg.string_value, full_peer)
                )
                self.clients[full_peer]["hello"] = msg.string_value
            if msg.command == commands_pb2.Command.ko:
                access_log.info("Worker got Ko {}".format(msg.string_value))
                return
            # now we can enter a long term relationship with this node.
            with self.clients_lock:
                # Set connected status
                self.clients[full_peer]["stats"][com_helpers.STATS_ACTIVEP] = True
                self.clients[full_peer]["stats"][
                    com_helpers.STATS_COSINCE
                ] = connect_time
            while not config.STOP_EVENT.is_set():
                if peer not in self.connect_to and self.state in [HNState.SYNCING]:
                    retry = False
                    raise ValueError("Closing for this round")
                if (
                    self.state
                    in (HNState.CATCHING_UP_PRESYNC, HNState.CATCHING_UP_SYNC)
                    and self.sync_from == full_peer
                ):
                    # Faster sync
                    app_log.info(">> Entering presync with {}".format(full_peer))
                    await async_sleep(config.SHORT_WAIT)
                    if self.state == HNState.CATCHING_UP_PRESYNC:
                        # Here, we check if our last block matches the peer's one.
                        # If not, we rollback one block at a time until we agree.
                        await com_helpers.async_send_int32(
                            commands_pb2.Command.blockinfo,
                            self.poschain.height_status.height,
                            stream,
                            full_peer,
                        )
                        msg = await com_helpers.async_receive(stream, full_peer)
                        # TODO: check message is blockinfo
                        info = posblock.PosHeight().from_proto(msg.height_value)
                        if self.verbose:  # FR: to remove later on
                            if self.poschain.height_status:
                                print(
                                    "self",
                                    self.poschain.height_status.to_dict(as_hex=True),
                                )
                            print("peer", info.to_dict(as_hex=True))
                        if (
                            self.poschain.height_status.block_hash == info.block_hash
                            and self.poschain.height_status.round == info.round
                        ):
                            # we are ok, move to next state
                            await self.change_state_to(HNState.CATCHING_UP_SYNC)
                            app_log.info(
                                ">> Common ancestor OK with {}, CATCHING MISSED BLOCKS".format(
                                    full_peer
                                )
                            )
                        else:
                            app_log.info(">> Block mismatch, will rollback")
                            # FR: find the common ancestor faster via height/hash list
                            while (
                                self.poschain.height_status.block_hash
                                != info.block_hash
                            ):
                                # TODO: limit possible rollback to a few heights, like 1 or 2 rounds worth of blocks.
                                if self.verbose:  # FR: remove later on
                                    print(
                                        "self",
                                        self.poschain.height_status.to_dict(
                                            as_hex=True
                                        ),
                                    )
                                    print("peer", info.to_dict(as_hex=True))
                                if self.poschain.height_status.height == 0:
                                    app_log.warning(">> Won't rollback block 0")
                                    # TODO: temp ban (store on disk)
                                    # TODO: send warning tx
                                    # allow to sync again from another one
                                    await self.change_state_to(HNState.SYNCING)
                                    # close
                                    return
                                await self.poschain.rollback()
                                await com_helpers.async_send_int32(
                                    commands_pb2.Command.blockinfo,
                                    self.poschain.height_status.height,
                                    stream,
                                    full_peer,
                                )
                                msg = await com_helpers.async_receive(stream, full_peer)
                                #  TODO: check message is blockinfo
                                info = posblock.PosHeight().from_proto(msg.height_value)
                                # await async_sleep(5)
                            app_log.info(
                                ">> Should have rolled back to {} level.".format(
                                    full_peer
                                )
                            )
                            # config.STOP_EVENT.set()
                            # sys.exit()

                    if self.state == HNState.CATCHING_UP_SYNC:
                        # We are on a compatible branch, lets get the missing blocks until we are sync.
                        # The peer will send as many blocks as he wants, and sends empty when it's over.
                        failed = False
                        # warning: we use a property that can be None instead of the method.
                        if self.net_height:
                            while (
                                self.net_height["height"]
                                > self.poschain.height_status.height
                            ):
                                try:
                                    await com_helpers.async_send_int32(
                                        commands_pb2.Command.blocksync,
                                        self.poschain.height_status.height + 1,
                                        stream,
                                        full_peer,
                                    )
                                    # TODO: Add some timeout not to be stuck if the peer does not answer.
                                    # TODO: or at least, go out of this sync mode if the sync peer closes.
                                    msg = await com_helpers.async_receive(
                                        stream, full_peer
                                    )
                                    if not msg.block_value:
                                        app_log.info(
                                            "No more blocks from {}".format(full_peer)
                                        )
                                        # Exit or we are stuck
                                        break
                                    else:
                                        blocks_count = 0
                                        for block in msg.block_value:
                                            if await self.poschain.digest_block(
                                                block, from_miner=False
                                            ):
                                                blocks_count += 1
                                            else:
                                                break  # no need to go on
                                        app_log.info(
                                            "Saved {}/{} blocks from {}".format(
                                                blocks_count,
                                                len(msg.block_value),
                                                full_peer,
                                            )
                                        )
                                        await self.poschain.async_commit()  # Should not be necessary
                                        if not blocks_count:
                                            app_log.error(
                                                "Error while inserting block from {}".format(
                                                    full_peer
                                                )
                                            )
                                            failed = True
                                            break
                                        if blocks_count < len(msg.block_value):
                                            app_log.error(
                                                "Error while inserting block from {}".format(
                                                    full_peer
                                                )
                                            )
                                            failed = True
                                            break
                                except Exception as e:
                                    app_log.error(
                                        "Connection to {} lost while CATCHING_UP_SYNC {}".format(
                                            peer[1], e
                                        )
                                    )
                                    failed = True
                                    break
                        try:
                            hn = await self.hn_db.hn_from_peer(full_peer, self.round)
                            if failed:
                                await self._new_tx(
                                    hn["address"],
                                    what=101,
                                    params="C.FAIL:{}".format(full_peer),
                                    value=self.round,
                                )
                                app_log.warning(
                                    ">> Net Synced failed via {}".format(full_peer)
                                )
                            else:
                                await self._new_tx(
                                    hn["address"],
                                    what=200,
                                    params="C.SYNC:{}".format(full_peer),
                                    value=self.round,
                                )
                                app_log.info(">> Net Synced via {}".format(full_peer))

                            # Trigger re-eval of peers and such (do that as blocks come?)
                            app_log.info("Re computing round info")
                            self.previous_round = 0  # Force re calc
                            await self.check_round()
                        finally:
                            await self.change_state_to(HNState.SYNCING)
                else:
                    await async_sleep(config.WAIT)
                    now = time()
                    if self.state not in (
                        HNState.STRONG_CONSENSUS,
                        HNState.MINIMAL_CONSENSUS,
                        HNState.CATCHING_UP_PRESYNC,
                        HNState.CATCHING_UP_SYNC,
                    ):
                        # If we are trying to reach consensus, don't ask for mempool sync so often.
                        # Peers may send anyway.
                        height_delay = 10
                        mempool_delay = 30
                    else:
                        # Not looking for consensus, but send our height every now and then to stay sync
                        height_delay = 30
                        mempool_delay = 20
                    if (
                        self.clients[full_peer]["stats"][com_helpers.STATS_LASTMPL]
                        < now - mempool_delay
                    ):
                        # Send our new tx from mempool if any, will get the new from peers.
                        if await self.mempool.tx_count():
                            #  Just don't waste bandwith if our mempool is empty.
                            await self._exchange_mempool(stream, full_peer)
                    if self.state not in (
                        HNState.CATCHING_UP_PRESYNC,
                        HNState.CATCHING_UP_SYNC,
                    ):
                        if (
                            self.clients[full_peer]["stats"][com_helpers.STATS_LASTHGT]
                            < now - height_delay
                        ):
                            # Time to send our last block info to the peer, he will answer back with his
                            await self._exchange_height(stream, full_peer)

                    # Only send ping if time is due.
                    if (
                        self.clients[full_peer]["stats"][com_helpers.STATS_LASTACT]
                        < now - config.PING_DELAY
                    ):
                        if self.verbose:
                            app_log.info("Sending ping to {}".format(full_peer))
                        # keeps connection active, or raise error if connection lost
                        await com_helpers.async_send_void(
                            commands_pb2.Command.ping, stream, full_peer
                        )
            retry = False
            raise ValueError("Closing")
        except (tornado.iostream.StreamClosedError, tornado.util.TimeoutError) as e:
            if self.verbose and "connections" in config.LOG:
                if retry:
                    app_log.warning(
                        "Connection lost to {} because {}. Retry in {} sec.".format(
                            peer[1], e, config.PEER_RETRY_SECONDS
                        )
                    )
                else:
                    app_log.warning(
                        "Connection lost to {} because {}. No Retry.".format(peer[1], e)
                    )
                    return
        except Exception as e:
            if retry:
                # TODO: You can do better
                if str(e) not in ["'NoneType' object has no attribute 'command'"]:
                    app_log.warning(
                        "Connection lost to {} because {}. Retry in {} sec.".format(
                            peer[1], e, config.PEER_RETRY_SECONDS
                        )
                    )
                else:
                    app_log.error(
                        "Connection lost to {} because {}. Retry in {} sec.".format(
                            peer[1], e, config.PEER_RETRY_SECONDS
                        )
                    )
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    app_log.error(
                        "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
                    )
            else:
                app_log.error("Connection lost to {} because {}.".format(peer[1], e))
                return
            try:
                stream.close()
            except:
                pass
            #  Wait here so we don't retry immediately
            await async_sleep(config.PEER_RETRY_SECONDS)
        finally:
            if stream:
                try:
                    stream.close()
                except:
                    pass
            try:
                with self.clients_lock:
                    # We could keep it and set to inactive, but is it useful? could grow too much
                    del self.clients[full_peer]
            except:
                pass

    async def _exchange_height(self, stream, full_peer):
        """
        Async. Send our height info to a peer, and process his in return.

        :param stream:
        :param full_peer:
        """
        # FR: do not send if our height did not change since the last time. Will spare net resources.
        if self.verbose and "workermsg" in config.LOG:
            app_log.info("Sending height to {}".format(full_peer))
        height = await self.poschain.async_height()
        self.clients[full_peer]["stats"][com_helpers.STATS_LASTHGT] = time()
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
        """
        Async. Send our mempool to a peer, and process his in return.

        :param stream:
        :param full_peer:
        """
        last = int(self.clients[full_peer]["stats"][com_helpers.STATS_LASTMPL])
        txs = await self.mempool.async_since(last)
        if self.verbose and "mempool" in config.LOG:
            app_log.info(
                "Worker sending {} txs from mempool to {}, ts={}".format(
                    len(txs), full_peer, last
                )
            )
        self.clients[full_peer]["stats"][com_helpers.STATS_LASTMPL] = time()
        await com_helpers.async_send_txs(
            commands_pb2.Command.mempool, txs, stream, full_peer
        )
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
        Async. Adjust peers and network properties, calc _consensus()
        Always called from the manager co-routine only.
        """
        try:
            inbound_count = len(self.inbound)
            clients_count = 0
            # Improve: use another list to avoid counting one by one?
            for who, client in self.clients.items():
                # Don't count the same peer twice
                if who not in self.inbound:
                    # Only count the ones we are effectively connected to
                    if client["stats"][com_helpers.STATS_ACTIVEP]:
                        clients_count += 1
            self.connected_count = inbound_count + clients_count
            # update our view of the network state
            await self._consensus()
        except Exception as e:
            app_log.error("_update_network: {}".format(str(e)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))
            raise

    #  TODO: refactor, this is confusing, there is a check_round for poshn, and one for poschain. Same name, but different function.
    async def check_round(self):
        """
        Async. Adjust round/slots depending properties.
        Always called from the manager co-routine only.
        Should not be called too often (1-10sec should be plenty)
        """
        self.round, self.sir = determine.timestamp_to_round_slot(time())
        if self.verbose:
            app_log.info("...check_round... R {} SIR {}".format(self.round, self.sir))
        while self.state in [HNState.NEWROUND]:
            # do not re-enter if new round ongoing
            await async_sleep(1)
        if (self.sir != self.previous_sir) or (self.round != self.previous_round):
            with self.round_lock:
                # If we forged the last block, forget.
                self.forged = False
                # Update all sir related info
                if self.verbose:
                    app_log.info(
                        ">> New Slot {} in Round {}".format(self.sir, self.round)
                    )
                self.tests_to_run = []
                self.tests_to_answer = []
                if self.round != self.previous_round:
                    await self.change_state_to(HNState.NEWROUND)
                    # let it sink
                    await async_sleep(0.2)
                    # Make sure the PoW node is working and synced.
                    await self.powchain.wait_synced()
                    # Update all round related info, we get here only once at the beginning of a new round
                    await self.refresh_last_block()
                    if self.verbose:
                        app_log.warning("New Round {}".format(self.round))
                    # Update possible new working vars
                    config.update_colored()
                    # Empty test list so we don't go over round boundaries if there were pending tests.
                    self.test_slots = []
                    self.no_test_this_round = False
                    self.no_test_sent = 0
                    # Update the HN list - First query the inactive HN for just finished round.
                    if (
                        len(self.all_peers) == 0
                        or self.all_peers == config.POC_HYPER_NODES_LIST
                    ):
                        # first run, let get it right
                        await self.powchain.load_hn_pow(
                            datadir=self.datadir,
                            inactive_last_round=[],
                            a_round=self.round,
                        )
                        if not self.powchain.regs:
                            app_log.error("Unable to load HN Regs")
                            sys.exit()
                        self.all_peers = [
                            (
                                items["pos"],
                                items["ip"],
                                items["port"],
                                items["weight"],
                                address,
                                items["reward"],
                            )
                            for address, items in self.powchain.regs.items()
                        ]
                    # print("all_peers", self.all_peers)
                    # sys.exit()
                    all_hns = set(
                        [peer[0] for peer in self.all_peers]
                    )  # This is wrong (empty at start, just 5)
                    active_hns = set(
                        await self.poschain.async_active_hns(self.round - 1)
                    )
                    self.round_meta["round"], self.round_meta["sir"] = (
                        self.round,
                        self.sir,
                    )
                    self.round_meta["all_hns_count"] = len(all_hns)
                    self.round_meta["all_hns_hash"] = sha256(
                        str(all_hns).encode("utf-8")
                    ).hexdigest()
                    inactive_hns = all_hns - active_hns
                    self.round_meta["inactive_hns_count"] = len(inactive_hns)
                    self.round_meta["inactive_hns_hash"] = sha256(
                        str(inactive_hns).encode("utf-8")
                    ).hexdigest()
                    # Fail safe to avoid disabling everyone on edge cases or attack scenarios
                    if len(active_hns) < config.MIN_ACTIVE_HNS:
                        # Also covers for recovering if previous round had no block because of low consensus.
                        inactive_hns = []
                        app_log.warning(
                            "Ignoring inactive HNs since there are not enough active ones."
                        )
                    # TODO: the flow is wrong. We end up doing 2 requests first time.
                    # Better ask once with no inactive, and filter out inactive ones before going on.
                    await self.powchain.load_hn_pow(
                        datadir=self.datadir,
                        inactive_last_round=list(inactive_hns),
                        a_round=self.round,
                    )
                    if not self.powchain.regs:
                        self.stop()
                    self.active_regs = [
                        items
                        for items in self.powchain.regs.values()
                        if items["active"]
                    ]
                    if self.verbose:
                        app_log.info(
                            "Status: {} registered HN, among which {} are active".format(
                                len(self.powchain.regs), len(self.active_regs)
                            )
                        )
                    with open("powreg.json", "w") as fp:
                        data = {
                            "round": self.round,
                            "inactive_last_round": list(inactive_hns),
                            "regs": self.powchain.regs,
                            "active_regs": self.active_regs,
                        }
                        json.dump(data, fp, indent=2)
                    self.round_meta["powchain_regs_count"] = len(self.powchain.regs)
                    self.round_meta["powchain_regs"] = sha256(
                        str(self.powchain.regs).encode("utf-8")
                    ).hexdigest()
                    self.round_meta["active_regs_count"] = len(self.active_regs)
                    self.round_meta["active_regs"] = sha256(
                        str(self.active_regs).encode("utf-8")
                    ).hexdigest()

                    # Now save these infos in the hn db
                    await self.hn_db.clear_rounds_before(
                        self.round - 2
                    )  # keep 2 old rounds for what it costs.
                    await self.hn_db.save_hn_from_regs(self.powchain.regs, self.round)

                    # FR: Should be some refactoring to do in all these mess of various structures.
                    # Recreate self.peers.
                    # list of ('BLYkQwGZmwjsh7DY6HmuNBpTbqoRqX14ne', '127.0.0.1', 6969, 1, "bis_addr_0", "bis_addr_0")
                    # for address, items in self.powchain.regs.items():
                    self.active_peers = [
                        (
                            items["pos"],
                            items["ip"],
                            items["port"],
                            items["weight"],
                            address,
                            items["reward"],
                        )
                        for address, items in self.powchain.regs.items()
                        if items["active"]
                    ]
                    self.all_peers = [
                        (
                            items["pos"],
                            items["ip"],
                            items["port"],
                            items["weight"],
                            address,
                            items["reward"],
                        )
                        for address, items in self.powchain.regs.items()
                    ]
                    self.registered_ips = [
                        items["ip"] for items in self.powchain.regs.values()
                    ]
                    self.current_round_start = int(time())
                    self.previous_round = self.round
                    # We try to connect to inactive peers anyway, or they have less chances of coming back.
                    self.connect_to = await determine.get_connect_to(
                        self.all_peers, self.round, self.address
                    )
                    # but tickets are only for previously active
                    tickets = await determine.hn_list_to_tickets(self.active_peers)
                    self.slots = await determine.tickets_to_jurors(
                        tickets, self.previous_hash
                    )
                    if self.verbose:
                        app_log.info("Slots {}".format(json.dumps(self.slots)))
                    self.round_meta["slots"] = sha256(
                        str(self.slots).encode("utf-8")
                    ).hexdigest()

                    # We also test inactive peers, or it would be biased against good nodes.
                    self.test_slots = await determine.hn_list_to_test_slots(
                        self.all_peers, self.slots
                    )
                    with open("slots.json", "w") as fp:
                        data = {
                            "round": self.round,
                            "slots": self.slots,
                            "tests": self.test_slots,
                        }
                        json.dump(data, fp, indent=2)
                    # Are we to play this round?
                    self.no_test_this_round = True
                    for a_slot_info in self.test_slots:
                        for a_test in a_slot_info:
                            if self.address in a_test:
                                # we have at least one test
                                self.no_test_this_round = False
                                break
                    if self.verbose and "determine" in config.LOG:
                        app_log.info(
                            "Tests Slots {} - No test this round={}".format(
                                json.dumps(self.test_slots), self.no_test_this_round
                            )
                        )
                    if self.no_test_this_round:
                        app_log.warning("No test this round {}".format(self.round))
                    # TODO: save this round info to db
                    # TODO: clean up old info from round db
                    await self.change_state_to(HNState.SYNCING)
                    # END NEW ROUND

                # We changed SIR, change tests for slots
                self.previous_sir = self.sir
                if self.sir < len(self.test_slots):
                    self.tests_to_run = [
                        test
                        for test in self.test_slots[self.sir]
                        if test[0] == self.address
                    ]
                    self.tests_to_answer = [
                        [
                            test
                            for test in self.test_slots[self.sir]
                            if test[1] == self.address
                        ]
                    ]

                if self.verbose:
                    app_log.info(
                        "Tests to run slot {}: {}".format(
                            self.sir, json.dumps(self.tests_to_run)
                        )
                    )
                    app_log.info(
                        "Tests to answer slot {}: {}".format(
                            self.sir, json.dumps(self.tests_to_answer)
                        )
                    )

                if self.sir < len(self.slots):
                    self.forger = self.slots[self.sir][0]
                    if self.verbose:
                        app_log.info("Forger is {}".format(self.forger))
                else:
                    self.forger = None

                # purge old tx
                await self.mempool.async_purge()

                if (
                    self.no_test_this_round
                    and (self.sir == 0)
                    and (self.no_test_sent == 0)
                ):
                    await async_sleep(5)
                    # FR: param is optional, all could go into 'what' to spare bandwith
                    self.no_test_sent += 1
                    await self._new_tx(
                        recipient=self.address,
                        what=201,
                        params="NO_TEST:1",
                        value=self.round,
                    )
                if (
                    self.no_test_this_round
                    and (
                        self.sir == config.MAX_ROUND_SLOTS + config.END_ROUND_SLOTS - 1
                    )
                    and (self.no_test_sent == 1)
                ):
                    self.no_test_sent += 1
                    await self._new_tx(
                        recipient=self.address,
                        what=201,
                        params="NO_TEST:2",
                        value=self.round,
                    )
                    # self.run_test(self.address, self.address, 0 )

    def serve(self):
        """
        Run the Tornado socket server.
        Once we called that, the calling thread is stopped until the server closes.
        """
        loop = get_event_loop()
        if config.DEBUG:
            loop.set_debug(True)

        try:
            loop.run_until_complete(self.init_check())
        except Exception as e:
            app_log.error("Serve Init: {}".format(str(e)))
            return
        if self.verbose:
            print("Initial status")
            loop.run_until_complete(self.status(log=True))
        try:
            server = HnServer()
            server.verbose = self.verbose
            server.mempool = self.mempool
            server.node = self
            # server.listen(port)
            server.bind(self.port, backlog=128, address=self.ip, reuse_port=REUSE_PORT)
            server.start(1)  # Forks multiple sub-processes
            if self.verbose:
                app_log.info(
                    "Starting server on tcp://localhost:{} , reuse_port={}".format(
                        self.port, REUSE_PORT
                    )
                )
            io_loop = IOLoop.instance()
            io_loop.spawn_callback(self.manager)
            """
            if self.verbose:
                EventLoopDelayMonitor(interval=1, loop=io_loop, logger=app_log)
            """
            self.connect()
            try:
                io_loop.start()
            except KeyboardInterrupt:
                config.STOP_EVENT.set()
                loop = get_event_loop()
                loop.run_until_complete(self.mempool.async_close())
                io_loop.stop()
                app_log.info("Serve: exited cleanly")
        except Exception as e:
            app_log.error("Serve: {}".format(str(e)))

    def connect(self, connect=True):
        """
        Set the "Shall I try to connect?" flag

        :param connect:
        """
        self.connecting = connect
        # Will be handled by the manager.

    async def init_check(self):
        """
        Initial coherence check. Raise on non coherent info.
        # FR: more checks

        """
        app_log.info("Initial mempool coherence check")
        # TODO: This is not needed since it's not persistent atm.
        try:
            # Now test coherence and mempool
            await self.mempool.async_purge()
            await self.mempool.async_purge_start(self.address)
            mem_txs = await self.mempool.async_alltxids()
            txs = []
            for tx in mem_txs:
                if await self.poschain.tx_exists(tx):
                    if "txdigest" in config.LOG:
                        app_log.info(
                            "Tx {} in our chain, removing from mempool".format(tx)
                        )
                    txs.append(tx)
            if len(txs):
                await self.mempool.async_del_txids(txs)
                app_log.info(
                    "removed {} tx(s) from mempool, were in our chain already.".format(
                        len(txs)
                    )
                )
            app_log.info(
                "Initial round check {} sir {} - Previous {} sir {}".format(
                    self.round, self.sir, self.last_round, self.last_sir
                )
            )
            await self.refresh_last_block()
            await self.check_round()
        except Exception as e:
            app_log.error("Coherence Check: {}".format(str(e)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            app_log.error("detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno))
            raise

    async def round_status(self) -> dict:
        """
        Async. Assemble and store the current round status as a dict.

        :return: Round Status info
        """
        status = {
            "start": self.current_round_start,
            "previous": self.previous_round,
            "connect_to": self.connect_to,
            "slots": self.slots,
            "test_slots": self.test_slots,
        }
        return status

    async def status(self, log: bool = True) -> dict:
        """
        Async. Assemble and store the node status as a dict.

        :return: HN Status info
        """
        poschain_status = await self.poschain.status()
        mempool_status = await self.mempool.status()
        extra = {"forged_count": self.forged_count}
        if self.process:
            of = len(self.process.open_files())
            fd = self.process.num_fds()
            co = len(self.process.connections(kind="tcp4"))
            extra["open_files"], extra["connections"], extra["num_fd"] = of, co, fd
            app_log.info(
                "Status: {} Open files, {} connections, {} FD used. Inbound {}, Outbound {}"
                " - Forged {} since start.".format(
                    of, co, fd, len(self.inbound), len(self.clients), self.forged_count
                )
            )
        pending_tasks = [task._coro for task in Task.all_tasks() if not task.done()]
        pending_tasks_names = [
            getattr(
                coro, "__qualname__", getattr(coro, "__name__", type(coro).__name__)
            )
            for coro in pending_tasks
        ]
        # print(pending_tasks_names)  # TODO: group by coro name
        tasks_detail = {
            task: pending_tasks_names.count(task) for task in set(pending_tasks_names)
        }
        # print([*map(asyncio.Task.print_stack, asyncio.Task.all_tasks())])
        # print(frequency)
        # pow = {"node_version": get_pow_node_version()}
        pow = get_pow_status()
        status = {
            "config": {
                "address": self.address,
                "ip": self.ip,
                "port": self.port,
                "verbose": self.verbose,
                "outip": self.outip,
            },
            "instance": {
                "version": self.client_version,
                "hn_version": __version__,
                "statustime": int(time()),
            },
            "chain": poschain_status,
            "mempool": mempool_status,
            "peers": {
                "connected_count": self.connected_count,
                "outbound": list(self.clients.keys()),
                "inbound": list(self.inbound.keys()),
                "net_height": self.net_height,
            },
            "state": {
                "state": self.state.name,
                "round": self.round,
                "sir": self.sir,
                "forger": self.forger,
            },
            "tasks": {"total": len(pending_tasks), "detail": tasks_detail},
            "extra": extra,
            "meta": self.round_meta,
            "pow": pow,
        }
        if self.process:
            status["PID"] = self.process.pid
        # 'peers': self.peers
        if self.address not in [peer[0] for peer in self.all_peers]:
            self.not_reg = True
            app_log.warning(
                "Status: This Hypernode is not registered nor activated yet."
            )
        else:
            self.not_reg = False
        if log:
            app_log.info("Status: {}".format(json.dumps(status)))
        if "connections" in config.LOG:
            for con in self.process.connections(kind="tcp4"):
                app_log.info(
                    "!C local {} rem {} state {}".format(
                        con.laddr, con.raddr, con.status
                    )
                )
        self.my_status = status
        try:
            with open("posstatus.json", "w") as fp:
                json.dump(status, fp, indent=2)
        except Exception as e:
            app_log.warning("Error {} saving pos status".format(e))
        return self.my_status
