"""Shard Interface Classes

   Based on former client- and server
   interface implementations
"""

# Work started on 28. Sep 2009
#
# Shard Client Interface extracted from
# shard.py on 22. Sep 2009
#
# Shard Message Buffer based on methods from
# ClientInterface and the ClienConnection class
# in ServerInterface
#
# Work on Shard server interface started
# on 24. Sep 2009

import shard

from collections import deque

import socket
import SocketServer

# Importing the Twisted base module for executable makers
#
import twisted

import twisted.internet
import twisted.internet.protocol
import twisted.internet.reactor
import twisted.internet.task

import cPickle

import time

# Base and helper classes

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

        self.setup_interface(address_port_tuple, logger)

        self.logger.debug("complete")

    def setup_interface(self, address_port_tuple, logger):
        """This method sets up:

           Interface.address_port_tuple
           (from address_port_tuple)

           Interface.logger
           (from logger)

           Interface.connections
           (a dict of (address, port) tuples
           mapping to MessageBuffer instances)

           Interface.shutdown_flag
           Interface.shutdown_confirmed
           (flags for shutdown handling)

           Be sure to call this method from
           __init__() when subclassing.
        """

        self.address_port_tuple = address_port_tuple

        # Attach logger
        #
        self.logger = logger

        # connections is a dict of MessageBuffer
        # instances, indexed by (address, port) tuples.
        #
        self.connections = {}

        # This is the flag which is set when shutdown()
        # is called.
        #
        self.shutdown_flag = False

        # And this is the one for the confirmation.
        #
        self.shutdown_confirmed = False

        self.logger.debug("complete")

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

        self.logger.debug("starting up")

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
           self.setup_message_buffer(). You
           should do so, too, when subclassing
           this with a custom implementation.
        """

        self.setup_message_buffer()

    def setup_message_buffer(self):
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


# UDP implementation
#
# TODO: This implementation may be defunct because of the Interface class refactoring. Check and refactor.

class UDPClientInterface(MessageBuffer, Interface):
    """This is the base class for a Shard Client Interface.
       Implementations should subclass this one an override
       the default methods, which showcase a simple example.
    """

    def __init__(self, address_port_tuple, logger):
        """Interface initialization.
        """

        # First call setup_interface() from the
        # base class
        #
        self.setup_interface(address_port_tuple, logger)

        # This is a subclass of MessageBuffer, but
        # since we override __init__(), we have to
        # call setup_message_buffer().
        #
        self.setup_message_buffer()

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
        """The task of this method is to do whatever is
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
           the thread.
        """

        self.logger.debug("starting up")

        # Run thread as long as no shutdown is requested
        #
        while not self.shutdown_flag:

            if self.messages_for_remote:

                self.logger.debug("sending 1 message of " + str(len(self.messages_for_remote)))

                # -1 = use highest available pickle protocol
                #
                self.sock.sendto(cPickle.dumps(self.messages_for_remote.popleft(), 0), 
                                 self.address_port_tuple)

            # Now listen for incoming server
            # messages for some time
            # (set in __init__()). This will
            # catch any messages received in
            # the meantime by the OS (tested).
            #
            data_received = ""

            try:

                # TODO: UDP sockets may lock up on large packets (tested). Use the struct module to encode events and messages.
                #
                data_received = self.sock.recv(16384)

            except socket.timeout:

                # We do not log here since this
                # happens too often
                #
                pass

            if data_received:

                # TODO: accepts data from *anywhere*

                self.logger.debug("received server message (" 
                                  + str(len(data_received))
                                  + "/16384 bytes)")

                self.messages_for_local.append(cPickle.loads(data_received))

        # Caught shutdown notification, stopping thread
        #
        self.logger.info("shutting down")

        self.shutdown_confirmed = True

        raise SystemExit


class UDPServerInterface(Interface):
    """This is the base class for a Shard Server Interface.
       Implementations should subclass this one an override
       the default methods, which do nothing.
    """

    def __init__(self, address_port_tuple, logger):
        """Interface initialization."""

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
        """The task of this method is to do whatever is
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
           the thread.
        """

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
                # (inbetween steps to avoid a long line ;-) )
                #
                message = cPickle.loads(self.request[0])

                message_buffer = client_connections_proxy[self.client_address]

                message_buffer.messages_for_local.append(message)

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

                message_buffer = self.client_connections[address_port_tuple]

                if message_buffer.messages_for_remote:

                    self.logger.debug("sending 1 message of "
                                      + str(len(message_buffer.messages_for_remote))
                                      + " to client "
                                      + str(address_port_tuple))

                    # -1 = use highest available pickle protocol
                    #
                    server.socket.sendto(cPickle.dumps(message_buffer.messages_for_remote.popleft(), -1),
                                         address_port_tuple)

        # Caught shutdown notification, stopping thread
        #
        self.logger.info("shutting down")

        self.shutdown_confirmed = True

        raise SystemExit


# TCP implementation uswing the Twisted framework
#
# Based on a pure socket implementation done in Oct 2009

class ProtocolMessageBuffer(MessageBuffer,
                            twisted.internet.protocol.Protocol):
    """Buffer messages received and to be sent
       over the network.
       An instance of this class is created by
       a Twisted Factory every time a connection
       is made.
    """

    def __init__(self, logger):
        """Set up the MessageBuffer attributes,
           the logger, buffer, flags.
        """

        self.setup_message_buffer()

        # Now we have:
        #
        # self.messages_for_local
        # self.messages_for_remote

        self.logger = logger

        self.data_buffer = ""

        self.connection_made = False

        self.logger.debug("complete")

    def connectionMade(self):
        """Standard Twisted Protocol method.
           Now ProtocolMessageBuffer.transport
           is ready to be used.
        """

        self.logger.debug("called")

        self.connection_made = True

    def dataReceived(self, data):
        """Twisted Protocol standard method:
           handle received data.
        """
        # From the Twisted documentation:
        #  "Please keep in mind that you will probably need
        #   to buffer some data, as partial (or multiple)
        #   protocol messages may be received! I recommend
        #   that unit tests for protocols call through to
        #   this method with differing chunk sizes, down to
        #   one byte at a time."

        self.logger.debug("received message: %s characters" % len(data))

        # Keep buffering data until we end up with a
        # double newline terminated message.
        #
        # TODO: This of course only works if some time passes between messages. Otherwise there might already be new data after the double newline.
        #
        self.data_buffer = self.data_buffer + data

        if self.data_buffer.endswith("\n\n"):

            # Now we have double newline terminated
            # data in self.data_buffer.

            self.logger.debug("message complete: %s characters"
                               % len(self.data_buffer))

            # Remove newlines and unpickle
            #
            message = cPickle.loads(self.data_buffer.rstrip("\n"))

            self.messages_for_local.append(message)

            self.data_buffer = ""

    def send_queued_message(self):
        """Actually send messages queued
           with MessageBuffer.send_message()
           across the network.
        """

        if self.connection_made and self.messages_for_remote:

            self.logger.debug("sending 1 message of %s" % len(self.messages_for_remote))

            # -1 = use highest available pickle protocol
            #
            # Separating messages with the standard
            # double newline.
            #
            # TODO: Check that double newlines are illegal in pickled data.
            #
            pickled_message = (cPickle.dumps(self.messages_for_remote.popleft(), -1)
                               + "\n\n")

            self.transport.write(pickled_message)

            self.logger.debug("sent %s characters" % len(pickled_message))

class TCPInterface(Interface):
    """A generic Shard Interface using TCP,
       built upon the Twisted framework.
    """

    def __init__(self, address_port_tuple, logger, interface_type, send_interval):
        """addres_port_tuple and logger are
           arguments for setup_interface.
           interface_type is either "client"
           or "server". send_interval is the
           interval of sending queued messages
           in seconds (float).
        """

        self.setup_interface(address_port_tuple, logger)

        self.interface_type = interface_type

        self.send_interval = send_interval

        self.logger.debug("complete")

    def handle_messages(self):
        """The task of this method is to do whatever is
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
           the thread.
        """

        # TODO: remove connections that caused an error?

        self.logger.debug("starting up")

        # We do all the Twisted setup here so
        # class instances can use the proxies
        # for the TCPClientInterface attributes.

        # Set up proxies
        #
        logger_proxy = self.logger
        connections_proxy = self.connections

        class MessageProtocolFactory(twisted.internet.protocol.ClientFactory):
            """Twisted ClientFactory implementation,
               producing a ProtocolMessageBuffer instance
               for every connection.
            """

            def buildProtocol(self, addr):
                """Standard Twisted Factory method which
                   creates an returns an instance of
                   ProtocolMessageBuffer.
                """

                protocol_message_buffer = ProtocolMessageBuffer(logger_proxy)

                # Register at Interface level
                #
                logger_proxy.info("adding new connection: (%s, %s)"
                                  % (addr.host, addr.port))

                connections_proxy[(addr.host, addr.port)] = protocol_message_buffer

                return protocol_message_buffer

            def clientConnectionFailed(self, connector, reason):

                logger_proxy.info("reason: %s" % reason)

            def clientConnectionLost(self, connector, reason):

                logger_proxy.info("reason: %s" % reason)

            #def startedConnecting(self, connector):
            #
            #    logger_proxy.info("called")

            # End of MessageProtocolFactory class

        # The following twists are lessons learned
        # from developing the Shard-based CharanisMLClient
        # in May 2008

        def check_shutdown():

            if self.shutdown_flag:

                self.logger.info("caught shutdown_flag, closing connection and stopping reactor")

                self.shutdown_confirmed = True

                for protocol_message_buffer in self.connections.values():

                    protocol_message_buffer.transport.loseConnection()

                twisted.internet.reactor.stop()

            # End of check_shutdown()

        def send_all_queued_messages():

            for protocol_message_buffer in self.connections.values():

                protocol_message_buffer.send_queued_message()

            # End of send_all_queued_messages()

        # Create Twisted LoopingCalls
        #
        check_shutdown_call = twisted.internet.task.LoopingCall(check_shutdown)

        send_all_queued_messages_call = twisted.internet.task.LoopingCall(send_all_queued_messages)

        # Check every 0.5s
        #
        check_shutdown_call.start(0.5)

        # Given in __init__ as send_interval
        #
        send_all_queued_messages_call.start(self.send_interval)

        # Get ready
        #
        if self.interface_type == "client":

            self.logger.info("running in client mode")

            twisted.internet.reactor.connectTCP(self.address_port_tuple[0],
                                                self.address_port_tuple[1],
                                                MessageProtocolFactory())
        else:

            self.logger.info("running in server mode")

            twisted.internet.reactor.listenTCP(self.address_port_tuple[1],
                                               MessageProtocolFactory(),
                                               interface = self.address_port_tuple[0])

        # Now run Twisted loop as long as no
        # shutdown is requested.
        #
        # installSignalHandlers=0 to run flawlessy in a thread
        #
        twisted.internet.reactor.run(installSignalHandlers = 0)

        # twisted.internet.reactor.run() returned
        #
        self.logger.info("connection closed, reactor stopped, stopping thread")

        raise SystemExit
