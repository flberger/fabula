"""Shard Server Core Engine

   Started with a dummy implementation on 25. Sep 2009

   Detailed work started on 30. Sep 2009
"""

import shard
import shard.coreengine
import signal
import time

class ServerCoreEngine(shard.coreengine.CoreEngine):
    """The ServerCoreEngine is the central management
       and control authority in Shard. It relies
       on the ServerInterface and the StoryEngine.
    """

    def __init__(self, interface_instance, plugin_instance, logger):
        """Initialize the ServerCoreEngine.
        """

        self.setup_core_engine(interface_instance,
                               plugin_instance,
                               logger)

        # Now we have:
        #
        # self.logger
        #
        #     logging.Logger instance
        #
        #
        # self.interface
        #
        #     An instance of
        #     shard.interfaces.ServerInterface
        #
        #
        #     self.interface.client_connections
        #
        #         A dict of MessageBuffer instances,
        #         indexed by (address, port) tuples
        #
        #
        #     MessageBuffer.send_message(message)
        #     MessageBuffer.grab_message()
        #
        #         Methods for sending and retrieving
        #         messages
        #
        #
        # self.plugin
        #
        #     StoryEngine
        #
        #
        # self.event_dict
        #
        #     Dictionary that maps event classes to
        #     functions to be called for the respective
        #     event
        #
        #
        # self.message_for_plugin
        #
        #     Events for special consideration for the
        #     plugin. Must be emptied once the plugin
        #     has processed all Events.
        #
        #
        # self.message_for_remote
        #
        #     Events to be sent to the remote host in
        #     each loop

        # Message to be broadcasted to all clients
        #
        self.message_for_all = shard.Message([])

        # Flag to be changed by signal handler
        #
        self.exit_requested = False

        # install signal handlers
        #
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGQUIT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)

    def run(self):
        """ServerCoreEngine main method, calling
           the StoryEngine in the process.
        """

        self.logger.info("starting")

        # MAIN LOOP
        #
        while not self.exit_requested:

            for address_port_tuple in self.interface.client_connections:

                current_message_buffer = self.interface.client_connections[address_port_tuple]

                message = current_message_buffer.grab_message()

                for event in message.event_list:

                    # This is a bit of Python magic. 
                    # self.event_dict is a dict which maps classes to handling
                    # functions. We use the class of the event supplied as
                    # a key to call the appropriate handler, and hand over
                    # the event.
                    # These methods may add events for the plugin engine
                    # to self.message_for_plugin
                    #
                    self.event_dict[event.__class__](event)

                    # Contrary to the ClientCoreEngine, the
                    # ServerCoreEngine calls its plugin engine
                    # on an event-by-event rather than on a
                    # message-by-message base to allow for
                    # quick and real-time reaction.

                    # First hand over / update the necessary data.
                    #
                    # self.plugin.data = self.data

                    # Now go for it. Must not take too long
                    # since the client is waiting.
                    #
                    message_from_plugin = self.plugin.process_message(self.message_for_plugin)

                    # The plugin returned. Clean up.
                    #
                    self.message_for_plugin = shard.Message([])

                    # Process events from the story engine
                    # before returning them to the client.
                    # We cannot just forward them since we
                    # may be required to change maps, spawn
                    # entities etc.
                    # TODO: should add them to a different queue of course
                    #
                    for event in message_from_plugin.event_list:
                        self.event_dict[event.__class__](event)

                    # TODO: could we be required to send any new events to the story engine?
                    #       But this could become an infinite loop!

                    # If this iteration yielded any events, send them.
                    # Message for remote host only
                    #
                    if self.message_for_remote.event_list:

                        current_message_buffer.send_message(self.message_for_remote)

                    # Broadcast message
                    #
                    if self.message_for_all.event_list:

                        for message_buffer in self.interface.client_connections.values():

                            message_buffer.send_message(self.message_for_all)

                    # Clean up
                    #
                    self.message_for_remote = shard.Message([])
                    self.message_for_all = shard.Message([])

                    # process next event in message from this client

                # read from next client message_buffer

            # There is no need to run as fast as possible.
            # We slow it down a bit to prevent high CPU load.
            #
            time.sleep(0.1)

            # reiterate over client connections

        # exit has been requested
        #
        self.logger.info("exit flag set, shutting down interface")

        # stop the Interface thread
        #
        self.interface.shutdown()

        self.logger.info("shutdown confirmed")

        # TODO: possibly exit cleanly from the plugin here

        return

    def handle_exit(self, signalnum, frame):
        """Stop the ServerCoreEngine when an
           according OS signal is received.
        """

        signal_dict = {2 : "SIGINT",
                       3 : "SIGQUIT",
                       15 : "SIGTERM"
                      }

        self.logger.info("caught signal "
              + str(signalnum)
              + " ("
              + signal_dict[signalnum]
              + "), setting exit flag")

        self.exit_requested = True

    # TODO: restart plugin when SIGHUP is received
