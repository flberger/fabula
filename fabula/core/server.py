"""Fabula Server Engine

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

# Started with a dummy implementation on 25. Sep 2009
#
# Detailed work started on 30. Sep 2009

import fabula
import fabula.core
import time

# TODO: Add a decent default server CLI.

class Server(fabula.core.Engine):
    """The Server is the central management and control authority in Fabula.
       It relies on the ServerInterface and the Plugin.

       Additional attributes:

       Server.interval
           1.0 / framerate

       Server.action_time
           The time between actions that do not happen instantly.
           Used by the Server Plugin.

       Server.message_for_all
           Message to be broadcasted to all clients

       Server.exit_requested
           Flag to be changed by signal handler
     """

    def __init__(self, interface_instance, framerate, action_time, threadsafe = True):
        """Initialise the Server.
           If threadsafe is True (default), no signal handlers are installed.
        """

        # Setup base class
        # Engine.__init__() calls EventProcessor.__init__()
        #
        fabula.core.Engine.__init__(self,
                                   interface_instance)

        # If framerate is 0, run as fast as possible
        #
        if framerate:
            self.interval = 1.0 / framerate
        else:
            self.interval = 0

        # The time between actions that do not happen instantly. Used by the
        # Server Plugin.
        #
        self.action_time = action_time

        # Message to be broadcasted to all clients
        #
        self.message_for_all = fabula.Message([])

        # Flag to be changed by signal handler
        #
        self.exit_requested = False

        if not threadsafe:

            # install signal handlers
            #
            import signal

            signal.signal(signal.SIGINT, self.handle_exit)
            signal.signal(signal.SIGTERM, self.handle_exit)

            try:
                signal.signal(signal.SIGQUIT, self.handle_exit)

            except:
                # Microsoft Windows has no SIGQUIT - ignore
                #
                pass

            # TODO: restart plugin when SIGHUP is received

        return

    def run(self):
        """Main loop of the Server.
           This is a blocking method. It calls all the process methods to
           process events, and then the plugin.
        """

        # TODO: retrieve connector from somewhere
        #
        connector = ("0.0.0.0", 6161)

        fabula.LOGGER.info("attempting to connect server interface to '{}'".format(connector))

        try:
            self.interface.connect(connector)

        except:
            fabula.LOGGER.warning("Exception in interface.connect() (server interface already connected?), continuing anyway")

        fabula.LOGGER.info("starting main loop")

        # MAIN LOOP
        # TODO: Server.exit_requested is inconsistent with Client.plugin.exit_requested
        #
        while not self.exit_requested:

            for connector in self.interface.connections:

                message = self.interface.connections[connector].grab_message()

                if len(message.event_list):

                    fabula.LOGGER.debug("{0} incoming: {1}".format(connector, message))

                    for event in message.event_list:

                        # TODO: most client implementations should be allowed to send a single event per turn only!
                        # Otherwise, a long burst of events might unfairly
                        # block other clients. (hint by Alexander Marbach)

                        # Be sceptical. Only accept typical client events.
                        # TODO: Include fabula.ChangePropertyEvent?
                        #
                        if isinstance(event, (fabula.InitEvent,
                                              fabula.AttemptEvent,
                                              fabula.SaysEvent)):

                            # This is a bit of Python magic.
                            # self.event_dict is a dict which maps classes to
                            # handling functions. We use the class of the event
                            # supplied as a key to call the appropriate handler, and
                            # hand over the event.
                            # These methods may add events for the plugin engine
                            # to self.message_for_plugin
                            #
                            # connector is not needed by all methods, but to
                            # avoid splitting this beautiful call we submit
                            # it to all of them.
                            #
                            self.event_dict[event.__class__](event,
                                                             message = self.message_for_plugin,
                                                             connector = connector)

                        else:
                            # Looks like the Client sent an Event typically
                            # issued by the Server. Let the Plugin handle that.
                            #
                            fabula.LOGGER.warning("'{}' is no typical client event, forwarding to Plugin".format(event.__class__.__name__))

                            self.message_for_plugin.event_list.append(event)

                        # Contrary to the Client, the Server calls its plugin
                        # engine on an event-by-event rather than on a
                        # message-by-message base to allow for quick and
                        # real-time reaction.

                        self.call_plugin(connector)

                        # process next event in message from this client

                else:
                    # len(message.event_list) == 0
                    # Call Plugin anyway to catch Plugin initiated Events
                    # self.message_for_plugin is already set to an empty Message
                    #
                    self.call_plugin(connector)

                # read from next client message_buffer

            # There is no need to run as fast as possible.
            # We slow it down a bit to prevent high CPU load.
            # Interval between loops has been computed from
            # framerate given.
            #
            time.sleep(self.interval)

            # reiterate over client connections
            #
            #fabula.LOGGER.info("reading client messages")

        # exit has been requested
        #
        fabula.LOGGER.info("exit flag set, shutting down interface")

        # stop the Interface thread
        #
        self.interface.shutdown()

        fabula.LOGGER.info("shutdown confirmed")

        # TODO: possibly exit cleanly from the plugin here

        return

    def call_plugin(self, connector):
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
        self.message_for_plugin = fabula.Message([])

        # Process events from the Plugin before returning them to the client.
        # We cannot just forward them since we may be required to change maps,
        # spawn entities etc.
        # Note that this time resulting events are queued for the remote host,
        # not the plugin.
        #
        # TODO: could we be required to send any new events to the Plugin? But this could become an infinite loop!
        # TODO: Again it's completely weird to give the Message as an argument. Functions should return Event lists instead.
        #
        for event in message_from_plugin.event_list:

            self.event_dict[event.__class__](event,
                                             message = self.message_for_remote,
                                             connector = connector)

        # If this iteration yielded any events, send them.
        # Message for remote host first
        #
        if self.message_for_remote.event_list:

            fabula.LOGGER.debug("{0} outgoing: {1}".format(connector,
                                                           self.message_for_remote))

            self.interface.connections[connector].send_message(self.message_for_remote)

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

                if isinstance(event, fabula.RoomCompleteEvent):

                    fabula.LOGGER.info("found RoomCompleteEvent, will skip room events")

                    skip_room_events = True

            if not skip_room_events:

                fabula.LOGGER.info("no RoomCompleteEvent found, will broadcast all events")

            for event in self.message_for_remote.event_list:

                if (skip_room_events
                    and isinstance(event, fabula.EnterRoomEvent)):

                    fabula.LOGGER.info("EnterRoomEvent found, starting to skip")

                    skip_room_events = "now"

                elif (skip_room_events == "now"
                      and isinstance(event, fabula.SpawnEvent)
                      and event.entity.identifier == self.room.active_clients[connector]):

                    fabula.LOGGER.debug("SpawnEvent for current player entity '{}' while skipping, broadcasting this one")

                    self.message_for_all.event_list.append(event)

                elif (skip_room_events == "now"
                      and isinstance(event, fabula.RoomCompleteEvent)):

                    fabula.LOGGER.info("RoomCompleteEvent found, stopping to skip")

                    skip_room_events = False

                elif not skip_room_events == "now":

                    if event.__class__ in [fabula.DropsEvent,
                                           fabula.MovesToEvent,
                                           fabula.PicksUpEvent,
                                           fabula.SaysEvent,
                                           fabula.SpawnEvent,
                                           fabula.DeleteEvent,
                                           fabula.ChangePropertyEvent,
                                           fabula.ChangeMapElementEvent,
                                           fabula.CanSpeakEvent,
                                           fabula.ManipulatesEvent,
                                           fabula.PerceptionEvent]:

                        # TODO: Is this Event type filter still necessary? We check identifiers in the Client. Most of them.

                        self.message_for_all.event_list.append(event)

                    else:
                        fabula.LOGGER.warning("Event not in whitelist for broadcasting, discarding: {}".format(event))

            # Only send self.message_for_all when not empty
            #
            if len(self.message_for_all.event_list):

                fabula.LOGGER.debug("message for all clients in current room: {}".format(self.message_for_all.event_list))

                for active_connector in self.room.active_clients.keys():

                    # Leave out current client which already has reveived the
                    # events above.
                    #
                    if not active_connector == connector:

                        self.interface.connections[active_connector].send_message(self.message_for_all)

        # Clean up
        #
        self.message_for_remote = fabula.Message([])
        self.message_for_all = fabula.Message([])

        return

    def handle_exit(self, signalnum, frame):
        """Callback to stop the Server when an according OS signal is received.
        """

        signal_dict = {2 : "SIGINT",
                       3 : "SIGQUIT",
                       15 : "SIGTERM"}

        fabula.LOGGER.info("caught signal {0} ({1}), setting exit flag".format(signalnum, signal_dict[signalnum]))

        self.exit_requested = True

        return

    def process_TriesToMoveEvent(self, event, **kwargs):
        """Perform sanity checks on target and either confirm, reject or forward to Plugin.
        """

        # TODO: design by contract: entity in entity_dict? Target a tuple? ...

        fabula.LOGGER.info("{0} -> {1}".format(event.identifier, event.target_identifier))

        if not self.room.entity_dict[event.identifier].mobile:

            fabula.LOGGER.info("'{}' is not mobile".format(event.identifier))

            kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

        elif not self.tile_is_walkable(event.target_identifier):

            fabula.LOGGER.info("{} not walkable".format(event.target_identifier))

            kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

        else:
            fabula.LOGGER.info("target clear, forwarding event to plugin")

            kwargs["message"].event_list.append(event)

        return

    def process_InitEvent(self, event, **kwargs):
        """Check if we already have a room and entities. If yes, send the data. If not, pass on to the plugin.
        """
        # TODO: update docstring

        fabula.LOGGER.info("sending Server parameters")

        self.message_for_remote.event_list.append(fabula.ServerParametersEvent(self.action_time))

        if self.room is not None:

            fabula.LOGGER.debug("creating and processing EnterRoomEvent for new client")

            enter_room_event = fabula.EnterRoomEvent(event.identifier,
                                                     self.room.identifier)

            # Process the Event right away, since it is not going through the
            # Plugin. This will also append the Event to self.message_for_remote.
            #
            self.process_EnterRoomEvent(enter_room_event,
                                        connector = kwargs["connector"],
                                        message = self.message_for_remote)

            fabula.LOGGER.info("sending existing floor_plan and entities")

            for tuple in self.room.floor_plan:

                tile = self.room.floor_plan[tuple].tile

                change_map_element_event = fabula.ChangeMapElementEvent(tile, tuple)

                # TODO: It's not very clean to write to self.message_for_remote directly since the procces_() methods are not supposed to do so.
                #
                self.message_for_remote.event_list.append(change_map_element_event)

            for identifier in self.room.entity_locations:

                entity = self.room.entity_dict[identifier]

                spawn_event = fabula.SpawnEvent(entity,
                                                self.room.entity_locations[identifier])

                self.message_for_remote.event_list.append(spawn_event)

                # Send properties of the Entity if there are any
                #
                for property in entity.property_dict.keys():

                    change_property_event = fabula.ChangePropertyEvent(entity.identifier,
                                                                       property,
                                                                       entity.property_dict[property])

                    self.message_for_remote.event_list.append(change_property_event)

        if len(self.rack.entity_dict):

            fabula.LOGGER.info("sending Spawn and PickUpEvents from existing rack")

            for identifier in self.rack.entity_dict:

                # We must spawn at a valid location. Spawning at the first
                # coordinate tuple in the room. Doesn't matter, it will be
                # picked up in an instant anyway.
                #
                spawn_event = fabula.SpawnEvent(self.rack.entity_dict[identifier],
                                                list(self.room.floor_plan.keys())[0])

                self.message_for_remote.event_list.append(spawn_event)

                # Owner may be 'None' when the Entity is in Rack because it
                # has been deleted. In this case, send DeleteEvent.
                #
                if self.rack.owner_dict[identifier] is None:

                    fabula.LOGGER.debug("owner of '{}' is None, sending DeleteEvent".format(identifier))

                    delete_event = fabula.DeleteEvent(identifier)

                    self.message_for_remote.event_list.append(delete_event)

                else:
                    picks_up_event = fabula.PicksUpEvent(self.rack.owner_dict[identifier],
                                                         identifier)

                    self.message_for_remote.event_list.append(picks_up_event)

        # If a room has already been sent, the plugin should only spawn a new
        # player entity.
        # The Plugin will add RoomCompleteEvent when processing InitEvent.
        #
        kwargs["message"].event_list.append(event)

        return

    def process_TriesToLookAtEvent(self, event, **kwargs):
        """Check what is being looked at, forward the Event and issue an according LookedAtEvent.
        """

        # TODO: contracts...

        if event.target_identifier in self.room.floor_plan:

            new_events = [event]
            entities = self.room.floor_plan[event.target_identifier].entities

            for entity in entities:

                event.target_identifier = entity.identifier

                new_events = [event,
                              fabula.LookedAtEvent(entity.identifier,
                                                  event.identifier)]

            fabula.LOGGER.info("forwarding event(s)")
            kwargs["message"].event_list.extend(new_events)

        else:
            fabula.LOGGER.info("AttemptFailed: {} not in floor_plan".format(event.target_identifier))

            # Issue AttemptFailed to unblock client.
            #
            kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

        return

    def process_TriesToTalkToEvent(self, event, **kwargs):
        """Check who is being talked to and forward the Event.
        """

        if event.target_identifier in self.room.floor_plan:

            if not self.room.floor_plan[event.target_identifier].entities:

                fabula.LOGGER.info("AttemptFailed: no entity to talk to at {}".format(event.target_identifier))
                fabula.LOGGER.debug("room.entity_locations == {}".format(self.room.entity_locations))

                kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

            else:
                # Pick last Entity
                #
                event.target_identifier = self.room.floor_plan[event.target_identifier].entities[-1].identifier

                fabula.LOGGER.info("forwarding event")

                kwargs["message"].event_list.append(event)

        else:
            fabula.LOGGER.info("AttemptFailed: no key '{}' in floor_plan".format(event.target_identifier))

            # Issue AttemptFailed to unblock client.
            #
            kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

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

                if entity.entity_type == fabula.ITEM:

                    new_event = fabula.TriesToManipulateEvent(event.identifier,
                                                             entity.identifier)
                else:
                    fabula.LOGGER.info("Entity type '{}' can not be manipulated".format(entity.entity_type))


        if new_event == None:

            fabula.LOGGER.info("AttemptFailed for {}".format(event))

            # Issue AttemptFailed to unblock client.
            #
            kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

        else:
            fabula.LOGGER.info("forwarding event")
            kwargs["message"].event_list.append(new_event)

        return

    def process_TriesToPickUpEvent(self, event, **kwargs):
        """Check what is being picked up, replace event.target_identifier with the identifier of the Entity to be picked up, then let the Plugin handle the Event.
        """

        fabula.LOGGER.debug("called")

        new_event = None

        # TODO: contracts...
        #
        if event.target_identifier in self.room.floor_plan:

            # TODO: This only tries to pick up the very last Entity encountered.
            #
            for entity in self.room.floor_plan[event.target_identifier].entities:

                if entity.entity_type == fabula.ITEM and entity.mobile:

                    fabula.LOGGER.info("trying to pick up '{}' at {}".format(entity.identifier,
                                                                            event.target_identifier))

                    new_event = fabula.TriesToPickUpEvent(event.identifier,
                                                         entity.identifier)

        if new_event is None:

            # Nothing to pick up.
            # Issue AttemptFailed to unblock client.
            #
            fabula.LOGGER.info("AttemptFailed for {}".format(event))
            kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

        else:
            fabula.LOGGER.info("forwarding event")
            kwargs["message"].event_list.append(new_event)

        return

    def process_TriesToDropEvent(self, event, **kwargs):
        """Perform checks and either forward the Event to the Plugin or issue AttemptFailedEvent.

           If the target tile is not in Room.floor_plan, the attempt fails.
           If the tile is not FLOOR, the attempt fails.
           If the item is not in Rack (but in Room), the event is forwarded to the Plugin to decide what to do.
           If the Entity who tries to drop the item from Rack does not own it, the attempt fails.
           If there is another Entity on the tile, it is marked as the target.
           In any other case, the Event is forwarded to the Plugin.
        """

        # TODO: What about Entities in walls?

        fabula.LOGGER.debug("called")

        # Check target
        #
        if event.target_identifier not in self.room.floor_plan:

            fabula.LOGGER.info("AttemptFailed: target {} not in Room.floor_plan".format(event.target_identifier, event.item_identifier))

            kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

            return

        elif self.room.floor_plan[event.target_identifier].tile.tile_type != fabula.FLOOR:

            fabula.LOGGER.info("AttemptFailed: tile at {} not FLOOR".format(event.target_identifier, event.item_identifier))

            kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

            return

        # If event.target_identifier has at least one Entity on it, replace
        # target_identifier with the first Entity's identifier.
        #
        if len(self.room.floor_plan[event.target_identifier].entities):

            target_identifier = self.room.floor_plan[event.target_identifier].entities[0].identifier

            event = fabula.TriesToDropEvent(event.identifier,
                                           event.item_identifier,
                                           target_identifier)

        # Check Rack and owner
        #
        if event.item_identifier not in self.rack.entity_dict.keys():

            if event.item_identifier in self.room.entity_dict.keys():
                fabula.LOGGER.info("'{}' not in rack but in room, forwarding event to plugin".format(event.item_identifier))
                kwargs["message"].event_list.append(event)

            else:
                fabula.LOGGER.info("AttemptFailed: '{}' neither in rack nor in room".format(event.item_identifier))
                kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

        elif self.rack.owner_dict[event.item_identifier] != event.identifier:

            fabula.LOGGER.info("AttemptFailed: '{}' does not own '{}' in Rack".format(event.identifier, event.item_identifier))
            kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

        else:
            fabula.LOGGER.info("looks OK, forwarding to plugin")
            kwargs["message"].event_list.append(event)

        return

    def process_EnterRoomEvent(self, event, **kwargs):
        """Register the client in the room and forward the Event.
           If the room does not exist, it will be created.
        """

        # TODO: Implement handling of multiple rooms.

        state = "new"

        if (self.room is None
            or self.room.identifier != event.room_identifier):

            self.room = fabula.Room(event.room_identifier)

        else:
            state = "existing"

        fabula.LOGGER.info("registering client '{}' in {} room '{}'".format(str(kwargs["connector"]),
                                                                          state,
                                                                          event.room_identifier))

        self.room.active_clients[kwargs["connector"]] = event.client_identifier

        kwargs["message"].event_list.append(event)

        return
