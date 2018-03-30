"""
POC for Bismuth PoS
Start of round calculations
"""

import sys
import time

# custom modules
sys.path.append('../modules')
import common
import determine


__version__ = '0.0.1'


if __name__ == "__main__":
    print("Round Start")
    print("--------------------------")
    print("Last Round broadhash", common.POC_LAST_BROADHASH.hexdigest())
    print("{} candidates, {} slots".format(len(common.POC_MASTER_NODES_LIST), common.MAX_ROUND_SLOTS))
    tickets = determine.mn_list_to_tickets(common.POC_MASTER_NODES_LIST)
    print("Tickets\n", tickets)
    slots = determine.tickets_to_delegates(tickets, common.POC_LAST_BROADHASH)
    print("Slots\n", slots)
    test_slots = determine.mn_list_to_test_slots(common.POC_MASTER_NODES_LIST, slots)
    print("Tests Slots\n", test_slots)
    print("")
    print("Timeslots test")
    print("--------------------------")
    expected = [(common.ORIGIN_OF_TIME, 0, 0), (common.ORIGIN_OF_TIME+common.POS_SLOT_TIME_SEC*(1.5), 0, 1), (common.ORIGIN_OF_TIME+common.ROUND_TIME_SEC+common.POS_SLOT_TIME_SEC*1.5, 1, 1)]
    for (test, expected_round, expected_slot) in expected:
        calc_round, calc_slot = determine.timestamp_to_round_slot(test)
        print("Time {}: Round {} - Slot {} (expected {} - {})".format(test, calc_round, calc_slot, expected_round, expected_slot))
    print("Basic forge simulation - 1/min")
    print("--------------------------")
    try:
        while True:
            test = round(time.time())
            calc_round, calc_slot = determine.timestamp_to_round_slot(test)
            print("Current Time {}: Round {} - Slot {}".format(test, calc_round, calc_slot))
            print("Forger is {}".format(slots[calc_slot][0]))
            print("Tests:", test_slots[calc_slot])
            time.sleep(60)
    except Exception as e:
        pass
