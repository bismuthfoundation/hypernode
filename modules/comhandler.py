# Command Handler
# Abstraction for the socket connection dialog

import struct
import socks
import time

# Our modules
import commands_pb2

__version__ = '0.0.2'

# Logical timeout
LTIMEOUT = 45
# Fixed header length for legacy protocol
SLEN = 10

# Index for stats 
STATS_COSINCE = 0
STATS_MSGSENT = 1
STATS_MSGRECV = 2
STATS_BYTSENT = 3
STATS_BYTRECV = 4


class Connection:
    """The connection layer and command hander"""

    def __init__(self, socket = None, logstats= True):
        """ Socket may be provided when in the context of a threaded TCP Server.
        """
        # cmd : from us to peer
        self.protocmd = commands_pb2.Command()
        # msg : from peer to us
        self.protomsg = commands_pb2.Command()
        self.logstats = logstats
        self.socket = socket
        self.peer_ip = ''
        self.connected = False
        # first 4 bytes allow to ID the protocol version, it's the message len on 4 bytes.
        self.first_bytes = []
        # connection stats
        self.stats = [0, 0, 0, 0, 0]
        # last socket activity
        self.last_activity = 0
        if socket:
            self.connected = True
            self.peer_ip = socket.getpeername()[0]
            if logstats:
                self.stats[STATS_COSINCE] = time.time()

    def status(self):
        """Returns a status as a dict"""
        status={"connected":self.connected, "peer_ip":self.peer_ip, "stats":self.stats}
        return status

    def connect(self, host='127.0.0.1', port=6568, timeout=LTIMEOUT):
        """
        Initiate connection to the given host,
        """
        self.socket = socks.socksocket()
        self.socket.settimeout(timeout)
        self.socket.connect((host, port))
        if self.socket:
            self.connected = True
            self.peer_ip = host
            if self.logstats:
                self.stats[STATS_COSINCE] = time.time()

    def _get(self, header=None):
        if not self.connected:
            raise ValueError("Not connected")
        if header == None:
            header=self.socket.recv(4)
        if len(header) < 4:
            raise RuntimeError("Socket EOF")
        size=struct.unpack('>i', header[:4])[0]
        if self.logstats:
            self.stats[STATS_MSGRECV] += 1
        data=self.socket.recv(size)
        self.protomsg.ParseFromString(data)
        self.last_activity = time.time()
        if self.logstats:
            self.stats[STATS_BYTRECV] += 4+size

    def init_client(self):
        """Call once for a new inbound client. Will Handle the Communication start
           The socket has to be new, nothing processed yet"""
        if not self.connected:
            raise ValueError("Not connected")
        self.first_bytes=self.socket.recv(4)
        if len(self.first_bytes) < 4:
            raise RuntimeError("Socket EOF")
        self._get(self.first_bytes)
        return self.protomsg

    def _send(self):
        if not self.connected:
            raise ValueError("Not connected")
        if self.logstats:
            self.stats[STATS_MSGSENT] += 1
        data = self.protocmd.SerializeToString()
        data_len = len(data)
        self.socket.sendall(struct.pack('>i', data_len) + data)
        self.last_activity = time.time()
        if self.logstats:
            self.stats[STATS_BYTSENT] += 4 + data_len

    def send_void(self, cmd):
        """sends a command without param"""
        self.protocmd.Clear()
        self.protocmd.command = cmd
        self._send()

    def send_string(self, cmd, value):
        """sends a command with string param"""
        self.protocmd.Clear()
        self.protocmd.command = cmd
        self.protocmd.string_value = value
        self._send()

    def send_int32(self, cmd, value):
        """sends a command with an int32 param"""
        self.protocmd.Clear()
        self.protocmd.command = cmd
        self.protocmd.int32_value = value
        self._send()

    def get_message(self):
        """returns a full message from a peer"""
        self._get()
        return self.protomsg
