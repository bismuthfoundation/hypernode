"""
Pos Masternode class for Bismuth
"""

import socketserver
import threading
import time

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
            while not MY_NODE.stop_event.is_set():
                try:
                    # Failsafe
                    if self.request == -1:
                        raise ValueError("Inbound: Closed socket from {}".format(peer_ip))
                        return
                    msg = com_handler.get_message()
                    print("Server got message from {}".format(peer_ip), msg.__str__())
                    if msg.command == commands_pb2.Command.hello:
                        print("Got Hello {}".format(msg.string_value))
                        # TODO: check and send back commands_pb2.Command.hello if something is wrong
                        com_handler.send_string(commands_pb2.Command.hello, common.POSNET + MY_NODE.address)
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

"""
PoS MN Classe
"""


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
        # List of client threads
        self.clients = {}
        # list of peers I should stay connected to for a given round
        self.connect_to = []
        # Does the node try to connect to others?
        self.connecting = False
        # Time sensitive props
        self.poschain = poschain.MemoryPosChain(verbose=verbose)
        self.is_delegate = False
        self.round = 0
        self.sir = 0
        self.previous_round = 0
        self.previous_sir = 0
        # Locks
        self.round_lock = threading.Lock()
        self.clients_lock = threading.Lock()
        #  Events
        self.stop_event = threading.Event()
        # Control thread(s)
        self.manager_thread = threading.Thread(target=self.manager)
        self.manager_thread.daemon = True
        self.manager_thread.start()

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

    def manager(self):
        """
        Manager thread
        :return:
        """
        if self.verbose:
            print("Started MN Manager")
        # Initialise round/sir data
        self._check_round()
        while not self.stop_event.is_set():
            print(' Manager blip')
            status={'chain': self.poschain.status(), 'outgoing':list(self.clients.keys())}
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
                                client_thread.start()
                                self.clients[peer[0]] = client_thread


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
        if self.sir != self.previous_sir:
            # Update all sir related info
            if self.verbose:
                print("New Slot {} in Round {}".format(self.sir, self.round))
            self.previous_sir = self.sir
            if self.round != self.previous_round:
                # Update all round related info, we get here only once at the beginning of a new round
                if self.verbose:
                    print("New Round {}".format(self.round))
                self.previous_rounf = self.round
                # TODO : if we have connections, drop them.
                # wait for new list, so we keep cnx if we already are. or drop anyway? no, would add general network load at each round start.
                self.connect_to = determine.get_connect_to(self.peers, self.round, self.address)


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

