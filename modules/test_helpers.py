"""
Common Helper functions for tests and benchmarks
"""


import os
from random import randint
import sys


sys.path.append('../modules')
import posblock


__version__ = '0.0.1'


def remove_mp():
    if os.path.isfile('./posmempool.db'):
        os.remove('./posmempool.db')


def create_txs(nb=10, sign=False):
    # Generate 1000 random tx
    txs = []
    for i in range(nb):
        txs.append(random_tx(sign=sign))
    return txs


def random_tx(sign=True):
    tx = posblock.PosMessage().from_values(recipient='BHbbLpbTAVKrJ1XDLMM48Qa6xJuCGofCuH', value=str(randint(0, 1000)))
    if sign:
        try:
            tx.sign()
        except Exception as e:
            print(e)
    return tx
