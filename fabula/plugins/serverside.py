"""Server-Side Plugins for Fabula

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

# work started on 27. Oct 2010

import fabula.plugins.pygameui
import fabula.assets
import os
import math
import pickle

def load_room_from_file(filename):
    """This function reads a Fabula room from the file and returns a list of corresponding Events.
       Returns None upon failure.

       The file must consist of lines of tab-separated elements:

       (x, y)    tile_type    tile_asset_desc    entity_type,identifier,entity_asset_desc
    """

    try:
        roomfile = open(filename, "rt")

    except IOError:

        return None

    event_list = [fabula.EnterRoomEvent(filename.split(".floorplan")[0])]

    for line in roomfile:

        # Remove whitespace. This also makes sure that the splitted line
        # will not end in a tab.
        #
        line = line.strip()

        # TODO: Check for tab-separated string
        # TODO: And more checks in general. fabula.FLOOR, asset_desc etc.
        #
        splitted_line = line.split("\t")

        coordiantes_string = splitted_line.pop(0)
        type = splitted_line.pop(0)
        asset_desc = splitted_line.pop(0)

        coordinates = eval(coordiantes_string)

        # Match only "(x, y)" coordinates
        #
        if fabula.str_is_tuple(coordiantes_string):

            tile = fabula.Tile(type, asset_desc)

            event = fabula.ChangeMapElementEvent(tile, coordinates)

            event_list.append(event)

        else:
            # TODO: warn here
            pass

        if len(splitted_line):
            # There is still something there. This should be Entities.

            for comma_sep_entity in splitted_line:

                entity_type, identifier, asset_desc = comma_sep_entity.split(",")

                entity = fabula.Entity(entity_type, identifier, asset_desc)

                event_list.append(fabula.SpawnEvent(entity, coordinates))

    event_list.append(fabula.RoomCompleteEvent())

    roomfile.close()

    return event_list

class DefaultGame(fabula.plugins.Plugin):
    """This is an off-the-shelf server plugin, running a default Fabula game.

       Additional attributes:

       DefaultGame.tries_to_move_dict
           Dict mapping Entity identifiers to target positions.

       DefaultGame.path_dict
           Dict mapping Entity identifiers to a list of coordinates walked so far.

       DefaultGame.condition_response_dict
           A dict mapping string representations of incoming Events to response
           Events.
    """

    def __init__(self, host):
        """Initialise.
        """
        # Call base class
        #
        fabula.plugins.Plugin.__init__(self, host)

        self.tries_to_move_dict = {}
        self.path_dict = {}
        self.condition_response_dict = {}

        # Load default logic.
        #
        self.logger.debug("attempting to load default game logic")
        self.load_condition_response_dict("default.logic")

        return

    def process_message(self, message):
        """DefaultGame main method.

           It calls the respective functions for the Events in message,
           processes pending moves from DefaultGame.tries_to_move_dict
           and returns DefaultGame.message_for_host.
        """

        # Copied from Plugin.process_message. We can not call the parent's
        # method here since we need to add Events inbetween.

        # Clear message for host
        #
        self.message_for_host = fabula.Message([])

        if message.event_list:

            self.logger.debug("processing message {}".format(message.event_list))

            for event in message.event_list:

                if event.__class__ in (fabula.InitEvent,
                                       fabula.TriesToMoveEvent,
                                       fabula.TriesToPickUpEvent,
                                       fabula.TriesToDropEvent,
                                       fabula.AttemptFailedEvent):

                    # These are handled by the according methods.
                    # process_TriesToDropEvent() will call respond() if appropriate.
                    # Use event_dict from EventProcessor base class.
                    #
                    self.event_dict[event.__class__](event)

                elif event.__class__ in (fabula.TriesToLookAtEvent,
                                         fabula.TriesToManipulateEvent,
                                         fabula.TriesToTalkToEvent):

                    # These are handled by respond()
                    #
                    self.respond(event)

                elif isinstance(event, fabula.PassiveEvent):

                    self.logger.debug("returning PassiveEvent instance to host")
                    self.message_for_host.event_list.append(event)

                else:
                    self.logger.critical("don't know how to process '{}'".format(event))
                    raise Exception("don't know how to process '{}'".format(event))

        # Process pending moves.
        # Create a new list to be able to change the dict during iteration.
        #
        for identifier in list(self.tries_to_move_dict.keys()):

            target_identifier = self.tries_to_move_dict[identifier]

            location = self.move_towards(identifier,
                                        target_identifier,
                                        self.path_dict[identifier])

            if location is None:

                self.logger.warning("no possible move for '{}', removing from tries_to_move_dict".format(identifier))

                del self.tries_to_move_dict[identifier]
                del self.path_dict[identifier]

                self.logger.warning("AttemptFailed for '{}'".format(identifier))
                self.message_for_host.event_list.append(fabula.AttemptFailedEvent(identifier))

            else:
                self.logger.debug("movement pending for '{}', last positions {}, best move towards {} is {}".format(identifier, self.path_dict[identifier], target_identifier, location))

                # Save current position before movement as last position
                #
                self.path_dict[identifier].append(self.host.room.entity_locations[identifier])

                self.message_for_host.event_list.append(fabula.MovesToEvent(identifier, location))

                if location == target_identifier:

                    self.logger.debug("target reached, removing from tries_to_move_dict")

                    del self.tries_to_move_dict[identifier]
                    del self.path_dict[identifier]

        return self.message_for_host

    def respond(self, event):
        """Add an Event from condition_response_dict corresponding to the Event given to message_for_host.
           If the Event is not found, return AttemptFailedEvent.
        """

        event_str = str(event)

        if event_str in self.condition_response_dict:

            self.logger.debug("returning corresponding event")
            self.message_for_host.event_list.append(self.condition_response_dict[event_str])

        else:
            self.logger.debug("event '{}' not found in condition_response_dict, returning AttemptFailedEvent to host".format(event_str))
            self.message_for_host.event_list.append(fabula.AttemptFailedEvent(event.identifier))

        return

    def process_InitEvent(self, event):
        """If there is no host.room yet, load default.floorplan and send it.
        """

        self.logger.debug("called")

        if self.host.room is not None:

            self.logger.debug("room already loaded, current room: {}".format(self.host.room.identifier))

        else:
            self.logger.debug("no room loaded yet, attempting to load 'default.floorplan'")

            event_list = load_room_from_file("default.floorplan")

            if event_list is None:

                self.logger.error("error opening file 'default.floorplan'")

            else:
                self.message_for_host.event_list = self.message_for_host.event_list + event_list

        return

    def process_TriesToMoveEvent(self, event):
        """Queue the target and make the Entity move one step at a time.
        """

        self.logger.debug("saving '{} : {}' in tries_to_move_dict".format(event.identifier,
                                                                          event.target_identifier))

        self.tries_to_move_dict[event.identifier] = event.target_identifier
        self.path_dict[event.identifier] = []

        return

    def process_TriesToPickUpEvent(self, event):
        """Return a PicksUpEvent to the Server.
        """

        self.logger.debug("returning PicksUpEvent")

        # The Server has performed basic sanity checks.
        # In addition, we restrict picking up to items right next to the player.
        # TODO: duplicate from PygameUserInterface.make_items_draggable()
        #
        player_location = self.host.room.entity_locations[event.identifier]

        surrounding_positions = [(player_location[0] - 1, player_location[1]),
                                 (player_location[0], player_location[1] - 1),
                                 (player_location[0] + 1, player_location[1]),
                                 (player_location[0], player_location[1] + 1)]

        if self.host.room.entity_locations[event.target_identifier] in surrounding_positions:

            self.message_for_host.event_list.append(fabula.PicksUpEvent(event.identifier,
                                                                       event.target_identifier))

        else:
            self.logger.debug("AttemptFailed: '{}' not next to player".format(event.target_identifier))

            self.message_for_host.event_list.append(fabula.AttemptFailedEvent(event.identifier))

        return

    def process_TriesToDropEvent(self, event):
        """Return a DropsEvent to the Server.
        """

        # Restrict drops to tiles right next to the player.
        # TODO: copied from process_TriesToPickUpEvent
        #
        player_location = self.host.room.entity_locations[event.identifier]

        surrounding_positions = [(player_location[0] - 1, player_location[1]),
                                 (player_location[0], player_location[1] - 1),
                                 (player_location[0] + 1, player_location[1]),
                                 (player_location[0], player_location[1] + 1)]

        # Server.process_TriesToDropEvent() has already done some checks,
        # so we can be sure that target_identifier is either a valid
        # coordinate tuple or an instance of fabula.Entity.
        #

        if event.target_identifier in self.host.room.entity_dict.keys():

            self.logger.debug("target '{}' is an entity identifier".format(event.target_identifier))

            if self.host.room.entity_locations[event.target_identifier] not in surrounding_positions:

                self.logger.debug("AttemptFailed: drop of '{}' on '{}' at {} not next to player: {}".format(event.item_identifier, event.target_identifier, self.host.room.entity_locations[event.target_identifier], surrounding_positions))
                self.message_for_host.event_list.append(fabula.AttemptFailedEvent(event.identifier))

            else:
                self.logger.debug("'{}' dropped on Entity '{}', forwarding to respond()".format(event.item_identifier, event.target_identifier))
                self.respond(event)

        else:
            self.logger.debug("target '{}' is not an entity identifier".format(event.target_identifier))

            if event.target_identifier not in surrounding_positions:

                self.logger.debug("AttemptFailed: drop of '{}' on {} not next to player: {}".format(event.item_identifier, event.target_identifier, surrounding_positions))
                self.message_for_host.event_list.append(fabula.AttemptFailedEvent(event.identifier))

            else:
                # Still, the Entity to be dropped may originate either from Room or from
                # Rack.
                #
                if event.item_identifier not in self.host.rack.entity_dict.keys():
                    self.logger.debug("item still in Room, returning PicksUpEvent")
                    self.message_for_host.event_list.append(fabula.PicksUpEvent(event.identifier,
                                                                               event.item_identifier))

                self.logger.debug("returning DropsEvent")
                self.message_for_host.event_list.append(fabula.DropsEvent(event.identifier,
                                                                         event.item_identifier,
                                                                         event.target_identifier))

        return

    def process_AttemptFailedEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def move_towards(self, identifier, target_identifier, forbidden_moves):
        """Return the coordinates of the next move of Entity 'identifier' towards target_identifier in the current room.
           forbidden_moves is a list of targets that should be considered as not walkable.
        """

        location = self.host.room.entity_locations[identifier]

        possible_moves = []

        for vector in ((-1, 0), (1, 0), (0, -1), (0, 1)):

            possible_move = (location[0] + vector[0], location[1] + vector[1])

            if (self.host.tile_is_walkable(possible_move)
                and possible_move not in forbidden_moves):

                possible_moves.append(possible_move)

        if len(possible_moves) == 0:

            return None

        elif len(possible_moves) == 1:

            return possible_moves[0]

        else:
            # self.logger.debug("possible_moves == {}".format(possible_moves))

            # Taking first as reference
            #
            best_move = possible_moves.pop(0)

            distance_vector = fabula.difference_2d(best_move, target_identifier)

            shortest_distance = math.sqrt(distance_vector[0] * distance_vector[0]
                                          + distance_vector[1] * distance_vector[1])

            # self.logger.debug("move {} has distance {}".format(best_move, shortest_distance))

            # Examine remaining
            #
            for move in possible_moves:

                distance_vector = fabula.difference_2d(move, target_identifier)

                distance = math.sqrt(distance_vector[0] * distance_vector[0]
                                     + distance_vector[1] * distance_vector[1])

                # self.logger.debug("move {} has distance {}".format(move, distance))

                if distance < shortest_distance:
                    shortest_distance = distance
                    best_move = move

            # self.logger.debug("choosing move {} with distance {}".format(best_move, shortest_distance))

            return best_move

    def load_condition_response_dict(self, filename):
        """Load response logic from the file given.
        """

        self.logger.debug("attempting to read from file '{}'".format(filename))

        if filename:

            try:
                file = open(filename, "rb")

                # TODO: Check, check, check
                #
                self.condition_response_dict = pickle.loads(file.read())

                file.close()

            except IOError:
                self.logger.error("could not read from file '{}', game logic not updated".format(filename))

        else:
            self.logger.error("no filename given")

        return

class Editor(DefaultGame):
    """This is the server-side Plugin for a Fabula map editor.

       Additional attributes:

       Editor.current_room
           Name of the current room.

       Editor.pygame_editor
           A PygameEditor where the editing is done.
    """

    # TODO: replace hardwired "player" with client id
    # TODO: PygameEditor and serverside.Editor should each care for their own data structures. So separate methods where applicable.

    def __init__(self, host):
        """Initialise.
        """
        # Call base class
        #
        DefaultGame.__init__(self, host)

        self.logger.debug("called")

        # TODO: When handling of multiple rooms is implemented, this should go into the base class.
        # TODO: Or is that one obsolete, since the name can be guessed from host.room.identifier?
        #
        self.current_room = ''

        # Impersonate a decent host.
        # self.room will point to self.host.room later, but chances are there
        # is no host yet.
        #
        self.room = self.host.room
        self.rack = self.host.rack
        self.player_id = "player"

        # Create a PygameEditor where the editing is done
        # TODO: hardcoded framerate
        #
        self.pygame_editor = fabula.plugins.pygameui.PygameEditor(fabula.assets.Assets(self.logger),
                                                                 60,
                                                                 self)

        self.logger.debug("complete")

    def process_message(self, message):
        """Editor main method.
           It calls the base class method, but before returning to the host
           it calls the local PygameUserInterface.
        """

        # Upon first call we have a host and thus a decent room and rack
        # TODO: of course it is a waste to set that on every call
        #
        self.room = self.host.room
        self.rack = self.host.rack

        self.message_for_host = DefaultGame.process_message(self, message)

        # By obscure means, retrieve Server outgoing Events from Server's MessageBuffer
        # TODO: should this be done in Interface.handle_messages?
        #
        message = fabula.Message([])

        if list(self.host.interface.connections.values())[0].messages_for_remote:

            message = list(self.host.interface.connections.values())[0].messages_for_remote.popleft()

        self.pygame_editor.process_message(message)

        # By similar obscure means, hand UserInterface Events over to the Server's MessageBuffer
        # TODO: should this be done in Interface.handle_messages?
        #
        list(self.host.interface.connections.values())[0].messages_for_local.append(self.pygame_editor.message_for_host)

        # Check PygameEditor exit request
        # TODO: Server does not check for Server.plugin.exit_requested
        #
        if self.pygame_editor.exit_requested:
            self.host.exit_requested = True

        # Note: self.pygame_editor may have appended new Events
        #
        return self.message_for_host

    def process_InitEvent(self, event):
        """Send a bare room, to be populated by the user.
        """

        # TODO: even InitEvent should call respond()

        self.logger.debug("called")

        if self.host.room is None:

            self.logger.debug("no room sent yet, sending initial room")

            self.message_for_host.event_list.append(fabula.EnterRoomEvent("edit_this"))

            tile = fabula.Tile(fabula.FLOOR, "100x100-gray.png")

            for x in range(8):
                for y in range(5):
                    event = fabula.ChangeMapElementEvent(tile, (x, y))
                    self.message_for_host.event_list.append(event)

            entity = fabula.Entity(fabula.PLAYER, "player", "player.png")

            self.message_for_host.event_list.append(fabula.SpawnEvent(entity,
                                                                     (0, 0)))

            self.message_for_host.event_list.append(fabula.RoomCompleteEvent())

    def send_room_events(self, option):
        """OptionList callback to read a Room from a file and send it to the Server.
        """

        self.logger.debug("called")

        event_list = load_room_from_file(option.text + ".floorplan")

        if event_list is None:

            self.logger.error("error opening file '{}.floorplan'".format(option.text + ".floorplan"))

        else:

            self.message_for_host.event_list.extend(event_list)

        self.logger.debug("complete")

        return

    def respond(self, event):
        """Add an Event from condition_response_dict corresponding to the Event given to message_for_host.
           If the Event is not found, make the user select a response.
        """

        event_str = str(event)

        if event_str in self.condition_response_dict:

            self.logger.debug("returning corresponding event")
            self.message_for_host.event_list.append(self.condition_response_dict[event_str])

        else:
            self.logger.debug("event '{}' not found in condition_response_dict, making user select a response".format(event_str))
            self.pygame_editor.select_event(event)

        return

    def add_response(self, trigger_event, response_event):
        """Set Editor.condition_response_dict[str(trigger_event)] = response_event.
        """

        # This could also be done in self.pygame_editor.event_edit_done(), but
        # it's cleaner to do here.
        #
        self.logger.debug("condition_response_dict[{}] = {}".format(trigger_event, response_event))

        self.condition_response_dict[str(trigger_event)] = response_event

        return

    def save_condition_response_dict(self, filename):
        """Save the response logic to the file given.
        """

        self.logger.debug("attempting to save to file '{}'".format(filename))

        if filename:

            file = open(filename, "wb")

            file.write(pickle.dumps(self.condition_response_dict, 0))

            file.close()

            # TODO: there should be something like pygame_ui.feedback or pygame_ui.okbox to display a message from here
            #
            self.pygame_editor.window.room.sub(fabula.plugins.pygameui.clickndrag.gui.OkBox("Logic saved to file '{}'.".format(filename)))

        else:
            self.logger.error("no filename given")

        return

    def clear_condition_response_dict(self):
        """Clear the response logic.
        """

        self.logger.debug("clearing condition_response_dict")

        self.condition_response_dict = {}

        # TODO: there should be something like pygame_ui.feedback or pygame_ui.okbox to display a message from here
        #
        self.pygame_editor.window.room.sub(fabula.plugins.pygameui.clickndrag.gui.OkBox("Logic cleared."))

        return

    # HERE BE DRAGONS #####################################################

#    def process_TriesToDropEvent(self, event):
#        """Return a DropsEvent to the Server.
#        """
#
#        # Restrict drops to tiles right next to the player.
#        # TODO: copied from process_TriesToPickUpEvent
#        #
#        player_location = self.host.room.entity_locations[event.identifier]
#
#        surrounding_positions = [(player_location[0] - 1, player_location[1]),
#                                 (player_location[0], player_location[1] - 1),
#                                 (player_location[0] + 1, player_location[1]),
#                                 (player_location[0], player_location[1] + 1)]
#
#        # Server.process_TriesToDropEvent() has already done some checks,
#        # so we can be sure that target_identifier is either a valid
#        # coordinate tuple or an instance of fabula.Entity.
#        #
#
#        if event.target_identifier in self.host.room.entity_dict.keys():
#
#            self.logger.debug("target '{}' is an entity identifier".format(event.target_identifier))
#
#            if self.host.room.entity_locations[event.target_identifier] not in surrounding_positions:
#
#                self.logger.debug("AttemptFailed: drop of '{}' on '{}' at {} not next to player: {}".format(event.item_identifier, event.target_identifier, self.host.room.entity_locations[event.target_identifier], surrounding_positions))
#                self.message_for_host.event_list.append(fabula.AttemptFailedEvent(event.identifier))
#
#            else:
#                self.logger.debug("AttemptFailed: '{}' has been dropped on Entity '{}'. Not supported.".format(event.item_identifier, event.target_identifier))
#                self.message_for_host.event_list.append(fabula.AttemptFailedEvent(event.identifier))
#
#        else:
#            self.logger.debug("target '{}' is not an entity identifier".format(event.target_identifier))
#
#            if event.target_identifier not in surrounding_positions:
#
#                self.logger.debug("AttemptFailed: drop of '{}' on {} not next to player: {}".format(event.item_identifier, event.target_identifier, surrounding_positions))
#                self.message_for_host.event_list.append(fabula.AttemptFailedEvent(event.identifier))
#
#            else:
#                # Still, the Entity to be dropped may originate either from Room or from
#                # Rack.
#                #
#                if event.item_identifier not in self.host.rack.entity_dict.keys():
#                    self.logger.debug("item still in Room, returning PicksUpEvent")
#                    self.message_for_host.event_list.append(fabula.PicksUpEvent(event.identifier,
#                                                                               event.item_identifier))
#
#                self.logger.debug("returning DropsEvent")
#                self.message_for_host.event_list.append(fabula.DropsEvent(event.identifier,
#                                                                         event.item_identifier,
#                                                                         event.target_identifier))
#
#        return
