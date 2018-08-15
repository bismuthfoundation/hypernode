"""
Common Helper functions for tests and benchmarks
"""


import os
from random import randint
import sys


sys.path.append('../modules')
import posblock


__version__ = '0.0.2'


def remove_mp():
    if os.path.isfile('./posmempool.db'):
        os.remove('./posmempool.db')


def remove_pc():
    if os.path.isfile('./poc_pos_chain.db'):
        os.remove('./poc_pos_chain.db')


def create_txs(nb=10, sign=False, block_height=0):
    # Generate 1000 random tx
    txs = []
    for i in range(nb):
        txs.append(random_tx(sign=sign, block_height=block_height))
    return txs


def random_tx(sign=True, block_height=0):
    tx = posblock.PosMessage().from_values(recipient='BHbbLpbTAVKrJ1XDLMM48Qa6xJuCGofCuH', value=str(randint(0, 1000)))
    tx.block_height = block_height
    if sign:
        try:
            tx.sign()
        except Exception as e:
            print(e)
    return tx
