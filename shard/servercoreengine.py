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

    def __init__(self, framerate, interface_instance, plugin_instance, logger):
        """Initialize the ServerCoreEngine.
        """

        self.interval = 1.0 / framerate

        # Setup base class
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
        # self.room = shard.Room()
        #
        #     self.room.entity_dict
        #         A dict of all Entities in this room,
        #         mapping Entity identifiers to Entity
        #         instances.
        #
        #     self.room.floor_plan
        #         A dict mapping 2D coordinate tuples
        #         to a FloorPlanElement instance.
        #
        #     self.room.entity_locations
        #         A dict mapping Entity identifiers to a
        #         2D coordinate tuple.

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

                message = self.interface.connections[address_port_tuple].grab_message()

                if len(message.event_list):

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
                        # client_key is really only needed
                        # by process_InitEvent, but to avoid splitting
                        # this beautiful call we submit it to all methods.
                        #
                        self.event_dict[event.__class__](event,
                                                         message = self.message_for_plugin,
                                                         client_key = address_port_tuple)

                        # Contrary to the ClientCoreEngine, the
                        # ServerCoreEngine calls its plugin engine
                        # on an event-by-event rather than on a
                        # message-by-message base to allow for
                        # quick and real-time reaction.

                        self.call_plugin(address_port_tuple)

                        # process next event in message from this client

                else:
                    # len(message.event_list) == 0
                    #
                    # Call Plugin anyway to catch
                    # Plugin initiated Events
                    #
                    # self.message_for_plugin is already set
                    # to an empty Message
                    #
                    self.call_plugin(address_port_tuple)

                # read from next client message_buffer

            # There is no need to run as fast as possible.
            # We slow it down a bit to prevent high CPU load.
            # Interval between loops has been computed from
            # framerate given.
            #
            time.sleep(self.interval)

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

    def call_plugin(self, address_port_tuple):
        """Call Plugin and process Plugin message.
           Auxiliary method.
        """

        # Put in a method to avoid duplication.

        # Must not take too long since the client
        # is waiting.
        #
        # Call Plugin to catch Plugin-initiated
        # Events even if there were no Events
        # from the client.
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
            self.event_dict[event.__class__](event,
                                             message = self.message_for_remote,
                                             client_key = address_port_tuple)

        # If this iteration yielded any events, send them.
        # Message for remote host first
        #
        if self.message_for_remote.event_list:

            self.interface.connections[address_port_tuple].send_message(self.message_for_remote)

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
                                   shard.DeleteEvent,
                                   shard.ChangeStateEvent]:

                self.message_for_all.event_list.append(event)

        # Only send self.message_for_all when not empty
        #
        if len(self.message_for_all.event_list):

            self.logger.debug("message for all clients in current room: %s"
                              % self.message_for_all.event_list)

            for client_key in self.room.active_clients:

                # Leave out current MessageBuffer which
                # already has reveived the events above.
                # We can compare MessageBuffer instances
                # right away. ;-)
                #
                if not client_key == address_port_tuple:

                    self.interface.connections[client_key].send_message(self.message_for_all)

        # Clean up
        #
        self.message_for_remote = shard.Message([])
        self.message_for_all = shard.Message([])

        return

    def handle_exit(self, signalnum, frame):
        """Stop the ServerCoreEngine when an
           according OS signal is received.
        """

        signal_dict = {2 : "SIGINT",
                       3 : "SIGQUIT",
                       15 : "SIGTERM"}

        self.logger.info("caught signal %s (%s), setting exit flag"
                         % (signalnum, signal_dict[signalnum]))


        self.exit_requested = True

        return

    def process_TriesToMoveEvent(self, event, **kwargs):
        """Test if the Entity is allowed to move
           to the desired location, and append an
           according event to the message.
        """

        # TODO: design by contract: entity in entity_dict? Target a tuple? ...

        self.logger.debug("%s -> %s" % (event.identifier, event.target_identifier))

        # Do we need to move / turn at all?
        #
        location = self.room.entity_locations[event.identifier]
        difference = shard.difference_2d(location,
                                         event.target_identifier)

        # Only allow certain vectors
        #
        if difference not in ((0, 1), (0, -1), (1, 0), (-1, 0)):

            kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

        else:

            # TODO: event.identifier in self.room.entity_dict? event.target_identifier in shard.DIRECTION_VECTOR?

            # Test if a movement from the current
            # entity location to the new location
            # on the map is possible
            #
            try:
                # Check tile type
                #
                tile = self.room.floor_plan[event.target_identifier].tile 

                if tile.tile_type == shard.FLOOR:

                    # Check if this field is occupied
                    #
                    occupied = False

                    for entity in self.room.floor_plan[event.target_identifier].entities:

                        if entity.entity_type == shard.ITEM_BLOCK:

                            occupied = True

                    if occupied:

                        kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

                    else:
                        # All clear. Go!
                        #
                        kwargs["message"].event_list.append(shard.MovesToEvent(event.identifier,
                                                                     event.target_identifier))

                else:

                    kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

            except KeyError:

                kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

        return

    def process_InitEvent(self, event, **kwargs):
        """Check if we already have a room and
           entities. If yes, send the data
           If not, pass on to the plugin.
        """

        if len(self.room.floor_plan):

            self.logger.debug("sending existing floor_plan and entities")

            # TODO: The following is even worse in terms on consistency. :-) Replace with a clean, room-oriented design.
            #
            # This will register the client in the room and forward
            # the Event.
            #
            self.process_EnterRoomEvent(shard.EnterRoomEvent(),
                                        message = self.message_for_remote,
                                        client_key = kwargs["client_key"])

            for tuple in self.room.floor_plan:

                tile = self.room.floor_plan[tuple].tile

                change_map_element_event = shard.ChangeMapElementEvent(tile, tuple)

                # TODO: It's not very clean to write to self.message_for_remote directly since the procces_() methods are not supposed to do so.
                #
                self.message_for_remote.event_list.append(change_map_element_event)

            for identifier in self.room.entity_locations:

                spawn_event = shard.SpawnEvent(self.room.entity_dict[identifier],
                                               self.room.entity_locations[identifier])

                self.message_for_remote.event_list.append(spawn_event)

            self.message_for_remote.event_list.append(shard.RoomCompleteEvent())

        if len(self.rack.entity_dict):

            self.logger.debug("sending Spawn and PickUpEvents from existing rack")

            for identifier in self.rack.entity_dict:

                # We must spawn at a valid location.
                # Spawning at the first coordinate
                # tuple in the room. Doesn't matter,
                # it will be picked up in an instant
                # anyway.
                #
                spawn_event = shard.SpawnEvent(self.rack.entity_dict[identifier],
                                               self.room.floor_plan.keys()[0])

                self.message_for_remote.event_list.append(spawn_event)

                picks_up_event = shard.PicksUpEvent(self.rack.owner_dict[identifier],
                                                    identifier)

                self.message_for_remote.event_list.append(picks_up_event)

        # If a room has already been sent,
        # the plugin should only spawn a
        # new player entity.
        #
        kwargs["message"].event_list.append(event)

        return

    def process_TriesToLookAtEvent(self, event, **kwargs):
        """Check what is being looked at and
           issue an according LookedAtEvent.
        """

        new_event = None

        # TODO: contracts...
        #
        if event.target_identifier in self.room.floor_plan:

            for entity in self.room.floor_plan[event.target_identifier].entities:

                if entity.entity_type in [shard.ITEM_BLOCK, shard.ITEM_NOBLOCK]:

                    new_event = shard.LookedAtEvent(entity.identifier,
                                                    event.identifier)

        if new_event == None:

            # Nothing to look at.
            # Issue AttemptFailed to unblock client.
            #
            kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

        else:
            kwargs["message"].event_list.append(new_event)

        return

    def process_TriesToManipulateEvent(self, event, **kwargs):
        """Check what is being manipulated,
           replace event.target_identifier
           with the identifier of the Entity
           to be manipulated, then let the
           Plugin handle the Event.
        """

        # TODO: duplicate from / similar to process_TriesToLookAtEvent

        new_event = None

        # TODO: contracts...
        #
        if event.target_identifier in self.room.floor_plan:

            for entity in self.room.floor_plan[event.target_identifier].entities:

                if entity.entity_type in [shard.ITEM_BLOCK, shard.ITEM_NOBLOCK]:

                    new_event = shard.TriesToManipulateEvent(event.identifier,
                                                             entity.identifier)

        if new_event == None:

            # Nothing to manipulate.
            # Issue AttemptFailed to unblock client.
            #
            kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

        else:
            kwargs["message"].event_list.append(new_event)

        return

    def process_TriesToPickUpEvent(self, event, **kwargs):
        """Check what is being picked up,
           replace event.target_identifier
           with the identifier of the Entity
           to be picked up, then let the
           Plugin handle the Event.
        """

        # TODO: duplicate from TriesToManipulateEvent

        new_event = None

        # TODO: contracts...
        #
        if event.target_identifier in self.room.floor_plan:

            # TODO: This only tries to pick up the very last Entity encountered.
            #
            for entity in self.room.floor_plan[event.target_identifier].entities:

                if entity.entity_type in [shard.ITEM_BLOCK, shard.ITEM_NOBLOCK]:

                    new_event = shard.TriesToPickUpEvent(event.identifier,
                                                         entity.identifier)

        if new_event == None:

            # Nothing to pick up.
            # Issue AttemptFailed to unblock client.
            #
            kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

        else:
            kwargs["message"].event_list.append(new_event)

        return

    def process_TriesToDropEvent(self, event, **kwargs):
        """If event.identifier does not own
           event.item_identifier in self.rack,
           the attempt fails.

           If event.target_identifier is not
           shard.FLOOR, the attempt fails.

           If event.target_identifier is
           shard.FLOOR and there is no Entity
           on it, pass event on to the Plugin.

           If event.target_identifier is
           shard.FLOOR and there is an Entity
           on it, replace target_identifier with
           Entity.identifier and pass on to the
           Plugin.
        """

        # TODO: These checks are so fundamental that they should probably be the default in CoreEngine.process_TriesToDropEvent

        self.logger.debug("called")

        # If event.identifier does not own
        # event.item_identifier in self.rack,
        # the attempt fails.
        #
        if self.rack.owner_dict[event.item_identifier] != event.identifier:

            kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))
        
        elif event.target_identifier not in self.room.floor_plan:

            kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

        elif self.room.floor_plan[event.target_identifier].tile.tile_type != shard.FLOOR:

            # If event.target_identifier is not
            # shard.FLOOR, the attempt fails.
            #
            kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

        elif len(self.room.floor_plan[event.target_identifier].entities):

            # If event.target_identifier is
            # shard.FLOOR and there is at least one
            # Entity on it, replace target_identifier
            # with the first Entity's identifier and
            # pass on to the Plugin.
            #
            target_identifier = self.room.floor_plan[event.target_identifier].entities[0].identifier

            kwargs["message"].event_list.append(shard.TriesToDropEvent(event.identifier,
                                                             event.item_identifier,
                                                             target_identifier))

        else:
            # If event.target_identifier is
            # shard.FLOOR and there is no Entity
            # on it, pass event on to the Plugin.
            #
            kwargs["message"].event_list.append(event)

        return

    def process_EnterRoomEvent(self, event, **kwargs):
        """Register the client in the room and 
           forward the Event.
        """

        # TODO: This is a hack. Implement correct handling of multiple rooms.
        #
        if kwargs["client_key"] in self.room.active_clients:

            self.logger.debug("client %s already in current room, deregistering"
                              % str(kwargs["client_key"]))

            self.room.active_clients.remove(kwargs["client_key"])

        else:

            self.logger.debug("registering client %s in current room"
                              % str(kwargs["client_key"]))

            self.room.active_clients.append(kwargs["client_key"])

        kwargs["message"].event_list.append(event)

        return
