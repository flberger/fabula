"""Fabula UDP Interface

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
import socket
import socketserver
import pickle

# UDP implementation
#
# Exctracted from fabula.interfaces on 26. Mar 2012

# TODO: This implementation may be defunct because of the Interface class refactoring. Check and refactor.

class UDPClientInterface(MessageBuffer, Interface):
    """This is the base class for a Fabula Client Interface.
       Implementations should subclass this one an override
       the default methods, which showcase a simple example.
    """

    def __init__(self, connector, logger):
        """Interface initialization.
        """

        # First call __init__() from the base class
        #
        Interface.__init__(self, connector, logger)

        # Convenience name to make code clearer
        #
        self.address_port_tuple = self.connector

        # This is a subclass of MessageBuffer, but
        # since we override __init__(), we have to
        # call the original method.
        #
        MessageBuffer.__init__(self)

        # Set up UDP socket
        # It wouldn't be unreasonable to also use
        # a socketserver on the client side. But
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

        fabula.LOGGER.debug("complete")

    def handle_messages(self):
        """The task of this method is to do whatever is necessary to send client messages and obtain server messages.
           It is meant to be the back end of send_message() and grab_message().
           Put some networking code, a GUI or a random generator here.
           This method is put in a background thread automatically, so it can
           do all sorts of polling or blocking IO.
           It should regularly check whether shutdown() has been called, and
           if so, it should notify shutdown() in some way (so that it can return
           True), and then raise SystemExit to stop the thread.
        """

        fabula.LOGGER.info("starting up")

        # Run thread as long as no shutdown is requested
        #
        while not self.shutdown_flag:

            if self.messages_for_remote:

                fabula.LOGGER.info("sending 1 message of " + str(len(self.messages_for_remote)))

                # -1 = use highest available pickle protocol
                #
                self.sock.sendto(pickle.dumps(self.messages_for_remote.popleft(), -1),
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

                fabula.LOGGER.info("received server message ("
                                  + str(len(data_received))
                                  + "/16384 bytes)")

                self.messages_for_local.append(pickle.loads(data_received))

        # Caught shutdown notification, stopping thread
        #
        fabula.LOGGER.info("shutting down")

        self.shutdown_confirmed = True

        raise SystemExit


class UDPServerInterface(Interface):
    """This is the base class for a Fabula Server Interface.
       Implementations should subclass this one an override
       the default methods, which do nothing.
    """

    def __init__(self, connector, logger):
        """Interface initialization."""

        # First call __init__() from the base class
        #
        Interface.__init__(self, connector, logger)

        # Convenience name to make code clearer
        #
        self.address_port_tuple = self.connector

        # client_connections is a dict of MessageBuffer
        # instances, indexed by (address, port) tuples.
        #
        self.client_connections = {}

        fabula.LOGGER.debug("complete")

    def handle_messages(self):
        """The task of this method is to do whatever is necessary to send server messages and obtain client messages.
           It is meant to be the back end of send_message() and grab_message().
           Put some networking code, a GUI or a random generator here.
           This method is put in a background thread automatically, so it can
           do all sorts of polling or blocking IO.
           It should regularly check whether shutdown() has been called, and if
           so, it should notify shutdown() in some way (so that it can return
           True), and then raise SystemExit to stop the thread.
        """

        fabula.LOGGER.info("starting up")

        client_connections_proxy = self.client_connections
        logger_proxy = self.logger

        # We define the class here to be able
        # to access variables of the ServerInterface
        # instance.
        #
        class FabulaRequestHandler(socketserver.BaseRequestHandler):

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
                message = pickle.loads(self.request[0])

                message_buffer = client_connections_proxy[self.client_address]

                message_buffer.messages_for_local.append(message)

                # End of handle() method.

        # End of class.

        server = socketserver.UDPServer(self.address_port_tuple, FabulaRequestHandler)

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

                    fabula.LOGGER.info("sending 1 message of "
                                      + str(len(message_buffer.messages_for_remote))
                                      + " to client "
                                      + str(address_port_tuple))

                    # -1 = use highest available pickle protocol
                    #
                    server.socket.sendto(pickle.dumps(message_buffer.messages_for_remote.popleft(), -1),
                                         address_port_tuple)

        # Caught shutdown notification, stopping thread
        #
        fabula.LOGGER.info("shutting down")

        self.shutdown_confirmed = True

        raise SystemExit
