"""Fabula Interface Base Classes and Standalone Interface

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
           shutdown() by setting self.shutdown_confirmed to True (so that
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
