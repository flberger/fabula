"""Shard Interface Classes

   Work started on 28. Sep 2009

   Based on former client- and server
   interface implementations

   Shard Client Interface extracted from
   shard.py on 22. Sep 2009

   Shard Message Buffer based on methods from
   ClientInterface and the ClienConnection class
   in ServerInterface

   Work on Shard server interface started
   on 24. Sep 2009
"""

import shard
from collections import deque
import socket
import cPickle
import SocketServer

class Interface:
    """This is a base class for Shard interfaces
       which handle all the network traffic. A
       custom implementation using Shard will
       likely have an client- and a server side
       interface.
    """

    def __init__(self, address_port_tuple, logger):
        """Most likey you will want to override
           this method. Be sure to call
           self.setup_interface() with the
           appropriate arguments in your
           implementation. This is also what
           the default implementation does.
        """

        setup_interface(address_port_tuple, logger)

    def setup_interface(self, address_port_tuple, logger):
        """An interface is initialized with an
           ("address", port) tuple holding the
           server's address and port, and an
           instance of logging.Logger. Be sure
           to call this method from __init__()
           when subclassing.
        """

        self.address_port_tuple = address_port_tuple

        # Attach logger
        #
        self.logger = logger

        # This is the flag which is set when shutdown()
        # is called.
        #
        self.shutdown_flag = False

        # And this is the one for the confirmation.
        #
        self.shutdown_confirmed = False

    def handle_messages(self):
        """This is the main method of an interface
           class. It must transfer all the messages
           between local and remote host. This
           method is put in a background thread by
           the startup script, so your implementation
           can do all sorts of polling or blocking IO.
           It should regularly check whether shutdown()
           has been called (checking self.shutdown_flag),
           and if so, it should notify shutdown() by
           setting self.shutdown_confirmed to true (so
           that method can return True itself), and then
           raise SystemExit to stop the thread.
           The default implementation does nothing, but
           will handle the shutdown as described.
        """

        # Run thread as long as no shutdown is requested
        #
        while not self.shutdown_flag:
            pass

        # Caught shutdown notification, stopping thread
        #
        self.logger.info("shutting down")

        self.shutdown_confirmed = True

        raise SystemExit

    def shutdown(self):
        """This method is called when the engine is
           about to exit. It notifies handle_messages()
           to raise SystemExit to stop the thread
           properly by setting self.shutdown_flag.
           shutdown() will return True when
           handle_messages() received the notification
           and is about to exit.
        """

        self.logger.info("called")

        # Set the flag to be caught by handle_messages()
        #
        self.shutdown_flag = True

        # Wait for confirmation (blocks interface and client!)
        #
        while not self.shutdown_confirmed:
            pass

        return True


class MessageBuffer:
    """Buffer messages received and to be sent
       over the network.
    """

    def __init__(self):
        """This is meant to be a base class
           to be inherited from. This default
           __init__() method simply calls
           self.message_buffer_setup(). You
           should do so, too, when subclassing
           this with a custom implementation.
        """

        self.message_buffer_setup()

    def message_buffer_setup(self):
        """This method sets up the internal
           queues (in this case instances
           of collections.deque)
        """

        # A hint from the Python documentation:
        # deques are a fast, thread-safe replacement
        # for queues.
        # Use deque.append(x) and deque.popleft()
        #
        self.messages_for_local = deque()
        self.messages_for_remote = deque()

    def send_message(self, message):
        """This method is called by the local
           engine with a message ready to be sent to
           the remote host. The Message object given
           is an instance of shard.Message. This method
           must return immediately to avoid blocking.
        """

        self.messages_for_remote.append(message)

        return

    def grab_message(self):
        """This method is called by the local
           engine to obtain a new buffered message
           from the remote host. It must return an
           instance of shard.Message, and it must
           do so immediately to avoid blocking. If
           there is no new message from remote, it
           must return an empty message.
        """

        if self.messages_for_local:

            return self.messages_for_local.popleft()

        else:
            # A Message must be returned, so create
            # an empty one
            #
            return shard.Message([])


class ClientInterface(MessageBuffer, Interface):
    '''This is the base class for a Shard Client Interface.
       Implementations should subclass this one an override
       the default methods, which showcase a simple example.'''

    def __init__(self, address_port_tuple, logger):
        '''Interface initialization.'''

        # First call setup_interface() from the
        # base class
        #
        self.setup_interface(address_port_tuple, logger)

        # This is a subclass of MessageBuffer, but
        # since we override __init__(), we have to
        # call message_buffer_setup().
        #
        self.message_buffer_setup()

        # Set up UDP socket
        # It wouldn't be unreasonable to also use
        # a SocketServer on the client side. But
        # since the client is only ever supposed
        # to handle one connection, direct socket
        # handling may be just right.
        #
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # The socket timeout is used for
        # socket.recv() operations, which
        # take turns with socket.sendto().
        #
        self.sock.settimeout(0.3)

        self.logger.info("complete")

    def handle_messages(self):
        '''The task of this method is to do whatever is
           necessary to send client messages and obtain 
           server messages. It is meant to be the back end 
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

        # Run thread as long as no shutdown is requested
        #
        while not self.shutdown_flag:

            if self.messages_for_remote:

                self.logger.debug("sending 1 message of " + str(len(self.messages_for_remote)))

                self.sock.sendto(cPickle.dumps(self.messages_for_remote.popleft()), 
                                 self.address_port_tuple)

            # Now listen for incoming server
            # messages for some time
            # (set in __init__()). This will
            # catch any messages received in
            # the meantime by the OS (tested).
            #
            data_received = ""

            try:

                data_received = self.sock.recv(4096)

            except socket.timeout:

                # We do not log here since this
                # happens too often
                #
                pass

            if data_received:

                # TODO: accepts data from *anywhere*

                self.logger.debug("received server message")

                self.messages_for_local.append(cPickle.loads(data_received))

        # Caught shutdown notification, stopping thread
        #
        self.logger.info("shutting down")

        self.shutdown_confirmed = True

        raise SystemExit


class ServerInterface(Interface):
    '''This is the base class for a Shard Server Interface.
       Implementations should subclass this one an override
       the default methods, which do nothing.'''

    def __init__(self, address_port_tuple, logger):
        '''Interface initialization.'''

        # First call setup_interface() from the
        # base class
        #
        self.setup_interface(address_port_tuple, logger)

        # client_connections is a dict of MessageBuffer
        # instances, indexed by (address, port) tuples.
        #
        self.client_connections = {}

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

                    # New client. Create a new MessageBuffer
                    # and add it to the dict
                    #
                    client_connections_proxy[self.client_address] = MessageBuffer()

                    logger_proxy.info("adding new client: "
                                      + str(self.client_address))

                # Append the message.
                # (inbetween steps to avoid a loong line ;-) )
                #
                message = cPickle.loads(self.request[0])

                messagebuffer = client_connections_proxy[self.client_address]

                messagebuffer.messages_for_local.append(message)

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

                messagebuffer = self.client_connections[address_port_tuple]

                if messagebuffer.messages_for_remote:

                    self.logger.debug("sending 1 message of "
                                      + str(len(messagebuffer.messages_for_remote))
                                      + " to client "
                                      + str(address_port_tuple))

                    server.socket.sendto(cPickle.dumps(messagebuffer.messages_for_remote.popleft()), 
                                         address_port_tuple)

        # Caught shutdown notification, stopping thread
        #
        self.logger.info("shutting down")

        self.shutdown_confirmed = True

        raise SystemExit
