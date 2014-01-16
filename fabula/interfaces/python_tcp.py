"""Fabula TCP Interface

   Copyright 2010 Florian Berger <mail@florian-berger.de>
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

# TCP implementation, using the socket and socketserver modules from the
# standard library, and clear text message representations.
# Includes code and lessons learned from an early UDP-, and older Twisted-, and
# an experimental asyncore implementation.
#
# Exctracted from fabula.interfaces on 26. Mar 2012

import fabula.interfaces
from time import sleep
import socket
import socketserver
import threading
import traceback

class TCPClientInterface(fabula.interfaces.Interface):
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
        fabula.interfaces.Interface.__init__(self)

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

            self.connections[connector] = fabula.interfaces.MessageBuffer()

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

                # Nobody likes us, evereyone left us, there all out without us,
                # having fun...
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

        # Deliver waiting local messages.
        #
        while len(message_buffer.messages_for_remote):

            # Copied from above

            fabula.LOGGER.debug("sending 1 message of {}".format(len(message_buffer.messages_for_remote)))

            # Send a clear-text representation. This is supposed to be a
            # Python expression to recreate the instance.
            #
            representation = repr(message_buffer.messages_for_remote.popleft())

            # Add a double newline as separator.
            # This may block for an arbitrary time, but here we can wait.
            #
            # TODO: Exception handling, especially here!
            #
            self.sock.sendall(bytes(representation + "\n\n", "utf8"))

        try:

            self.sock.shutdown(socket.SHUT_RDWR)

        except:

            # Socket may be unavailable already
            #
            fabula.LOGGER.warning("could not shut down socket")

        self.sock.close()

        fabula.LOGGER.info("server connection closed")

        fabula.LOGGER.info("stopping thread")

        self.shutdown_confirmed = True

        raise SystemExit

class TCPServerInterface(fabula.interfaces.Interface):
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
        fabula.interfaces.Interface.__init__(self)

        self.server = None

        self.thread_list = []

        parent = self

        # We define the class here to be able to access local variables through
        # parent.
        #
        class FabulaRequestHandler(socketserver.BaseRequestHandler):

            def handle(self):

                # TODO: this will run in a thread spawned by the custom ThreadingTCPServer class. How thread safe are these operations?

                # Fabula uses persistent TCP connections, so every call to this
                # method should be from a new client. Blindly add this one.
                #
                message_buffer = parent.connections[self.client_address] = fabula.interfaces.MessageBuffer()

                fabula.LOGGER.info("adding and handling new client: {}".format(self.client_address))

                # Register in thread list, which is used for Interface shutdown
                #
                parent.thread_list.append(threading.current_thread())

                # Now, handle messages in a persistent fashion.

                self.request.settimeout(0.3)

                received_data = bytearray()

                while not parent.shutdown_flag:

                    # TODO: partly copied from TCPClientInterface.handle_messages() with a few renamings

                    # First deliver waiting local messages.
                    #
                    if message_buffer.messages_for_remote:

                        fabula.LOGGER.debug("sending 1 message of {} to {}".format(len(message_buffer.messages_for_remote),
                                                                                   self.client_address))

                        # Send a clear-text representation. This is supposed to
                        # be a Python expression to recreate the instance.
                        #
                        representation = repr(message_buffer.messages_for_remote.popleft())

                        try:
                            # Add a double newline as separator.
                            #
                            self.request.sendall(bytes(representation + "\n\n", "utf8"))

                        except socket.error:

                            fabula.LOGGER.error("socket error while sending to {}".format(self.client_address))

                            try:
                                fabula.LOGGER.debug("closing socket")

                                self.request.shutdown(socket.SHUT_RDWR)

                            except:

                                # Socket may be unavailable already
                                #
                                fabula.LOGGER.warning("could not shut down socket")

                            self.request.close()

                            fabula.LOGGER.info("handler connection closed")

                            # This is the only way to notify the Server
                            #
                            fabula.LOGGER.debug("removing connection from connections dict")

                            del parent.connections[self.client_address]

                            fabula.LOGGER.debug("removing thread from thread list")

                            parent.thread_list.remove(threading.current_thread())

                            fabula.LOGGER.info("stopping thread")

                            raise SystemExit

                    # Only the Interface may add connections to
                    # Interface.connections, but the server may remove them if
                    # a client exits on the application level.
                    # Now check whether the client handled by this
                    # FabulaRequestHandler has been removed, and if so,
                    # terminate.
                    #
                    if not self.client_address in parent.connections.keys():

                        fabula.LOGGER.info("client '{}' has been removed by the server".format(self.client_address))

                        # We are *not* setting parent.shutdown_flag, since only
                        # this connection should terminate.

                        try:

                            self.request.shutdown(socket.SHUT_RDWR)

                        except:

                            # Socket may be unavailable already
                            #
                            fabula.LOGGER.warning("could not shut down socket")

                        self.request.close()

                        fabula.LOGGER.info("handler connection closed, stopping thread")

                        raise SystemExit

                    # Now listen for incoming client messages for some time (set
                    # above). This should catch any messages received in the
                    # meantime by the OS.
                    #
                    chunk = None

                    try:

                        # TODO: evaluate recv size
                        #
                        chunk = self.request.recv(4096)

                    except socket.timeout:

                        # Nobody likes us, evereyone left us, there all out
                        # without us, having fun...
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
