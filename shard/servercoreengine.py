"""Shard Server Core Engine
"""

# Started with a dummy implementation on 25. Sep 2009
#
# Detailed work started on 30. Sep 2009

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

        # First setup base class
        #
        self.setup_eventprocessor()

        # Now we have:
        #
        # self.event_dict
        #
        #     Dictionary that maps event classes to
        #     functions to be called for the respective
        #     event

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
        #     self.interface.connections
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
        #
        #
        # self.entity_dict = {}
        #
        #     self.entity_dict keeps track of all active Entites.
        #     It uses the identifier as a key, assuming that it
        #     is unique.
        #
        #
        # self.map = {}
        #
        #
        #     self.map is an attempt of an efficient storage of
        #     an arbitrary two-dimensional map. To save space, 
        #     only explicitly defined elements are stored. This
        #     is done in a dict whose keys are tuples. Access the
        #     element using self.map[(x, y)]. The upper left element
        #     is self.map[(0, 0)].

        # Message to be broadcasted to all clients
        #
        self.message_for_all = shard.Message([])

        # Flag to be changed by signal handler
        #
        self.exit_requested = False

        # install signal handlers
        #
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)

        try:
            signal.signal(signal.SIGQUIT, self.handle_exit)

        except:
            # Microsoft Windows has no SIGQUIT - ignore
            #
            pass

        # TODO: restart plugin when SIGHUP is received

    def run(self):
        """ServerCoreEngine main method, calling
           the StoryEngine in the process.
        """

        self.logger.info("starting")

        # MAIN LOOP
        #
        while not self.exit_requested:

            for address_port_tuple in self.interface.connections:

                current_message_buffer = self.interface.connections[address_port_tuple]

                message = current_message_buffer.grab_message()

                for event in message.event_list:

                    # TODO: most client implementations should be allowed to send a single event per turn only!
                    # Otherwise, a long burst of events might unfairly
                    # block other clients. (hint by Alexander Marbach)

                    # TODO: call story engine even if client message is empty!
                    # Probably at the end of the connections loop, treating 
                    # the plugin as another client (idea Alexander Marbach).

                    # This is a bit of Python magic. 
                    # self.event_dict is a dict which maps classes to handling
                    # functions. We use the class of the event supplied as
                    # a key to call the appropriate handler, and hand over
                    # the event.
                    # These methods may add events for the plugin engine
                    # to self.message_for_plugin
                    #
                    self.event_dict[event.__class__](event, self.message_for_plugin)

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
                    # Note that this time resulting events
                    # are queued for the remote host, not
                    # the plugin.
                    #
                    # TODO: could we be required to send any new events to the story engine?
                    #       But this could become an infinite loop!
                    #
                    for event in message_from_plugin.event_list:
                        self.event_dict[event.__class__](event, self.message_for_remote)

                    # If this iteration yielded any events, send them.
                    # Message for remote host first
                    #
                    if self.message_for_remote.event_list:

                        current_message_buffer.send_message(self.message_for_remote)

                    # Build broadcast message for all clients
                    #
                    for event in self.message_for_remote.event_list:

                        # We currently leave out ChangeMapElementEvent
                        # since it is tightly coupled to EnterRoom.
                        #
                        # We also broadcast all SpawnEvents. That means
                        # that when a new client joins, all entities
                        # (in the current room) are respawned.
                        # process_SpawnEvent in the core engine will
                        # filter duplicate entities, so no harm done.
                        # 
                        # TODO: respawning might cause some loss of internal entity state
                        #
                        if event.__class__ in [shard.DropsEvent, 
                                               shard.MovesToEvent, 
                                               shard.PicksUpEvent,
                                               shard.SaysEvent,
                                               shard.SpawnEvent,
                                               shard.DeleteEvent]:

                            self.message_for_all.event_list.append(event)

                    self.logger.debug("message for all clients: "
                                      + str(self.message_for_all.event_list))

                    # Only send self.message_for_all when not empty
                    #
                    if len(self.message_for_all.event_list):

                        for message_buffer in self.interface.connections.values():

                            # Leave out current MessageBuffer which
                            # already has reveived the events above.
                            # We can compare MessageBuffer instances
                            # right away. ;-)
                            #
                            if not message_buffer == current_message_buffer:

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
            #
            #self.logger.debug("reading client messages")

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

    def process_TriesToMoveEvent(self, event, message):
        """Test if the Entity is allowed to move
           to the desired location, and append an
           according event to the message.
        """

        self.logger.debug("called")

        # TODO: design by contract: entity in entity_dict? Target a tuple? ...

        self.logger.debug("%s -> %s" % (event.identifier, event.target_identifier))

        # In case of an AttemptEvent, make the
        # affected entity turn into the direction
        # of the event
        #
        direction = shard.difference_2d(self.entity_dict[event.identifier].location,
                                        event.target_identifier)

        self.entity_dict[event.identifier].direction = direction

        # Test if a movement from the current
        # entity location to the new location
        # on the map is possible
        #
        # TODO: Entities should be able to make a map element an obstacle. But not all entities, so an attribute might be needed.
        #
        try:
            if self.map[event.target_identifier].tile_type == "FLOOR":

                message.event_list.append(shard.MovesToEvent(event.identifier,
                                                             event.target_identifier))
            else:

                message.event_list.append(shard.AttemptFailedEvent(event.identifier))

        except KeyError:

            message.event_list.append(shard.AttemptFailedEvent(event.identifier))

    def process_InitEvent(self, event, message):
        """Check if we already have a room and
           entities and send the data to the
           client. If not, pass on to the plugin.
        """

        if len(self.map):

            self.logger.debug("sending existing map and entities")

            # It's not very clean to write to
            # self.message_for_remote directly
            # since the procces_() methods are
            # not supposed to do so.
            #
            self.message_for_remote.event_list.append(shard.EnterRoomEvent())

            for tuple in self.map:

                self.message_for_remote.event_list.append(shard.ChangeMapElementEvent(self.map[tuple],
                                                                                      tuple))

            for entity in self.entity_dict.values():

                self.message_for_remote.event_list.append(shard.SpawnEvent(entity))

            self.message_for_remote.event_list.append(shard.RoomCompleteEvent())

        # If a room has already been sent,
        # the plugin should only spawn a
        # new player entity.
        #
        message.event_list.append(event)
