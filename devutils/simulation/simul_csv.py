"""
Creates csv with many params and simulation results
"""

import json
# import os
import subprocess
import sys

#
HN_COUNT = 200
HN_UPTIME = 0.9
WAIT = 10
TESTS_PER_SLOT = 5

FNAME = 'simul_{}_{}_{}_{}_19slots.csv'.format(HN_COUNT, HN_UPTIME, WAIT, TESTS_PER_SLOT)

HEADERS = 'hn_count,hn_uptime,wait,test_per_slots,hn_to_juror,hn_to_hn,juror_to_juror'
HEADERS += ','
HEADERS += 'size_round,bps_per_node,mean_path,time_to_sync,disconnected,avg_degree,avg_degree_juror,min_degree_juror,' \
           'max_degree_juror,avg_degree_non_juror'


def simulate(HN_TO_JUROR, HN_TO_HN, JUROR_TO_JUROR):
    out = subprocess.getoutput(["python simul01.py {} {} {}".format(HN_TO_JUROR, HN_TO_HN, JUROR_TO_JUROR)])
    # print("out", out)
    first, second = out.split("\n")
    second = json.loads(second)
    csv1 = "{},{},{},{},{},{},{}".\
        format(HN_COUNT, HN_UPTIME, WAIT, TESTS_PER_SLOT, HN_TO_JUROR, HN_TO_HN, JUROR_TO_JUROR)
    csv2 = [str(value) for key, value in second.items() if key in
            ["size_round", "bps_per_node", "mean_path", "time_to_sync", "disconnected", "avg_degree",
             "avg_degree_juror", "min_degree_juror", "max_degree_juror", "avg_degree_non_juror"]]
    csv2 = ','.join(csv2)
    return csv1 + ',' + csv2


if __name__ == "__main__":
    with open(FNAME, 'w') as f:
        f.write(HEADERS + "\n")
        for hn_to_juror in range(1, 5):
            for hn_to_hn in range(5, 26):
                for juror_to_juror in range(5, 12):
                    print(hn_to_juror, hn_to_hn, juror_to_juror)
                    res = simulate(hn_to_juror + 1, hn_to_hn + 1, juror_to_juror +1)
                    f.write(res + "\n")
                    #print(res)
