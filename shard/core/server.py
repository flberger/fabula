"""Shard Server Engine
"""

# Started with a dummy implementation on 25. Sep 2009
#
# Detailed work started on 30. Sep 2009

import shard
import shard.core
import signal
import time

class Server(shard.core.Engine):
    """The Server is the central management and control authority in Shard.
       It relies on the ServerInterface and the Plugin.

       Additional attributes:

       Server.interval
           1.0 / framerate

       Server.message_for_all
           Message to be broadcasted to all clients

       Server.exit_requested
           Flag to be changed by signal handler
     """

    def __init__(self, interface_instance, plugin_instance, logger, framerate):
        """Initialise the Server.
        """

        # Setup base class
        # Engine.__init__() calls EventProcessor.__init__()
        #
        shard.core.Engine.__init__(self,
                                   interface_instance,
                                   plugin_instance,
                                   logger)

        # If framerate is 0, run as fast as possible
        #
        if framerate:
            self.interval = 1.0 / framerate
        else:
            self.interval = 0

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
        """Server main method, calling the Plugin in the process.
        """

        self.logger.info("starting")

        # MAIN LOOP
        #
        while not self.exit_requested:

            for address_port_tuple in self.interface.connections:

                message = self.interface.connections[address_port_tuple].grab_message()

                if len(message.event_list):

                    self.logger.debug("{0} incoming: {1}".format(address_port_tuple, message))

                    for event in message.event_list:

                        # TODO: most client implementations should be allowed to send a single event per turn only!
                        # Otherwise, a long burst of events might unfairly
                        # block other clients. (hint by Alexander Marbach)

                        # Be sceptical. Only accept typical client events.
                        # TODO: Include shard.ChangeStateEvent?
                        #
                        if isinstance(event, (shard.InitEvent,
                                              shard.AttemptEvent,
                                              shard.SaysEvent)):

                            # This is a bit of Python magic. 
                            # self.event_dict is a dict which maps classes to
                            # handling functions. We use the class of the event
                            # supplied as a key to call the appropriate handler, and
                            # hand over the event.
                            # These methods may add events for the plugin engine
                            # to self.message_for_plugin
                            #
                            # client_key is really only needed by process_InitEvent,
                            # but to avoid splitting this beautiful call we submit
                            # it to all methods.
                            #
                            self.event_dict[event.__class__](event,
                                                             message = self.message_for_plugin,
                                                             client_key = address_port_tuple)
                        else:
                            # Looks like the Client sent an Event typically
                            # issued by the Server. Let the Plugin handle that.
                            #
                            self.logger.debug("'{}' is no typical client event, forwarding to Plugin".format(event.__class__.__name__))
                            self.message_for_plugin.event_list.append(event)

                        # Contrary to the Client, the Server calls its plugin
                        # engine on an event-by-event rather than on a
                        # message-by-message base to allow for quick and
                        # real-time reaction.

                        self.call_plugin(address_port_tuple)

                        # process next event in message from this client

                else:
                    # len(message.event_list) == 0
                    # Call Plugin anyway to catch Plugin initiated Events
                    # self.message_for_plugin is already set to an empty Message
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
        # Must not take too long since the client is waiting.
        # Call Plugin even if there were no Events from the client to catch
        # Plugin-initiated Events.
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
        # TODO: could we be required to send any new events to the story engine? But this could become an infinite loop!
        #
        for event in message_from_plugin.event_list:

            self.event_dict[event.__class__](event,
                                             message = self.message_for_remote,
                                             client_key = address_port_tuple)

        # If this iteration yielded any events, send them.
        # Message for remote host first
        #
        if self.message_for_remote.event_list:

            self.logger.debug("{0} outgoing: {1}".format(address_port_tuple,
                                                         self.message_for_remote))

            self.interface.connections[address_port_tuple].send_message(self.message_for_remote)

            ### Build broadcast message for all clients
            #
            # TODO: this of course has to be refactored thoroughly for multiple room handling

            # Triple flag:
            # True: skip on EnterRoomEvent
            # "now": now skip all events
            # False: stop skipping
            #
            skip_room_events = False

            # TODO: Skipping is not all too clever. There might be SpawnEvents that should go to all clients but are missed now.
            # TODO: The following ifs and loops can surely be optimized.
            #
            for event in self.message_for_remote.event_list:

                if isinstance(event, shard.RoomCompleteEvent):

                    self.logger.debug("found RoomCompleteEvent, will skip room events")

                    skip_room_events = True

            if not skip_room_events:

                self.logger.debug("no RoomCompleteEvent found, broadcasting all events")

            for event in self.message_for_remote.event_list:

                # We also broadcast all SpawnEvents. That means
                # that when a new client joins, all entities
                # (in the current room) are respawned.
                # process_SpawnEvent in the engine will
                # filter duplicate entities, so no harm done.
                # 
                # TODO: respawning might cause some loss of internal entity state
                #
                if (skip_room_events
                    and
                    isinstance(event, shard.EnterRoomEvent)):

                    self.logger.debug("EnterRoomEvent found, starting to skip")

                    skip_room_events = "now"

                elif (skip_room_events == "now"
                      and
                      isinstance(event, shard.RoomCompleteEvent)):

                    self.logger.debug("RoomCompleteEvent found, stopping to skip")

                    skip_room_events = False

                elif (not skip_room_events == "now"
                      and
                      event.__class__ in [shard.DropsEvent, 
                                          shard.MovesToEvent, 
                                          shard.PicksUpEvent,
                                          shard.SaysEvent,
                                          shard.SpawnEvent,
                                          shard.DeleteEvent,
                                          shard.ChangeStateEvent,
                                          shard.ChangeMapElementEvent]):

                    self.message_for_all.event_list.append(event)

            # Only send self.message_for_all when not empty
            #
            if len(self.message_for_all.event_list):

                self.logger.debug("message for all clients in current room: {}".format(self.message_for_all.event_list))

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
        """Stop the Server when an according OS signal is received.
        """

        signal_dict = {2 : "SIGINT",
                       3 : "SIGQUIT",
                       15 : "SIGTERM"}

        self.logger.info("caught signal {0} ({1}), setting exit flag".format(signalnum, signal_dict[signalnum]))

        self.exit_requested = True

        return

    def process_TriesToMoveEvent(self, event, **kwargs):
        """Test if the Entity is allowed to move to the desired location,
           and append an according event to the message.
        """

        # TODO: design by contract: entity in entity_dict? Target a tuple? ...

        self.logger.debug("{0} -> {1}".format(event.identifier, event.target_identifier))

        # Do we need to move / turn at all?
        #
        location = self.room.entity_locations[event.identifier]

        difference = shard.difference_2d(location,
                                         event.target_identifier)

        # Only allow certain vectors
        #
        if difference not in ((0, 1), (0, -1), (1, 0), (-1, 0)):

            kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

            # TODO: we exit here to hunt bugs
            #
            raise shard.ShardException("invalid difference in TriesToMoveEvent: {}".format(difference))

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

                    self.logger.debug("tile_type == shard.FLOOR")

                    # Check if this field is occupied
                    #
                    occupied = False

                    for entity in self.room.floor_plan[event.target_identifier].entities:

                        if entity.entity_type == shard.ITEM_BLOCK:

                            occupied = True

                    if occupied:

                        self.logger.debug("occupied by shard.ITEM_BLOCK")

                        kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

                    else:
                        # All clear. Go!
                        #
                        kwargs["message"].event_list.append(shard.MovesToEvent(event.identifier,
                                                                     event.target_identifier))

                else:

                    self.logger.debug("tile_type != shard.FLOOR")

                    kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

            except KeyError:

                self.logger.debug("KeyError")

                kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

        return

    def process_InitEvent(self, event, **kwargs):
        """Check if we already have a room and entities.
           If yes, send the data. If not, pass on to the plugin.
        """
        # TODO: update docstring

        self.logger.debug("called")

        if self.room is not None:

            self.logger.debug("sending existing floor_plan and entities")

            # TODO: The following is even worse in terms on consistency. :-) Replace with a clean, room-oriented design.
            #
            # This will register the client in the room and forward the Event.
            #
            self.process_EnterRoomEvent(shard.EnterRoomEvent(self.room.identifier),
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

                # We must spawn at a valid location. Spawning at the first
                # coordinate tuple in the room. Doesn't matter, it will be
                # picked up in an instant anyway.
                #
                spawn_event = shard.SpawnEvent(self.rack.entity_dict[identifier],
                                               self.room.floor_plan.keys()[0])

                self.message_for_remote.event_list.append(spawn_event)

                picks_up_event = shard.PicksUpEvent(self.rack.owner_dict[identifier],
                                                    identifier)

                self.message_for_remote.event_list.append(picks_up_event)

        # If a room has already been sent, the plugin should only spawn a new
        # player entity.
        #
        kwargs["message"].event_list.append(event)

        return

    def process_TriesToLookAtEvent(self, event, **kwargs):
        """Check what is being looked at and issue an according LookedAtEvent.
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
           replace event.target_identifier with the identifier of the Entity
           to be manipulated, then let the Plugin handle the Event.
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
        """Check what is being picked up, replace event.target_identifier with the identifier of the Entity to be picked up, then let the Plugin handle the Event.
        """

        # TODO: duplicate from TriesToManipulateEvent

        self.logger.debug("called")

        new_event = None

        # TODO: contracts...
        #
        if event.target_identifier in self.room.floor_plan:

            # TODO: This only tries to pick up the very last Entity encountered.
            #
            for entity in self.room.floor_plan[event.target_identifier].entities:

                if entity.entity_type in [shard.ITEM_BLOCK, shard.ITEM_NOBLOCK]:

                    self.logger.debug("trying to pick up '{}' at {}".format(entity.identifier,
                                                                            event.target_identifier))

                    new_event = shard.TriesToPickUpEvent(event.identifier,
                                                         entity.identifier)

        if new_event == None:

            # Nothing to pick up.
            # Issue AttemptFailed to unblock client.
            #
            self.logger.debug("AttemptFailed for {}".format(event))
            kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

        else:
            kwargs["message"].event_list.append(new_event)

        return

    def process_TriesToDropEvent(self, event, **kwargs):
        """Check for a valid drop action and issue DropsEvent or AttemptFailedEvent.

           If event.identifier does not own event.item_identifier in self.rack,
           the attempt fails.

           If event.target_identifier is not shard.FLOOR, the attempt fails.

           If event.target_identifier is shard.FLOOR and there is no Entity on
           it, pass event on to the Plugin.

           If event.target_identifier is shard.FLOOR and there is an Entity on
           it, replace target_identifier with Entity.identifier and pass on to
           the Plugin.
        """

        # TODO: These checks are so fundamental that they should probably be the default in Engine.process_TriesToDropEvent
        # TODO: What about Entities in walls?

        self.logger.debug("called")

        if event.item_identifier not in self.rack.entity_dict.keys():

            self.logger.debug("AttemptFailed: '{}' not in Rack".format(event.item_identifier))
            kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

        # If event.identifier does not own event.item_identifier in self.rack,
        # the attempt fails.
        #
        elif self.rack.owner_dict[event.item_identifier] != event.identifier:

            self.logger.debug("AttemptFailed: '{}' does not own '{}' in Rack".format(event.identifier, event.item_identifier))
            kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))
        
        elif event.target_identifier not in self.room.floor_plan:

            self.logger.debug("AttemptFailed: target {} not in Room.floor_plan".format(event.target_identifier, event.item_identifier))
            kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

        elif self.room.floor_plan[event.target_identifier].tile.tile_type != shard.FLOOR:

            # If event.target_identifier is not shard.FLOOR, the attempt fails.
            #
            self.logger.debug("AttemptFailed: tile at {} not FLOOR".format(event.target_identifier, event.item_identifier))
            kwargs["message"].event_list.append(shard.AttemptFailedEvent(event.identifier))

        elif len(self.room.floor_plan[event.target_identifier].entities):

            # If event.target_identifier is shard.FLOOR and there is at least
            # one Entity on it, replace target_identifier with the first
            # Entity's identifier and pass on to the Plugin.
            #
            target_identifier = self.room.floor_plan[event.target_identifier].entities[0].identifier

            kwargs["message"].event_list.append(shard.TriesToDropEvent(event.identifier,
                                                             event.item_identifier,
                                                             target_identifier))

        else:
            # If event.target_identifier is shard.FLOOR and there is no Entity
            # on it, pass event on to the Plugin.
            #
            kwargs["message"].event_list.append(event)

        return

    def process_EnterRoomEvent(self, event, **kwargs):
        """Register the client in the room and forward the Event.
        """

        self.logger.debug("called, room: {}".format(event.room_identifier))

        # TODO: Implement correct handling of multiple rooms.

        if self.room is None:

            self.room = shard.Room(event.room_identifier)
            self.logger.debug("registering client {} in new room".format(str(kwargs["client_key"])))
            self.room.active_clients.append(kwargs["client_key"])

        else:
            if event.room_identifier == self.room.identifier:

                if kwargs["client_key"] in self.room.active_clients:

                    self.logger.debug("client {} already in current room".format(str(kwargs["client_key"])))

                else:
                    self.logger.debug("registering client {} in current room".format(str(kwargs["client_key"])))
                    self.room.active_clients.append(kwargs["client_key"])

            else:
                self.room = shard.Room(event.room_identifier)
                self.logger.debug("registering client {} in new room".format(str(kwargs["client_key"])))
                self.room.active_clients.append(kwargs["client_key"])

        kwargs["message"].event_list.append(event)

        return
