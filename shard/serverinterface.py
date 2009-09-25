"""Shard Server Interface

   Work started on 24. Sep 2009
"""

import shard
import cPickle
import SocketServer
import socket
from collections import deque

class ServerInterface:
    '''This is the base class for a Shard Server Interface.
       Implementations should subclass this one an override
       the default methods, which do nothing.'''

    def __init__(self, address_port_tuple, logger):
        '''Interface initialization.'''

        self.address_port_tuple = address_port_tuple

        # Attach logger
        #
        self.logger = logger

        # client_connections is a dict of
        # ClientConnection instances, indexed by
        # (address, port) tuples.
        #
        self.client_connections = {}

        # This is the flag which is set when shutdown()
        # is called.
        #
        self.shutdown_flag = False

        # And this is the one for the confirmation.
        #
        self.shutdown_confirmed = False

        self.logger.debug("complete")

    def handle_messages(self):
        '''The task of this method is to do whatever is
           necessary to send server messages and obtain 
           client messages. It is meant to be the back end 
           of send_message() and grab_message(). Put some 
           networking code, a GUI or a random generator 
           here. 
           This method is put in a background thread 
           automatically, so it can do all sorts of 
           polling or blocking IO.
           It should regularly check whether shutdown()
           has been called, and if so, it should notify
           shutdown() in some way (so that it can return
           True), and then raise SystemExit to stop 
           the thread.'''

        self.logger.debug("starting up")

        client_connections_proxy = self.client_connections
        logger_proxy = self.logger

        # We define the class here to be able
        # to access variables of the ServerInterface
        # instance.
        #
        class ShardRequestHandler(SocketServer.BaseRequestHandler):

            def handle(self):

                logger_proxy.debug("called")

                # Test for new client,
                # i.e. not (address, port) tuple in keys
                #
                if not self.client_address in client_connections_proxy:

                    # New client. Create a new ClientConnection
                    # and add it to the dict
                    #
                    client_connections_proxy[self.client_address] = ClientConnection()

                    logger_proxy.info("adding new client: " + str(self.client_address))

                # Append the message.
                # (inbetween steps to avoid a loong line ;-) )
                #
                message = cPickle.loads(self.request[0])

                connection = client_connections_proxy[self.client_address]

                connection.client_messages.append(message)

                # End of handle() method.

        # End of class.

        server = SocketServer.UDPServer(self.address_port_tuple, ShardRequestHandler)

        # Server timeout, so server.handle_request()
        # doesn't wait forever, which would prevent
        # shutdown.
        #
        server.timeout = 0.1

        # Run thread as long as no shutdown is requested
        #
        while not self.shutdown_flag:

            # TODO: several threads for send and receive

            # wait at most server.timeout seconds
            # until a request comes in:
            #
            server.handle_request()

            # Flush server event queues.
            # Iterate over dict keys:
            #
            for address_port_tuple in self.client_connections:

                connection = self.client_connections[address_port_tuple]

                if connection.server_messages:

                    self.logger.debug("sending 1 message of "
                                      + str(len(connection.server_messages))
                                      + " to client "
                                      + str(address_port_tuple))

                    server.socket.sendto(cPickle.dumps(connection.server_messages.popleft()), 
                                         address_port_tuple)

        # Caught shutdown notification, stopping thread
        #
        self.logger.info("shutting down")

        self.shutdown_confirmed = True

        raise SystemExit

    def shutdown(self):
        '''This method is called when the server is
           about to exit. It should notify 
           handle_messages() to raise SystemExit to stop 
           the thread properly. shutdown() must return 
           True when handle_messages() received the 
           notification and is about to exit.'''

        self.logger.info("called")

        # Set the flag to be caught by handle_messages()
        #
        self.shutdown_flag = True

        # Wait for confirmation (blocks interface and client!)
        #
        while not self.shutdown_confirmed:
            pass

        return True

class ClientConnection:
    '''For each client connection an instance of
       this class is created. 
    '''

    def __init__(self):

        # A hint from the Python documentation:
        # deques are a fast, thread-safe replacement
        # for queues.
        # Use deque.append(x) and deque.popleft()
        #
        self.client_messages = deque()
        self.server_messages = deque()

    def send_message(self, message):
        '''This method is called by the client 
           ClientControlEngine with a message ready to be sent to
           the server. The Message object given is an
           an instance of shard.Message. This method
           must return immediately to avoid blocking
           the client.'''

        self.server_messages.append(message)

        return

    def grab_message(self):
        '''This method is called by the client 
           ClientControlEngine to obtain a new server message.
           It must return an instance of shard.Message, 
           and it must do so immediately to avoid
           blocking the client. If there is no new
           server message, it must return an empty
           message.'''

        if self.client_messages:

            return self.client_messages.popleft()

        else:
            # A Message must be returned, so create
            # an empty one
            #
            return shard.Message([])
