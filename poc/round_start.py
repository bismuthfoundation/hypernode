"""
POC for Bismuth PoS
Start of round calculations
"""

import sys

# custom modules
sys.path.append('../modules')
import common
import determine


__version__ = '0.0.1'


if __name__ == "__main__":
    print("Last Round broadhash", common.POC_LAST_BROADHASH.hexdigest())
    print("{} candidates, {} slots".format(len(common.POC_MASTER_NODES_LIST), common.MAX_ROUND_SLOTS))
    tickets = determine.mn_list_to_tickets(common.POC_MASTER_NODES_LIST)
    print("Tickets\n", tickets)
    slots = determine.tickets_to_delegates(tickets, common.POC_LAST_BROADHASH)
    print("Slots\n", slots)
