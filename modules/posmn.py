"""
Pos Masternode class for Bismuth
"""

import socketserver
import threading
import time
from enum import Enum

# Our modules
import commands_pb2
import comhandler
import common
import determine
import poschain

__version__ = '0.0.1'

"""
I use a global object to keep the state and route data between the servers and threads.
This looks not clean to me.
Will have to refactor if possible all in a single object, but looks hard enough, so postponing. 
"""
MY_NODE = None


"""
TCP Server Classes
"""


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


ThreadedTCPServer.allow_reuse_address = True
ThreadedTCPServer.daemon_threads = True
ThreadedTCPServer.timeout = 60
ThreadedTCPServer.request_queue_size = 100


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):  # server defined here
        global MY_NODE
        peer_ip = 'n/a'  # in case request fails.
        peer_ip = self.request.getpeername()[0]
        # TODO: here, use tiered system to reserve safe slots for jurors, some slots for non juror mns, and some others for other clients (non mn clients)
        # and reject right here from ip
        """
        if threading.active_count() < thread_limit_conf or peers.is_whitelisted(peer_ip):
            capacity = 1
        else:
            capacity = 0
            try:
                self.request.close()
                #app_log.info("Free capacity for {} unavailable, disconnected".format(peer_ip))
                # if you raise here, you kill the whole server
            except:
                pass
            finally:
                return
        """
        try:
            com_handler = comhandler.Connection(socket=self.request)
            # TODO: here, allow for a shorter timeout, so we don't lock up a thread for 45 sec if a node just connects and does nothing
            msg = com_handler.get_message()
            print("Server got message from {}".format(peer_ip), msg.__str__())
            if msg.command == commands_pb2.Command.hello:
                print("Got Hello {}".format(msg.string_value))
                # TODO: check and send back commands_pb2.Command.ko if something is wrong
                com_handler.send_string(commands_pb2.Command.hello, common.POSNET + MY_NODE.address)
                MY_NODE.add_inbound(peer_ip, {'hello': msg.string_value})
            else:
                print("{} did not say hello".format(peer_ip))
                # TODO: Should we send back a proper ko message in that case?
                return
            # Here, the client has proved to be valid, so we enter a long term relationship
            while not MY_NODE.stop_event.is_set():
                try:
                    # Failsafe
                    if self.request == -1:
                        raise ValueError("Inbound: Closed socket from {}".format(peer_ip))
                        return
                    msg = com_handler.get_message()
                    print("Server got message from {}".format(peer_ip), msg.__str__())
                    if msg.command == commands_pb2.Command.ping:
                        print("Got Ping {}".format(msg.string_value))

                    #data = connections.receive(self.request, 10)
                    print(' TCP blip', peer_ip)
                    #print(MY_NODE.status())
                    #time.sleep(10)
                except Exception as e:
                    print("TCP Server loop", peer_ip, e)
                    return
        except Exception as e:
            print("TCP Server init", peer_ip, e)
            return
        finally:
            MY_NODE.remove_inbound(peer_ip)

"""
PoS MN Classe
"""


class MNState(Enum):
    """
    Current State of the MN
    """
    START = 0
    SYNCING = 1
    TESTING = 2
    STRONG_CONSENSUS = 3
    MINIMAL_CONSENSUS = 4
    FORGING = 5
    SENDING = 6


class Posmn:
    """The PoS Masternode object"""

    def __init__(self, ip, port, address='', peers=None, verbose = False):
        self.ip = ip
        self.port = port
        self.address = address
        self.peers = peers
        self.verbose = verbose
        self.server_thread = None
        self.server = None
        self.state = MNState.START
        # List of client threads
        self.clients = {}
        # list of inbound server connections
        self.inbound = {}
        # list of peers I should stay connected to for a given round
        self.connect_to = []
        # Does the node try to connect to others?
        self.connecting = False
        # Time sensitive props
        self.poschain = poschain.MemoryPosChain(verbose=verbose)
        self.is_delegate = False
        self.round = -1
        self.sir = -1
        self.previous_round = 0
        self.previous_sir = 0
        self.forger = None
        # Locks
        self.round_lock = threading.Lock()
        self.clients_lock = threading.Lock()
        self.inbound_lock = threading.Lock()
        #  Events
        self.stop_event = threading.Event()
        # Control thread(s)
        self.manager_thread = threading.Thread(target=self.manager)
        self.manager_thread.daemon = True
        self.manager_thread.start()

    def add_inbound(self, ip, properties={}):
        """
        Safely add a distant peer from server thread.
        This is called only after initial exchange and approval
        :param ip:
        :param properties:
        :return:
        """
        with self.inbound_lock:
            self.inbound[ip] = properties

    def remove_inbound(self, ip):
        """
        Safely remove a distant peer from server thread
        :param ip:
        :return:
        """
        with self.inbound_lock:
            del self.inbound[ip]

    def update_inbound(self, ip, properties):
        """
        Safely update info for a connected peer
        :param ip:
        :param properties:
        :return:
        """
        with self.inbound_lock:
            self.inbound[ip] = properties

    def stop(self):
        """
        Signal to stop cleanly
        :return:
        """
        print("Trying to close nicely...")
        self.stop_event.set()
        # TODO: wait for potential threads to finish
        try:
            pass
            # A long sleep time will make nice close longer if we wait for the thread to finish
            # Since it's a daemon thread, we can leave it alone
            # self.manager_thread.join()
        except Exception as e:
            print("Closing", e)
        print("Closed.")

    @property
    def connected_count(self):
        """
        True is at least one client or server connection is active.
        :return:
        """
        inbound_count = len(self.inbound)
        clients_count = 0
        # TODO: use another list to avoid counting one by one?
        for client in self.clients:
            if client[1]:
                clients_count += 1
        return inbound_count + clients_count

    def manager(self):
        """
        Manager thread. Responsible for managing inner state of the node.
        :return:
        """
        if self.verbose:
            print("Started MN Manager")
        # Initialise round/sir data
        self._check_round()
        while not self.stop_event.is_set():
            # Ajust state depending of the connection state
            if self.connected_count > 0:
                if self.state == MNState.START:
                    self.state = MNState.SYNCING
            elif self.state == MNState.SYNCING:
                self.state = MNState.START
            print(' Manager blip')
            status={'chain': self.poschain.status(),
                    'outgoing':list(self.clients.keys()),
                    'state':{'state': self.state.name,
                             'round':self.round,
                             'sir':self.sir,
                             'forger':self.forger}}
            print(status)
            if self.connecting:
                if len(self.clients) < len(self.connect_to):
                    # Try to connect to our missing pre-selected peers
                    for peer in self.connect_to:
                        if peer[0] not in self.clients:
                            """
                            if self.verbose:
                                print("Trying to connect to ", peer[0])
                            """
                            # Will be self-deleted from self.clients when thread closes
                            client_thread = threading.Thread(target=self.client_worker,  args=(peer,))
                            client_thread.daemon = True
                            with self.clients_lock:
                                self.clients[peer[0]] = [client_thread, False]
                                client_thread.start()


            # TODO: variable sleep time depending on the elapsed loop time
            time.sleep(10)
            self._check_round()

    def client_worker(self, peer):
        """
        Client worker, running in a thread.
        Tries to connect to the given peer, terminates on error and deletes itself on close.
        :param peer:
        :return:
        """
        try:
            if self.verbose:
                print("Should try to connect to", peer)
            com_handler = comhandler.Connection()
            com_handler.connect(peer[1], peer[2])
            com_handler.send_string(commands_pb2.Command.hello, common.POSNET+self.address)
            msg = com_handler.get_message()
            if msg.command == commands_pb2.Command.hello:
                # TOOO: decompose posnet/address and check. use helper.
                print("Worker got Hello {}".format(msg.string_value))
            if msg.command == commands_pb2.Command.ko:
                print("Worker got ko {}".format(msg.string_value))
                # Wait here so we don't retry immediatly?
                time.sleep(60)
                return
            # now we can enter a long term relationship with this node.
            with self.clients_lock:
                # Set connected status
                self.clients[peer[0]][1] = True
            while not self.stop_event.is_set():
                time.sleep(10)
                # Only send ping if time is due.
                if com_handler.last_activity < time.time()-30:
                    if self.verbose:
                        print("Sending ping to", peer[0])
                    com_handler.send_void(commands_pb2.Command.ping)  # keeps connection active, or raise error if connection lost
            raise ValueError("Closing")
        except Exception as e:
            if self.verbose:
                print("Connection lost to {} because {}".format(peer[0], e))
        finally:
            with self.clients_lock:
                del self.clients[peer[0]]

    def _check_round(self):
        """
        Adjust round/slots depending properties.
        Always called from the manager thread only.
        Should not be called too often (1-10sec should be plenty)
        :return:
        """
        self.round, self.sir = determine.timestamp_to_round_slot(time.time())
        if (self.sir != self.previous_sir) or (self.round != self.previous_round):
            with self.round_lock:
                # Update all sir related info
                if self.verbose:
                    print("New Slot {} in Round {}".format(self.sir, self.round))
                self.previous_sir = self.sir
                if self.round != self.previous_round:
                    # Update all round related info, we get here only once at the beginning of a new round
                    if self.verbose:
                        print("New Round {}".format(self.round))
                    self.previous_round = self.round
                    # TODO : if we have connections, drop them.
                    # wait for new list, so we keep cnx if we already are. or drop anyway? no, would add general network load at each round start.
                    self.connect_to = determine.get_connect_to(self.peers, self.round, self.address)
                    tickets = determine.mn_list_to_tickets(self.peers)
                    # TODO: real hash
                    self.slots = determine.tickets_to_delegates(tickets, common.POC_LAST_BROADHASH)
                    if self.verbose:
                        print("Slots\n", self.slots)
                    self.test_slots = determine.mn_list_to_test_slots(self.peers, self.slots)
                if self.sir < len(self.slots):
                    self.forger = self.slots[self.sir][0]
                    if self.verbose:
                        print("Forger is {}".format(self.forger))
                else:
                    self.forger = None


    def serve(self):
        """
        Run the socker server
        :return:
        """
        if self.verbose:
            print(self.status())
        try:
            self.server = ThreadedTCPServer((self.ip, self.port), ThreadedTCPRequestHandler)
            # Start a thread with the server -- that thread will then start one
            # more thread for each request
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            # Exit the server thread when the main thread terminates
            self.server_thread.daemon = True
            self.server_thread.start()
            if self.verbose:
                print("Server started {}:{}".format(self.ip, self.port))
        except Exception as e:
            print("Serve", e)

    def connect(self):
        """
        Initiate outgoing connections
        :return:
        """
        self.connecting = True
        # Will be handled by the manager.


    def status(self):
        """
        :return: MN Status info
        """
        return {'config':{'ip':self.ip, 'port':self.port, 'verbose':self.verbose},
                'peers': self.peers,
                'round':{'ts':time.time(), 'round':self.round, 'sir':self.sir}}

