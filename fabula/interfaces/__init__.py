"""Fabula Interface Classes

   Copyright 2010 Florian Berger <fberger@florian-berger.de>
"""

# This file is part of Fabula.
#
# Fabula is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Fabula is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fabula.  If not, see <http://www.gnu.org/licenses/>.

# Based on former client- and server interface implementations
#
# Work started on 28. Sep 2009
#
# Fabula Client Interface extracted from shard.py on 22. Sep 2009
#
# Fabula Message Buffer based on methods from ClientInterface and the
# ClientConnection class in ServerInterface
#
# Work on Fabula server interface started on 24. Sep 2009

import fabula
from collections import deque
from time import sleep
# For the TCP Interfaces
import socket
import socketserver
import threading
import traceback

class Interface:
    """This is a base class for Fabula interfaces which handle all the network traffic.
       A customised implementation will likely have a client- and a server side
       interface.

       Attributes:

       Interface.connections
           A dict of connector objects mapping to MessageBuffer instances.
           A connector is an object that specifies how to connect to the remote
           host.

       Interface.connected
           Flag to indicate whether Interface.connect() has been called.
           Initially False.

       Interface.shutdown_flag
       Interface.shutdown_confirmed
           Flags for shutdown handling.
    """

    def __init__(self):
        """Initialisation.
        """

        # connections is a dict of MessageBuffer instances, indexed by
        # connectors.
        #
        self.connections = {}

        # Flag to indicate whether Interface.connect() has been called.
        #
        self.connected = False

        # This is the flag which is set when shutdown() is called.
        #
        self.shutdown_flag = False

        # And this is the one for the confirmation.
        #
        self.shutdown_confirmed = False

        fabula.LOGGER.debug("complete")

        return

    def connect(self, connector):
        """Connect to the remote host specified by connector and create a MessageBuffer at Interface.connections[connector].

           connector must be an object that specifies how to connect to the
           remote host (for clients) or where to listen for client messages
           (for the server).

           The connector is implementation dependent. A TCP/IP implementation
           will likely use a tuple (ip_address, port).

           A connector must be valid as a dictionary key.

           This method should not return until the connection is established.

           This method must raise an exception if it is called more than once.

           The default implementation issues a warning and creates a dummy
           MessageBuffer.
        """

        if self.connected:

            fabula.LOGGER.error("this Interface is already connected")

            raise Exception("this Interface is already connected")

        fabula.LOGGER.warning("this is a dummy implementation, not actually connecting to '{}'".format(connector))

        self.connections[connector] = MessageBuffer()

        self.connected = True

        return

    def handle_messages(self):
        """This is the main method of an interface class.

           It must continuously receive messages from the remote host and store
           them in MessageBuffer.messages_for_local in the according
           MessageBuffer in Interface.connections as well as check for messages
           in MessageBuffer.messages_for_remote and send them to the remote host.

           This method is put in a background thread by the startup script,
           so an implementation can do all sorts of polling or blocking IO.

           It should regularly check whether shutdown() has been called
           (checking self.shutdown_flag), and if so, it should notify
           shutdown() by setting self.shutdown_confirmed to true (so that
           method can return True itself), and then raise SystemExit to stop
           the thread.

           The default implementation does nothing, but will handle the shutdown
           as described.
        """

        fabula.LOGGER.info("starting up")

        # Run thread as long as no shutdown is requested
        #
        while not self.shutdown_flag:

            # No need to run as fast as possible
            #
            sleep(1/60)

        # Caught shutdown notification, stopping thread
        #
        fabula.LOGGER.info("shutting down")

        for connector in self.connections.keys():

            if len(self.connections[connector].messages_for_remote):

                msg = "{} unsent messages left in queue for '{}'"

                fabula.LOGGER.warning(msg.format(len(self.connections[connector].messages_for_remote),
                                                 connector))

        self.shutdown_confirmed = True

        raise SystemExit

    def shutdown(self):
        """This is called by the engine when it is about to exit.
           It notifies handle_messages() to raise SystemExit to stop the thread
           properly by setting self.shutdown_flag.
           shutdown() will return True when handle_messages() received the
           notification and is about to exit.
        """

        fabula.LOGGER.debug("called")

        # Set the flag to be caught by handle_messages()
        #
        self.shutdown_flag = True

        # Wait for confirmation (blocks interface and client!)
        #
        while not self.shutdown_confirmed:

            # No need to run as fast as possible.
            #
            sleep(1/60)

        return True

class MessageBuffer:
    """Buffer messages received and to be sent over the network.

       Attributes:

       MessageBuffer.messages_for_local
           A deque, buffering messages from the remote host.

       MessageBuffer.messages_for_remote
           A deque, buffering messages from the local host.
    """

    def __init__(self):
        """This method sets up the internal queues.
        """

        # A hint from the Python documentation:
        # deques are a fast, thread-safe replacement for queues.
        # Use deque.append(x) and deque.popleft()
        #
        self.messages_for_local = deque()
        self.messages_for_remote = deque()

        return

    def send_message(self, message):
        """Called by the local engine with a message ready to be sent to the remote host.
           The Message object given is an instance of fabula.Message.
           This method must return immediately to avoid blocking.
        """

        self.messages_for_remote.append(message)

        return

    def grab_message(self):
        """Called by the local engine to obtain a new buffered message from the remote host.
           It must return an instance of fabula.Message, and it must do so
           immediately to avoid blocking. If there is no new message from
           remote, it must return an empty message.
        """

        if self.messages_for_local:

            return self.messages_for_local.popleft()

        else:
            # A Message must be returned, so create an empty one
            #
            return fabula.Message([])

class StandaloneInterface(Interface):
    """An Interface that is meant to be used in conjunction with run.App.run_standalone().
    """

    def __init__(self, framerate):
        """Initialise.
        """

        # Call base class
        #
        Interface.__init__(self)

        self.framerate = framerate

        fabula.LOGGER.debug("complete")

        return

    def handle_messages(self, remote_message_buffer):
        """This background thread method transfers messages between local and remote MessageBuffer.
           It uses representations of the Events being sent to create new copies
           of the original ones.
        """

        fabula.LOGGER.info("starting up")

        # Run thread as long as no shutdown is requested
        #
        while not self.shutdown_flag:

            # Get messages from remote
            #
            if remote_message_buffer.messages_for_remote:

                original_message = remote_message_buffer.messages_for_remote.popleft()

                new_message = fabula.Message([])

                for event in original_message.event_list:

                    if isinstance(event, fabula.SpawnEvent) and event.entity.__class__ is not fabula.Entity:

                        # These need special care. We need to have a canonic
                        # fabula.Entity. Entity.clone() will produce one.
                        #
                        fabula.LOGGER.debug("cloning canonical Entity from {}".format(event.entity))

                        event = fabula.SpawnEvent(event.entity.clone(),
                                                  event.location)

                    # Create new instances from string representations to avoid
                    # concurrent access of client and server to the object
                    #
                    fabula.LOGGER.debug("evaluating: '{}'".format(repr(event)))

                    try:
                        new_message.event_list.append(eval(repr(event)))

                    except SyntaxError:

                        # Well, well, well. Some __repr__ does not return a
                        # string that can be evaluated here!
                        #
                        fabula.LOGGER.error("error: can not evaluate '{}', skipping".format(repr(event)))

                # Blindly use the first connection
                #
                list(self.connections.values())[0].messages_for_local.append(new_message)

            # No need to deliver messages to remote since it will grab them -
            # see above.

            # No need to run as fast as possible
            #
            sleep(1 / self.framerate)

        # Caught shutdown notification, stopping thread
        #
        fabula.LOGGER.info("shutting down")

        self.shutdown_confirmed = True

        raise SystemExit

# TCP implementation, using the socket and socketserver modules from the
# standard library, and clear text message representations.
# Includes code and lessons learned from an early UDP-, and older Twisted-, and
# an experimental asyncore implementation.
#
class TCPClientInterface(Interface):
    """Fabula Client interface using TCP.

       Additional attributes:

       TCPClientInterface.sock
           socket instance, connected to the server. Initially None.

       TCPClientInterface.received_data
           A bytearray to buffer incoming data.
    """

    def __init__(self):
        """Initialisation.
        """

        # Call base class
        #
        Interface.__init__(self)

        self.sock = None

        self.received_data = bytearray()

        return

    def connect(self, connector):
        """Connect to the remote host specified by connector and create a MessageBuffer at Interface.connections[connector].

           connector must be a tuple (ip_address, port).
        """

        if self.connected:

            fabula.LOGGER.error("this Interface is already connected")

            raise Exception("this Interface is already connected")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # The socket timeout is used for socket.recv() operations, which take
        # turns with socket.sendall().
        #
        self.sock.settimeout(0.3)

        fabula.LOGGER.info("connecting to {}:{}".format(connector[0],
                                                        connector[1]))

        countdown = list(range(1, 11))

        while not self.connected and countdown:

            try:

                self.sock.connect(connector)

                self.connected = True

            except socket.error:

                fabula.LOGGER.error("error while connecting in attempt {}, trying again".format(countdown[0]))

                sleep(1)

                del countdown[0]

        if self.connected:

            fabula.LOGGER.info("connected, local address is {}".format(self.sock.getsockname()))

            self.connections[connector] = MessageBuffer()

        else:

            fabula.LOGGER.critical("could not connect to server on {}:{}".format(connector[0],
                                                                                 connector[1]))

            raise Exception("could not connect to server on {}:{}".format(connector[0],
                                                                          connector[1]))

        return

    def handle_messages(self):
        """Main method of TCPClientInterface.

           This method will be put in a background thread by the startup script,
        """

        fabula.LOGGER.info("waiting for server connection")

        while not self.connections:

            if self.shutdown_flag:

                fabula.LOGGER.info("shutdown before server connection")

                self.shutdown_confirmed = True

                raise SystemExit

            # No need to run as fast as possible.
            #
            sleep(1/60)

        fabula.LOGGER.info("connected to server, starting loop")

        # On the client side, there will only ever be one MessageBuffer element.
        #
        message_buffer = list(self.connections.values())[0]

        # Run thread as long as no shutdown is requested
        #
        while not self.shutdown_flag:

            # First deliver waiting local messages.
            #
            if message_buffer.messages_for_remote:

                fabula.LOGGER.debug("sending 1 message of {}".format(len(message_buffer.messages_for_remote)))

                # Send a clear-text representation. This is supposed to be a
                # Python expression to recreate the instance.
                #
                representation = repr(message_buffer.messages_for_remote.popleft())

                # Add a double newline as separator.
                # TODO: this may block for an arbitrary time. Delegate to a new thread.
                #
                self.sock.sendall(bytes(representation + "\n\n", "utf8"))

            # Now listen for incoming server messages for some time (set in
            # connect()). This should catch any messages received in the
            # meantime by the OS.
            #
            chunk = None

            try:

                # TODO: evaluate recv size
                #
                chunk = self.sock.recv(4096)

            except socket.timeout:

                # Nobody likes us, evereyone left us, there all out without
                # us, having fun...
                #
                pass

            except socket.error:

                fabula.LOGGER.error("socket error while receiving")

            if chunk:

                fabula.LOGGER.debug("received {} bytes from server".format(len(chunk)))

                # Assuming we are dealing with bytes here
                #
                self.received_data.extend(chunk)

                # Now: look for Messages, separated by double newlines.
                #
                double_newline_index = self.received_data.find(b"\n\n")

                # There actually may be more than one b"\n\n" separator in a
                # message. Catch them all!
                #
                while double_newline_index > -1:

                    # Found!

                    message_str = str(self.received_data[:double_newline_index], "utf8")

                    self.received_data = self.received_data[double_newline_index + 2:]

                    msg = "message complete at {} bytes, {} left in buffer"

                    fabula.LOGGER.debug(msg.format(len(message_str),
                                                   len(self.received_data)))

                    # TODO: eval() is the most dangerous thing you can do with data just received over the network.
                    #
                    message_buffer.messages_for_local.append(eval(message_str))

                    # Next
                    #
                    double_newline_index = self.received_data.find(b"\n\n")

                # No more double newlines, end of evaluation.

            # No need to run as fast as possible.
            #
            sleep(1/60)

            # Check shutdown_flag. Possibly start again.

        fabula.LOGGER.info("caught shutdown notification")

        try:

            self.sock.shutdown(socket.SHUT_RDWR)

        except:

            # Socket may be unavailable already
            #
            fabula.LOGGER.warning("could not shut down socket")

        self.sock.close()

        fabula.LOGGER.info("server connection closed")

        # Copied from base class
        #
        for connector in self.connections.keys():

            if len(self.connections[connector].messages_for_remote):

                msg = "{} unsent messages left in queue for '{}'"

                fabula.LOGGER.warning(msg.format(len(self.connections[connector].messages_for_remote),
                                                 connector))

        fabula.LOGGER.info("stopping thread")

        self.shutdown_confirmed = True

        raise SystemExit

class TCPServerInterface(Interface):
    """Fabula Server interface using TCP.

       Additional attributes:

       TCPServerInterface.server
           socketserver.TCPServer instance, handling incoming client requests.
           Initially None.

       TCPServerInterface.FabulaRequestHandler
           An subclass of socketserver.BaseRequestHandler to handle incoming
           connections.

       TCPServerInterface.thread_list
           A list of threads spawned for handling incoming connections.
    """

    def __init__(self):
        """Initialisation.
        """

        # Call base class
        #
        Interface.__init__(self)

        self.server = None

        self.thread_list = []

        parent = self

        # We define the class here to be able to access local variables.
        #
        class FabulaRequestHandler(socketserver.BaseRequestHandler):

            def handle(self):

                # TODO: this will run in a thread spawned by the custom ThreadingTCPServer class. How thread safe are these operations?

                # Fabula uses persistent TCP connections, so every call to this
                # method should be from a new client. Blindly add this one.
                #
                message_buffer = parent.connections[self.client_address] = MessageBuffer()

                fabula.LOGGER.info("adding and handling new client: {}".format(self.client_address))

                # Register in thread list, which is used for Interface shutdown
                #
                parent.thread_list.append(threading.current_thread())

                # Now, handle messages in a persistent fashion.

                self.request.settimeout(0.3)

                received_data = bytearray()

                while not parent.shutdown_flag:

                    # TODO: copied from TCPClientInterface.handle_messages() with a few renamings

                    # First deliver waiting local messages.
                    #
                    if message_buffer.messages_for_remote:

                        fabula.LOGGER.debug("sending 1 message of {} to {}".format(len(message_buffer.messages_for_remote),
                                                                                   self.client_address))

                        # Send a clear-text representation. This is supposed to
                        # be a Python expression to recreate the instance.
                        #
                        representation = repr(message_buffer.messages_for_remote.popleft())

                        # Add a double newline as separator.
                        #
                        self.request.sendall(bytes(representation + "\n\n", "utf8"))

                    # Now listen for incoming server messages for some time (set
                    # above). This should catch any messages received in the
                    # meantime by the OS.
                    #
                    chunk = None

                    try:

                        # TODO: evaluate recv size
                        #
                        chunk = self.request.recv(4096)

                    except socket.timeout:

                        # Nobody likes us, evereyone left us, there all out without
                        # us, having fun...
                        #
                        pass

                    except socket.error:

                        fabula.LOGGER.error("socket error while receiving")

                    if chunk:

                        fabula.LOGGER.debug("received {} bytes from {}".format(len(chunk),
                                                                               self.client_address))

                        # Assuming we are dealing with bytes here
                        #
                        received_data.extend(chunk)

                        # Now: look for Messages, separated by double newlines.
                        #
                        double_newline_index = received_data.find(b"\n\n")

                        # There actually may be more than one b"\n\n" separator
                        # in a message. Catch them all!
                        #
                        while double_newline_index > -1:

                            # Found!

                            message_str = str(received_data[:double_newline_index], "utf8")

                            received_data = received_data[double_newline_index + 2:]

                            msg = "message from {} complete at {} bytes, {} left in buffer"

                            fabula.LOGGER.debug(msg.format(self.client_address,
                                                           len(message_str),
                                                           len(received_data)))

                            # TODO: eval() is the most dangerous thing you can do with data just received over the network.
                            #
                            message_buffer.messages_for_local.append(eval(message_str))

                            # Next
                            #
                            double_newline_index = received_data.find(b"\n\n")

                        # No more double newlines, end of evaluation.

                    # No need to run as fast as possible.
                    #
                    sleep(1/60)

                fabula.LOGGER.debug("shutdown flag set in parent")

                # Deliver waiting local messages.
                #
                while len(message_buffer.messages_for_remote):

                    # Copied from above
                    #
                    fabula.LOGGER.debug("sending 1 message of {} to {}".format(len(message_buffer.messages_for_remote),
                                                                               self.client_address))

                    # Send a clear-text representation. This is supposed to
                    # be a Python expression to recreate the instance.
                    #
                    representation = repr(message_buffer.messages_for_remote.popleft())

                    # Add a double newline as separator.
                    #
                    self.request.sendall(bytes(representation + "\n\n", "utf8"))

                try:

                    self.request.shutdown(socket.SHUT_RDWR)

                except:

                    # Socket may be unavailable already
                    #
                    fabula.LOGGER.warning("could not shut down socket")

                self.request.close()

                fabula.LOGGER.info("handler connection closed, stopping thread")

                raise SystemExit

        # End of class.

        self.FabulaRequestHandler = FabulaRequestHandler

        return

    def connect(self, connector):
        """Create a socketserver.TCPServer which will listen for incoming client connections.

           connector must be a tuple (ip_address, port) giving address and port
           to listen on.
        """

        if self.connected:

            fabula.LOGGER.error("this Interface is already connected")

            raise Exception("this Interface is already connected")

        fabula.LOGGER.info("creating server to listen on {}:{}".format(connector[0],
                                                                       connector[1]))

        # Since we use persistent TCP connections, the first handler would block
        # the whole server. So we use the ThreadingMixIn, which spawns a thread
        # for every handler.
        #
        class ThreadingTCPServer(socketserver.ThreadingMixIn,
                                 socketserver.TCPServer):

            def handle_error(self, request, client_address):
                """Log the exception using fabula.LOGGER.
                """

                exception = traceback.format_exc()

                # TODO: handle exited clients, which raise 'socket.error: [Errno 32] Broken pipe'
                #
                fabula.LOGGER.warning("exception in handle():\n{}".format(exception))

                return

        self.server = ThreadingTCPServer(connector, self.FabulaRequestHandler)

        # Server timeout, so server.handle_request() doesn't wait forever, which
        # would prevent shutdown.
        #
        self.server.timeout = 0.1

        self.connected = True

        return

    def handle_messages(self):
        """Main method of TCPServerInterface.

           This method will be put in a background thread by the startup script,
        """

        fabula.LOGGER.info("waiting for server to be created")

        while self.server is None:

            if self.shutdown_flag:

                fabula.LOGGER.info("shutdown before server creation")

                self.shutdown_confirmed = True

                raise SystemExit

            # No need to run as fast as possible.
            #
            sleep(1/60)

        fabula.LOGGER.info("server created, starting loop")

        # Run thread as long as no shutdown is requested
        #
        while not self.shutdown_flag:

            # Wait at most server.timeout seconds until a request comes in:
            #
            self.server.handle_request()

        fabula.LOGGER.info("caught shutdown notification")

        # Build a list of MessageBuffer instances that still have unsent
        # Messages for remote as an indicator of whether to wait.
        # Go, Python!
        #
        while len([mess_buffer for mess_buffer in self.connections.values() if len(mess_buffer.messages_for_remote)]):

            fabula.LOGGER.debug("waiting for buffered Messages to be sent")

            self.server.handle_request()

        try:

            self.server.socket.shutdown(socket.SHUT_RDWR)

        except:

            # Socket may be unavailable already
            #
            fabula.LOGGER.warning("could not shut down socket")

        self.server.socket.close()

        fabula.LOGGER.info("server connection closed")

        for thread in self.thread_list:

            fabula.LOGGER.info("waiting for thread {} to terminate".format(thread))

            thread.join()

        fabula.LOGGER.info("stopping thread")

        self.shutdown_confirmed = True

        raise SystemExit

# UDP implementation
#
# TODO: This implementation may be defunct because of the Interface class refactoring. Check and refactor.

# For UDP
#
#import socket
#import socketserver
#import pickle

#class UDPClientInterface(MessageBuffer, Interface):
#    """This is the base class for a Fabula Client Interface.
#       Implementations should subclass this one an override
#       the default methods, which showcase a simple example.
#    """

#    def __init__(self, connector, logger):
#        """Interface initialization.
#        """

#        # First call __init__() from the base class
#        #
#        Interface.__init__(self, connector, logger)

#        # Convenience name to make code clearer
#        #
#        self.address_port_tuple = self.connector

#        # This is a subclass of MessageBuffer, but
#        # since we override __init__(), we have to
#        # call the original method.
#        #
#        MessageBuffer.__init__(self)

#        # Set up UDP socket
#        # It wouldn't be unreasonable to also use
#        # a socketserver on the client side. But
#        # since the client is only ever supposed
#        # to handle one connection, direct socket
#        # handling may be just right.
#        #
#        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#        # The socket timeout is used for
#        # socket.recv() operations, which
#        # take turns with socket.sendto().
#        #
#        self.sock.settimeout(0.3)

#        fabula.LOGGER.debug("complete")

#    def handle_messages(self):
#        """The task of this method is to do whatever is necessary to send client messages and obtain server messages.
#           It is meant to be the back end of send_message() and grab_message().
#           Put some networking code, a GUI or a random generator here.
#           This method is put in a background thread automatically, so it can
#           do all sorts of polling or blocking IO.
#           It should regularly check whether shutdown() has been called, and
#           if so, it should notify shutdown() in some way (so that it can return
#           True), and then raise SystemExit to stop the thread.
#        """

#        fabula.LOGGER.info("starting up")

#        # Run thread as long as no shutdown is requested
#        #
#        while not self.shutdown_flag:

#            if self.messages_for_remote:

#                fabula.LOGGER.info("sending 1 message of " + str(len(self.messages_for_remote)))

#                # -1 = use highest available pickle protocol
#                #
#                self.sock.sendto(pickle.dumps(self.messages_for_remote.popleft(), -1),
#                                 self.address_port_tuple)

#            # Now listen for incoming server
#            # messages for some time
#            # (set in __init__()). This will
#            # catch any messages received in
#            # the meantime by the OS (tested).
#            #
#            data_received = ""

#            try:

#                # TODO: UDP sockets may lock up on large packets (tested). Use the struct module to encode events and messages.
#                #
#                data_received = self.sock.recv(16384)

#            except socket.timeout:

#                # We do not log here since this
#                # happens too often
#                #
#                pass

#            if data_received:

#                # TODO: accepts data from *anywhere*

#                fabula.LOGGER.info("received server message ("
#                                  + str(len(data_received))
#                                  + "/16384 bytes)")

#                self.messages_for_local.append(pickle.loads(data_received))

#        # Caught shutdown notification, stopping thread
#        #
#        fabula.LOGGER.info("shutting down")

#        self.shutdown_confirmed = True

#        raise SystemExit


#class UDPServerInterface(Interface):
#    """This is the base class for a Fabula Server Interface.
#       Implementations should subclass this one an override
#       the default methods, which do nothing.
#    """

#    def __init__(self, connector, logger):
#        """Interface initialization."""

#        # First call __init__() from the base class
#        #
#        Interface.__init__(self, connector, logger)

#        # Convenience name to make code clearer
#        #
#        self.address_port_tuple = self.connector

#        # client_connections is a dict of MessageBuffer
#        # instances, indexed by (address, port) tuples.
#        #
#        self.client_connections = {}

#        fabula.LOGGER.debug("complete")

#    def handle_messages(self):
#        """The task of this method is to do whatever is necessary to send server messages and obtain client messages.
#           It is meant to be the back end of send_message() and grab_message().
#           Put some networking code, a GUI or a random generator here.
#           This method is put in a background thread automatically, so it can
#           do all sorts of polling or blocking IO.
#           It should regularly check whether shutdown() has been called, and if
#           so, it should notify shutdown() in some way (so that it can return
#           True), and then raise SystemExit to stop the thread.
#        """

#        fabula.LOGGER.info("starting up")

#        client_connections_proxy = self.client_connections
#        logger_proxy = self.logger

#        # We define the class here to be able
#        # to access variables of the ServerInterface
#        # instance.
#        #
#        class FabulaRequestHandler(socketserver.BaseRequestHandler):

#            def handle(self):

#                logger_proxy.debug("called")

#                # Test for new client,
#                # i.e. not (address, port) tuple in keys
#                #
#                if not self.client_address in client_connections_proxy:

#                    # New client. Create a new MessageBuffer
#                    # and add it to the dict
#                    #
#                    client_connections_proxy[self.client_address] = MessageBuffer()

#                    logger_proxy.info("adding new client: "
#                                      + str(self.client_address))

#                # Append the message.
#                # (inbetween steps to avoid a long line ;-) )
#                #
#                message = pickle.loads(self.request[0])

#                message_buffer = client_connections_proxy[self.client_address]

#                message_buffer.messages_for_local.append(message)

#                # End of handle() method.

#        # End of class.

#        server = socketserver.UDPServer(self.address_port_tuple, FabulaRequestHandler)

#        # Server timeout, so server.handle_request()
#        # doesn't wait forever, which would prevent
#        # shutdown.
#        #
#        server.timeout = 0.1

#        # Run thread as long as no shutdown is requested
#        #
#        while not self.shutdown_flag:

#            # TODO: several threads for send and receive

#            # wait at most server.timeout seconds
#            # until a request comes in:
#            #
#            server.handle_request()

#            # Flush server event queues.
#            # Iterate over dict keys:
#            #
#            for address_port_tuple in self.client_connections:

#                message_buffer = self.client_connections[address_port_tuple]

#                if message_buffer.messages_for_remote:

#                    fabula.LOGGER.info("sending 1 message of "
#                                      + str(len(message_buffer.messages_for_remote))
#                                      + " to client "
#                                      + str(address_port_tuple))

#                    # -1 = use highest available pickle protocol
#                    #
#                    server.socket.sendto(pickle.dumps(message_buffer.messages_for_remote.popleft(), -1),
#                                         address_port_tuple)

#        # Caught shutdown notification, stopping thread
#        #
#        fabula.LOGGER.info("shutting down")

#        self.shutdown_confirmed = True

#        raise SystemExit


# TCP implementation using the Twisted framework
#
# Based on a pure socket implementation done in Oct 2009

# Twisted has not yet been ported to Python 3.
#
# # Importing the Twisted base module for executable makers
# #
# import twisted
#
# import twisted.internet
# import twisted.internet.protocol
# import twisted.internet.reactor
# import twisted.internet.task

#class ProtocolMessageBuffer(MessageBuffer,
#                            twisted.internet.protocol.Protocol):
#    """Buffer messages received and to be sent over the network.
#       An instance of this class is created by a Twisted Factory
#       every time a connection is made.
#    """

#    def __init__(self, logger):
#        """Set up the MessageBuffer attributes, the logger, buffer, flags.
#        """

#        MessageBuffer.__init__(self)

#        # Now we have:
#        #
#        # self.messages_for_local
#        # self.messages_for_remote

#        self.logger = logger

#        self.data_buffer = ""

#        self.connection_made = False

#        fabula.LOGGER.debug("complete")

#    def connectionMade(self):
#        """Standard Twisted Protocol method.
#           Now ProtocolMessageBuffer.transport is ready to be used.
#        """

#        fabula.LOGGER.debug("called")

#        self.connection_made = True

#    def dataReceived(self, data):
#        """Standard Twisted Protocol method: handle received data.
#        """
#        # From the Twisted documentation:
#        #  "Please keep in mind that you will probably need
#        #   to buffer some data, as partial (or multiple)
#        #   protocol messages may be received! I recommend
#        #   that unit tests for protocols call through to
#        #   this method with differing chunk sises, down to
#        #   one byte at a time."

#        fabula.LOGGER.info("received message: %s characters" % len(data))

#        # Keep buffering data until we find a
#        # dot (the pickle STOP opcode) followed
#        # by a double newline in a message.
#        #
#        self.data_buffer = self.data_buffer + data

#        double_newline_index = self.data_buffer.find(".\n\n")

#        # There actually may be more than one
#        # ".\n\n" separator in a message. Catch
#        # them all!
#        #
#        while double_newline_index > -1:

#            # Found!

#            message = self.data_buffer[:double_newline_index] + "."

#            self.data_buffer = self.data_buffer[double_newline_index + 3:]

#            fabula.LOGGER.info("message complete at %s characters, %s left in buffer"
#                               % (len(message),
#                                  len(self.data_buffer)))

#            message = pickle.loads(message)

#            self.messages_for_local.append(message)

#            # Next
#            #
#            double_newline_index = self.data_buffer.find(".\n\n")

#    def send_queued_message(self, address_port_tuple):
#        """Actually send messages queued with MessageBuffer.send_message()
#           across the network.
#        """

#        if self.connection_made and self.messages_for_remote:

#            fabula.LOGGER.info("sending 1 message of %s to %s"
#                              % (len(self.messages_for_remote),
#                                 address_port_tuple))

#            # -1 = use highest available pickle protocol
#            #
#            # Separating messages with the standard
#            # double newline.
#            #
#            # TODO: Check that double newlines are illegal in pickled data.
#            #
#            pickled_message = pickle.dumps(self.messages_for_remote.popleft(), -1)

#            self.transport.write(pickled_message + "\n\n")

#            fabula.LOGGER.info("sent %s characters" % len(pickled_message))

#class TCPInterface(Interface):
#    """A generic Fabula Interface using TCP, built upon the Twisted framework.
#    """

#    def __init__(self, connector, logger, interface_type, send_interval):
#        """Initialisation.
#           connector and logger are arguments for Interface.__init__.
#           interface_type is either "client" or "server". send_interval is the
#           interval of sending queued messages in seconds (float).
#        """

#        Interface.__init__(self, connector, logger)

#        # Convenience name to make code clearer
#        #
#        self.address_port_tuple = self.connector

#        self.interface_type = interface_type

#        self.send_interval = send_interval

#        fabula.LOGGER.debug("complete")

#    def handle_messages(self):
#        """The task of this method is to do whatever is necessary to send client messages and obtain server messages.
#           It is meant to be the back end of send_message() and grab_message().
#           Put some networking code, a GUI or a random generator here.
#           This method is put in a background thread automatically, so it can
#           do all sorts of polling or blocking IO.
#           It should regularly check whether shutdown() has been called, and
#           if so, it should notify shutdown() in some way (so that it can return
#           True), and then raise SystemExit to stop the thread.
#        """

#        # TODO: remove connections that caused an error?

#        fabula.LOGGER.info("starting up")

#        # We do all the Twisted setup here so
#        # class instances can use the proxies
#        # for the TCPClientInterface attributes.

#        # Set up proxies
#        #
#        logger_proxy = self.logger
#        connections_proxy = self.connections

#        class MessageProtocolFactory(twisted.internet.protocol.ClientFactory):
#            """Twisted ClientFactory implementation,
#               producing a ProtocolMessageBuffer instance for every connection.
#            """

#            def buildProtocol(self, addr):
#                """Standard Twisted Factory method
#                   which creates an returns an instance of ProtocolMessageBuffer.
#                """

#                protocol_message_buffer = ProtocolMessageBuffer(logger_proxy)

#                # Register at Interface level
#                #
#                logger_proxy.info("adding new connection: (%s, %s)"
#                                  % (addr.host, addr.port))

#                connections_proxy[(addr.host, addr.port)] = protocol_message_buffer

#                return protocol_message_buffer

#            def clientConnectionFailed(self, address_port_tuple, reason):

#                logger_proxy.info("reason: %s" % reason)

#            def clientConnectionLost(self, address_port_tuple, reason):

#                logger_proxy.info("reason: %s" % reason)

#            #def startedConnecting(self, address_port_tuple):
#            #
#            #    logger_proxy.debug("called")

#            # End of MessageProtocolFactory class

#        # The following twists are lessons learned
#        # from developing the Fabula-based CharanisMLClient
#        # in May 2008

#        def check_shutdown():

#            if self.shutdown_flag:

#                fabula.LOGGER.info("caught shutdown_flag, closing connection and stopping reactor")

#                self.shutdown_confirmed = True

#                for protocol_message_buffer in self.connections.values():

#                    protocol_message_buffer.transport.loseConnection()

#                twisted.internet.reactor.stop()

#            # End of check_shutdown()

#        def send_all_queued_messages():

#            for address_port_tuple in self.connections:

#                # TODO: that's a very round-the-corner way supply address and port to the method
#                #
#                self.connections[address_port_tuple].send_queued_message(address_port_tuple)

#            # End of send_all_queued_messages()

#        # Create Twisted LoopingCalls
#        #
#        check_shutdown_call = twisted.internet.task.LoopingCall(check_shutdown)

#        send_all_queued_messages_call = twisted.internet.task.LoopingCall(send_all_queued_messages)

#        # Check every 0.5s
#        #
#        check_shutdown_call.start(0.5)

#        # Given in __init__ as send_interval
#        #
#        send_all_queued_messages_call.start(self.send_interval)

#        # Get ready
#        #
#        if self.interface_type == "client":

#            fabula.LOGGER.info("running in client mode")

#            twisted.internet.reactor.connectTCP(self.address_port_tuple[0],
#                                                self.address_port_tuple[1],
#                                                MessageProtocolFactory())
#        else:

#            fabula.LOGGER.info("running in server mode")

#            twisted.internet.reactor.listenTCP(self.address_port_tuple[1],
#                                               MessageProtocolFactory(),
#                                               interface = self.address_port_tuple[0])

#        # Now run Twisted loop as long as no
#        # shutdown is requested.
#        #
#        # installSignalHandlers=0 to run flawlessy in a thread
#        #
#        twisted.internet.reactor.run(installSignalHandlers = 0)

#        # twisted.internet.reactor.run() returned
#        #
#        fabula.LOGGER.info("connection closed, reactor stopped, stopping thread")

#        raise SystemExit
