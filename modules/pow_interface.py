"""
Helpers and classes to interface with the main Bismuth PoW chain

"""

import asyncio
import ipaddress
import json
import math
import os
import re
import sqlite3
import sys
import time
from math import floor
from os import path
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.iostream import StreamClosedError
from base64 import b85encode
from hashlib import md5
from typing import Union

# Our modules
import config
import poscrypto
import poshelpers
import testvectors
from fakelog import FakeLog
from sqlitebase import SqliteBase
from determine import timestamp_to_round_slot
from polysign.signerfactory import SignerFactory
from powasyncclient import PoWAsyncClient


__version__ = "0.2.1"

"""
SQL_BLOCK_HEIGHT_PRECEDING_TS_SLOW = (
    "SELECT block_height FROM transactions WHERE timestamp <= ? "
    "ORDER BY block_height DESC limit 1"
)

SQL_BLOCK_HEIGHT_PRECEDING_TS = (
    "SELECT max(block_height) FROM transactions WHERE timestamp <= ? AND reward > 0"
)

SQL_TS_OF_BLOCK = (
    "SELECT timestamp FROM transactions WHERE reward > 0 AND block_height = ?"
)

SQL_REGS_FROM_TO = (
    "SELECT block_height, address, operation, openfield, timestamp FROM transactions "
    "WHERE (operation='hypernode:register' OR operation='hypernode:unregister') "
    "AND block_height >= ? AND block_height <= ? "
    "ORDER BY block_height ASC"
)

SQL_QUICK_BALANCE_CREDITS = "SELECT sum(amount+reward) FROM transactions WHERE recipient = ? AND block_height <= ?"

SQL_QUICK_BALANCE_DEBITS = (
    "SELECT sum(amount+fee) FROM transactions WHERE address = ? AND block_height <= ?"
)

SQL_QUICK_BALANCE_ALL = (
    "SELECT sum(a.amount+a.reward)-debit FROM transactions as a , "
    "(SELECT sum(b.amount+b.fee) as debit FROM transactions b "
    "WHERE address = ? AND block_height <= ?) "
    "WHERE a.recipient = ? AND a.block_height <= ?"
)

SQL_QUICK_BALANCE_ALL_MIRROR = (
    "SELECT sum(a.amount+a.reward)-debit FROM transactions as a , "
    "(SELECT sum(b.amount+b.fee) as debit FROM transactions b "
    "WHERE address = ? AND abs(block_height) <= ?) "
    "WHERE a.recipient = ? AND abs(a.block_height) <= ?"
)

SQL_LAST_BLOCK_TS = (
    "SELECT timestamp FROM transactions WHERE block_height = "
    "(SELECT max(block_height) FROM transactions)"
)
"""

# ================== Helpers ================


def validate_pow_address(address: str) -> Union[None, bool]:
    """
    Validate a bis (PoW address).

    :param address:
    :return: True if address is valid, raise a ValueError exception if not.
    """
    # TODO!: To evolve with more addresses
    # if re.match("[abcdef0123456789]{56}", address):
    if SignerFactory.address_is_valid(address):
        return True
    raise ValueError("Bis Address format error: {}".format(address))


def checksum(string: str) -> str:
    """ Base 64 checksum of MD5. Used by bisurl"""
    m = md5()
    m.update(string.encode("utf-8"))
    return b85encode(m.digest()).decode("utf-8")


def create_bis_url(recipient: str, amount: str, operation: str, openfield: str) -> str:
    """
    Constructs a bis url from tx elements
    """
    # Only command supported so far.
    command = "pay"
    openfield_b85_encode = b85encode(openfield.encode("utf-8")).decode("utf-8")
    operation_b85_encode = b85encode(operation.encode("utf-8")).decode("utf-8")
    url_partial = "bis://{}/{}/{}/{}/{}/".format(
        command, recipient, amount, operation_b85_encode, openfield_b85_encode
    )
    url_constructed = url_partial + checksum(url_partial)
    return url_constructed


def read_node_version_from_file(filename):
    for line in open(filename):
        if "VERSION" in line:
            # VERSION = "4.2.6"  # .03 - more hooks again
            return (
                line.split("=")[-1]
                .split("#")[0]
                .replace('"', "")
                .replace("'", "")
                .strip()
            )
    return None


def get_pow_node_version():
    """
    Returns PoW node version
    """
    # creates dir if need to be
    node_filename = path.abspath(
        config.POW_LEDGER_DB.replace("static/", "").replace("ledger.db", "node.py")
    )
    node_version = read_node_version_from_file(node_filename)
    return node_version


def get_pow_status():
    """
    Returns full json status from pow node - Requires 0.0.62+ companion plugin
    """
    status_filename = path.abspath(
        config.POW_LEDGER_DB.replace("static/", "").replace(
            "ledger.db", "powstatus.json"
        )
    )
    try:
        with open(status_filename, "r") as f:
            status = json.load(f)
        return status
    except Exception as e:
        return {"Error": str(e)}


# ================== Classes ================


class PowInterface:
    def __init__(
        self, app_log=None, verbose: bool = None, distinct_process: bool = False
    ):
        """
        Interface to the PoW chain.

        :param app_log:
        :param verbose:
        :param distinct_process: If True, does not connect directly to the db,
        but calls - async - an external process with timeout.
        """
        if not app_log:
            app_log = FakeLog()
        self.app_log = app_log
        self.verbose = config.VERBOSE if verbose is None else verbose
        self.distinct_process = distinct_process
        self.regs = {}

    async def wait_synced(self):
        """
        Waits until the PoW chain is synced.
        """
        if self.verbose:
            self.app_log.info("Checking PoW sync state...")
        synced = False
        while not synced:
            try:
                pow = PoWAsyncClient(config.POW_IP, config.POW_PORT, self.app_log)
                res = await pow.async_command("HN_last_block_ts")
                pow.close()
                last_ts = res
            except:
                last_ts = -1
            delay_min = (time.time() - last_ts) / 60
            if self.verbose:
                self.app_log.info(
                    "Last TS: {}, {:0.2f} min.".format(last_ts, delay_min)
                )
            # Up to 15 min late is ok (rollback, hard block)
            synced = delay_min < 15
            if not synced:
                self.app_log.warning(
                    "Last block {:0.2f} mins in the past, waiting 30 sec for PoW sync.".format(
                        delay_min
                    )
                )
                await asyncio.sleep(30)


    async def load_hn_same_process_old(
        self,
        a_round: int=0,
        datadir: str="",
        inactive_last_round=None,
        force_all: bool=False,
        no_cache: bool=False,
        ignore_config: bool=False,
        ip: str="",
        balance_check: bool=False,
        collateral_dropped=None,
    ):
        try:
            if a_round:
                round_ts = config.ORIGIN_OF_TIME + a_round * config.ROUND_TIME_SEC
            else:
                round_ts = int(time.time())
            pow_cache_file_name = "{}/powhncache.json".format(datadir)
            # FR: Check the pow chain is up to date?
            # beware, we can't print what we want, output is read as json.
            # latest_ts =  await self.pow_chain.async_get_last_ts()
            # Current height, or height at begin of the new round.
            height = await self.pow_chain.async_get_block_before_ts(round_ts)
            # print("after height", time.time())
            # Now take back 30 blocks to account for possible large rollbacks
            height -= 30
            # And round to previous multiple of 60
            height = 60 * floor(height / 60)
            if force_all:
                height = 8000000
            if self.verbose:
                self.app_log.info("Same Process, ref height={}".format(height))
            # FR: this should be part of the bootstrap archive
            if os.path.isfile(pow_cache_file_name) and not no_cache:
                self.app_log.info("powhncache exists in {}".format(datadir))
                # load this checkpoint and go on since there.
                # take latest checkpoint anyway, even if we wanted an older one? means we can't verify a posteriori
                # unless we store per round in DB (do it)
                with open(pow_cache_file_name, "r") as f:
                    # Save before we filter out inactive
                    cache = json.load(f)
                    self.regs = cache["HNs"]
                checkpoint = 773800  # TODO: adjust from cache file
            else:
                if self.verbose:
                    self.app_log.info("no powhncache in {}".format(datadir))
                # Start from scratch and reconstruct current state from history
                self.regs = {}
                checkpoint = 773800  # No Hypernode tx earlier

            if self.verbose:
                self.app_log.info(
                    "Parsing reg messages from {} to {}, {} inactive HNs.".format(
                        checkpoint + 1, height, len(inactive_last_round)
                    )
                )
            """
            if config.LOAD_HN_FROM_POW or force_all or ignore_config:
                # TEMP
                if self.verbose:
                    self.app_log.info(
                        "Running {} {} {}".format(
                            SQL_REGS_FROM_TO, checkpoint + 1, height
                        )
                    )
                #  print("c1", time.time())
                cursor = await self.pow_chain.async_fetchall(
                    SQL_REGS_FROM_TO, (checkpoint + 1, height)
                )
                # print("c2", time.time())
            else:
                if False:
                    # Temp DEV test
                    cursor = testvectors.POW_HN_CURSOR
                else:
                    self.regs = poshelpers.fake_hn_dict(
                        inactive_last_round, self.app_log
                    )
                    return self.regs
            """
            # Temp
            if self.verbose:
                self.app_log.info("Parsing reg info...")
            #for row in cursor:
            if True:  # fake for temp. compile
                block_height, address, operation, openfield, timestamp = row
                # TEMP
                valid = True
                show = False
                try:
                    if ip and "{}:".format(ip) in openfield:
                        show = True
                        self.app_log.info(
                            "Row {}: {}, {}, {}".format(
                                block_height, address, operation, openfield
                            )
                        )
                    hip, port, pos, reward = self.reg_extract(openfield, address)
                    if operation == "hypernode:register":
                        # There is a small hack here: the following tests seem to do nothing, but they DO
                        # raise an exception if there is a dup. Allow for single line faster test.
                        # since list comprehension is heavily optimized.
                        # invalid ip
                        ipaddress.ip_address(hip)
                        # invalid bis addresses
                        validate_pow_address(address)
                        validate_pow_address(reward)
                        # invalid pos address
                        poscrypto.validate_address(pos)
                        # Dup ip?
                        [1 / 0 for items in self.regs.values() if items["ip"] == hip]
                        # Dup pos address?
                        [1 / 0 for items in self.regs.values() if items["pos"] == pos]
                        # Dup pow address?
                        if address in self.regs:
                            raise ValueError("Already an active registration")
                        # Requires a db query, runs last - Will raise if not enough.
                        # print("w1", time.time())
                        weight = await self.reg_check_balance(address, block_height)
                        # print("w2", time.time())
                        active = True  # by default
                        # inactive last round will no longer get a ticket.
                        # When computing reward, they will not be counted for the round.
                        # if config.COMPUTING_REWARD or a_round >= config.NEXT_HF_AT_ROUND:
                        if pos in inactive_last_round:
                            active = False
                        self.regs[address] = dict(
                            zip(
                                [
                                    "ip",
                                    "port",
                                    "pos",
                                    "reward",
                                    "weight",
                                    "timestamp",
                                    "active",
                                ],
                                [
                                    str(hip),
                                    port,
                                    str(pos),
                                    str(reward),
                                    weight,
                                    timestamp,
                                    active,
                                ],
                            )
                        )
                        if show:
                            self.app_log.info("Ok, Weight={}".format(weight))
                    else:
                        pass
                        # It's an unreg
                        if address in self.regs:
                            # unreg from owner
                            if (hip, port, pos) == (
                                self.regs[address]["ip"],
                                self.regs[address]["port"],
                                self.regs[address]["pos"],
                            ):
                                # same info
                                del self.regs[address]
                            else:
                                raise ValueError("Invalid unregistration params")

                        elif address == config.POW_CONTROL_ADDRESS:
                            self.regs = {
                                key: items
                                for key, items in self.regs.items()
                                if (items["ip"], items["port"], items["pos"])
                                != (hip, port, pos)
                            }
                            if show:
                                self.app_log.warning(
                                    "Unreg by controller, reason '{}'.".format(
                                        self.extract_reason(openfield)
                                    )
                                )
                        else:
                            raise ValueError("Invalid un-registration sender")
                        if show:
                            self.app_log.info("Ok")


                except (ValueError, ZeroDivisionError) as e:
                    # print(e)
                    valid = False
                    if show:
                        self.app_log.warning("Ko: {}".format(e))
                    pass
                """
                if self.verbose:
                    self.app_log.info("{}".format(valid))
                """
            if self.verbose:
                # self.app_log.info("{} PoW Valid HN :{}".format(len(self.regs), json.dumps(self.regs)))
                if self.regs:
                    self.app_log.info("{} PoW Valid HN.".format(len(self.regs)))
                else:
                    self.app_log.warning("No PoW Valid HN.")

            # TODO this part to port over below.
            if balance_check:
                # recheck all balances
                self.app_log.warning(
                    "Balance check required for PoW height {}".format(height)
                )
                bad_balance = []
                for pow_address, detail in self.regs.items():
                    # print(pow_address, detail)
                    """
                    {'ip': '51.15.95.155', 'port': '6969', 'pos': 'BLYkQwGZmwjsh7DY6HmuNBpTbqoRqX14ne',
                     'reward': '8f2d03c817c3d36a864c99a27f6b6179eb1898a631bc007a7e0ffa39', 'weight': 3,
                     'timestamp': 1534711530.06, 'active': True}
                    """
                    weight = await self.reg_check_balance(pow_address, height)
                    if weight < detail["weight"]:
                        # Can be more, can't be less.
                        self.app_log.warning(
                            "PoW address {}, weight {} instead of {} - removing from list.".format(
                                pow_address, weight, detail["weight"]
                            )
                        )
                        if type(collateral_dropped) == list:
                            collateral_dropped.append(
                                {
                                    "pow": pow_address,
                                    "ip": detail["ip"],
                                    "port": detail["port"],
                                    "pos": detail["pos"],
                                    "weight": weight,
                                    "registered_weight": detail["weight"],
                                }
                            )
                        # Remove from the list.
                        # self.regs.pop(pow_address, None)
                        self.regs[pow_address]["active"] = False
                        bad_balance.append(pow_address)
                # now remove the balance cheaters
                for pow_address in bad_balance:
                    self.regs.pop(pow_address, None)

        except Exception as e:
            self.app_log.error("load_hn_same_process Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            sys.exit()

    async def stream_subprocess_old(self, cmd, timeout=1):
        """

        :param cmd:
        :param timeout:
        :return:
        """
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            p = await asyncio.wait_for(process.wait(), timeout)
        except Exception:
            p = None
        if not (p is None):
            if p == 0:
                out = await process.stdout.read()
                out = out.decode("utf8")
                return out
            """
            print("p", p)  # return code (0 if ok)
            print("stdout:", (await process.stdout.read()).decode('utf8'))
            print("stderr:", (await process.stderr.read()).decode('utf8'))
            """
        return "false"

    async def load_hn_distinct_process_old(
        self,
        a_round: int = 0,
        datadir: str = "",
        inactive_last_round=None,
        force_all: bool = False,
        no_cache: bool = False,
        ignore_config: bool = False,
        ip="",
        balance_check=False,
        collateral_dropped=None,
    ):
        """
        Load from async sqlite3 connection from an external process with timeout.

        :param a_round:
        :param datadir:
        :param inactive_last_round:
        :param force_all:
        :param no_cache:
        :param ignore_config:
        :param ip:
        :param balance_check: Force balance check for all HN at the end of the call
        :return:
        """
        if collateral_dropped:
            print("collateral_dropped only valid for same process query")
        try:
            extra = "-b" if balance_check else ""
            if ip:
                cmd = [
                    config.PYTHON_EXECUTABLE,
                    "hn_reg_feed.py --ip={} {}".format(ip, extra),
                ]
                if a_round > 0:
                    cmd = [
                        config.PYTHON_EXECUTABLE,
                        "hn_reg_feed.py",
                        "-r {} --ip={} {}".format(a_round, ip, extra),
                    ]
                res = await self.stream_subprocess(cmd, timeout=config.PROCESS_TIMEOUT)
                print(res)
                self.regs = {}
                return
            else:
                cmd = [config.PYTHON_EXECUTABLE, "hn_reg_feed.py"]
                if a_round > 0:
                    cmd = [
                        config.PYTHON_EXECUTABLE,
                        "hn_reg_feed.py",
                        "-r {}".format(a_round),
                    ]
                self.regs = json.loads(
                    await self.stream_subprocess(cmd, timeout=config.PROCESS_TIMEOUT)
                )
            if self.verbose:
                count = 0
                if self.regs:
                    count = len(self.regs)
                # self.app_log.info("{} PoW Valid HN :{}".format(count, json.dumps(self.regs)))
                self.app_log.info("{} PoW Valid HN".format(count))
        except Exception as e:
            self.app_log.error("load_hn_distinct_process Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            sys.exit()

    async def load_hn_remote_url_old(
        self,
        a_round: int = 0,
        datadir: str = "",
        inactive_last_round=None,
        force_all: bool = False,
        no_cache: bool = False,
        ignore_config: bool = False,
        ip="",
        balance_check=False,
        url="",
    ):
        """
        Load from an external url. Fallback for weak nodes that can't properly handle sqlite db sharing across processes.

        :param a_round:
        :param datadir:
        :param inactive_last_round:
        :param force_all:
        :param no_cache:
        :param ignore_config:
        :param ip:
        :param balance_check: Force balance check for all HN at the end of the call
        :param url the base url to fetch json from
        :return:
        """
        if balance_check:
            self.app_log.error("load_hn_remote_url Error, can't do balance check.")
            sys.exit()
        if ip:
            self.app_log.error("load_hn_remote_url Error, can't do ip.")
            sys.exit()
        if a_round <= 0:
            a_round, a_slot = timestamp_to_round_slot(time.time())
        try:
            a_round = str(a_round)
            # self.app_log.info("load_hn_remote_url around {}".format(a_round))
            http_client = AsyncHTTPClient()
            try:
                full_url = "{}{}/{}/{}.json".format(
                    url, a_round[0], a_round[1], a_round
                )
                self.app_log.info("load_hn_remote_url {}".format(full_url))
                response = await http_client.fetch(full_url)
                self.regs = json.loads(response.body.decode("utf-8"))
                self.app_log.info("load_hn_remote_urlok")
            except HTTPError as e:
                # HTTPError is raised for non-200 responses; the response
                # can be found in e.response.
                self.app_log.error("load_hn_remote_url http Error {}".format(str(e)))
                self.regs = False
            except Exception as e:
                # Other errors are possible, such as IOError.
                self.app_log.error("load_hn_remote_url other Error {}".format(str(e)))
                self.regs = False
            # http_client.close()  # unneeded for async
            if self.verbose:
                count = 0
                if self.regs:
                    count = len(self.regs)
                # self.app_log.info("{} PoW Valid HN :{}".format(count, json.dumps(self.regs)))
                self.app_log.info("{} PoW Valid HN".format(count))
        except Exception as e:
            self.app_log.error("load_hn_remote_url Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            sys.exit()

    async def load_hn_pow(
        self,
        a_round: int=0,
        datadir: str="",
        inactive_last_round=None,
        force_all: bool=False,
        no_cache: bool=False,
        ignore_config: bool=False,
        distinct_process=None,
        ip: str = "",
        balance_check: bool=False,
        collateral_dropped=None,
    ):
        """
        Async Get HN from the pow. Called at launch (a_round=0) then at each new round.

        :param a_round:
        :param datadir:
        :param inactive_last_round: list of pos_address that did not sent any tx previous round, to drop from list.
        :param force_all:
        :param no_cache:
        :param ignore_config:
        :param distinct_process:
        :param ip:
        :param balance_check: Force balance check for all HN at the end of the call
        """
        if ip == "":
            ip = False

        if self.verbose:
            self.app_log.info("load_hn_pow, round {}".format(a_round))
        try:

            if not inactive_last_round:
                inactive_last_round = []

            """
            await self.load_hn_same_process(
                a_round,
                inactive_last_round=inactive_last_round,
                datadir=datadir,
                force_all=force_all,
                ignore_config=ignore_config,
                ip=ip,
                balance_check=balance_check,
                collateral_dropped=collateral_dropped,
            )
            """
            pow_height = 0
            if force_all:
                pow_height = 8000000
            if a_round <= 0:
                a_round, a_slot = timestamp_to_round_slot(time.time())
            timestamp = config.ORIGIN_OF_TIME + a_round * config.ROUND_TIME_SEC
            pow = PoWAsyncClient(config.POW_IP, config.POW_PORT, self.app_log)
            # TODO: try more ?
            try:
                res = await pow.async_command("HN_reg_round {} {} {} {}".format(a_round, timestamp, pow_height, ip),
                                              timeout=60)
            except (StreamClosedError, TimeoutError):
                await pow.close()
                self.app_log.warning("pow connect failed, try 2")
                await asyncio.sleep(2)
                try:
                    res = await pow.async_command("HN_reg_round {} {} {} {}".format(a_round, timestamp, pow_height, ip),
                                                  timeout=60)
                except (StreamClosedError, TimeoutError):
                    await pow.close()
                    self.app_log.warning("pow connect failed, try 3")
                    await asyncio.sleep(5)
                    res = await pow.async_command("HN_reg_round {} {} {} {}".format(a_round, timestamp, pow_height, ip),
                                                  timeout=60)
            if ip:
                return res['ip_feed']

            self.regs = res['regs']
            if balance_check:
                # TODO
                self.app_log.warning("I should handle balance checks")
            if collateral_dropped:
                # TODO
                self.app_log.warning("I should handle collateral dropped")

            pow.close()
            # Here we have self.regs

            # Now, if round > 0, set active state depending on last round activity
            if self.regs:
                for address, items in self.regs.items():
                    if items["pos"] in inactive_last_round:
                        self.regs[address]["active"] = False
            if self.verbose:
                if self.regs:
                    # self.app_log.info("PoW+PoS Valid HN :{}".format(json.dumps(self.regs)))
                    self.app_log.info("{} PoW+PoS Valid HN.".format(len(self.regs)))
                else:
                    self.app_log.warning("No PoW+PoS Valid HN. Try restarting.")
            # sys.exit()
            # TODO: save in local DB for this round
            return self.regs
        except Exception as e:
            self.app_log.error("load_hn_pow Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            sys.exit()

