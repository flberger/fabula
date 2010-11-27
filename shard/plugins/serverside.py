"""Server-Side Plugins for Shard

   (c) Florian Berger <fberger@florian-berger.de>
"""

# work started on 27. Oct 2010

import shard.plugins
import re
import os
import math

def load_room_from_file(filename):
    """This function reads a Shard room from the file and returns a list of corresponding Events.
       Returns None upon failure.

       The file must consist of lines of tab-separated elements:

       (x, y)    tile_type    tile_asset_desc    entity_type,identifier,entity_asset_desc
    """

    try:
        roomfile = open(filename, "rt")

    except IOError:

        return None

    event_list = [shard.EnterRoomEvent(filename.split(".floorplan")[0])]

    for line in roomfile:

        # Remove whitespace. This also makes sure that the splitted line
        # will not end in a tab.
        #
        line = line.strip()

        # TODO: Check for tab-separated string
        # TODO: And more checks in general. shard.FLOOR, asset_desc etc.
        #
        splitted_line = line.split("\t")

        coordiantes_string = splitted_line.pop(0)
        type = splitted_line.pop(0)
        asset_desc = splitted_line.pop(0)

        coordinates = eval(coordiantes_string)

        # Match only "(x, y)" coordinates
        #
        if re.match("^\([0-9]+\s*,\s*[0-9]+\)$", coordiantes_string):

            tile = shard.Tile(type, asset_desc)

            event = shard.ChangeMapElementEvent(tile, coordinates)

            event_list.append(event)

        else:
            # TODO: warn here
            pass

        if len(splitted_line):
            # There is still something there. This should be Entities.

            for comma_sep_entity in splitted_line:

                entity_type, identifier, asset_desc = comma_sep_entity.split(",")

                entity = shard.Entity(entity_type, identifier, asset_desc)

                event_list.append(shard.SpawnEvent(entity, coordinates))

    event_list.append(shard.RoomCompleteEvent())

    roomfile.close()

    return event_list

class DefaultGame(shard.plugins.Plugin):
    """This is an off-the-shelf server plugin, running a default Shard game.

       Additional attributes:

       DefaultGame.tries_to_move_dict
           Dict mapping Entity identifiers to coordinate tuples to be moved
           towards.

       DefaultGame.last_position_dict
           Dict mapping Entity identifiers to their last position before a
           movement.
    """

    def __init__(self, logger):
        """Initialise.
        """
        # Call base class
        #
        shard.plugins.Plugin.__init__(self, logger)

        self.tries_to_move_dict = {}
        self.last_position_dict = {}

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
        self.message_for_host = shard.Message([])

        if message.event_list:

            self.logger.debug("processing message {}".format(message.event_list))

            for event in message.event_list:

                # event_dict from EventProcessor base class
                #
                self.event_dict[event.__class__](event)

        # Process pending moves.
        # Create a new list to be able to change the dict during iteration.
        #
        for identifier in list(self.tries_to_move_dict.keys()):

            target_identifier = self.tries_to_move_dict[identifier]

            location = self.move_towards(identifier, target_identifier)

            if location is None:

                self.logger.warning("no possible move for '{}', removing from tries_to_move_dict".format(event.identifier))

                del self.tries_to_move_dict[identifier]
                del self.last_position_dict[identifier]

            else:

                if location == self.last_position_dict[identifier]:

                    self.logger.warning("'{}' would move back to last position, removing from tries_to_move_dict".format(identifier))

                    del self.tries_to_move_dict[identifier]
                    del self.last_position_dict[identifier]

                else:
                    self.logger.debug("movement pending for '{}', last position {}, best move towards {} is {}".format(identifier, self.last_position_dict[identifier], target_identifier, location))
                    
                    # Save current position before movement as last position
                    #
                    self.last_position_dict[identifier] = self.host.room.entity_locations[identifier]

                    self.message_for_host.event_list.append(shard.MovesToEvent(identifier, location))

                    if location == target_identifier:

                        self.logger.debug("target reached, removing from tries_to_move_dict")

                        del self.tries_to_move_dict[identifier]
                        del self.last_position_dict[identifier]

        return self.message_for_host

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
        self.last_position_dict[event.identifier] = self.host.room.entity_locations[event.identifier]

        return

    def process_TriesToLookAtEvent(self, event):
        """Return AttemptFailedEvent to the host.
        """

        self.logger.debug("returning AttemptFailedEvent to host")
        self.message_for_host.event_list.append(shard.AttemptFailedEvent(event.identifier))
        return

    def process_TriesToPickUpEvent(self, event):
        """Return a PicksUpEvent to the Server.
        """

        self.logger.debug("returning PicksUpEvent")

        # The Server has already performed sanity checks.
        #
        self.message_for_host.event_list.append(shard.PicksUpEvent(event.identifier,
                                                                   event.target_identifier))
        return

    def process_TriesToDropEvent(self, event):
        """Return a DropsEvent to the Server.
        """

        # Server.process_TriesToDropEvent() has already done some checks,
        # so we can be sure that target_identifier is either a valid
        # coordinate tuple or an instance of shard.Entity.
        # Still, the Entity to be dropped may originate either from Room or from
        # Rack.
        #
        if isinstance(event.target_identifier, shard.Entity):
            self.logger.debug("'{}' has been dropped on Entity '{}'. Not supported.".format(event.item_identifier, event.target_identifier))

        else:
            if event.item_identifier not in self.host.rack.entity_dict.keys():
                self.logger.debug("item still in Room, returning PicksUpEvent")
                self.message_for_host.event_list.append(shard.PicksUpEvent(event.identifier,
                                                                           event.item_identifier))

            self.logger.debug("returning DropsEvent")
            self.message_for_host.event_list.append(shard.DropsEvent(event.identifier,
                                                                     event.item_identifier,
                                                                     event.target_identifier))

        return

    def process_TriesToManipulateEvent(self, event):
        """Return AttemptFailedEvent to the host.
        """

        self.logger.debug("returning AttemptFailedEvent to host")
        self.message_for_host.event_list.append(shard.AttemptFailedEvent(event.identifier))
        return

    def process_TriesToTalkToEvent(self, event):
        """Return AttemptFailedEvent to the host.
        """

        self.logger.debug("returning AttemptFailedEvent to host")
        self.message_for_host.event_list.append(shard.AttemptFailedEvent(event.identifier))
        return

    def process_MovesToEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_PicksUpEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_DropsEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_ManipulatesEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_CanSpeakEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_AttemptFailedEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_PerceptionEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_SaysEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_ChangeStateEvent(self, event):
        """Return the Event to the host.
        """
        # ChangeState is based on a concept by Alexander Marbach.

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_PassedEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_LookedAtEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_PickedUpEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_DroppedEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_SpawnEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_DeleteEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_EnterRoomEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_RoomCompleteEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_ChangeMapElementEvent(self, event):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def move_towards(self, identifier, target_identifier):
        """Return the coordinates of the next move of Entity 'identifier' towards target_identifier in the current room.
        """

        location = self.host.room.entity_locations[identifier]

        possible_moves = []

        for vector in ((-1, 0), (1, 0), (0, -1), (0, 1)):

            possible_move = (location[0] + vector[0], location[1] + vector[1])

            if self.host.tile_is_walkable(possible_move):

                possible_moves.append(possible_move)

        if len(possible_moves) == 0:

            return None

        elif len(possible_moves) == 1:

            return possible_moves[0]

        else:
            # Taking first as reference
            #
            best_move = possible_moves.pop(0)

            distance_vector = shard.difference_2d(best_move, target_identifier)

            shortest_distance = math.sqrt(distance_vector[0] * distance_vector[0]
                                          + distance_vector[1] * distance_vector[1])

            # Examine remaining
            #
            for move in possible_moves:

                distance_vector = shard.difference_2d(move, target_identifier)

                distance = math.sqrt(distance_vector[0] * distance_vector[0]
                                     + distance_vector[1] * distance_vector[1])

                if distance < shortest_distance:
                    shortest_distance = distance
                    best_move = move

            return best_move

class MapEditor(DefaultGame):
    """This is the server-side Plugin for a Shard map editor.

       Additional attributes:

       MapEditor.current_room
           name of the current room
    """

    # TODO: replace hardwired "player" with client id

    def __init__(self, logger):
        """Initialise.
        """
        # Call base class
        #
        DefaultGame.__init__(self, logger)

        # TODO: When handling of multiple rooms is implemented, this should go into the base class.
        # TODO: Or is that one obsolete, since the name can be guessed from host.room.identifier?
        #
        self.current_room = ''

    def process_InitEvent(self, event):
        """Send a bare room, to be populated by the user.
        """

        self.logger.debug("called")

        if self.host.room is None:

            self.logger.debug("no room sent yet, sending initial room")

            self.message_for_host.event_list.append(shard.EnterRoomEvent("edit_this"))

            tile = shard.Tile(shard.FLOOR, "100x100-gray.png")

            for x in range(8):
                for y in range(5):
                    event = shard.ChangeMapElementEvent(tile, (x, y))
                    self.message_for_host.event_list.append(event)

            entity = shard.Entity(shard.PLAYER, "player", "player.png")

            self.message_for_host.event_list.append(shard.SpawnEvent(entity,
                                                                     (0, 0)))

            self.message_for_host.event_list.append(shard.RoomCompleteEvent())

    def process_EnterRoomEvent(self, event):
        """Save the name of the room to be entered and forward the event to the Server to update the Room.
        """
        self.logger.debug(str(event))
        self.current_room = event.room_identifier
        self.message_for_host.event_list.append(event)

    def process_RoomCompleteEvent(self, event):
        """Save the Room to a local file, then forward the event to the Server .
        """

        self.logger.debug("called")

        roomfile = open(self.current_room + ".floorplan", "wt")

        for coordinates in self.host.room.floor_plan:

            tile = self.host.room.floor_plan[coordinates].tile

            entities_string = ""

            for entity in self.host.room.floor_plan[coordinates].entities:

                # TODO: make sure commas are not present in the other strings
                #
                entities_string = entities_string + "\t{},{},{}".format(entity.entity_type,
                                                                        entity.identifier,
                                                                        entity.asset_desc)

            roomfile.write("{}\t{}\t{}{}\n".format(repr(coordinates),
                                                     tile.tile_type,
                                                     tile.asset_desc,
                                                     entities_string))

            # TODO: save FloorPlanElement.entities = []

        roomfile.close()

        self.logger.debug("wrote {}".format(self.current_room + ".floorplan"))

        self.message_for_host.event_list.append(event)

    def process_TriesToTalkToEvent(self, event):
        """Return the CanSpeakEvent to offer a selection to the player.
        """
        self.logger.debug("called")

        if event.target_identifier == "load_room":

            room_list = []

            for filename in os.listdir(os.getcwd()):

                if filename.endswith(".floorplan"):

                    room_list.append(filename.split(".floorplan")[0])

            event = shard.CanSpeakEvent(event.identifier, room_list)

            self.message_for_host.event_list.append(event)

    def process_SaysEvent(self, event):
        """If the text matches a room file, load and send the room.
        """

        self.logger.debug("called")

        if event.text + ".floorplan" not in os.listdir(os.getcwd()):

            self.logger.debug("'{}.floorplan' not found, cannot load room".format(event.text))

        else:
            self.logger.debug("'{}.floorplan' exists, attempting to load".format(event.text))

            event_list = load_room_from_file(event.text + ".floorplan")

            if event_list is None:

                self.logger.error("error opening file 'default.floorplan'")

            else:
                self.message_for_host.event_list = self.message_for_host.event_list + event_list

        return
