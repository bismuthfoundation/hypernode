"""
Helpers and classes to interface with the main Bismuth PoW chain

"""

import asyncio
import json
import os
import sys
import time
from base64 import b85encode
from hashlib import md5
from os import path
from typing import Union

from polysign.signerfactory import SignerFactory
from tornado.iostream import StreamClosedError

# Our modules
import config
from determine import timestamp_to_round_slot, round_to_reference_timestamp
from fakelog import FakeLog
from powasyncclient import PoWAsyncClient

__version__ = "0.2.2"


# ================== Helpers ================


def validate_pow_address(address: str) -> Union[None, bool]:
    """
    Validate a bis (PoW address).

    :param address:
    :return: True if address is valid, raise a ValueError exception if not.
    """
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
                try:
                    pow_client = PoWAsyncClient(
                        config.POW_IP, config.POW_PORT, self.app_log
                    )
                    res = await pow_client.async_command("HN_last_block_ts")
                    pow_client.close()
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
            except:
                pass

    async def load_hn_pow(
        self,
        a_round: int = 0,
        datadir: str = "",
        inactive_last_round=None,
        force_all: bool = False,
        no_cache: bool = False,
        ignore_config: bool = False,
        distinct_process=None,
        ip: str = "",
        balance_check: bool = False,
        collateral_dropped=None,
    ):
        """
        Async Get HN from the pow. Called at launch (a_round=0) then at each new round.

        :param a_round: pos round number
        :param datadir: kept  for compatibility
        :param inactive_last_round: list of pos_address that did not sent any tx previous round, to drop from list.
        :param force_all: Optional, take last pow block as reference for reg feed
        :param no_cache: kept  for compatibility
        :param ignore_config: kept  for compatibility
        :param distinct_process: kept  for compatibility
        :param ip: Optional, do not cache, take from beginning, show all reg status for that one.
        :param balance_check: Force balance check for all HN at the end of the call
        :param collateral_dropped: Give bisurls for auto unregs at the end.
        """
        if ip == "":
            ip = False

        if self.verbose:
            self.app_log.info("load_hn_pow, round {}".format(a_round))
        try:

            if not inactive_last_round:
                inactive_last_round = []

            pow_height = 0
            if force_all:
                pow_height = 8000000
            if a_round <= 0:
                a_round, a_slot = timestamp_to_round_slot(time.time())

            ref_timestamp = round_to_reference_timestamp(a_round)

            pow_client = PoWAsyncClient(config.POW_IP, config.POW_PORT, self.app_log)
            command = "HN_reg_round {} {} {} {}".format(
                a_round, ref_timestamp, pow_height, ip
            )
            # print("COMMAND", command)
            try:
                res = await pow_client.async_command(
                    "HN_reg_round {} {} {} {}".format(
                        a_round, ref_timestamp, pow_height, ip
                    ),
                    timeout=60,
                    retry=3,
                    retry_pause=2,
                )
                if not res:
                    # Query failed, likely pow node behind.
                    self.app_log.error("pow reg query failed")
                    sys.exit()
            except (StreamClosedError, TimeoutError):
                self.app_log.error("pow connect failed")
                sys.exit()
            if ip:
                return res["ip_feed"]

            self.regs = res["regs"]
            collateral_dropped = []
            if balance_check:
                self.app_log.warning("Balance checks asked...")
                addresses = ",".join(self.regs.keys())
                weights = await pow_client.async_command(
                    "HN_reg_check_weights {} {}".format(addresses, ref_timestamp),
                    timeout=60,
                )
                # print("RES weights", weights)

                bad_balance = []
                for pow_address, detail in self.regs.items():
                    weight = weights.get(pow_address, -1)
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

            if collateral_dropped:
                # self.app_log.warning("I should handle collateral dropped")
                for dropped in collateral_dropped:
                    bisurl = create_bis_url(recipient=dropped["pow"],
                                            amount="0",
                                            operation="hypernode:unregister",
                                            openfield="{}:{}:{},reason=Collateral drop".format(dropped["ip"],
                                                                        dropped["port"],
                                                                        dropped["pos"]))
                    print(bisurl)

            pow_client.close()
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
            # TODO: save in local DB for this round?
            return self.regs
        except Exception as e:
            self.app_log.error("load_hn_pow Error {}".format(e))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.app_log.error(
                "detail {} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            )
            sys.exit()
