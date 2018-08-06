"""
Connectivity simulation
"""

from igraph import *
import json
import math
import random
import sys

from utils import bytes2human

# Distribution of the HN weights
WEIGHT_PROFILE = [1,1,1,1,1,1,2,2,2,3,3]

HN_COUNT = 100
# not used in practice
JURORS_COUNT = 51

MAX_ROUND_SLOTS = 11
END_ROUND_SLOTS = 1

HN_TO_JUROR = 1
HN_TO_HN = 1  # math.ceil((HN_COUNT - JURORS_COUNT) / 50.0)
JUROR_TO_JUROR = 5  # math.ceil(JURORS_COUNT * 1.0 / 3.0)

"""
HN_TO_JUROR = 3
HN_TO_HN = 10  
JUROR_TO_JUROR = 11  
"""

HN_TO_JUROR = 1
HN_TO_HN = 5
JUROR_TO_JUROR = 3

#
HN_UPTIME = 0.9

# ------------------------------------------------------------------
WAIT = 10
TESTS_PER_SLOT = 5

TX_PER_SLOT = HN_COUNT * HN_UPTIME * TESTS_PER_SLOT

TX_AVG_SIZE_BYTES = 256

MESSAGE_AVG_SIZE_BYTES = 64

# test with 2h round and 10 min slot time
ROUND_TIME_SEC = 3600

SLOT_TIME_SEC = ROUND_TIME_SEC / (MAX_ROUND_SLOTS + END_ROUND_SLOTS)

MESSAGE_PER_LINK_PER_ROUND = 2 * ROUND_TIME_SEC / WAIT

BLOCK_SIZE = TX_PER_SLOT * TX_AVG_SIZE_BYTES + MESSAGE_AVG_SIZE_BYTES

NETWORK_BYTES_PER_ROUND_PER_LINK = MESSAGE_PER_LINK_PER_ROUND * MESSAGE_AVG_SIZE_BYTES \
                                   + TX_AVG_SIZE_BYTES * TX_PER_SLOT * MAX_ROUND_SLOTS \
                                   + BLOCK_SIZE * MAX_ROUND_SLOTS

# ------------------------------------------------------------------

# number of runs to compute stats upon
RUNS = 50  # 100
# number of rounds to simulate with a given network topology/state (weigths, on/off, but connections and jurors changes)
ROUNDS_PER_RUN = 2  # 5

# --------------------------------------------------------------------
PALETTE = ["#DB79F9","#5C69F0","#79C011","#A298AD","#5ECE8E","#F58737","#633F34","#F88FD4","#1A519E","#607802","#9F0D24"]
# PALETTE = ["#4BC8D3","#86CB8D","#EA4900","#957F05","#EC85EE","#94C2D7","#185616","#C18593","#6E3090","#F350AE","#A10F5D"]


def calc_tickets():
    global TICKETS
    TICKETS = []
    # If we have less candidates than seats, re-add the list until we have enough.
    # Always parse the full list even if this means adding too many candidates
    # (this ensures everyone gets the same chance)
    tid = 0
    while len(TICKETS) < MAX_ROUND_SLOTS:
        for hn in NODES:
            for chances in range(hn['weight']):
                TICKETS.append((hn['index'], tid))
                tid += 1


def add_link(from_node, to_node):
    global NODES
    global LINKS
    # print(from_node, to_node)
    LINKS.append((from_node, to_node))
    NODES[from_node]['out'] += 1
    NODES[to_node]['in'] += 1


def build_nodes():
    global NODES
    global DOWN_COUNT
    NODES = []
    # random.seed("Fix me")
    # Create the HN list
    DOWN_COUNT = 0
    for i in range(HN_COUNT):
        # Some will be down
        down = random.random() > HN_UPTIME
        if down:
            DOWN_COUNT += 1
        weight = random.choice(WEIGHT_PROFILE)
        hn = {"index": i, 'in': 0, 'out': 0, 'juror': False, 'down': down, 'weight': weight, 'times_juror': 0}
        NODES.append(hn)

def do_run():
    global TICKETS
    global LINKS

    TICKETS = []
    LINKS = []
    # Reset state
    for i in range(HN_COUNT):
        NODES[i]['juror'] = False
        NODES[i]['in'] = 0
        NODES[i]['out'] = 0
    # define the jurors
    calc_tickets()
    random.shuffle(TICKETS)
    TICKETS = TICKETS[:MAX_ROUND_SLOTS]
    jurors = []
    for ticket in TICKETS:
        NODES[ticket[0]]['juror'] = True
        NODES[ticket[0]]['times_juror'] += 1
        jurors.append(ticket[0])
    # Avoid dups
    jurors = list(set(jurors))
    # print(jurors)
    non_jurors = [node['index'] for node in NODES if not node['juror']]  # list of non jurors index
    # up_jurors = [juror for juror in jurors if not NODES[juror]['down']]
    # jurors_count = len(jurors)
    # up_jurors_count = len(up_jurors)
    # Connect
    for i in range(HN_COUNT):
        # print('node', i, NODES[i]['juror'])
        if NODES[i]['down']:
            continue  # host is non connectible.
        if NODES[i]['juror']:
            # jurors connect to JUROR_TO_JUROR other jurors
            candidates = [juror for juror in jurors if juror != i]  # remove myself
            random.shuffle(candidates)
            candidates = candidates[:JUROR_TO_JUROR]
            for candidate in candidates:
                if not NODES[candidate]['down']:
                    add_link(i, candidate)
        else:
            # regular nodes connect to 3 jurors
            random.shuffle(jurors)
            candidates = jurors[:HN_TO_JUROR]
            # print("candidates", candidates)
            for candidate in candidates:
                if not NODES[candidate]['down']:
                    add_link(i, candidate)
            # and to HN_TO_HN regular
            random.shuffle(non_jurors)
            candidates = non_jurors[:HN_TO_HN]
            for candidate in candidates:
                if not NODES[candidate]['down']:
                    add_link(i, candidate)


def color(node):
    if node['juror']:
        color = PALETTE[0]
    else:
        color = PALETTE[1]
    if node['down']:
        if node['juror']:
            color = PALETTE[2]
        else:
            color = PALETTE[3]
    return color


def get_stats():
    global g
    global DOWN_COUNT
    g = Graph()
    g.add_vertices(len(NODES))
    for link in LINKS:
        from_juror = NODES[link[0]]['juror']
        link_color = PALETTE[0] if from_juror else "#aaaaaa"
        g.add_edge(link[0], link[1], link_color=link_color)
    # print(g.degree_distribution())
    giant = max(g.components().sizes())
    running = HN_COUNT - DOWN_COUNT
    stats = {}
    stats['down_count'] = DOWN_COUNT
    stats['size_round'] = int(len(LINKS) * NETWORK_BYTES_PER_ROUND_PER_LINK)
    stats['size_round_human'] = bytes2human(stats['size_round']) + 'Byte'
    stats['byte_per_sec'] = int(stats['size_round'] / ROUND_TIME_SEC)
    stats['size_round_per_node'] = int(stats['size_round'] / HN_COUNT)
    stats['byte_per_sec_per_node'] = int(stats['byte_per_sec'] / HN_COUNT)
    stats['bps_per_node'] = int(stats['byte_per_sec'] / HN_COUNT * 8)
    stats['bps_node_human'] = bytes2human(stats['byte_per_sec'] / HN_COUNT * 8) + 'bps'
    stats['monthly_node_traffic_human'] = bytes2human(stats['byte_per_sec'] / HN_COUNT * 3600 * 24 * 30.5) + 'B'
    path_length_hist = g.path_length_hist(directed=False)
    stats['mean_path'] = path_length_hist.mean
    stats['time_to_sync'] = math.ceil(stats['mean_path']) * WAIT
    stats['time_to_sync_pc_human'] = str(math.ceil(stats['time_to_sync'] / SLOT_TIME_SEC * 100)) + '%'
    stats['disconnected'] = running - giant
    stats['avg_degree'] = mean([node['in'] + node['out'] for node in NODES])
    stats['avg_degree_juror'] = mean([node['in'] + node['out'] for node in NODES if node['juror']])
    stats['avg_degree_non_juror'] = mean([node['in'] + node['out'] for node in NODES if not node['juror']])
    return stats


def show_graph():
    global g
    # layout_kamada_kawai
    # layout_fruchterman_reingold
    # layout_reingold_tilford_circular
    # layout_drl #no
    layout = g.layout_kamada_kawai()
    #  layout = g.layout_reingold_tilford_circular()
    visual_style = {}
    visual_style["vertex_size"] = [6 * node['weight'] for node in NODES]
    visual_style["vertex_color"] = [color(node) for node in NODES]
    visual_style["edge_arrow_size"] = 0.6;
    visual_style["arrow_width"] = 5;
    visual_style["edge_curved"] = 0.5;
    visual_style["edge_color"] = "#666666"
    visual_style["edge_color"] = [link['link_color'] for link in g.es.select()]
    #  visual_style["edge_width"] = [1 + 4*link['from_juror'] for link in g.es.select()]
    # g.es.select(_source=2)
    plot(g, "test1.png", layout=layout, **visual_style)
    g.write_edgelist("test1.txt")
    plot(g, layout=layout, **visual_style)


def global_stats(verbose=True):
    global STATS
    total = {key:0 for key in STATS[0] if not 'human' in key}
    for stat in STATS:
        for key in total:
            total[key] += stats[key]
    for key in total:
        total[key] /= len(STATS)
    total['size_round_human'] = bytes2human(total['size_round']) + 'Byte'
    total['bps_node_human'] = bytes2human(total['byte_per_sec'] / HN_COUNT * 8) + 'bps'
    total['monthly_node_traffic_human'] = bytes2human(total['byte_per_sec'] / HN_COUNT * 3600 * 24 * 30.5) + 'B'
    total['time_to_sync_pc_human'] = str(math.ceil(total['time_to_sync'] / SLOT_TIME_SEC * 100)) + '%'
    if verbose:
        print(json.dumps(total))
    return total


if __name__ == "__main__":
    if len(sys.argv) > 1:
        HN_TO_JUROR , HN_TO_HN, JUROR_TO_JUROR = map(int, sys.argv[1:])
    print(json.dumps({"HN_COUNT": HN_COUNT, "HN_TO_JUROR": HN_TO_JUROR, "HN_TO_HN": HN_TO_HN,
                      "JUROR_TO_JUROR": JUROR_TO_JUROR, "HN_UPTIME": HN_UPTIME, "WAIT": WAIT,
                      "TESTS_PER_SLOT": TESTS_PER_SLOT}))
    STATS = []
    for run in range(RUNS):
        build_nodes()
        for round in range(ROUNDS_PER_RUN):
            do_run()
            stats = get_stats()
            STATS.append(stats)
    global_stats(True)
    # show_graph()
