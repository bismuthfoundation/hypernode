#!/usr/bin/env python3
"""
Checks the wallet, config, and tells if an hn instance is running.

"""

import argparse
import json
import os
import resource
import subprocess
import sys
import time
from distutils.version import LooseVersion
from os import path
from shutil import copyfile
from warnings import filterwarnings
from warnings import resetwarnings

from psutil import process_iter, swap_memory, virtual_memory
from ipwhois import IPWhois

# custom modules
sys.path.append("../modules")
import config
import poshn
import poscrypto


__version__ = "0.0.7"

ONE_GB = 1024 * 1024 * 1024


def check_os(a_status):
    """
    Dup from hn_client. FR: factorize
    """
    if os.name == "posix":
        limit = resource.getrlimit(resource.RLIMIT_NOFILE)
        a_status["flimit"] = limit
        if limit[0] < 1024:
            a_status["errors"].append(
                "Too small ulimit, please tune your system, \nsee https://github.com/bismuthfoundation/Bismuth-FAQ/blob/master/Install/Linux.md#os-config"
            )
            sys.exit()
        if limit[0] < 65000:
            a_status["errors"].append(
                "ulimit shows non optimum value, consider tuning your system, \nsee https://github.com/bismuthfoundation/Bismuth-FAQ/blob/master/Install/Linux.md#os-config"
            )
    else:
        a_status["flimit"] = "N/A"
        a_status["errors"].append(
            "Non Posix system, requirements are not satisfied. Use at your own risks."
        )
    # Number of cores
    a_status["cpu_cores"] = os.cpu_count()
    if os.cpu_count() < 2:
        a_status["errors"].append(
            "Too few cpu ({}) compared to official requirements (2). Use at your own risks."
        )
    # Available Ram
    mem = virtual_memory()
    a_status["ram"] = mem.total
    a_status["ram_gb"] = mem.total / ONE_GB
    if mem.total < 1.9 * ONE_GB: # 2GB
        a_status["errors"].append(
            "Less than 2GB Physical Ram. Likely not to work. Setup a swap file and use at your own risks."
        )
        swap = swap_memory()
        a_status["errors"].append(
            "Current swap file is {:.2f}Gb, {}% free".format(swap.total / ONE_GB, swap.percent)
        )
    elif mem.total < 3.5 * ONE_GB: # 4GB, with sdome margin
        a_status["errors"].append(
            "Less than 4GB Physical Ram (official requirements). A swap file could prove useful. Use at your own risks."
        )
        swap = swap_memory()
        a_status["errors"].append(
            "Current swap file is {:.2f}Gb, {}% free".format(swap.total / ONE_GB, swap.percent)
        )


def get_ip_provider(ip: str):
    """
    Returns the description of the network provider for the public ip.
    Dupped code from plugin

    :param ip: str
    :return: str
    """
    filterwarnings(action="ignore")
    obj = IPWhois(ip)
    res = obj.lookup_whois()
    desc = res.get("asn_description")
    resetwarnings()
    return desc


def read_version_from_file(filename):
    for line in open(filename):
        if "__version__" in line:
            return line.split("=")[-1].replace("'", "").replace("\"", "").strip()
    return None


def check_plugin():
    """
    Checks the companion plugin is installed and right version.

    If not, do it.
    """
    # creates dir if need to be
    plugin_dir = path.abspath(
        config.POW_LEDGER_DB.replace("static", "plugins").replace(
            "ledger.db", "500_hypernode"
        )
    )
    # print(plugin_dir)
    if not path.isdir(plugin_dir):
        os.makedirs(plugin_dir, exist_ok=True)
    # copy file over if it does not exists
    plugin_file_dest = "{}/__init__.py".format(plugin_dir)
    if not path.isfile(plugin_file_dest):
        copyfile("../node_plugin/__init__.py", plugin_file_dest)
        print("\n>> Bismuth Node restart required!!!\n")
    plugin_ver = read_version_from_file(plugin_file_dest)
    ok = LooseVersion(plugin_ver) >= LooseVersion(config.PLUGIN_VERSION)
    if not ok:
        # was there but not right or high enough version
        copyfile("../node_plugin/__init__.py", plugin_file_dest)
        print("\n>> Bismuth Node restart required!!!\n")
    plugin_ver = read_version_from_file(plugin_file_dest)
    ok = LooseVersion(plugin_ver) >= LooseVersion(config.PLUGIN_VERSION)
    print(
        "Companion plugin Version {}, required {}, {}".format(
            plugin_ver, config.PLUGIN_VERSION, ok
        )
    )
    if not ok:
        print("\n>> Bad companion plugin version\n")


def check_node_version():
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
    print(
        "Companion node Version {}, required {}, {}".format(
            node_version, config.REQUIRED_NODE_VERSION, ok
        )
    )
    if not ok:
        print("\n>> Bad companion node version\n")


def check_pow_status():
    """
    This is a check that node runs with the right plugin version and updates powstatus.json
    :return:
    """
    # FR: rule of 3: 3 times we do that hack to get a filename, use a helper.
    status_filename = path.abspath(
        config.POW_LEDGER_DB.replace("static/", "").replace(
            "ledger.db", "powstatus.json"
        )
    )
    if not path.isfile(status_filename):
        print(
            "\n>>No powstatus.json. Make sure the node runs. If it does, wait 5 min and retry.\n"
        )
    elif os.path.getmtime(status_filename) < time.time() - 6 * 60:
        print(
            "\n>>powstatus.json seems too old. Make sure the node runs. If it does, wait 5 min and retry.\n"
        )
    else:
        print("powstatus.json ok.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bismuth HyperNode Check")
    parser.add_argument(
        "-v", "--verbose", action="count", default=False, help="Be verbose."
    )
    parser.add_argument(
        "-j", "--json", action="count", default=False, help="Return json content"
    )
    parser.add_argument(
        "-N",
        "--interface",
        type=str,
        default="",
        help="Use a specific network interface",
    )
    # parser.add_argument("--action", type=str, default=None, help='Specific action. ')
    args = parser.parse_args()
    wallet_name = "poswallet.json"
    poscrypto.load_keys(wallet_name)
    status = {"address": poscrypto.ADDRESS, "errors": []}
    status["hn_lib_version"] = poshn.__version__
    status["config"] = config.load()
    check_os(status)
    check_plugin()
    check_node_version()
    check_pow_status()
    # check if db exists
    if not path.isfile(config.POW_LEDGER_DB):
        status["errors"].append(
            "Bismuth Full ledger not found at {}".format(config.POW_LEDGER_DB)
        )
    # check if process runs
    instances = [
        p.info
        for p in process_iter(attrs=["pid", "name", "exe", "cmdline"])
        if "python" in p.info["name"] and "hn_instance.py" in p.info["cmdline"]
    ]
    nb_instances = len(instances)
    python = instances[0]["exe"] if nb_instances else "N/A"
    status["running_instances"] = nb_instances
    status["python"] = python
    status["python_version"] = subprocess.getoutput(
        "{} --version".format(config.PYTHON_EXECUTABLE)
    )
    status["pwd"] = subprocess.getoutput("pwd")
    if args.interface:
        status["external_ip"] = subprocess.getoutput(
            "curl --interface {} -4 -s ifconfig.co".format(args.interface)
        )
        status["interface"] = args.interface
    else:
        status["external_ip"] = subprocess.getoutput("curl -4 -s ifconfig.co")
        status["interface"] = ""
    status["provider"] = get_ip_provider(status["external_ip"])
    status["default_port"] = config.DEFAULT_PORT
    with open("check.json", "w") as f:
        json.dump(status, f)
    if args.json:
        print(json.dumps(status))
    else:
        if args.verbose:
            for var in [
                "address",
                "default_port",
                "external_ip",
                "running_instances",
                "hn_lib_version",
                "python",
                "python_version",
                "interface",
                "pwd",
                "flimit",
            ]:
                print(var, ":", json.dumps(status[var]))
            print("\n== Config ==\n")
            for var, value in status["config"].items():
                print(var, ":", json.dumps(value))
        else:
            for var in [
                "address",
                "default_port",
                "external_ip",
                "running_instances",
                "hn_lib_version",
                "python_version",
                "pwd",
            ]:
                print(var, ":", json.dumps(status[var]))
            for var in ["POW_LEDGER_DB"]:
                print(var, ":", json.dumps(status["config"][var]))
        if len(status["errors"]):
            print("\n!! There are error(s) !!\n")
            for value in status["errors"]:
                print("Error:", value)
