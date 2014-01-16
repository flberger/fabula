"""Fabula Twisted Interface

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

import fabula
from collections import deque
from time import sleep
# Importing the Twisted base module for executable makers
import twisted
import twisted.internet
import twisted.internet.protocol
import twisted.internet.reactor
import twisted.internet.task

# TCP implementation using the Twisted framework
#
# Based on a pure socket implementation done in Oct 2009
#
# Exctracted from fabula.interfaces on 26. Mar 2012

# Twisted has not yet been ported to Python 3.

class ProtocolMessageBuffer(MessageBuffer,
                            twisted.internet.protocol.Protocol):
    """Buffer messages received and to be sent over the network.
       An instance of this class is created by a Twisted Factory
       every time a connection is made.
    """

    def __init__(self, logger):
        """Set up the MessageBuffer attributes, the logger, buffer, flags.
        """

        MessageBuffer.__init__(self)

        # Now we have:
        #
        # self.messages_for_local
        # self.messages_for_remote

        self.logger = logger

        self.data_buffer = ""

        self.connection_made = False

        fabula.LOGGER.debug("complete")

    def connectionMade(self):
        """Standard Twisted Protocol method.
           Now ProtocolMessageBuffer.transport is ready to be used.
        """

        fabula.LOGGER.debug("called")

        self.connection_made = True

    def dataReceived(self, data):
        """Standard Twisted Protocol method: handle received data.
        """
        # From the Twisted documentation:
        #  "Please keep in mind that you will probably need
        #   to buffer some data, as partial (or multiple)
        #   protocol messages may be received! I recommend
        #   that unit tests for protocols call through to
        #   this method with differing chunk sises, down to
        #   one byte at a time."

        fabula.LOGGER.info("received message: %s characters" % len(data))

        # Keep buffering data until we find a
        # dot (the pickle STOP opcode) followed
        # by a double newline in a message.
        #
        self.data_buffer = self.data_buffer + data

        double_newline_index = self.data_buffer.find(".\n\n")

        # There actually may be more than one
        # ".\n\n" separator in a message. Catch
        # them all!
        #
        while double_newline_index > -1:

            # Found!

            message = self.data_buffer[:double_newline_index] + "."

            self.data_buffer = self.data_buffer[double_newline_index + 3:]

            fabula.LOGGER.info("message complete at %s characters, %s left in buffer"
                               % (len(message),
                                  len(self.data_buffer)))

            message = pickle.loads(message)

            self.messages_for_local.append(message)

            # Next
            #
            double_newline_index = self.data_buffer.find(".\n\n")

    def send_queued_message(self, address_port_tuple):
        """Actually send messages queued with MessageBuffer.send_message()
           across the network.
        """

        if self.connection_made and self.messages_for_remote:

            fabula.LOGGER.info("sending 1 message of %s to %s"
                              % (len(self.messages_for_remote),
                                 address_port_tuple))

            # -1 = use highest available pickle protocol
            #
            # Separating messages with the standard
            # double newline.
            #
            # TODO: Check that double newlines are illegal in pickled data.
            #
            pickled_message = pickle.dumps(self.messages_for_remote.popleft(), -1)

            self.transport.write(pickled_message + "\n\n")

            fabula.LOGGER.info("sent %s characters" % len(pickled_message))

class TCPInterface(Interface):
    """A generic Fabula Interface using TCP, built upon the Twisted framework.
    """

    def __init__(self, connector, logger, interface_type, send_interval):
        """Initialisation.
           connector and logger are arguments for Interface.__init__.
           interface_type is either "client" or "server". send_interval is the
           interval of sending queued messages in seconds (float).
        """

        Interface.__init__(self, connector, logger)

        # Convenience name to make code clearer
        #
        self.address_port_tuple = self.connector

        self.interface_type = interface_type

        self.send_interval = send_interval

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

        # TODO: remove connections that caused an error?

        fabula.LOGGER.info("starting up")

        # We do all the Twisted setup here so
        # class instances can use the proxies
        # for the TCPClientInterface attributes.

        # Set up proxies
        #
        logger_proxy = self.logger
        connections_proxy = self.connections

        class MessageProtocolFactory(twisted.internet.protocol.ClientFactory):
            """Twisted ClientFactory implementation,
               producing a ProtocolMessageBuffer instance for every connection.
            """

            def buildProtocol(self, addr):
                """Standard Twisted Factory method
                   which creates an returns an instance of ProtocolMessageBuffer.
                """

                protocol_message_buffer = ProtocolMessageBuffer(logger_proxy)

                # Register at Interface level
                #
                logger_proxy.info("adding new connection: (%s, %s)"
                                  % (addr.host, addr.port))

                connections_proxy[(addr.host, addr.port)] = protocol_message_buffer

                return protocol_message_buffer

            def clientConnectionFailed(self, address_port_tuple, reason):

                logger_proxy.info("reason: %s" % reason)

            def clientConnectionLost(self, address_port_tuple, reason):

                logger_proxy.info("reason: %s" % reason)

            #def startedConnecting(self, address_port_tuple):
            #
            #    logger_proxy.debug("called")

            # End of MessageProtocolFactory class

        # The following twists are lessons learned
        # from developing the Fabula-based CharanisMLClient
        # in May 2008

        def check_shutdown():

            if self.shutdown_flag:

                fabula.LOGGER.info("caught shutdown_flag, closing connection and stopping reactor")

                self.shutdown_confirmed = True

                for protocol_message_buffer in self.connections.values():

                    protocol_message_buffer.transport.loseConnection()

                twisted.internet.reactor.stop()

            # End of check_shutdown()

        def send_all_queued_messages():

            for address_port_tuple in self.connections:

                # TODO: that's a very round-the-corner way supply address and port to the method
                #
                self.connections[address_port_tuple].send_queued_message(address_port_tuple)

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

            fabula.LOGGER.info("running in client mode")

            twisted.internet.reactor.connectTCP(self.address_port_tuple[0],
                                                self.address_port_tuple[1],
                                                MessageProtocolFactory())
        else:

            fabula.LOGGER.info("running in server mode")

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
        fabula.LOGGER.info("connection closed, reactor stopped, stopping thread")

        raise SystemExit
