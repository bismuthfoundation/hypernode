"""
Test suite for crypto/addresses functions

Needs pytest, just run pytest -v in the test directory.
"""

import sys
import pytest
# import pytest_benchmark

sys.path.append('../modules')
import poscrypto


def test_make_addresses():
    pub_key = "d3ccc2eb64d578582d39924246f2c2bf0768491b85235f242e37f65c3a7ce77569fec4c67cba6d457a5d9a6ad8cecc15584f51bc401e1d7683db6c470acbe776".encode('ascii')
    print("pub_key", pub_key, "network", b'\x19')
    address = poscrypto.pub_key_to_addr(pub_key, b'\x19')
    print("address", address)
    assert address == 'B9oMPPW5hZEAAuq8oCpT6i6pavPJhgXViq'
    print("pub_key", pub_key, "network", b'\x55')
    address = poscrypto.pub_key_to_addr(pub_key, b'\x55')
    print("address", address)
    assert address == 'bJ5YTuPNJP2jEvCLGNoaCES2MBquR1nsLF'

    address = 'B9oMPPW5hZEAAuq8oCpT6i6pavPJhgXViq'
    poscrypto.validate_address(address, b'\x19')


def test_good_address():
    # Good address with good network
    address = 'B9oMPPW5hZEAAuq8oCpT6i6pavPJhgXViq'
    poscrypto.validate_address(address, b'\x19')


def test_mismatch_network():
    # Good address but mismatching network
    with pytest.raises(ValueError, match=r'Invalid Network'):
        address = 'bJ5YTuPNJP2jEvCLGNoaCES2MBquR1nsLF'
        poscrypto.validate_address(address, b'\x19')


def test_bad_format():
    # bad address format (alphabet)
    with pytest.raises(ValueError, match=r'Invalid address format'):
        address = 'bJ5YTuPNJP2jEV!CLGNoaCES2MBquR1nsLF'
        poscrypto.validate_address(address, b'\x19')

    # bad address format (len)
    with pytest.raises(ValueError, match=r'Invalid address format'):
        address = 'bJ5YTuPNJP2jEV!CLGoaCES2MBquR1nsLF'
        poscrypto.validate_address(address, b'\x19')


def test_bad_checksum():
    # bad address
    with pytest.raises(ValueError, match=r'Invalid address checksum'):
        address = 'bJ5YTuPNJP2jEVCLGNoaCES2MBquR1nsLF'
        poscrypto.validate_address(address, b'\x19')


if __name__ == "__main__":
    print("Run pytest -v for tests.\n")
    test_make_addresses()
