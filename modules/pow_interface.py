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

# Our modules
import config
import poscrypto
import poshelpers
import testvectors
from fakelog import FakeLog
from sqlitebase import SqliteBase
from determine import timestamp_to_round_slot

__version__ = '0.1.8'


SQL_BLOCK_HEIGHT_PRECEDING_TS_SLOW = 'SELECT block_height FROM transactions WHERE timestamp <= ? ' \
                                'ORDER BY block_height DESC limit 1'

SQL_BLOCK_HEIGHT_PRECEDING_TS = 'SELECT max(block_height) FROM transactions WHERE timestamp <= ? AND reward > 0'

SQL_TS_OF_BLOCK = 'SELECT timestamp FROM transactions WHERE reward > 0 AND block_height = ?'

SQL_REGS_FROM_TO = "SELECT block_height, address, operation, openfield, timestamp FROM transactions " \
                   "WHERE (operation='hypernode:register' OR operation='hypernode:unregister') " \
                   "AND block_height >= ? AND block_height <= ? " \
                   "ORDER BY block_height ASC"

SQL_QUICK_BALANCE_CREDITS = "SELECT sum(amount+reward) FROM transactions WHERE recipient = ? AND block_height <= ?"

SQL_QUICK_BALANCE_DEBITS = "SELECT sum(amount+fee) FROM transactions WHERE address = ? AND block_height <= ?"

SQL_QUICK_BALANCE_ALL = "SELECT sum(a.amount+a.reward)-debit FROM transactions as a , " \
                        "(SELECT sum(b.amount+b.fee) as debit FROM transactions b " \
                        "WHERE address = ? AND block_height <= ?) " \
                        "WHERE a.recipient = ? AND a.block_height <= ?"

SQL_QUICK_BALANCE_ALL_MIRROR = "SELECT sum(a.amount+a.reward)-debit FROM transactions as a , " \
                        "(SELECT sum(b.amount+b.fee) as debit FROM transactions b " \
                        "WHERE address = ? AND abs(block_height) <= ?) " \
                        "WHERE a.recipient = ? AND abs(a.block_height) <= ?"

SQL_LAST_BLOCK_TS = "SELECT timestamp FROM transactions WHERE block_height = " \
                    "(SELECT max(block_height) FROM transactions)"


# ================== Helpers ================


def validate_pow_address(address: str):
    """
    Validate a bis (PoW address).

    :param address:
    :return: True if address is valid, raise a ValueError exception if not.
    """
    if re.match('[abcdef0123456789]{56}', address):
        return True
    raise ValueError('Bis Address format error')


def read_node_version_from_file(filename):
    for line in open(filename):
        if "VERSION" in line:
            # VERSION = "4.2.6"  # .03 - more hooks again
            return line.split("=")[-1].split("#")[0].replace('"', '').replace("'", '').strip()
    return None


def get_pow_node_version():
    """
    Returns PoW node version
    """
    # creates dir if need to be
    node_filename = path.abspath(config.POW_LEDGER_DB.replace('static/', '').replace('ledger.db', 'node.py'))
    node_version = read_node_version_from_file(node_filename)
    return node_version


def get_pow_status():
    """
    Returns full json status from pow node - Requires 0.0.62+ companion plugin
    """
    status_filename = path.abspath(config.POW_LEDGER_DB.replace('static/', '').replace('ledger.db', 'powstatus.json'))
    try:
        with open(status_filename, 'r') as f:
            status = json.load(f)
        return status
    except Exception as e:
        return {"Error": str(e)}


# ================== Classes ================

class PowInterface:

    def __init__(self, app_log=None, verbose: bool=None, distinct_process: bool=False):
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
        """
        registered HN from PoW. Can be temp. wrong when updating. Calling object must keep a cached working version. 
        Indexed by pow address.
        """
        self.pow_chain = SqlitePowChain(db_path=config.POW_LEDGER_DB, verbose=self.verbose, app_log=app_log)

    async def wait_synced(self):
        """
        Waits until the PoW chain is synced.
        """
        if self.verbose:
            self.app_log.info("Checking PoW sync state...")
        synced = False
        while not synced:
            try:
                res = await self.pow_chain.async_fetchone(SQL_LAST_BLOCK_TS)
                last_ts = res[0]
            except:
                last_ts = -1
            delay_min = (time.time() - last_ts) / 60
            if self.verbose:
                self.app_log.info("Last TS: {}, {:0.2f} min.".format(last_ts, delay_min))
            # Up to 15 min late is ok (rollback, hard block)
            synced = (delay_min < 15 )
            if not synced:
                self.app_log.warning("Last block {:0.2f} mins in the past, waiting for PoW sync.".format(delay_min))
                await asyncio.sleep(30)

    async def reg_check_balance(self, address, height):
        """
        Calc rough estimate (not up to 1e-8) of the balance of an account at a certain point in the past.
        Raise if not enough for an HN, or return the matching Weight.

        Requires a full ledger.

        :param address:
        :param height:
        :return: weight (1, 2 or 3)
        """
        # TODO
        # TODO: check that there was no temporary out tx during the last round that lead to an inferior weight.
        # needs previous round boundaries. Can use an approx method to be faster.

        # credits = await self.pow_chain.async_fetchone(SQL_QUICK_BALANCE_CREDITS, (address, height))
        # debits = await self.pow_chain.async_fetchone(SQL_QUICK_BALANCE_DEBITS, (address, height))
        # balance = credits[0] - debits[0]
        res = await self.pow_chain.async_fetchone(SQL_QUICK_BALANCE_ALL, (address, height, address, height))
        balance = res[0]
        weight = math.floor(balance/10000)
        if weight > 3:
            weight = 3
        # print(credits[0], debits[0], balance, weight)
        return weight

    def quick_check_balance(self, address, height):
        """
        Calc rough estimate (not up to 1e-8) of the balance of an account at a certain point in the past.
        return the matching balance

        Requires a full ledger.

        :param address:
        :param height: pow block (inclusive)
        :return: balance
        """
        # TODO
        # TODO: check that there was no temporary out tx during the last round that lead to an inferior weight.
        # needs previous round boundaries. Can use an approx method to be faster.

        res = self.pow_chain.fetchone(SQL_QUICK_BALANCE_ALL_MIRROR, (address, height, address, height))
        balance = res[0]
        return balance

    def reg_extract(self, openfield, address):
        """
        Extract data from openfield. 'ip:port:pos' or with option 'ip2:port:pos2,reward=bis2a'

        :param openfield: str
        :param address: str
        :return: tuple (ip, port, pos, reward)
        """
        options = {}
        if ',' in openfield:
            # Only allow for 1 extra param at a time. No need for more now, but beware if we add!
            parts = openfield.split(',')
            openfield = parts.pop(0)
            for extra in parts:
                key, value = extra.split('=')
                options[key] = value
        ip, port, pos = openfield.split(':')
        reward = options['reward'] if 'reward' in options else address
        source = options['source'] if 'source' in options else None
        if source and source != address:
            raise ValueError("Bad source address")
        return ip, port, pos, reward

    def extract_reason(self, openfield):
        """
        Extract optional reason data from openfield.

        :param openfield: str
        :return: str
        """
        if ',' in openfield:
            # Only allow for 1 extra param at a time. No need for more now, but beware if we add!
            parts = openfield.split(',')
            parts.pop(0)
            for extra in parts:
                key, value = extra.split('=')
                if key == 'reason':
                    return value
        return ''

    async def load_hn_same_process(self, a_round: int=0, datadir: str='', inactive_last_round=None,
                                   force_all: bool=False, no_cache: bool=False, ignore_config: bool=False,
                                   ip: str='', balance_check: bool=False):
        """
        Load from async sqlite3 connection from the same process.
        Been experienced an can hang the whole HN on busy nodes.

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
                with open(pow_cache_file_name, 'r') as f:
                    # Save before we filter out inactive
                    cache = json.load(f)
                    self.regs = cache['HNs']
                checkpoint = 773800  # TODO: adjust from cache file
            else:
                if self.verbose:
                    self.app_log.info("no powhncache in {}".format(datadir))
                # Start from scratch and reconstruct current state from history
                self.regs = {}
                checkpoint = 773800  # No Hypernode tx earlier

            if self.verbose:
                self.app_log.info("Parsing reg messages from {} to {}, {} inactive HNs."
                                  .format(checkpoint + 1, height, len(inactive_last_round)))
            if config.LOAD_HN_FROM_POW or force_all or ignore_config:
                # TEMP
                if self.verbose:
                    self.app_log.info("Running {} {} {}".format(SQL_REGS_FROM_TO, checkpoint + 1, height))
                #  print("c1", time.time())
                cursor = await self.pow_chain.async_fetchall(SQL_REGS_FROM_TO, (checkpoint + 1, height))
                # print("c2", time.time())
            else:
                if False:
                    # Temp DEV test
                    cursor = testvectors.POW_HN_CURSOR
                else:
                    self.regs = poshelpers.fake_hn_dict(inactive_last_round, self.app_log)
                    return self.regs

            # Temp
            if self.verbose:
                self.app_log.info("Parsing reg info...")
            for row in cursor:
                block_height, address, operation, openfield, timestamp = row
                # TEMP
                if self.verbose:
                    self.app_log.info("Row {}: {}, {}, {}".format(block_height, address, operation, openfield))
                valid = True
                show = False
                try:
                    if ip and "{}:".format(ip) in openfield:
                        show = True
                        self.app_log.info("Row {}: {}, {}, {}".format(block_height, address, operation, openfield))
                    hip, port, pos, reward = self.reg_extract(openfield, address)
                    if operation == 'hypernode:register':
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
                        [1 / 0 for items in self.regs.values() if items['ip'] == hip]
                        # Dup pos address?
                        [1 / 0 for items in self.regs.values() if items['pos'] == pos]
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
                        self.regs[address] = dict(zip(['ip', 'port', 'pos', 'reward', 'weight', 'timestamp', 'active'],
                                                      [str(hip), port, str(pos), str(reward), weight, timestamp, active]))
                        if show:
                            self.app_log.info("Ok, Weight={}".format(weight))
                    else:
                        pass
                        # It's an unreg
                        if address in self.regs:
                            # unreg from owner
                            if (hip, port, pos) == (self.regs[address]['ip'], self.regs[address]['port'],
                                                    self.regs[address]['pos']):
                                # same info
                                del self.regs[address]
                            else:
                                raise ValueError("Invalid unregistration params")

                        elif address == config.POW_CONTROL_ADDRESS:
                            self.regs = {key: items for key, items in self.regs.items()
                                         if (items['ip'], items['port'], items['pos']) != (hip, port, pos)}
                            if show:
                                self.app_log.warning("Unreg by controller, reason '{}'."
                                                     .format(self.extract_reason(openfield)))
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
                if self.verbose:
                    """self.app_log.info("{} msg {} from {} : {}. ({})".format(
                        valid, operation, address, openfield, block_height))
                    """
                    self.app_log.info("{}".format(valid))
            if self.verbose:
                # self.app_log.info("{} PoW Valid HN :{}".format(len(self.regs), json.dumps(self.regs)))
                if self.regs:
                    self.app_log.info("{} PoW Valid HN.".format(len(self.regs)))
                else:
                    self.app_log.warning("No PoW Valid HN.")
            if balance_check:
                # recheck all balances
                self.app_log.warning("Balance check required for PoW height {}".format(height))
                bad_balance = []
                for pow_address, detail in self.regs.items():
                    # print(pow_address, detail)
                    """
                    {'ip': '51.15.95.155', 'port': '6969', 'pos': 'BLYkQwGZmwjsh7DY6HmuNBpTbqoRqX14ne',
                     'reward': '8f2d03c817c3d36a864c99a27f6b6179eb1898a631bc007a7e0ffa39', 'weight': 3,
                     'timestamp': 1534711530.06, 'active': True}
                    """
                    weight = await self.reg_check_balance(pow_address, height)
                    if weight < detail['weight']:
                        # Can be more, can't be less.
                        self.app_log.warning("PoW address {}, weight {} instead of {} - removing from list.".format(pow_address, weight, detail['weight']))
                        # Remove from the list.
                        #self.regs.pop(pow_address, None)
                        self.regs[pow_address]['active'] = False
                        bad_balance.append(pow_address)
                # now remove the balance cheaters
                for pow_address in bad_balance:
                    self.regs.pop(pow_address, None)

        except Exception as e:
            self.app_log.error("load_hn_same_process Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
            sys.exit()

    async def stream_subprocess(self, cmd, timeout=1):
        """

        :param cmd:
        :param timeout:
        :return:
        """
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE,
                                                       stderr=asyncio.subprocess.PIPE)
        try:
            p = await asyncio.wait_for(process.wait(), timeout)
        except Exception:
            p = None
        if not (p is None):
            if p == 0:
                out = await process.stdout.read()
                out = out.decode('utf8')
                return out
            """
            print("p", p)  # return code (0 if ok)
            print("stdout:", (await process.stdout.read()).decode('utf8'))
            print("stderr:", (await process.stderr.read()).decode('utf8'))
            """
        return 'false'

    async def load_hn_distinct_process(self, a_round: int=0, datadir: str='', inactive_last_round=None,
                                       force_all: bool=False, no_cache: bool=False, ignore_config: bool=False, ip='',
                                       balance_check=False):
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
        try:
            extra= '-b' if balance_check else ''
            if ip:
                cmd = [config.PYTHON_EXECUTABLE, "hn_reg_feed.py --ip={} {}".format(ip, extra)]
                if a_round > 0:
                    cmd = [config.PYTHON_EXECUTABLE, "hn_reg_feed.py", "-r {} --ip={} {}".format(a_round, ip, extra)]
                res = await self.stream_subprocess(cmd, timeout=config.PROCESS_TIMEOUT)
                print(res)
                self.regs = {}
                return
            else:
                cmd = [config.PYTHON_EXECUTABLE, "hn_reg_feed.py"]
                if a_round > 0:
                    cmd = [config.PYTHON_EXECUTABLE, "hn_reg_feed.py", "-r {}".format(a_round)]
                self.regs = json.loads(await self.stream_subprocess(cmd, timeout=config.PROCESS_TIMEOUT))
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
            self.app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
            sys.exit()

    async def load_hn_remote_url(self, a_round: int=0, datadir: str='', inactive_last_round=None,
                                       force_all: bool=False, no_cache: bool=False, ignore_config: bool=False, ip='',
                                       balance_check=False, url=''):
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
                full_url = "{}{}/{}/{}.json".format(url, a_round[0], a_round[1], a_round)
                self.app_log.info("load_hn_remote_url {}".format(full_url))
                response = await http_client.fetch(full_url)
                self.regs = json.loads(response.body.decode('utf-8'))
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
            self.app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
            sys.exit()

    async def load_hn_pow(self, a_round: int=0, datadir: str='', inactive_last_round=None,
                          force_all: bool=False, no_cache: bool=False, ignore_config: bool=False,
                          distinct_process=None, ip: str='', balance_check: bool=False):
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
        if ip == '':
            ip = False
        # TODO: check it's not a round we have in our local DB first.
        # If we have, just return the one stored.
        if distinct_process is None:
            distinct_process = config.POW_DISTINCT_PROCESS
        self.distinct_process = distinct_process

        if self.verbose:
            self.app_log.info("load_hn_pow, round {}".format(a_round))
        try:

            if not inactive_last_round:
                inactive_last_round = []
            # print("h1", time.time())

            # Here query one way or the other
            if config.POW_ALTERNATE_URL != '':
                self.app_log.info("Trying to load round {} from alternate URL".format(a_round))
                # TODO: try to load from url
                await self.load_hn_remote_url(a_round, inactive_last_round=inactive_last_round, datadir=datadir,
                                                    force_all=force_all, ignore_config=ignore_config, ip=ip,
                                                    balance_check=balance_check, url=config.POW_ALTERNATE_URL)
            if not self.regs:
                if self.distinct_process:
                    await self.load_hn_distinct_process(a_round, inactive_last_round=inactive_last_round, datadir=datadir,
                                                        force_all=force_all, ignore_config=ignore_config, ip=ip,
                                                        balance_check=balance_check)
                else:
                    await self.load_hn_same_process(a_round, inactive_last_round=inactive_last_round, datadir=datadir,
                                                    force_all=force_all, ignore_config=ignore_config, ip=ip,
                                                    balance_check=balance_check)

            # Here we have self.regs

            # await cursor.close()
            # TEMP
            # sys.exit()

            if False:  # not no_cache:
                with open(pow_cache_file_name, 'w') as f:
                    # Save before we filter out inactive
                    cache = {"height": height, "timestamp": int(time.time()), "HNs": self.regs}
                    # TODO: Error Object of type 'TextIOWrapper' is not JSON serializable
                    # TODO test cache.
                    json.dump(f, cache)
            # Now, if round > 0, set active state depending on last round activity
            if self.regs:
                for address, items in self.regs.items():
                    if items['pos'] in inactive_last_round:
                        self.regs[address]['active'] = False
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
            self.app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
            sys.exit()


class SqlitePowChain(SqliteBase):

    def __init__(self, verbose=False, db_path='data/', app_log=None):
        SqliteBase.__init__(self, verbose=verbose, db_path=db_path, db_name='', app_log=app_log)
        # Sqlitebase converts path + db_name into db_path
        self.db = None
        self.check()

    def check(self):
        if not os.path.isfile("{}".format(self.db_path)):
            raise ValueError("Bismuth PoW Ledger not found at {}.".format(self.db_path))
        if not self.db:
            self.db = sqlite3.connect(self.db_path, timeout=10)
            self.db.text_factory = str
            self.cursor = self.db.cursor()

    def get_block_before_ts(self, a_timestamp):
        """
        Returns the last PoW block height preceding the given timestamp.

        :param a_timestamp:
        :return: block_height preceding the given TS
        """
        height = self.fetchone(SQL_BLOCK_HEIGHT_PRECEDING_TS, (a_timestamp,))
        height = height[0]
        if self.verbose:
            self.app_log.info("Block before ts {} is {}".format(a_timestamp, height))
        return height

    def get_ts_of_block(self, block_height):
        """
        Returns the timestamp of the given block height.

        :param block_height:
        :return: int timestamp
        """
        ts = self.fetchone(SQL_TS_OF_BLOCK, (block_height,))
        if not ts:
            return None
        ts = ts[0]
        if self.verbose:
            self.app_log.info("Block {} has ts {}".format(block_height, ts))
        return ts

    async def async_get_block_before_ts(self, a_timestamp):
        """
        Async. Returns the last PoW block height preceding the given timestamp.

        :param a_timestamp:
        :return: block_height preceding the given TS
        """
        height = await self.async_fetchone(SQL_BLOCK_HEIGHT_PRECEDING_TS, (a_timestamp,))
        height = height[0]
        if self.verbose:
            self.app_log.info("Block before ts {} is {}".format(a_timestamp, height))
        return height
