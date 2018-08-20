"""
Checks the wallet, config, and tells if an hn instance is running.

"""

import argparse
import json
from os import path
import subprocess
import sys

# custom modules
sys.path.append('../modules')
import config
import poshn
import poscrypto
import psutil


__version__ = '0.0.1'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Bismuth HyperNode Check')
    parser.add_argument("-v", "--verbose", action="count", default=False, help='Be verbose.')
    parser.add_argument("-j", "--json", action="count", default=False, help='Return json content')
    # parser.add_argument("--action", type=str, default=None, help='Specific action. ')
    args = parser.parse_args()
    wallet_name = "poswallet.json"
    poscrypto.load_keys(wallet_name)
    status = {"address": poscrypto.ADDRESS, "errors": []}
    status['hn_lib_version'] = poshn.__version__
    status['config'] = config.load()
    # check if db exists
    if not path.isfile(config.POW_LEDGER_DB):
        status['errors'].append("Bismuth Full ledger not found at {}".format(config.POW_LEDGER_DB))
    # check if process runs
    instances = [p.info for p in psutil.process_iter(attrs=['pid', 'name', 'exe', 'cmdline']) if 'python' in p.info['name'] and 'hn_instance.py' in p.info['cmdline']]
    nb_instances = len(instances)
    python = instances[0]['exe'] if nb_instances else 'N/A'
    status['running_instances'] = nb_instances
    status['python'] = python
    status['external_ip'] = subprocess.getoutput("curl -4 -s ifconfig.co")
    status['default_port'] = config.DEFAULT_PORT
    if args.json:
        print(json.dumps(status))
    else:
        if args.verbose:
            for var in ['address', 'hn_lib_version', 'default_port', 'external_ip', 'running_instances', 'python']:
                print(var, ':', json.dumps(status[var]))
            print("\n== Config ==\n")
            for var, value in status['config'].items():
                print(var, ':', json.dumps(value))
        else:
            for var in ['address', 'default_port', 'external_ip', 'running_instances']:
                print(var, ':', json.dumps(status[var]))
            for var in ['POW_LEDGER_DB']:
                print(var, ':', json.dumps(status['config'][var]))
        if len(status['errors']):
            print("\n!! There are error(s) !!\n")
            for value in status['errors']:
                print("Error:", value)



