"""
Deterministic helpers and/or classes for Bismuth PoS
"""

# Custom modules
import common
import poscrypto
import distance

__version__ = '0.0.1'

# local verbose switch
VERBOSE = True

REF_HASH = ''
REF_HASH_BIN = ''


def hash_distance(hash):
    """
    Returns Hamming's distance between the REF_HASH and the given hash
    :param hash1:
    :param hash2:
    :return:
    """
    global REF_HASH
    temp = distance.hamming(REF_HASH, hash)
    print(hash, temp)
    return temp


def hamming_distance(bin_hash):
    global REF_HASH_BIN
    return sum(ch1 != ch2 for ch1, ch2 in zip(REF_HASH_BIN, bin_hash))


def my_distance(hash):
    """
    Return the Hamming distance between a ticket and the ref hash
    :param string:
    :return:
    """
    global REF_HASH_BIN
    # Start with a distance of zero, and count up
    distance = 0
    # Loop over the indices of the string
    L = len(REF_HASH_BIN)
    hash = poscrypto.bin_convert(poscrypto.blake(hash[0]+str(hash[1])).hexdigest())
    for i in range(L):
        # Add 1 to the distance if these two characters are not equal
        if REF_HASH_BIN[i] != hash[i]:
            distance += 1  # abs(ord(REF_HASH_BIN[i]) - ord(hash[i]))
    # Return the final count of differences
    #if VERBOSE:
    #    print(hash, distance)
    return distance


def mn_list_to_tickets(mn_list):
    """
    :param mn_list: list of mn with properties
    :return: list of tickets for delegates determination
    """
    # mn_list is supposed to be ordered the same for everyone
    tickets = []
    # If we have less candidates than seats, re-add the list until we have enough.
    # Always parse the full list even if this means adding too many candidates
    # (this ensures everyone gets the same chance)
    id = 0
    while len(tickets) < common.MAX_ROUND_SLOTS:
        for mn in mn_list:
            # a more compact and faster version can be written, I prefer to aim at clarity
            for chances in range(mn[3]):  # index 3 is the weight
                tickets.append((mn[0], id))
                id += 1
    return tickets


def tickets_to_delegates(tickets_list, reference_hash):
    """
    Order and extract only the required number of candidates from the tickets
    :param tickets_list:
    :param reference_hash:
    :return:
    """
    # Set the reference Hash
    global REF_HASH
    global REF_HASH_BIN
    # For POC, we use the hex string, TODO: use raw digest() later.
    REF_HASH = reference_hash.hexdigest()
    # TODO: this is copied from Bismuth, need to use more efficient methond, no need to take the bin string conversion path.
    REF_HASH_BIN = poscrypto.bin_convert(REF_HASH)
    # sort the tickets according to their hash distance.
    tickets_list.sort(key=my_distance)
    if VERBOSE:
        #print("Ref Hash Bin", REF_HASH_BIN)
        print("Sorted Tickets:\n", tickets_list)
    return tickets_list[:common.MAX_ROUND_SLOTS]


if __name__ == "__main__":
    print("I'm a module, can't run!")