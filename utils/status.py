"""
Temp Util. Checks a list of HNs to id sync status

Have the HNs to query as a dict {ip: label} in
hns_status.json

Adapted from https://github.com/bismuthfoundation/util/blob/master/hypernode_monitoring/hn_monitor.py
Thanks geho2!

"""

import sys
import json
import asyncio
from tornado.tcpclient import TCPClient

# custom modules
sys.path.append('../modules')
import com_helpers
import commands_pb2
import poshelpers


STATUSES = dict()  # ip: status

# Test address
HN_ADDRESS = 'BMMZtCSRRTVoNTe3cv1JQN1ohL1GYUgZkU'

HNS = dict()


async def get_status(ip, port, timeout=30):
    global STATUSES
    try:
        if ip in STATUSES:
            if STATUSES[ip]:
                return
        tcp_client = TCPClient()
        stream = await tcp_client.connect(ip, port, timeout=timeout)
        # Hello string
        hello_string = poshelpers.hello_string(port=101, posnet="posnet0002", address=HN_ADDRESS)
        # print("Hello", hello_string)
        await com_helpers.async_send_string(commands_pb2.Command.hello, hello_string, stream, ip)
        msg = await com_helpers.async_receive(stream, ip, timeout=timeout)
        # Now request status
        await com_helpers.async_send_void(commands_pb2.Command.status, stream, ip)
        msg = await com_helpers.async_receive(stream, ip, timeout=timeout)
        if msg.command == commands_pb2.Command.status:
            data = json.loads(msg.string_value)
            STATUSES[ip] = data
        # print(ip, "ok")
    except Exception as e:
        # print(str(e))
        STATUSES[ip] = False


async def query(timeout=30):
    tasks = list()
    for ip, label in HNS.items():
        tasks.append(get_status(ip, 6969, timeout=timeout))
    await asyncio.wait(tasks)


if __name__ == "__main__":

    with open("hns_status.full.json", 'r') as fp:
        HNS = json.load(fp)

    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(query(timeout=15))
    event_loop.run_until_complete(query(timeout=45))

    for ip, label in HNS.items():
        status = STATUSES[ip]
        ip = ip.ljust(16, ' ')
        if status:
            print(f"{ip}: Height {status['chain']['block_height']}/{status['peers']['net_height']['height']}\t"
                  f"Round/slot {status['chain']['round']}/{status['chain']['sir']}\t"
                  f"State {status['state']['state'].ljust(20)} Forger {status['state']['forger']}\t"
                  f"v{status['instance']['hn_version']}\t {label}")
            if "meta" in status:
                print(f"        Meta all/inactive {status['meta']['all_hns_count']}/ {status['meta']['inactive_hns_count']}\t"
                      f"Meta pow reg/active {status['meta']['powchain_regs_count']}/ {status['meta']['active_regs_count']}")
                print(status['meta'])
        else:
            print(f"{ip}: Ko")
    """
    with open(hn_config.OUTFILE_3, 'w') as outfile:
        json.dump(status_ex, outfile)
    """

    """
    Status: {
      "config": {"address": "BMMZtCSRRTVoNTe3cv1JQN1ohL1GYUgZkU", "ip": null, "port": 6969, "verbose": 1, "outip": "109.190.174.238"}, 
      "instance": {"version": "0.0.58", "hn_version": "0.0.98p", "statustime": 1562428499}, 
      "chain": {
        "block_height": 90486, "Genesis": "BKYnuT4Pt8xfZrSKrY3mUyf9Cd9qJmTgBn", 
        "height": 90486, "round": 7697, "sir": 17, "block_hash": "d4a0e486980a5cc2948b53d60bb09cd5f1345ba3", 
        "uniques": 400, "uniques_round": 175, "forgers": 353, "forgers_round": 7}, 
      "mempool": {"NB": 116}, 
      "peers": {"connected_count": 30, "outbound": ["91.121.87.99:06969", "206.189.217.196:06969", "104.238.173.26:06969", "198.54.123.177:06969", "45.32.44.46:06969", "155.138.215.140:06969", "45.32.115.135:06969", "91.121.216.89:06969", "185.244.129.72:06969", "185.244.129.31:06969", "51.15.95.155:06969", "209.250.237.229:06969", "209.246.143.198:06969", "149.28.20.99:06969", "204.48.18.50:06969", "116.203.45.9:06969", "149.28.188.158:06969", "163.172.222.163:06969", "144.202.49.76:06969", "207.148.0.65:06969", "128.199.62.76:06969", "188.165.45.239:06969", "178.62.68.118:06969", "147.135.239.138:06969", "5.135.24.201:06969", "193.37.214.35:06969", "45.32.49.12:06969"], 
      "inbound": [], 
      "net_height": {"height": 90486, "round": 7697, "sir": 17, "block_hash": "d4a0e486980a5cc2948b53d60bb09cd5f1345ba3", "uniques": 400, "uniques_round": 175, "forgers": 353, "forgers_round": 7, "count": 1, "peers": ["155.138.215.140:06969"]}}, 
      "state": {"state": "SYNCING", "round": 7697, "sir": 17, "forger": "B6zwYk2iuv9oAM7gAhcoyJYkuoJyPKFhBz"}, 
      "tasks": {"total": 28, "detail": {"Poshn.manager": 1, "Poshn.client_worker": 27}}, 
      "extra": {"forged_count": 0, "open_files": 12, "connections": 25, "num_fd": 46}, 
      "meta": {"round": 7697, "sir": 0, "all_hns_count": 245, "all_hns_hash": "d9e88bec55f6b6509a06d592854409802f05247fa23508f43b31a6d9af46b4fa", "inactive_hns_count": 83, "inactive_hns_hash": "f914ca2259307e7bc78e320c54d48f451f8f103f9c9acfdf8ce6191357bd21d8", "powchain_regs_count": 245, "powchain_regs": "a29c279843f64e4067d9d818175eb06120c4b2505fada193d7519ced3700b7cb", "active_regs_count": 147, "active_regs": "7b062c3de774b4971c9722e1ae32bbac57b7083ab7c703ac728e07bf94f0dceb", "slots": "2ac9d36cfb2d4b21e1a83cc20407a4b62e1007f09cc34a661d8f1c02ca0c8188"}, 
      "pow": {"protocolversion": "mainnet0020", "walletversion": "4.3.0.0", "testnet": false, "blocks": 1243008, "timeoffset": 0, "connections": 11, "difficulty": 106.0209201709, "threads": 51, "uptime": 594791, "consensus": 1243008, "consensus_percent": 90.9090909090909, "last_block_ago": 26.17354702949524}, 
      "PID": 8893}

    """
