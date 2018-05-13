import struct
import time

import commands_pb2


__version__ = '0.0.31'


# Index for clients stats
STATS_ACTIVEP = 0
STATS_COSINCE = 1
STATS_LASTACT = 2
STATS_MSGSENT = 3
STATS_MSGRECV = 4
STATS_BYTSENT = 5
STATS_BYTRECV = 6
STATS_LASTMPL = 7
STATS_LASTHGT = 8

"""
Generic async stream com 
# TODO: move into a class?
"""

MY_NODE = None


def cmd_to_text(command):
    """
    Converts a protobuf Command id to a text
    :param command:
    :return:
    """
    return commands_pb2._COMMAND_TYPE.values[command].name


async def async_receive(stream, ip):
    """
    Get a command, async version
    :param stream:
    :param ip:
    :return:
    """
    global MY_NODE
    protomsg = commands_pb2.Command()
    header = await stream.read_bytes(4)
    if len(header) < 4:
        raise RuntimeError("Socket EOF")
    data_len = struct.unpack('>i', header[:4])[0]
    data = await stream.read_bytes(data_len)
    try:
        MY_NODE.clients[ip]['stats'][STATS_LASTACT] = time.time()
        MY_NODE.clients[ip]['stats'][STATS_MSGRECV] += 1
        MY_NODE.clients[ip]['stats'][STATS_BYTRECV] += 4 + data_len
    except:
        pass
    protomsg.ParseFromString(data)
    return protomsg


async def async_send(cmd, stream, ip):
    """
    Sends a protobuf command to the stream, async.
    :param cmd:
    :param stream:
    :param ip:
    :return:
    """
    # global app_log
    global MY_NODE
    # TODO : stats and time, ping
    try:
        data = cmd.SerializeToString()
        data_len = len(data)
        await stream.write(struct.pack('>i', data_len) + data)
        # print(MY_NODE.clients)
        try:
            MY_NODE.clients[ip]['stats'][STATS_LASTACT] = time.time()
            MY_NODE.clients[ip]['stats'][STATS_MSGSENT] += 1
            MY_NODE.clients[ip]['stats'][STATS_BYTSENT] += 4 + data_len
        except:
            pass
    except Exception as e:
        # app_log.error("_send ip {}: {}".format(ip, e))
        """
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        """
        raise


async def async_send_string(cmd, value, stream, ip):
    """
    Sends a command with string param to the stream, async.
    :param cmd:
    :param value:
    :param stream:
    :param ip:
    :return:
    """
    protocmd = commands_pb2.Command()
    protocmd.Clear()
    protocmd.command = cmd
    protocmd.string_value = value
    await async_send(protocmd, stream, ip)


async def async_send_int32(cmd, value, stream, ip):
    """
    Sends a command with int32 param to the stream, async.
    :param cmd:
    :param value:
    :param stream:
    :param ip:
    :return:
    """
    protocmd = commands_pb2.Command()
    protocmd.Clear()
    protocmd.command = cmd
    protocmd.int32_value = value
    await async_send(protocmd, stream, ip)


async def async_send_void(cmd, stream, ip):
    """
    Sends a command to the stream, async.
    :param cmd:
    :param stream:
    :param ip:
    :return:
    """
    protocmd = commands_pb2.Command()
    protocmd.Clear()
    protocmd.command = cmd
    await async_send(protocmd, stream, ip)


async def async_send_txs(cmd, txs, stream, ip):
    """
    Sends a list of tx to the stream, async.
    :param cmd:
    :param txs: a list of tx
    :param stream:
    :param ip:
    :return:
    """
    protocmd = commands_pb2.Command()
    protocmd.Clear()
    protocmd.command = cmd
    for tx in txs:
        tx.add_to_proto(protocmd)
    await async_send(protocmd, stream, ip)


async def async_send_height(cmd, height, stream, ip):
    """
    Sends a height status to the stream, async.
    :param cmd:
    :param height: a PosHeight object
    :param stream:
    :param ip:
    :return:
    """
    protocmd = commands_pb2.Command()
    protocmd.Clear()
    protocmd.command = cmd
    height.to_proto(protocmd.height_value)
    await async_send(protocmd, stream, ip)
