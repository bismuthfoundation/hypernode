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

# Our modules
import config
import poscrypto
import poshelpers
import testvectors
from fakelog import FakeLog
from sqlitebase import SqliteBase

__version__ = '0.1.3'


SQL_BLOCK_HEIGHT_PRECEDING_TS_SLOW = 'SELECT block_height FROM transactions WHERE timestamp <= ? ' \
                                'ORDER BY block_height DESC limit 1'

SQL_BLOCK_HEIGHT_PRECEDING_TS = 'SELECT max(block_height) FROM transactions WHERE timestamp <= ? '

SQL_REGS_FROM_TO = "SELECT block_height, address, operation, openfield, timestamp FROM transactions " \
                   "WHERE (operation='hypernode:register' OR operation='hypernode:unregister') " \
                   "AND block_height >= ? AND block_height <= ? " \
                   "ORDER BY block_height ASC"

SQL_QUICK_BALANCE_CREDITS = "SELECT sum(amount+reward) FROM transactions WHERE recipient = ? AND block_height <= ?"

SQL_QUICK_BALANCE_DEBITS = "SELECT sum(amount+fee) FROM transactions WHERE address = ? AND block_height <= ?"

SQL_QUICK_BALANCE_ALL = "SELECT sum(a.amount+a.reward)-debit FROM transactions as a , " \
                        "(SELECT sum(b.amount+b.fee) as debit FROM transactions b WHERE address = ? AND block_height <= ?) " \
                        "WHERE a.recipient = ? AND a.block_height <= ?"


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

    def reg_extract(self, openfield, address):
        """
        Extract data from openfield. 'ip:port:pos' or with option 'ip2:port:pos2,reward=bis2a'

        :param openfield: str
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

    async def load_hn_same_process(self, a_round: int=0, datadir: str='', inactive_last_round=None,
                          force_all: bool=False, no_cache: bool=False, ignore_config: bool=False, ip=''):
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
        :return:
        """
        try:
            if a_round:
                round_ts = config.ORIGIN_OF_TIME + a_round * config.ROUND_TIME_SEC
            else:
                round_ts = int(time.time())
            pow_cache_file_name = "{}/powhncache.json".format(datadir)
            # FR: Check the pow chain is up to date?
            # beware, we can't print what we want, output is read as json.
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
                                # same infos
                                del self.regs[address]
                            else:
                                raise ValueError("Invalid unregistration params")

                        elif address == config.POS_CONTROL_ADDRESS:
                            self.regs = {key: items for key, items in self.regs.items()
                                         if (items['ip'], items['port'], items['pos']) != (hip, port, pos)}
                        else:
                            raise ValueError("Invalid unregistration sender")
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
                self.app_log.info("{} PoW Valid HN :{}".format(len(self.regs), json.dumps(self.regs)))
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
        p = None
        try:
            p = await asyncio.wait_for(process.wait(), timeout)
        except Exception as e:
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
                          force_all: bool=False, no_cache: bool=False, ignore_config: bool=False, ip=''):
        """
        Load from async sqlite3 connection from an external process with timeout.

        :param a_round:
        :param datadir:
        :param inactive_last_round:
        :param force_all:
        :param no_cache:
        :param ignore_config:
        :param ip:
        :return:
        """
        try:
            if ip:
                cmd = [config.PYTHON_EXECUTABLE, "hn_reg_feed.py --ip={}".format(ip)]
                if a_round > 0:
                    cmd = [config.PYTHON_EXECUTABLE, "hn_reg_feed.py", "-r {} --ip={}".format(a_round, ip)]
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
                self.app_log.info("{} PoW Valid HN :{}".format(count, json.dumps(self.regs)))
        except Exception as e:
            self.app_log.error("load_hn_distinct_process Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error('detail {} {} {}'.format(exc_type, fname, exc_tb.tb_lineno))
            sys.exit()

    async def load_hn_pow(self, a_round=0, datadir='', inactive_last_round=None,
                          force_all=False, no_cache=False, ignore_config=False, distinct_process=None, ip=''):
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
            if self.distinct_process:
                await self.load_hn_distinct_process(a_round, inactive_last_round=inactive_last_round, datadir=datadir,
                                                    force_all=force_all, ignore_config=ignore_config, ip=ip)
            else:
                await self.load_hn_same_process(a_round, inactive_last_round=inactive_last_round, datadir=datadir,
                                                force_all=force_all, ignore_config=ignore_config, ip=ip)

            # Here we have self.regs

            # await cursor.close()
            # TEMP
            # sys.exit()

            if False:  # not no_cache:
                with open(pow_cache_file_name, 'w') as f:
                    # Save before we filter out inactive
                    cache = { "height": height, "timestamp": int(time.time()), "HNs": self.regs}
                    # TODO: Error Object of type 'TextIOWrapper' is not JSON serializable
                    # TODO test cache.
                    json.dump(f, cache)
            # Now, if round > 0, set active state depending on last round activity
            if self.regs:
                for address, items in self.regs.items():
                    if items['pos'] in inactive_last_round:
                        self.regs[address]['active'] = False
            if self.verbose:
                self.app_log.info("PoW+PoS Valid HN :{}".format(json.dumps(self.regs)))
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
