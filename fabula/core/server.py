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
import traceback
import datetime
import collections
import itertools

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

       Server.ipaddress
           A string holding the IP address to listen on. Initially "0.0.0.0".

       Server.room_by_id
           A collections.OrderedDict, mapping room identifiers to Room instances.

       Server.room_by_client
           A dict, mapping client identifiers to Room instances.

       Server.message_by_room_id
           A dict of outgoing Messages, indexed by room identifier.

       Server.message_timestamp
           Timestamp for messages. Initially None.

       Server.exit_requested
           Flag to be changed by signal handler
     """

    def __init__(self,
                 interface_instance,
                 framerate,
                 action_time,
                 ipaddress = "0.0.0.0",
                 threadsafe = True):
        """Initialise the Server.
           If threadsafe is True (default), no signal handlers are installed.
        """

        # Setup base class
        # Engine.__init__() calls EventProcessor.__init__()
        #
        fabula.core.Engine.__init__(self,
                                   interface_instance)

        # Override logfile name
        #
        self.logfile_name = "messages-server-received.log"

        # Timestamp for messages
        #
        self.message_timestamp = None

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

        self.ipaddress = ipaddress

        # The server manages multiple rooms
        #
        self.room_by_id = collections.OrderedDict()
        self.room_by_client = {}

        # Outgoing Messages, indexed by room identifier
        #
        self.message_by_room_id = {}

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
        """Main method of the Server.

           This is a blocking method. It calls all the process methods to
           process events, and then the plugin.

           This method will print usage information and status reports to STDOUT.
        """

        print("============================================================")
        print("Fabula {} Server".format(fabula.VERSION))
        print("------------------------------------------------------------\n")

        # Listen on port 0xfab == 4011 :-)
        #
        connector = (self.ipaddress, 4011)

        fabula.LOGGER.info("attempting to connect server interface to '{}'".format(connector))

        try:
            self.interface.connect(connector)

            print("Listening on IP {}, port {}\n".format(connector[0],
                                                         connector[1]))

        except:
            fabula.LOGGER.warning("Exception in interface.connect() (server interface already connected?), continuing anyway")
            fabula.LOGGER.debug(traceback.format_exc())

        print("Press [Ctrl] + [C] to stop the server.")

        fabula.LOGGER.info("starting main loop")

        # MAIN LOOP
        # TODO: Server.exit_requested is inconsistent with Client.plugin.exit_requested
        #
        while not self.exit_requested:

            self._main_loop()

        # exit has been requested
        #
        print("\nShutting down server.\n")

        fabula.LOGGER.info("exit flag set")

        fabula.LOGGER.info("sending ExitEvent to all connected Clients")

        for message_buffer in self.interface.connections.values():

            message_buffer.send_message(fabula.Message([fabula.ExitEvent("server")]))

        # stop the Interface thread
        #
        fabula.LOGGER.info("shutting down interface")

        self.interface.shutdown()

        fabula.LOGGER.info("shutdown confirmed")

        # TODO: possibly exit cleanly from the plugin here

        print("Shutdown complete. A log file should be at fabula-server.log\n")

        return

    def _main_loop(self):
        """Auxiliary method. Execute the main loop of the server once.
        """

        # Client connections may come and go. So rebuild the list of
        # connections at every run.
        #
        connector_list = list(self.interface.connections.keys())

        self._check_exit(connector_list)

        for connector in connector_list:

            message = self.interface.connections[connector].grab_message()

            if len(message.event_list):

                fabula.LOGGER.debug("'{0}' incoming: {1}".format(connector, message))

                self._write_logfile(message)

                for event in message.event_list:

                    # TODO: most client implementations should be allowed to send a single event per turn only!
                    # Otherwise, a long burst of events might unfairly
                    # block other clients. (hint by Alexander Marbach)

                    # Be sceptical. Only accept typical client events.
                    # TODO: Include fabula.ChangePropertyEvent?
                    #
                    if isinstance(event, (fabula.InitEvent,
                                          fabula.ExitEvent,
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
                    # on an event-by-event rather than on a
                    # message-by-message base to allow for quick and
                    # real-time reaction.

                    self._call_plugin(connector)

                    # process next event in message from this client

            else:
                # len(message.event_list) == 0
                # Call Plugin anyway to catch Plugin initiated Events
                # self.message_for_plugin is already set to an empty Message
                #
                self._call_plugin(connector)

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

        return

    def _check_exit(self, connector_list):
        """Auxiliary method. Check if someone has left who is supposed to be there.
        """

        for room in self.room_by_id.values():

            # Create a list copy, for the same reason as above
            #
            active_list = list(room.active_clients.keys())

            for connector in active_list:

                if not connector in connector_list:

                    client_id = room.active_clients[connector]

                    msg = "client '{}' {} has left without notice, removing"

                    fabula.LOGGER.warning(msg.format(client_id, connector))

                    self.process_ExitEvent(fabula.ExitEvent(client_id),
                                           connector = connector)

                    # Since we do this outside the loop, we have to clean
                    # up to not confuse the next iteration
                    #
                    self.message_for_remote = fabula.Message([])

                    self._add_event_to_room_message(fabula.DeleteEvent(client_id), room)

        return

    def _write_logfile(self, message):
        """Auxiliary method. Log to logfile.
        """

        # Clear file and start Message log timer with first incoming
        # message
        #
        if self.message_timestamp is None:

            fabula.LOGGER.debug("Clearing log file")

            message_log_file = open(self.logfile_name, "wt")
            message_log_file.write("")
            message_log_file.close()

            fabula.LOGGER.debug("Starting message log timer")

            self.message_timestamp = datetime.datetime.today()

        message_log_file = open(self.logfile_name, "at")

        timedifference = datetime.datetime.today() - self.message_timestamp

        # Logging time difference in seconds and message, tab-separated,
        # terminated with double-newline.
        # timedifference as seconds + tenth of a second
        #
        message_log_file.write("{}\t{}\n\n".format(timedifference.seconds + timedifference.microseconds / 1000000.0,
                                                   repr(message)))

        message_log_file.close()

        # Renew timestamp
        #
        self.message_timestamp = datetime.datetime.today()

        return

    def _call_plugin(self, connector):
        """Auxiliary method, to be called from _main_loop(). Call Plugin and process Plugin message.
        """

        # TODO: Check all code relying on connector being the origin of an Event - this might not be the case!!!

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

            if not len(self.room_by_id):

                msg = "The plugin has not established any rooms. Cannot continue."

                fabula.LOGGER.critical(msg)

                raise RuntimeError(msg)

            # Sort Events by Room

            entered_room_id = None

            for event in self.message_for_remote.event_list:

                if isinstance(event, fabula.EnterRoomEvent):

                    entered_room_id = event.room_identifier

                    self._add_event_to_room_message(event)

                elif isinstance(event, fabula.RoomCompleteEvent):

                    if entered_room_id is not None:

                        self._add_event_to_room_message(event, self.room_by_id[entered_room_id])

                        entered_room_id = None

                    else:
                        msg = "No EnterRoomEvent preceding {}".format(event)

                        fabula.LOGGER.error(msg)

                        raise RuntimeError(msg)

                elif isinstance(event, fabula.DeleteEvent):

                    # NOTE: HACK: as the Entity is already removed from all rooms, we have no way of knowing where it was before. So add DeleteEvent to all rooms.
                    #
                    [self._add_event_to_room_message(event, current_room) for current_room in self.room_by_id.values()]

                else:

                    self._add_event_to_room_message(event)

            # Now process each room's message
            #
            for room_identifier, room_message in self.message_by_room_id.items():

                # Find active clients and build a message for each client
                #
                client_message_dict = {}

                for client_identifier in self.room_by_id[room_identifier].active_clients.values():

                    client_message_dict[client_identifier] = fabula.Message([])

                # Sort this room's events into client messages. Not everyone
                # might get the same ones.

                single_client = None

                for event in room_message.event_list:

                    if isinstance(event, fabula.EnterRoomEvent):

                        # Start collecting messages for single client only
                        #
                        single_client = event.client_identifier

                        client_message_dict[single_client].event_list.append(event)

                    elif isinstance(event, fabula.RoomCompleteEvent):

                        client_message_dict[single_client].event_list.append(event)

                        # Stop collecting messages for single client only
                        #
                        single_client = None

                    # TODO: re-check the multiple room entity.id == client_id convention, and possibly make that visible in attribute names
                    #
                    elif (isinstance(event, fabula.SpawnEvent)
                          and single_client is not None
                          and event.entity.identifier == single_client):

                            # This is supposed to be the SpawnEvent for the
                            # new player - send to all
                            #
                            for message in client_message_dict.values():

                                message.event_list.append(event)

                    else:

                        if single_client is None:

                            # That's for all, folks
                            #
                            for message in client_message_dict.values():

                                message.event_list.append(event)

                        else:

                            client_message_dict[single_client].event_list.append(event)

                fabula.LOGGER.debug("client_message_dict == {}".format(client_message_dict))

                # Now. Off with them!
                #
                for connector, client_identifier in self.room_by_id[room_identifier].active_clients.items():

                    message = client_message_dict[client_identifier]

                    if len(message.event_list):

                        fabula.LOGGER.debug("'{}' ({}) outgoing: {}".format(connector,
                                                                            client_identifier,
                                                                            message))

                        try:
                            self.interface.connections[connector].send_message(message)

                        except KeyError:

                            msg = "connection to client '{}' not found, could not send Message"

                            fabula.LOGGER.error(msg.format(connector))

        # Clean up
        #
        self.message_for_remote = fabula.Message([])
        self.message_by_room_id = {}

        return

    def _add_event_to_room_message(self, event, room = None):
        """Add event to the respective Message in Server.message_by_room_id.

           If room is not given, it will be inferred from the event.

           This method will raise a RuntimeError if no fitting room can
           be found. Make sure to call this only for events for which a room
           can be found.
        """

        if room is None:

            fabula.LOGGER.debug("No room given, trying to infer from Event {}".format(event))

            if (isinstance(event, fabula.SpawnEvent)
                or isinstance(event, fabula.ChangeMapElementEvent)):

                # Assuming Event.location == (x, y, "room_identifier")
                #
                room = self.room_by_id[event.location[2]]

            elif isinstance(event, fabula.EnterRoomEvent):

                # Room should be established
                #
                room = self.room_by_id[event.room_identifier]

            elif isinstance(event, fabula.ServerParametersEvent):

                room = self.room_by_client[event.client_identifier]

            elif "identifier" in event.__dict__.keys():

                for current_room in self.room_by_id.values():

                    if event.identifier in current_room.entity_dict.keys():

                        room = current_room

                if room is None:

                    msg = "Identifier '{}' of Event {} not found in any room: {}"

                    msg = msg.format(event.identifier,
                                     event,
                                     [str(room) for room in self.room_by_id.values()])

                    fabula.LOGGER.error(msg)

                    raise RuntimeError(msg)

            else:
                msg = "No Room found that fits Event {}".format(event)

                fabula.LOGGER.error(msg)

                raise RuntimeError(msg)

            fabula.LOGGER.debug("Inferred Room '{}'".format(room.identifier))

        if room.identifier in self.message_by_room_id.keys():

            self.message_by_room_id[room.identifier].event_list.append(event)

        else:
            self.message_by_room_id[room.identifier] = fabula.Message([event])

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

        room = None

        for current_room in self.room_by_id.values():

            if event.identifier in current_room.entity_dict.keys():

                room = current_room

        if not room.entity_dict[event.identifier].mobile:

            fabula.LOGGER.info("'{}' is not mobile".format(event.identifier))

            kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

        elif not room.tile_is_walkable(event.target_identifier):

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

        # A guard clause first.
        #
        if event.identifier in self.room_by_client.keys():

            msg = "Client id '{}' already exists in room_by_client == {}, sending ExitEvent at once and terminating connection"

            fabula.LOGGER.warning(msg.format(event.identifier,
                                             self.room_by_client))

            try:
                self.interface.connections[kwargs["connector"]].send_message(fabula.Message([fabula.ExitEvent(event.identifier)]))

            except KeyError:

                msg = "connection to client '{}' not found, could not send Message"

                fabula.LOGGER.error(msg.format(kwargs["connector"]))

            fabula.LOGGER.debug("removing interface.connections[{}]".format(kwargs["connector"]))

            try:
                del self.interface.connections[kwargs["connector"]]

            except KeyError:

                fabula.LOGGER.warning("connection {} is already gone".format(kwargs["connector"]))

            return

        fabula.LOGGER.info("sending Server parameters")

        self.message_for_remote.event_list.append(fabula.ServerParametersEvent(event.identifier, self.action_time))

        if len(self.room_by_id):

            # TODO: Spawning in first room in room_by_id by default. Is this ok as a convention, or do we need some way to configure that? Or a standard name for the first room to spawn in?

            room = list(self.room_by_id.values())[0]

            fabula.LOGGER.debug("creating and processing EnterRoomEvent for new client")

            fabula.LOGGER.info("Spawning client '{}' in first room '{}' by convention".format(event.identifier, room.identifier))

            enter_room_event = fabula.EnterRoomEvent(event.identifier,
                                                     room.identifier)

            # Process the Event right away, since it is not going through the
            # Plugin. This will also append the Event to self.message_for_remote.
            #
            self.process_EnterRoomEvent(enter_room_event,
                                        connector = kwargs["connector"],
                                        message = self.message_for_remote)

            fabula.LOGGER.info("Sending existing floor_plan, entities and Rack")

            # TODO: It's not very clean to write to self.message_for_remote directly since the procces_() methods are not supposed to do so.
            #
            self.message_for_remote.event_list.extend(self._generate_room_rack_events(room.identifier))

        # If a room has already been sent, the plugin should only spawn a new
        # player entity.
        # The Plugin will add RoomCompleteEvent when processing InitEvent.
        #
        kwargs["message"].event_list.append(event)

        return

    def _generate_room_rack_events(self, room_identifier):
        """Generate and return a series of Events that establish an existing Room and the Rack.

           EnterRoomEvent and RoomCompleteEvent will not be included.
        """

        event_list = []

        room = self.room_by_id[room_identifier]

        for tuple in room.floor_plan:

            tile = room.floor_plan[tuple].tile

            change_map_element_event = fabula.ChangeMapElementEvent(tile, tuple + (room.identifier, ))

            event_list.append(change_map_element_event)

        for identifier in room.entity_locations:

            entity = room.entity_dict[identifier]

            spawn_event = fabula.SpawnEvent(entity,
                                            room.entity_locations[identifier] + (room.identifier, ))

            event_list.append(spawn_event)

            # Set properties of the Entity if there are any
            #
            for property in entity.property_dict.keys():

                change_property_event = fabula.ChangePropertyEvent(entity.identifier,
                                                                   property,
                                                                   entity.property_dict[property])

                event_list.append(change_property_event)

        if len(self.rack.entity_dict):

            for identifier in self.rack.entity_dict:

                # We must spawn at a valid location. Spawning at the first
                # coordinate tuple in the room. Doesn't matter, it will be
                # picked up in an instant anyway.
                #
                spawn_event = fabula.SpawnEvent(self.rack.entity_dict[identifier],
                                                list(room.floor_plan.keys())[0] + (room.identifier, ))

                event_list.append(spawn_event)

                picks_up_event = fabula.PicksUpEvent(self.rack.owner_dict[identifier],
                                                     identifier)

                event_list.append(picks_up_event)

        return event_list

    def process_TriesToLookAtEvent(self, event, **kwargs):
        """Check what is being looked at, forward the Event and issue an according LookedAtEvent.
        """

        # TODO: contracts...

        room = None

        if (event.target_identifier in self.rack.entity_dict.keys()
            and self.rack.owner_dict[event.target_identifier] == event.identifier):

            # Pass to plugin unchanged
            #
            kwargs["message"].event_list.append(event)

        else:

            # Not in Rack - try to infer a Room.
            #
            for current_room in self.room_by_id.values():

                if event.identifier in current_room.entity_dict.keys():

                    room = current_room

            if room is not None and event.target_identifier in room.floor_plan:

                # Pick last Entity
                #
                event.target_identifier = room.floor_plan[event.target_identifier].entities[-1].identifier

                fabula.LOGGER.info("forwarding event(s)")

                kwargs["message"].event_list.append(event)

                kwargs["message"].event_list.append(fabula.LookedAtEvent(event.target_identifier,
                                                                         event.identifier))

            else:
                msg = "AttemptFailed: '{}' not in Rack and not a valid location in any room's floor_plan"

                fabula.LOGGER.info(msg.format(event.target_identifier))

                # Issue AttemptFailed to unblock client.
                #
                kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

        return

    def process_TriesToTalkToEvent(self, event, **kwargs):
        """Check who is being talked to and forward the Event.

           It is not supported to talk to Entites that are currently in the Rack.
        """

        # NOTE: not checking for an attempt to talk to something in Rack.

        room = None

        for current_room in self.room_by_id.values():

            if event.identifier in current_room.entity_dict.keys():

                room = current_room

        if room is not None and event.target_identifier in room.floor_plan:

            if not room.floor_plan[event.target_identifier].entities:

                fabula.LOGGER.info("AttemptFailed: no entity to talk to at location '{}'".format(event.target_identifier))
                fabula.LOGGER.debug("room.entity_locations == {}".format(room.entity_locations))

                kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

            else:
                # Pick last Entity
                #
                event.target_identifier = room.floor_plan[event.target_identifier].entities[-1].identifier

                fabula.LOGGER.info("forwarding event")

                kwargs["message"].event_list.append(event)

        else:
            fabula.LOGGER.info("AttemptFailed: '{}' is not a valid location in floor_plan".format(event.target_identifier))

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

        room = None

        if (event.target_identifier in self.rack.entity_dict.keys()
            and self.rack.owner_dict[event.target_identifier] == event.identifier):

            # Pass to plugin unchanged
            #
            kwargs["message"].event_list.append(event)

        else:

            # Not in Rack - try to infer a Room.
            #
            for current_room in self.room_by_id.values():

                if event.identifier in current_room.entity_dict.keys():

                    room = current_room

            # TODO: contracts...
            #
            if room is not None and event.target_identifier in room.floor_plan:

                for entity in room.floor_plan[event.target_identifier].entities:

                    if entity.entity_type == fabula.ITEM:

                        event.target_identifier = entity.identifier

                    else:
                        fabula.LOGGER.debug("Entity type '{}' can not be manipulated".format(entity.entity_type))

                fabula.LOGGER.info("forwarding event")

                kwargs["message"].event_list.append(event)

            else:
                fabula.LOGGER.info("AttemptFailed for {}".format(event))

                # Issue AttemptFailed to unblock client.
                #
                kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

        return

    def process_TriesToPickUpEvent(self, event, **kwargs):
        """Check what is being picked up, replace event.target_identifier with the identifier of the Entity to be picked up, then let the Plugin handle the Event.
        """

        fabula.LOGGER.debug("called")

        new_event = None

        room = None

        for current_room in self.room_by_id.values():

            if event.identifier in current_room.entity_dict.keys():

                room = current_room

        # TODO: contracts...
        #
        if room is not None and event.target_identifier in room.floor_plan:

            # TODO: This only tries to pick up the very last Entity encountered.
            #
            for entity in room.floor_plan[event.target_identifier].entities:

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
           If the target is in Rack and the Entity does not own it, the attempt fails.
           If the target is in Rack and the Entity owns it, the event is forwarded to the Plugin to decide what to do.
           In any other case, the Event is forwarded to the Plugin.
        """

        # TODO: What about Entities in walls?

        fabula.LOGGER.debug("called")

        room = None

        if event.target_identifier in self.rack.entity_dict.keys():

            if self.rack.owner_dict[event.target_identifier] == event.identifier:

                # Pass to plugin unchanged
                #
                kwargs["message"].event_list.append(event)

                return

            else:
                fabula.LOGGER.warning("AttemptFailed: '{}' does not own '{}' in Rack".format(event.identifier, event.target_identifier))

                kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

                return

        # Not in Rack - try to infer a Room.
        #
        for current_room in self.room_by_id.values():

            if event.identifier in current_room.entity_dict.keys():

                room = current_room

        if room is None:

            fabula.LOGGER.warning("AttemptFailed: no room containing '{}'".format(event.identifier))

            kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

            return

        # Check target
        #
        elif event.target_identifier[:2] not in room.floor_plan:

            fabula.LOGGER.info("AttemptFailed: target '{}' is not a valid location in floor_plan".format(event.target_identifier[:2], event.item_identifier))

            kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

            return

        elif room.floor_plan[event.target_identifier[:2]].tile.tile_type != fabula.FLOOR:

            fabula.LOGGER.info("AttemptFailed: tile at '{}' not FLOOR".format(event.target_identifier[:2], event.item_identifier))

            kwargs["message"].event_list.append(fabula.AttemptFailedEvent(event.identifier))

            return

        # If event.target_identifier[:2] has at least one Entity on it, replace
        # target_identifier[:2] with the first Entity's identifier.
        #
        if len(room.floor_plan[event.target_identifier[:2]].entities):

            target_identifier = room.floor_plan[event.target_identifier[:2]].entities[0].identifier

            event = fabula.TriesToDropEvent(event.identifier,
                                            event.item_identifier,
                                            target_identifier)

        # Check Rack and owner
        #
        if event.item_identifier not in self.rack.entity_dict.keys():

            if event.item_identifier in room.entity_dict.keys():
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
        """Remove the client from its old room, register the client in the room and forward the Event.
           If the room does not exist, it will be created.
        """

        connector = None

        if event.client_identifier in self.room_by_client.keys():

            fabula.LOGGER.info("removing client '{}' from room '{}'".format(event.client_identifier,
                                                                            self.room_by_client[event.client_identifier]))

            # TODO: remove player Entity here?
            #
            msg = "NOT removing possible player Entity for '{}' from room '{}'"

            fabula.LOGGER.warning(msg.format(event.client_identifier,
                                             self.room_by_client[event.client_identifier]))

            # NOTE: The Event may result from a player-initiated action, or from a queued Event. That means we can *not* rely on kwargs["connector"] being the actual trigger of the Event!

            # Reverse dict trick from http://stackoverflow.com/a/14131104/1132250
            #
            connector = {value: key for key, value in self.room_by_client[event.client_identifier].active_clients.items()}[event.client_identifier]

            fabula.LOGGER.debug("Using existing connector '{}' for client '{}'".format(connector,
                                                                                       event.client_identifier))

            # TODO: Manage active clients rather in Room methods than here, from the outside? See also process_ExitEvent().
            #
            del self.room_by_client[event.client_identifier].active_clients[connector]

            del self.room_by_client[event.client_identifier]

        else:
            fabula.LOGGER.debug("Client '{}' is not yet in any room".format(event.client_identifier))

            connector = kwargs["connector"]

            fabula.LOGGER.info("Assuming connector '{}' for client '{}'".format(connector,
                                                                                event.client_identifier))

        state = "new"

        if event.room_identifier not in self.room_by_id.keys():

            self.room_by_id[event.room_identifier] = fabula.Room(event.room_identifier)

        else:
            state = "existing"

        fabula.LOGGER.info("registering client '{}' in {} room '{}'".format(connector,
                                                                            state,
                                                                            event.room_identifier))

        self.room_by_id[event.room_identifier].active_clients[connector] = event.client_identifier

        self.room_by_client[event.client_identifier] = self.room_by_id[event.room_identifier]

        kwargs["message"].event_list.append(event)

        return

    def process_MovesToEvent(self, event, **kwargs):
        """Let the according room process the event and pass it on.
        """

        room = None

        for current_room in self.room_by_id.values():

            if event.identifier in current_room.entity_dict.keys():

                room = current_room

        fabula.LOGGER.debug("%s location before: %s "
                          % (event.identifier,
                             room.entity_locations[event.identifier]))

        room.process_MovesToEvent(event)

        fabula.LOGGER.info("%s location after: %s "
                          % (event.identifier,
                             room.entity_locations[event.identifier]))

        kwargs["message"].event_list.append(event)

        return

    def process_PicksUpEvent(self, event, **kwargs):
        """Save the Entity to be picked up in Engine.rack, delete it from respective room and pass the PicksUpEvent on.
        """

        fabula.LOGGER.debug("called")

        room = None

        for current_room in self.room_by_id.values():

            if event.item_identifier in current_room.entity_dict.keys():

                room = current_room

        # Save the Entity to be picked up in Engine.rack
        #
        picked_entity = room.entity_dict[event.item_identifier]

        self.rack.store(picked_entity, event.identifier)

        # Delete it from room
        #
        # TODO: Why not pass the PicksUpEvent to the room and let it handle an according removal?
        #
        delete_event = fabula.DeleteEvent(event.item_identifier)

        room.process_DeleteEvent(delete_event)

        # and pass the PicksUpEvent on
        #
        kwargs["message"].event_list.append(event)

        return

    def process_DropsEvent(self, event, **kwargs):
        """Respawn the Entity to be dropped in the respective room, delete it from Engine.rack and pass the PicksUpEvent on.
        """

        fabula.LOGGER.debug("called")

        room = None

        for current_room in self.room_by_id.values():

            if event.identifier in current_room.entity_dict.keys():

                room = current_room

        # Respawn the Entity to be dropped in room
        # Delete it from Engine.rack
        #
        # TODO: Fails when Entity not in rack. Contracts.
        #
        fabula.LOGGER.info("removing '{}' from Rack and respawning in Room".format(event.item_identifier))

        dropped_entity = self.rack.retrieve(event.item_identifier)

        spawn_event = fabula.SpawnEvent(dropped_entity, event.location)

        room.process_SpawnEvent(spawn_event)

        # and pass the DropsEvent on
        #
        kwargs["message"].event_list.append(event)

        return

    def process_ChangePropertyEvent(self, event, **kwargs):
        """Let the Entity handle the Event. Then add the event to the message.
        """

        msg = "forwarding property change '{}'->'{}' to Entity '{}' in current room"

        fabula.LOGGER.debug(msg.format(event.property_key,
                                       event.property_value,
                                       event.identifier))

        room = None

        for current_room in self.room_by_id.values():

            if event.identifier in current_room.entity_dict.keys():

                room = current_room

        if room:

            room.entity_dict[event.identifier].process_ChangePropertyEvent(event)

        else:
            fabula.LOGGER.warning("received ChangePropertyEvent before Room was established")

        kwargs["message"].event_list.append(event)

        return

    def process_SpawnEvent(self, event, **kwargs):
        """Let the first room process the event and pass it on.

           This method assumes that event.location is (x, y, "room_identifier").
        """

        fabula.LOGGER.info("spawning entity '{}', type {}, location {}".format(event.entity.identifier,
                                                                               event.entity.entity_type,
                                                                               event.location))

        if len(event.location) == 3:

            self.room_by_id[event.location[2]].process_SpawnEvent(event)

        else:
            # Fall back to first room.
            #
            # TODO: remove this default behaviour?
            #
            # Since Server.room_by_id is an ordered dict, this will always be
            # the first room created.
            #
            list(self.room_by_id.values())[0].process_SpawnEvent(event)

        kwargs["message"].event_list.append(event)

        return

    def process_DeleteEvent(self, event, **kwargs):
        """Delete the Entity from the respective room and pass the DeleteEvent on.
        """

        fabula.LOGGER.debug("called")

        room = None

        for current_room in self.room_by_id.values():

            if event.identifier in current_room.entity_dict.keys():

                room = current_room

        if room is None:

            fabula.LOGGER.error("Cannot delete Entity '{}', no room found to delete from".format(event.identifier))

        else:

            # Delete it from room
            #
            room.process_DeleteEvent(event)

        # Pass the Event on
        #
        kwargs["message"].event_list.append(event)

        return

    def process_ChangeMapElementEvent(self, event, **kwargs):
        """Let the Room instance process the Event and add it to message.

           This method assumes that event.location is (x, y, "room_identifier").
        """

        fabula.LOGGER.debug("called")

        self.room_by_id[event.location[2]].process_ChangeMapElementEvent(event)

        kwargs["message"].event_list.append(event)

        return

    def process_ExitEvent(self, event, **kwargs):
        """Handle ExitEvent.
           Items that the player has picked up will be kept in self.rack.
        """

        fabula.LOGGER.info("client '{}' exiting".format(event.identifier))

        fabula.LOGGER.debug("removing interface.connections[{}]".format(kwargs["connector"]))

        try:
            del self.interface.connections[kwargs["connector"]]

        except KeyError:

            fabula.LOGGER.warning("connection {} is already gone".format(kwargs["connector"]))

        # No room, nothing to delete.
        #
        if event.identifier in self.room_by_client.keys():

            fabula.LOGGER.debug("removing room.active_clients[{}]".format(kwargs["connector"]))

            # TODO: Manage active clients rather in Room methods than here, from the outside?
            #
            del self.room_by_client[event.identifier].active_clients[kwargs["connector"]]

            del self.room_by_client[event.identifier]

            # Delete player Entity
            # Process the Event right away, since it is not going through the
            # Plugin. This will also append the Event to self.message_for_remote.
            #
            self.process_DeleteEvent(fabula.DeleteEvent(event.identifier),
                                     connector = kwargs["connector"],
                                     message = self.message_for_remote)

        return
