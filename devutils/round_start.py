"""
POC for Bismuth PoS
Start of round calculations
"""

import sys
import time
import asyncio

# custom modules
sys.path.append('../modules')
import config
import determine

__version__ = '0.0.1'


async def round_start():
    print("Round Start")
    print("--------------------------")
    print("Last Round broadhash", config.POC_LAST_BROADHASH)
    print("{} candidates, {} slots".format(len(config.POC_HYPER_NODES_LIST), config.MAX_ROUND_SLOTS))
    tickets = await determine.hn_list_to_tickets(config.POC_HYPER_NODES_LIST)
    print("Tickets\n", tickets)
    slots = await determine.tickets_to_delegates(tickets, config.POC_LAST_BROADHASH)
    print("Slots\n", slots)
    test_slots = await determine.hn_list_to_test_slots(config.POC_HYPER_NODES_LIST, slots)
    print("Tests Slots\n", test_slots)
    print("")
    print("Timeslots test")
    print("--------------------------")
    expected = [(config.ORIGIN_OF_TIME, 0, 0),
                (config.ORIGIN_OF_TIME + config.POS_SLOT_TIME_SEC * 1.5, 0, 1),
                (config.ORIGIN_OF_TIME + config.ROUND_TIME_SEC + config.POS_SLOT_TIME_SEC * 0.5, 1, 0),
                (config.ORIGIN_OF_TIME + config.ROUND_TIME_SEC + config.POS_SLOT_TIME_SEC * 1.5, 1, 1),
                (config.ORIGIN_OF_TIME + config.ROUND_TIME_SEC + config.POS_SLOT_TIME_SEC * 2.5, 1, 2),
                (config.ORIGIN_OF_TIME + config.ROUND_TIME_SEC + config.POS_SLOT_TIME_SEC * 3.5, 1, 3)
                ]
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
            if calc_slot < len(slots):
                print("Forger is {}".format(slots[calc_slot][0]))
                print("Tests:", test_slots[calc_slot])
            else:
                print("End of round...")
            time.sleep(60)
    except Exception as e:
        print(e)
        pass

if __name__ == "__main__":

    asyncio.Task(round_start())
    loop = asyncio.get_event_loop()
    loop.run_forever()
