"""
Helpers and classes to interface with the main Bismuth PoW chain

"""

from math import floor
import json
import os
import sqlite3
import sys
import time

# Our modules
import config
from fakelog import FakeLog
import poshelpers
from sqlitebase import SqliteBase
import testvectors

__version__ = '0.0.2'


SQL_BLOCK_HEIGHT_PRECEDING_TS = 'SELECT block_height FROM transactions WHERE timestamp <= ? ' \
                                'ORDER BY block_height DESC limit 1'

SQL_REGS_FROM_TO = "SELECT block_height, address, operation, openfield, timestamp FROM transactions " \
                   "WHERE (operation='hypernode:register' OR operation='hypernode:unregister') " \
                   "AND block_height >= ? AND block_height <= ? " \
                   "ORDER BY block_height ASC"


class PowInterface:

    def __init__(self, app_log=None):
        if not app_log:
            app_log = FakeLog()
        self.app_log = app_log
        self.verbose = config.VERBOSE
        self.regs = {}
        """
        registered HN from PoW. Can be temp. wrong when updating. Calling object must keep a cached working version. 
        Indexed by pow address.
        """
        self.pow_chain = SqlitePowChain(db_path=config.POW_LEDGER_DB, verbose=config.VERBOSE, app_log=app_log)

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
        return 1

    def reg_extract(self, openfield, address):
        """
        Extract data from openfield. 'ip:port:pos' or with option 'ip2:port:pos2,reward=bis2a'

        :param openfield: str
        :return: tuple (ip, port, pos, reward)
        """
        options = {}
        if ',' in openfield:
            # Only allow for 1 extra param at a time. No need for more now, but beware if we add!
            openfield, extra = openfield.split(',')
            key, value = extra.split('=')
            options[key] = value
        ip, port, pos = openfield.split(':')
        reward = options['reward'] if 'reward' in options else address
        return ip, port, pos, reward

    async def load_hn_pow(self, a_round=0, datadir='', inactive_last_round=None):
        """
        Async Get HN from the pow. Called at launch (a_round=0) then at each new round.

        :param a_round:
        :param datadir:
        :param inactive_last_round: list of pos_address that did not sent any tx previous round, to drop from list.
        """
        try:
            if a_round:
                round_ts = config.ORIGIN_OF_TIME + a_round * config.ROUND_TIME_SEC
            else:
                round_ts = int(time.time())
            if not inactive_last_round:
                inactive_last_round = []
            pow_cache_file_name = "{}/powhncache.json".format(datadir)
            # Current height, or height at begin of the new round.
            height = self.pow_chain.get_block_before_ts(round_ts)
            # Now take back 30 minutes to account for possible large rollbacks
            height -= 30
            # And round to previous multiple of 60
            height = 60 * floor(height / 60)
            # print('ref height', height)
            # FR: this should be part of the bootstrap archive
            if os.path.isfile(pow_cache_file_name):
                self.app_log.info("powhncache exists in {}".format(datadir))
                # load this checkpoint and go on since there.
                # take latest checkpoint anyway, even if we wanted an older one.
                with open(pow_cache_file_name, 'r') as f:
                    # Save before we filter out inactive
                    cache =json.load(f)
                    self.regs = cache['HNs']
            else:
                self.app_log.info("no powhncache in {}".format(datadir))
                # Start from scratch and reconstruct current state from history
                self.regs = {}
                checkpoint = 773800  # No Hypernode tx earlier

            if self.verbose:
                self.app_log.info("Parsing reg messages from {} to {}, {} inactive HNs."
                                  .format(checkpoint +1, height, len(inactive_last_round)))
            if config.LOAD_HN_FROM_POW:
                cursor = self.pow_chain.execute(SQL_REGS_FROM_TO, (checkpoint +1, height))
            else:
                if False:
                    # Temp DEV test
                    cursor = testvectors.POW_HN_CURSOR
                else:
                    self.regs = poshelpers.fake_hn_dict(inactive_last_round, self.app_log)
                    return self.regs

            for row in cursor:
                block_height, address, operation, openfield, timestamp = row
                valid = True
                try:
                    ip, port, pos, reward = self.reg_extract(openfield, address)
                    if operation=='hypernode:register':
                        # There is a small hack here: the following tests seem to do nothing, but they DO
                        # raise an exception if there is a dup. Allow for single line faster test.
                        # since list comprehension is heavily optimized.
                        # Dup ip?
                        [1/0 for items in self.regs.values() if items['ip']==ip]
                        # Dup pos address?
                        [1/0 for items in self.regs.values() if items['pos']==pos]
                        # Dup pow address?
                        if address in self.regs:
                            raise ValueError("Already an active registration")
                        # Requires a db query, runs last - Will raise if not enough.
                        weight = await self.reg_check_balance(address, block_height)
                        active = True  # by default
                        self.regs[address] = dict(zip(['ip', 'port', 'pos', 'reward', 'weight', 'timestamp', 'active'],
                                                      [ip, port, pos, reward, weight, timestamp, active]))
                    else:
                        pass
                        # It's an unreg
                        if address in self.regs:
                            # unreg from owner
                            if (ip, port, pos) == (self.regs[address]['ip'], self.regs[address]['port'],
                                                   self.regs[address]['pos']):
                                # same infos
                                del self.regs[address]
                            else:
                                raise ValueError("Invalid unregistration params")

                        elif address == config.POS_CONTROL_ADDRESS:
                            self.regs = {key:items for key,items in self.regs.items()
                                         if (items['ip'], items['port'], items['pos']) != (ip, port, pos)}
                        else:
                            raise ValueError("Invalid unregistration sender")

                except (ValueError, ZeroDivisionError) as e:
                    valid = False
                    pass
                if self.verbose:
                    self.app_log.info("{} msg {} from {} : {}. ({})".format(
                        valid, operation, address, openfield, block_height))
            if self.verbose:
                self.app_log.info("PoW Valid HN :{}".format(json.dumps(self.regs)))
            with open(pow_cache_file_name, 'w') as f:
                # Save before we filter out inactive
                cache = { "height": height, "timestamp": int(time.time()), "HNs": self.regs}
                json.dump(f, cache)
            # Now, if round > 0, set active state depending on last round activity
            for address, items in self.regs.items():
                if items['pos'] in inactive_last_round:
                    self.regs[address]['active'] = False
            if self.verbose:
                self.app_log.info("PoW+PoS Valid HN :{}".format(json.dumps(self.regs)))
            # sys.exit()
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
            self.db = sqlite3.connect(self.db_path, timeout=1)
            self.db.text_factory = str
            self.cursor = self.db.cursor()

    def get_block_before_ts(self, a_timestamp):
        """
        Returns the last PoW block height preceding the given timestamp.

        :param a_timestamp:
        :return: block_height preceding the given TS
        """
        height = self.fetch_one(SQL_BLOCK_HEIGHT_PRECEDING_TS, (a_timestamp,))
        height = height[0]
        if self.verbose:
            self.app_log.info("Block before ts {} is {}".format(a_timestamp, height))
        return height
