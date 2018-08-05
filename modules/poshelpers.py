"""
Bismuth
Common helpers for PoS
"""

import os
import shutil
import tarfile
import logging

import requests

__version__ = '0.0.1'


# GENERIC HELPERS ##############################################################


def download_file(url: str, filename: str):
    """
    Fetch a file from an URL with progress indicator

    :param url:
    :param filename:
    :return:
    """
    r = requests.get(url, stream=True)
    total_size = int(r.headers.get('content-length')) / 1024
    with open(filename, 'wb') as filename:
        chunkno = 0
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                chunkno = chunkno + 1
                if chunkno % 10000 == 0:  # every x chunks
                    print("Downloaded {} %".format(int(100 * (chunkno / total_size))))
                filename.write(chunk)
                filename.flush()
        print("Downloaded 100 %")


def update_source(url: str, app_log: logging.log=None):
    """
    Update source file from an url

    :param url: url of the tgz archive
    :param app_log: optional log handler
    :return:
    """
    try:
        archive_path = "./hnd.tgz"
        download_file(url, archive_path)
        tar = tarfile.open(archive_path)
        tar.extractall("./")
        tar.close()
        # move to current dir
        from_dir = "./hnd_zip/"
        files = os.listdir(from_dir)
        for f in files:
            shutil.move(from_dir + f, './' + f)
    except Exception as e:
        if app_log:
            app_log.warning("Something went wrong in update_source: {}, aborted".format(e))
        raise


# Height Helpers #####################################################################


def same_height(peer_status: dict, our_status: dict):
    """
    Compares not only the height but the whole properties, including Round, Slot In Round and block hash.

    :param peer_status:
    :param our_status:
    :return: Boolean
    """
    for key in ("height", "round", "sir", "block_hash"):
        if peer_status[key] != our_status[key]:
            return False
    return True


def first_height_is_better(height_a: dict, height_b: dict):
    """
    Compares properties of the heights to tell which one is to keep in case of forks.
    Uses 'forgers', 'forgers_round', 'uniques', 'uniques_round', 'round', 'height'

    :param height_a:
    :param height_b:
    :return: Boolean, True if a is > b
    """
    if height_a['forgers'] > height_b['forgers']:
        return True
    if height_a['forgers_round'] > height_b['forgers_round']:
        return True
    if height_a['uniques_round'] > height_b['uniques_round']:
        return True
    if height_a['round'] > height_b['round']:
        return True
    if height_a['height'] > height_b['height']:
        return True
    """
    if height_a['uniques'] > height_b['uniques']:
        return True
    """
    return False


def heights_match(height_a: dict, height_b: dict):
    """
    Checks if simulated height_b fits the predicate height_a
    only checks the current round info, not the whole chain.

    :param height_a: a height dict
    :param height_b: a height dict
    :return: boolean
    """
    for key in ('height', 'round', 'sir', 'block_hash', 'uniques_round', 'forgers_round'):
        if height_a.get(key) != height_b.get(key):
            return False
    return True


# Peer format helpers ###########################################################################

def peer_to_fullpeer(peer: tuple):
    """
    converts a tuple (address, ip, port, active) to a string ip:0port

    :param peer:
    :return:
    """
    return peer[1] + ':' + str(peer[2]).zfill(5)


def ipport_to_fullpeer(ip: str, port: int):
    return ip + ':' + str(port).zfill(5)


if __name__ == "__main__":
    print("I'm a module, can't run!")
