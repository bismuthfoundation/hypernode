"""
Benchmark for crypto/addresses functions

Needs pytest, just run pytest  in the test directory.
"""

import sys

sys.path.append('../modules')
import poscrypto
import test_helpers


def make_addresses():
    pub_key = "d3ccc2eb64d578582d39924246f2c2bf0768491b85235f242e37f65c3a7ce77569fec4c67cba6d457a5d9a6ad8cecc15584f51bc401e1d7683db6c470acbe776".encode('ascii')
    address = poscrypto.pub_key_to_addr(pub_key, b'\x19')
    assert address == 'B9oMPPW5hZEAAuq8oCpT6i6pavPJhgXViq'
    address = poscrypto.pub_key_to_addr(pub_key, b'\x55')
    assert address == 'bJ5YTuPNJP2jEvCLGNoaCES2MBquR1nsLF'
    address = 'B9oMPPW5hZEAAuq8oCpT6i6pavPJhgXViq'
    poscrypto.validate_address(address, b'\x19')


def validate_address():
    # Good address with good network
    address = 'B9oMPPW5hZEAAuq8oCpT6i6pavPJhgXViq'
    poscrypto.validate_address(address, b'\x19')


def test_bench_create(benchmark):
    """

    :param benchmark:
    :return:
    """
    # see http: // pytest - benchmark.readthedocs.io / en / stable / usage.html
    benchmark(make_addresses)


def test_bench_verify(benchmark):
    benchmark(validate_address)


def sign_txs(txs, verify=False):
    for tx in txs:
        tx.sign(verify=verify)


def test_tx_unsigned10(benchmark):
    poscrypto.load_keys('./bench_wallet.json')
    if benchmark:
        benchmark(test_helpers.create_txs, 10, False)
    else:
        test_helpers.create_txs(10, False)


def test_tx_sign10check(benchmark):
    poscrypto.load_keys('./bench_wallet.json')
    txs = test_helpers.create_txs(10, False)
    if benchmark:
        benchmark(sign_txs, txs, True)
    else:
        sign_txs(txs)


def test_tx_sign10nocheck(benchmark):
    poscrypto.load_keys('./bench_wallet.json')
    txs = test_helpers.create_txs(10, False)
    if benchmark:
        benchmark(sign_txs, txs, False)
    else:
        sign_txs(txs)


def test_tx_signed10(benchmark):
    poscrypto.load_keys('./bench_wallet.json')
    if benchmark:
        benchmark(test_helpers.create_txs, 10, True)
    else:
        test_helpers.create_txs(10, True)


if __name__ == "__main__":
    print("Run pytest -v for tests.\n")
    test_tx_signed10(None)
