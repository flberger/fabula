"""Server-Side Plugins for Fabula

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

# work started on 27. Oct 2010

import fabula.plugins
import os
import math
import time
import re

# TODO: DefaultGame data structures as DefaultGame.tries_to_move_dict, DefaultGame.path_dict should most certainly bee room specific, and be cared for when Entities change rooms

def load_room_from_file(filename, complete = True):
    """This function reads a Fabula room from the file and returns a list of corresponding Events.

       The introducing EnterRoomEvent(client_identifier, room_identifier) will
       not be included, as the client id is only known to the caller.

       If 'complete' is True, a RoomCompleteEvent will be added, otherwise it
       will be left out.

       The ChangeMapElementEvents created by this function will use
       the filename minus extension as the room identifier.

       An Assets() instance will be used to retrieve the file, and its search
       strategies apply.

       The file must consist of lines of tab-separated strings:

       "(x, y)"TAB"tile_type, tile_asset_uri[, tile_asset_uri, ...]"TAB"identifier, entity_type, blocking, mobile, entity_asset_uri[, entity_asset_uri, ...]"[TAB"identifier, entity_type, blocking, mobile, entity_asset_uri[, entity_asset_uri, ...]"]

       The quotes enclosing the strings can also be left out.
    """

    # TODO: add parameter for Room identifier

    # Use a Fabula asset manager to locate the file.
    # Will raise an IOError if the file does not exist.
    # This must be handled by the caller.
    #
    roomfile = fabula.assets.Assets().fetch(filename, "t")

    room_identifier = os.path.splitext(os.path.basename(filename))[0]

    event_list = []

    for line in roomfile:

        # Remove whitespace. This also makes sure that the splitted line will
        # not end in a tab.
        #
        line = line.strip()

        # TODO: Check for tab-separated string
        # TODO: And more checks in general. fabula.FLOOR, asset_desc etc.
        #
        splitted_line = line.split("\t")

        # We support enclosing quotes, but they need not be there.
        #
        splitted_line = [element.strip("\"\'") for element in splitted_line]

        coordiantes_string = splitted_line.pop(0)

        # TODO: Blindly assuming CSV. Check before.
        #
        tile_type_uris = splitted_line.pop(0).split(",")

        location = None

        # Match only "(x, y)" coordinates
        #
        if fabula.str_is_tuple(coordiantes_string):

            tile_type = tile_type_uris.pop(0)

            asset_dict = {}

            for new_asset_dict in [fabula.infer_asset(uri.strip()) for uri in tile_type_uris]:

                asset_dict.update(new_asset_dict)

            tile = fabula.Tile(tile_type, asset_dict)

            location = eval(coordiantes_string) + (room_identifier, )

            event = fabula.ChangeMapElementEvent(tile, location)

            event_list.append(event)

        else:
            fabula.LOGGER.error("Line in '{}'does not start with a coordinate tuple: {}".format(filename, line))
            raise RuntimeError("Line in '{}'does not start with a coordinate tuple: {}".format(filename, line))

        if len(splitted_line):

            # There is still something there. This should be Entities.
            #
            for comma_sep_entity in splitted_line:

                # TODO: Blindly assuming CSV. Check before.
                #
                comma_sep_entity = comma_sep_entity.split(",")

                identifier = comma_sep_entity.pop(0).strip()
                entity_type = comma_sep_entity.pop(0).strip()
                blocking = comma_sep_entity.pop(0).strip()
                mobile = comma_sep_entity.pop(0).strip()

                if blocking in ("True", "False"):

                    blocking = eval(blocking)

                else:
                    blocking = False

                if mobile in ("True", "False"):

                    mobile = eval(mobile)

                else:
                    mobile = True

                # The rest should be asset URIs
                #
                asset_dict = {}

                for new_asset_dict in [fabula.infer_asset(uri.strip()) for uri in comma_sep_entity]:

                    asset_dict.update(new_asset_dict)

                entity = fabula.Entity(identifier,
                                       entity_type,
                                       blocking,
                                       mobile,
                                       asset_dict)

                event_list.append(fabula.SpawnEvent(entity, location))

    roomfile.close()

    if complete:
        event_list.append(fabula.RoomCompleteEvent())

    return event_list

def replace_identifier(event_list, identifier, replacement):
    """Return a list of Events where alle occurences of identifier are replaced by replacement.
    """

    fabula.LOGGER.debug("replacing identifier '{}' with '{}'".format(identifier, replacement))

    list_repr, replacements = re.subn(r"([^_])identifier = '{}'".format(identifier),
                                      r"\1identifier = '{}'".format(replacement),
                                      repr(event_list))

    fabula.LOGGER.debug("original: {}, replacement: {}".format(event_list, list_repr))

    fabula.LOGGER.debug("made {} replacements".format(replacements))

    return eval(list_repr)


class DefaultGame(fabula.plugins.Plugin):
    """This is an off-the-shelf server plugin, running a default Fabula game.

       Additional attributes:

       DefaultGame.tries_to_move_dict
           Dict mapping Entity identifiers to target positions.

       DefaultGame.path_dict
           Dict mapping Entity identifiers to a list of coordinates walked so far.

       DefaultGame.condition_response_dict
           A dict mapping then string representation of a trigger Event to a
           tuple of response Events.

       DefaultGame.talk_to_dict
           A dict caching the source and targets of TriesToTalkToEvents,
           mapping identifiers to identifiers.

       DefaultGame.message_queue
           A list queueing lists of Messages. Processed in
           DefaultGame.next_action().

       DefaultGame.action_time_reference
           A time value used as reference to compute time between calls to
           DefaultGame.next_action().

       DefaultGame.taken_locations
           A list of locations that are going to be occupied as a result of
           processing an incoming message. Will be reset to an empty list
           by DefaultGame.process_message().
   """

    # TODO: Add a method change_room() or the like, which makes a player change from one room to another. Basically Server._generate_room_events() + Delete and Spawn + deleting pending movements.

    def __init__(self, host):
        """Initialise.
        """

        # Call base class
        #
        fabula.plugins.Plugin.__init__(self, host)

        self.tries_to_move_dict = {}
        self.path_dict = {}
        self.condition_response_dict = {}
        self.talk_to_dict = {}

        self.message_queue = []

        self.action_time_reference = time.time()

        self.taken_locations = []

        # Load default logic.
        #
        fabula.LOGGER.info("attempting to load default game logic")
        self.load_condition_response_dict("default.logic")

        return

    def process_message(self, message):
        """DefaultGame main method.

           It calls the respective functions for the Events in message.

           It will call DefaultGame.next_action() every host.action_time seconds.

           Returns DefaultGame.message_for_host.
        """

        # First check whether action_time has passed since we do not want to
        # catch any Messages that are supposed to be processed in the next cycle.
        #
        next_action_events = []

        if time.time() - self.action_time_reference >= self.host.action_time:

            # Cache
            #
            next_action_events.extend(self.next_action())

            self.action_time_reference = time.time()

        # Now call the base class method, which in turn calls the processing
        # methods. Results are added to self.message_for_host.
        # Cave: wipes self.message_for_host, that's why we cache next_action_events
        #
        fabula.plugins.Plugin.process_message(self, message)

        # Append events returned by next_action()
        #
        self.message_for_host.event_list.extend(next_action_events)

        # Clear this step's list of taken locations
        #
        self.taken_locations = []

        return self.message_for_host

    def respond(self, event):
        """Add an Event from condition_response_dict corresponding to the Event given to message_for_host.

           If the Event is not found, return AttemptFailedEvent.

           This method will replace the Entity identifier with the string
           'player' before looking it up in condition_response_dict, and vice
           versa for response Events.
        """

        # Replace event.identifier with 'player' for lookup
        #
        event_str = repr(replace_identifier([event],
                                            event.identifier,
                                            "player")[0])

        if event_str in self.condition_response_dict:

            fabula.LOGGER.info("returning corresponding events")

            self.message_for_host.event_list.extend(replace_identifier(self.condition_response_dict[event_str],
                                                                       "player",
                                                                       event.identifier))

        else:
            fabula.LOGGER.info("event '{}' not found in condition_response_dict, returning AttemptFailedEvent to host".format(event_str))
            self.message_for_host.event_list.append(fabula.AttemptFailedEvent(event.identifier))

        return

    def next_action(self):
        """Called after after Server.action_time has passed to compute and return the next Events.
           The default implementation processes pending Entity movements and
           should be called from all subclasses of DefaultGame.
        """

        event_list = []

        # Process Message queue
        # NOTE: Doing this first, it might establish a Room for a client to handle MovesToEvents.
        #
        if len(self.message_queue):

            fabula.LOGGER.info("adding events from message_queue")

            for message in self.message_queue.pop(0):

                event_list.extend(message.event_list)

        # Create a new list to be able to change the dict during iteration.
        #
        for identifier in list(self.tries_to_move_dict.keys()):

            # TODO: HACK: selecting room by checking where the Entity exists right now. When the Entity has changed rooms, this will lead to leftover movements being executed.

            room = None

            for current_room in self.host.room_by_id.values():

                if identifier in current_room.entity_dict.keys():

                    room = current_room

            # Check if the Entity still exists
            #
            if room is None:

                fabula.LOGGER.debug("Entity '{}' gone from all rooms, removing from tries_to_move_dict".format(identifier))

                del self.tries_to_move_dict[identifier]
                del self.path_dict[identifier]

            else:
                fabula.LOGGER.debug("Using inferred room '{}' for Entity '{}'".format(room.identifier, identifier))

                target_identifier = self.tries_to_move_dict[identifier]

                location = self.move_towards(identifier,
                                             target_identifier,
                                             self.path_dict[identifier] + self.taken_locations)

                if location is None:

                    fabula.LOGGER.debug("no possible move for '{}', removing from tries_to_move_dict and returning AttemptFailedEvent".format(identifier))

                    del self.tries_to_move_dict[identifier]
                    del self.path_dict[identifier]

                    event_list.append(fabula.AttemptFailedEvent(identifier))

                else:
                    fabula.LOGGER.info("movement pending for '{}'".format(identifier))
                    fabula.LOGGER.debug("last positions {}, best move towards {} is {}".format(self.path_dict[identifier], target_identifier, location))

                    # Check if the Entity is blocking, and if so, block the new
                    # location internally
                    #
                    if room.entity_dict[identifier].blocking:

                        fabula.LOGGER.debug("adding location '{}' to the list of taken locations".format(location))

                        self.taken_locations.append(location)

                    # Save current position before movement as last position
                    #
                    self.path_dict[identifier].append(room.entity_locations[identifier])

                    event_list.append(fabula.MovesToEvent(identifier, location))

                    if location == target_identifier:

                        fabula.LOGGER.info("target reached, removing from tries_to_move_dict")

                        del self.tries_to_move_dict[identifier]
                        del self.path_dict[identifier]

        return event_list

    def queue_messages(self, *messages):
        """Queue messages to be executed after host.action_time seconds have passed.

           If multiple messages are given, host.action_time will pass between
           each of them.

           Multiple calls to this method will merge the message list given to
           the existing queue. Symbolically, if the queue is [[1], [2], [3]], a
           call of queue_messages([4, 5, 6]) will result in a queue of
           [[1, 4], [2, 5], [3, 6]]
        """

        # Superseding fabula.join_lists()

        # TODO: the current implementation requires argument unpacking when called with a list (queue_messages(*COMPUTED_LIST)). Support calling with lists.

        if len(messages):

            for message in messages:

                if not isinstance(message, fabula.Message):

                    fabula.LOGGER.error("cannot queue {}: not a Message instance".format(message))

                    # TODO: exit properly
                    #
                    raise RuntimeError("cannot queue {}: not a Message instance".format(message))

            # Make a list to be able to extract elements
            #
            messages = list(messages)

            fabula.LOGGER.debug("got {}".format(messages))

            # First append to existing Message lists.
            # Observe that each of self.message_queue or messages may be
            # exhausted first.
            #
            i = len(self.message_queue)

            if len(messages) < i:

                i = len(messages)

            j = 0

            while i:

                self.message_queue[j].append(messages.pop(0))

                j += 1
                i -= 1

            # Queue the rest as lists
            #
            self.message_queue.extend([[message] for message in messages])

            fabula.LOGGER.debug("message_queue is now {}".format(self.message_queue))

        return

    def process_InitEvent(self, event):
        """Conditionally load default.floorplan and send it, or just spawn the player Entity.

           Calls load_room_from_file() to retrieve the default.floorplan file.

           If a room is sent, all SpawnEvents with Entity type PLAYER whose
           identifier does not match event.identifier will be removed.
        """

        fabula.LOGGER.debug("called")

        fabula.LOGGER.info("attempting to load 'default.floorplan'")

        try:
            event_list = [fabula.EnterRoomEvent(event.identifier,
                                                "default")] + load_room_from_file("default.floorplan")

        except:

            fabula.LOGGER.error("error opening file 'default.floorplan'")
            raise

        if len(self.host.room_by_id):

            # NOTE: using first room by default
            #
            room = list(self.host.room_by_id.values())[0]

            fabula.LOGGER.info("Server already has room '{}', only sending SpawnEvent and RoomCompleteEvent".format(room.identifier))

            for returned_event in event_list:

                if (isinstance(returned_event, fabula.SpawnEvent)
                    and returned_event.entity.entity_type == fabula.PLAYER
                    and returned_event.entity.identifier == event.identifier):

                    self.message_for_host.event_list.append(returned_event)

                    # Creating the room is a joint undertaking by Server and
                    # Plugin, but now it is complete!
                    #
                    self.message_for_host.event_list.append(fabula.RoomCompleteEvent())

        else:
            fabula.LOGGER.info("Server has no room, sending Events from default.floorplan")

            self.message_for_host.event_list.extend(self._filter_spawn_events(event_list, event.identifier))

        return

    def _filter_spawn_events(self, event_list, identifier):
        """Remove all PLAYER SpawnEvents from event_list whose identifier does not match the given identifier.

           Returns a new list of events.
        """

        new_list = []

        spawn_events = removed_events = 0

        for event in event_list:

            if (isinstance(event, fabula.SpawnEvent)
                and event.entity.entity_type == fabula.PLAYER):

                spawn_events += 1

                if event.entity.identifier == identifier:

                    new_list.append(event)

                else:
                    msg = "Discarding PLAYER SpawnEvent because identifier does not match: {}"

                    fabula.LOGGER.info(msg.format(event))

                    removed_events += 1

            else:
                new_list.append(event)

        fabula.LOGGER.info("Found {} SpawnEvents, {} removed".format(spawn_events,
                                                                     removed_events))

        if removed_events == spawn_events:

            fabula.LOGGER.warning("All SpawnEvents removed! proceeding with undefined results")

        return new_list

    def process_TriesToMoveEvent(self, event):
        """Queue the target to make the Entity move one step at a time.
        """

        room = None

        for current_room in self.host.room_by_id.values():

            if event.identifier in current_room.entity_dict.keys():

                room = current_room

        if event.identifier in self.tries_to_move_dict.keys():

            fabula.LOGGER.debug("removing existing target {} for '{}'".format(self.tries_to_move_dict[event.identifier],
                                                                              event.identifier))

            del self.tries_to_move_dict[event.identifier]

        # Clear, whether the key exists or not
        #
        self.path_dict[event.identifier] = []

        # Partly copied from next_action()

        location = self.move_towards(event.identifier,
                                     event.target_identifier[:2],
                                     self.path_dict[event.identifier] + self.taken_locations)

        if location is None:

            fabula.LOGGER.warning("no possible move for '{}', not recording in tries_to_move_dict".format(event.identifier))

            fabula.LOGGER.info("AttemptFailed for '{}'".format(event.identifier))
            self.message_for_host.event_list.append(fabula.AttemptFailedEvent(event.identifier))

        else:
            msg = "movement requested for '{}', best move towards {} is {}"

            fabula.LOGGER.debug(msg.format(event.identifier,
                                           event.target_identifier[:2],
                                           location))

            # Check if the Entity is blocking, and if so, block the new location
            # internally
            #
            if room.entity_dict[event.identifier].blocking:

                fabula.LOGGER.debug("adding current target '{}' to the list of taken locations".format(location))

                self.taken_locations.append(location)

            # Save current position before movement as last position
            #
            self.path_dict[event.identifier].append(room.entity_locations[event.identifier])

            self.message_for_host.event_list.append(fabula.MovesToEvent(event.identifier, location))

            if location == event.target_identifier[:2]:

                fabula.LOGGER.debug("target reached, not recording in tries_to_move_dict")

                del self.path_dict[event.identifier]

            else:

                fabula.LOGGER.debug("saving '{} : {}' in tries_to_move_dict".format(event.identifier,
                                                                                    event.target_identifier[:2]))

                self.tries_to_move_dict[event.identifier] = event.target_identifier[:2]

        return

    def process_TriesToPickUpEvent(self, event):
        """Return a PicksUpEvent to the Server.
        """

        room = None

        for current_room in self.host.room_by_id.values():

            if event.identifier in current_room.entity_dict.keys():

                room = current_room

        # The Server has performed basic sanity checks.
        # In addition, we restrict picking up to items right next to the player.
        #
        player_location = room.entity_locations[event.identifier]

        surrounding_positions = fabula.surrounding_positions(player_location)

        if room.entity_locations[event.target_identifier] in surrounding_positions:

            fabula.LOGGER.info("returning PicksUpEvent")

            self.message_for_host.event_list.append(fabula.PicksUpEvent(event.identifier,
                                                                       event.target_identifier))

        else:
            fabula.LOGGER.info("AttemptFailed: '{}' not next to player".format(event.target_identifier))

            self.message_for_host.event_list.append(fabula.AttemptFailedEvent(event.identifier))

        return

    def process_TriesToDropEvent(self, event):
        """If the target is an Entity, forward to respond(). If the target is a position, create a DropsEvent.
        """

        # Server.process_TriesToDropEvent() has already done some checks,
        # so we can be sure that target_identifier is either a valid
        # coordinate tuple or an instance of fabula.Entity.
        #
        if event.target_identifier in self.host.rack.entity_dict.keys():

            fabula.LOGGER.debug("target '{}' is an entity identifier in Rack".format(event.target_identifier))

            fabula.LOGGER.info("'{}' dropped on Entity '{}', forwarding to respond()".format(event.item_identifier, event.target_identifier))

            self.respond(event)

            return

        # Not in Rack - try to infer a Room.
        #
        room = None

        for current_room in self.host.room_by_id.values():

            if event.identifier in current_room.entity_dict.keys():

                room = current_room

        # Restrict drops to tiles right next to the player.
        #
        player_location = room.entity_locations[event.identifier]

        surrounding_positions = fabula.surrounding_positions(player_location)

        # Include own position to allow drop on self
        #
        surrounding_positions += [player_location]

        if event.target_identifier in room.entity_dict.keys():

            fabula.LOGGER.debug("target '{}' is an entity identifier in room '{}'".format(event.target_identifier, room.identifier))

            if room.entity_locations[event.target_identifier] not in surrounding_positions:

                msg = "AttemptFailed: drop of '{}' on '{}' at {} not next to player: {}"

                fabula.LOGGER.info(msg.format(event.item_identifier,
                                              event.target_identifier,
                                              room.entity_locations[event.target_identifier],
                                              surrounding_positions))

                self.message_for_host.event_list.append(fabula.AttemptFailedEvent(event.identifier))

            else:
                fabula.LOGGER.info("'{}' dropped on Entity '{}', forwarding to respond()".format(event.item_identifier, event.target_identifier))
                self.respond(event)

            return

        fabula.LOGGER.debug("target '{}' is not an entity identifier".format(event.target_identifier[:2]))

        if event.target_identifier[:2] not in surrounding_positions:

            fabula.LOGGER.info("AttemptFailed: drop of '{}' on {} not next to player: {}".format(event.item_identifier, event.target_identifier[:2], surrounding_positions))
            self.message_for_host.event_list.append(fabula.AttemptFailedEvent(event.identifier))

            return

        # Still, the Entity to be dropped may originate either from Room or
        # from Rack.
        #
        entity = None

        if event.item_identifier not in self.host.rack.entity_dict.keys():

            fabula.LOGGER.info("item still in Room, returning PicksUpEvent")

            self.message_for_host.event_list.append(fabula.PicksUpEvent(event.identifier,
                                                                        event.item_identifier))

            entity = room.entity_dict[event.item_identifier]

        if entity is None:

            entity = self.host.rack.entity_dict[event.item_identifier]

        fabula.LOGGER.info("returning DropsEvent")

        self.message_for_host.event_list.append(fabula.DropsEvent(event.identifier,
                                                                  entity,
                                                                  event.target_identifier[:2]))

        # Check if the dropped Entity is blocking, and if so, block
        # the spot internally
        #
        if entity.blocking:

            fabula.LOGGER.debug("adding target '{}' to the list of taken locations".format(event.target_identifier[:2]))

            self.taken_locations.append(event.target_identifier[:2])

        return

    def process_AttemptFailedEvent(self, event):
        """Return the Event to the host.
        """

        fabula.LOGGER.info("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_SaysEvent(self, event):
        """This is a convenience hook to override.
           The default implementation sends the SaysEvent back to the Client and
           calls DefaultGame.respond().
        """

        fabula.LOGGER.debug("called")

        self.message_for_host.event_list.append(event)

        self.respond(event)

        return

    def process_TriesToLookAtEvent(self, event):
        """This is a convenience hook to override.
           The default implementation calls DefaultGame.respond().
        """

        fabula.LOGGER.debug("called")
        self.respond(event)
        return

    def process_TriesToManipulateEvent(self, event):
        """This is a convenience hook to override.
           The default implementation calls DefaultGame.respond().
        """

        fabula.LOGGER.debug("called")
        self.respond(event)
        return

    def process_TriesToTalkToEvent(self, event):
        """Cache source and target of the event in self.talk_to_dict, then call DefaultGame.respond().
        """

        fabula.LOGGER.debug("called")

        # Cache source and target
        #
        self.talk_to_dict[event.identifier] = event.target_identifier

        self.respond(event)

        return

    def move_towards(self, identifier, target_identifier, forbidden_moves):
        """Return the coordinates of the next move of Entity 'identifier' towards target_identifier in the current room.
           forbidden_moves is a list of targets that should be considered as not walkable.
        """

        room = None

        for current_room in self.host.room_by_id.values():

            if identifier in current_room.entity_dict.keys():

                room = current_room

        location = room.entity_locations[identifier]

        possible_moves = []

        for vector in ((-1, 0), (1, 0), (0, -1), (0, 1)):

            possible_move = (location[0] + vector[0], location[1] + vector[1])

            if (room.tile_is_walkable(possible_move)
                and possible_move not in forbidden_moves):

                possible_moves.append(possible_move)

            elif possible_move == target_identifier:

                # This means we are next to the target, but it is either
                # forbidden or blocked by an entity. Don't go wandering, stop.
                #
                fabula.LOGGER.info("next to target {}, but target is blocked. Stopping movement.".format(target_identifier))

                return None

        if len(possible_moves) == 0:

            return None

        elif len(possible_moves) == 1:

            return possible_moves[0]

        else:
            # fabula.LOGGER.debug("possible_moves == {}".format(possible_moves))

            # Taking first as reference
            #
            best_move = possible_moves.pop(0)

            distance_vector = fabula.difference_2d(best_move, target_identifier)

            shortest_distance = math.sqrt(distance_vector[0] * distance_vector[0]
                                          + distance_vector[1] * distance_vector[1])

            # fabula.LOGGER.debug("move {} has distance {}".format(best_move, shortest_distance))

            # Examine remaining
            #
            for move in possible_moves:

                distance_vector = fabula.difference_2d(move, target_identifier)

                distance = math.sqrt(distance_vector[0] * distance_vector[0]
                                     + distance_vector[1] * distance_vector[1])

                # fabula.LOGGER.debug("move {} has distance {}".format(move, distance))

                if distance < shortest_distance:
                    shortest_distance = distance
                    best_move = move

            # Does that move actually bring us any closer to the target?
            # This check will stop Entities from wandering around, but they will
            # miss winding ways to the target.
            #
            current_vector = fabula.difference_2d(location, target_identifier)

            current_distance = math.sqrt(current_vector[0] * current_vector[0]
                                         + current_vector[1] * current_vector[1])

            if shortest_distance >= current_distance:

                fabula.LOGGER.info("best move does not reduce distance to target, stopping movement")

                return None

            # fabula.LOGGER.debug("choosing move {} with distance {}".format(best_move, shortest_distance))

            return best_move

    def load_condition_response_dict(self, filename):
        """Load response logic from the file given.
        """

        fabula.LOGGER.debug("attempting to read from file '{}'".format(filename))

        if filename:

            try:
                # Always supply explicit encoding
                #
                file = open(filename, "rt", encoding = "utf8")

                logic_textdump = file.read()

                file.close()

                # Remove formatting
                #
                logic_textdump = logic_textdump.replace('\n', '')

                # TODO: Check, check, check
                #
                self.condition_response_dict = eval(logic_textdump)

            except IOError:
                fabula.LOGGER.error("could not read from file '{}', game logic not updated".format(filename))

            except SyntaxError:
                fabula.LOGGER.error("SyntaxError in '{}', game logic not updated".format(filename))

        else:
            fabula.LOGGER.error("no filename given")

        fabula.LOGGER.debug("{} condition-response records".format(len(self.condition_response_dict)))

        return

class Editor(DefaultGame):
    """This is the server-side Plugin for a Fabula map editor.

       Additional attributes:

       Editor.pygameui
           The fabula.plugins.pygameui module.

       Editor.pygame_editor
           A PygameEditor where the editing is done.
    """

    # TODO: replace hardwired "player" with client id
    # TODO: PygameEditor and serverside.Editor should each care for their own data structures. So separate methods where applicable.

    def __init__(self, host):
        """Initialise.
        """

        import fabula.plugins.pygameui
        import fabula.assets

        self.pygameui = fabula.plugins.pygameui

        # Call base class
        #
        DefaultGame.__init__(self, host)

        fabula.LOGGER.debug("called")

        # Trick Interface into believing a client is there
        #
        self.host.interface.connect("dummy_client")

        init_event = fabula.Message([fabula.InitEvent("player")])

        self.host.interface.connections["dummy_client"].messages_for_local.append(init_event)

        # Impersonate a decent host.
        # self.room will point to self.host.room later, but chances are there
        # is no host yet.
        #
        self.room = None
        self.rack = self.host.rack
        self.client_id = "player"

        # Create a PygameEditor where the editing is done
        # TODO: hardcoded framerate
        #
        self.pygame_editor = self.pygameui.PygameEditor(fabula.assets.Assets(),
                                                        60,
                                                        self)

        fabula.LOGGER.debug("complete")

    def process_message(self, message):
        """Editor main method.
           It calls the base class method, but before returning to the host
           it calls the local PygameUserInterface.
        """

        # Upon first call we have a host and thus a decent room and rack
        # TODO: of course it is a waste to set that on every call
        # HACK: using last room in host TODO: fix
        #
        if len(self.host.room_by_id):
            self.room = list(self.host.room_by_id.values())[-1]
        else:
            # Dummy room for the meantime
            #
            self.room = fabula.Room("dummy")

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

        fabula.LOGGER.debug("called")

        if not len(self.host.room_by_id):

            fabula.LOGGER.info("no room sent yet, sending initial room")

            self.message_for_host.event_list.append(fabula.EnterRoomEvent(self.client_id,
                                                                          "edit_this"))

            tile = fabula.Tile(fabula.FLOOR, {"image/png": fabula.Asset("100x100-gray.png")})

            event = fabula.ChangeMapElementEvent(tile, (0, 0, "edit_this"))

            self.message_for_host.event_list.append(event)

            # TODO: use a safe filename or a fallback for player, or no player at all
            #
            entity = fabula.Entity(identifier = "player",
                                   entity_type = fabula.PLAYER,
                                   blocking = False,
                                   mobile = True,
                                   assets = {"image/png": fabula.Asset("player-fabulasheet.png")})

            self.message_for_host.event_list.append(fabula.SpawnEvent(entity,
                                                                     (0, 0, "edit_this")))

            # Force recreation of the tiles plane
            #
            self.message_for_host.event_list.append(fabula.RoomCompleteEvent())

    def process_TriesToDropEvent(self, event):
        """A custom version of DefaultGame.process_TriesToDropEvent(), allowing to drop Entities anywhere.
        """

        # NOTE: tons of duplicated code

        # Server.process_TriesToDropEvent() has already done some checks,
        # so we can be sure that target_identifier is either a valid
        # coordinate tuple or an instance of fabula.Entity.
        #
        if event.target_identifier in self.room.entity_dict.keys():

            fabula.LOGGER.info("'{}' dropped on Entity '{}', forwarding to respond()".format(event.item_identifier, event.target_identifier))
            self.respond(event)

        else:
            fabula.LOGGER.debug("target '{}' is not an entity identifier".format(event.target_identifier))

            # Still, the Entity to be dropped may originate either from Room
            # or from Rack.
            #
            entity = None

            if event.item_identifier not in self.host.rack.entity_dict.keys():

                fabula.LOGGER.info("item still in Room, returning PicksUpEvent")

                self.message_for_host.event_list.append(fabula.PicksUpEvent(event.identifier,
                                                                            event.item_identifier))

                entity = self.room.entity_dict[event.item_identifier]

            if entity is None:

                entity = self.host.rack.entity_dict[event.item_identifier]

            fabula.LOGGER.info("returning DropsEvent")

            self.message_for_host.event_list.append(fabula.DropsEvent(event.identifier,
                                                                      entity,
                                                                      event.target_identifier))

            # Check if the dropped Entity is blocking, and if so, block
            # the spot internally
            #
            if entity.blocking:

                fabula.LOGGER.debug("adding target '{}' to the list of taken locations".format(event.target_identifier))

                self.taken_locations.append(event.target_identifier)

        return

    def process_TriesToPickUpEvent(self, event):
        """A custom version of DefaultGame.process_TriesToPickUpEvent(), allowing to pick up Entities from anywhere.
        """

        fabula.LOGGER.info("returning PicksUpEvent")

        self.message_for_host.event_list.append(fabula.PicksUpEvent(event.identifier,
                                                                   event.target_identifier))

        return

    def send_room_events(self, option):
        """OptionSelector callback to read a Room from a file and send it to the Server.
        """

        fabula.LOGGER.debug("called")

        try:
            event_list = [fabula.EnterRoomEvent(self.client_id,
                                                option.text)] + load_room_from_file(option.text + ".floorplan")

        except:

            fabula.LOGGER.error("error opening file '{}.floorplan'".format(option.text + ".floorplan"))

            return

        self.message_for_host.event_list.extend(event_list)

        fabula.LOGGER.debug("complete")

        return

    def respond(self, event):
        """Add an Event from condition_response_dict corresponding to the Event given to message_for_host.
           If the Event is not found, make the user select a response.
        """

        event_str = str(event)

        if event_str in self.condition_response_dict:

            fabula.LOGGER.info("returning corresponding events")
            self.message_for_host.event_list = self.message_for_host.event_list + self.condition_response_dict[event_str]

        else:
            fabula.LOGGER.info("event '{}' not found in condition_response_dict, making user select a response".format(event_str))
            self.pygame_editor.select_event(event)

        return

    def add_response(self, trigger_event, response_event):
        """Add the respone to Editor.condition_response_dict.
        """

        # This could also be done in self.pygame_editor.event_edit_done(), but
        # it's cleaner to do here.
        #
        fabula.LOGGER.info("adding response: {} -> {}".format(trigger_event, response_event))

        if str(trigger_event) in self.condition_response_dict.keys():

            if response_event in self.condition_response_dict[str(trigger_event)]:

                fabula.LOGGER.info("response already defined for this trigger")

            else:

                self.condition_response_dict[str(trigger_event)].append(response_event)

        else:
            self.condition_response_dict[str(trigger_event)] = [response_event]

        return

    def save_condition_response_dict(self, filename):
        """Save the response logic to the file given.
        """

        fabula.LOGGER.info("attempting to save to file '{}'".format(filename))

        if filename:

            logic_textdump = repr(self.condition_response_dict)

            # Do a little neat wrapping
            #
            logic_textdump = logic_textdump.replace(')": ', ')":\n    ')
            logic_textdump = logic_textdump.replace('),', '),\n    ')
            logic_textdump = logic_textdump.replace(']', '\n    ]')
            logic_textdump = logic_textdump.replace('],', '],\n')
            logic_textdump = logic_textdump.replace('}', '\n}\n')

            # Always supply explicit encoding
            #
            file = open(filename, "wt", encoding = "utf8")

            file.write(logic_textdump)

            file.close()

            # TODO: there should be something like pygame_ui.feedback or pygame_ui.okbox to display a message from here
            #
            ok_box = self.pygameui.planes.gui.OkBox("Logic saved to file '{}'.".format(filename))

            ok_box.rect.center = self.pygame_editor.window.rect.center

            self.pygame_editor.window.sub(ok_box)

        else:
            fabula.LOGGER.error("no filename given")

        return

    def clear_condition_response_dict(self):
        """Clear the response logic.
        """

        fabula.LOGGER.info("clearing condition_response_dict")

        self.condition_response_dict = {}

        # TODO: there should be something like pygame_ui.feedback or pygame_ui.okbox to display a message from here
        #
        ok_box = self.pygameui.planes.gui.OkBox("Logic cleared.")

        ok_box.rect.center = self.pygame_editor.window.rect.center

        self.pygame_editor.window.sub(ok_box)

        return

class CommandLine(DefaultGame):
    """This is a command-line interface server plugin.
    """

    def __init__(self, host):
        """Initialise.
        """

        # Call base class
        #
        DefaultGame.__init__(self, host)

        self.client_id = None

        print("Welcome to the Fabula command-line interface.")
        print()
        print("Available commands:")
        print("move   IDENTIFIER X Y         Make IDENTIFIER move to location (X, Y).")
        print("pick   IDENTIFIER ITEM        Make IDENTIFIER pick up ITEM.")
        print("drop   IDENTIFIER ITEM X Y    Make IDENTIFIER drop ITEM at location (X, Y).")
        print("say    IDENTIFIER TEXT        Make IDENTIFIER say TEXT.")
        print("load   NAME                   Load room NAME from local file NAME.floorplan.")
        print("failed IDENTIFIER             Deny the attempt by IDENTIFIER.")
        print()
        print("Or hit RETURN at the prompt to proceed with default game responses.")
        print()

        return

    def process_message(self, message):
        """Display the incoming Message, and return typed Events as a Message.
        """

        # Clear message for host
        #
        self.message_for_host = fabula.Message([])

        for event in message.event_list:

            print("-> {}".format(event))

            # Catch player identifier
            #
            if self.client_id is None and isinstance(event, fabula.InitEvent):

                self.client_id = event.identifier

        input_string = input("? ")

        if input_string == "":

            print("Proceeding with default game responses...")

            # Call base class
            #
            self.message_for_host = DefaultGame.process_message(self, message)

        else:

            return_string, return_events = self.parse(input_string)

            print(return_string)

            self.message_for_host = fabula.Message(return_events)

        return self.message_for_host

    def parse(self, input_string):
        """This method parses the input string and returns a tuple (string, event_list).
           The string and event list may be empty.
        """

        return_string = "Unknown command."
        return_events = []

        token_list = input_string.lower().strip().split()

        if token_list[0] == "load" and len(token_list) == 2:

            return_string = "Loading room '{0}' from file {0}.floorplan".format(token_list[1])

            return_events = [fabula.EnterRoomEvent("player", token_list[1])] + load_room_from_file(token_list[1] + ".floorplan")

            return_events = replace_identifier(return_events,
                                               "player",
                                               self.client_id)

        elif token_list[0] == "failed" and len(token_list) == 2:

            event = fabula.AttemptFailedEvent(token_list[1])

            return_string = "<- {}".format(event)

            return_events.append(event)

        elif token_list[0] == "move" and len(token_list) == 4:

            event = fabula.MovesToEvent(token_list[1],
                                        (int(token_list[2]), int(token_list[3])))

            return_string = "<- {}".format(event)

            return_events.append(event)

        elif token_list[0] == "pick" and len(token_list) == 3:

            event = fabula.PicksUpEvent(token_list[1], token_list[2])

            return_string = "<- {}".format(event)

            return_events.append(event)

        elif token_list[0] == "drop" and len(token_list) == 5:

            event = fabula.DropsEvent(token_list[1],
                                      self.host.rack.entity_dict(token_list[2]),
                                      (int(token_list[3]), int(token_list[4])))

            return_string = "<- {}".format(event)

            return_events.append(event)

        elif token_list[0] == "say" and len(token_list) > 2:

            text = " ".join(token_list[2:])

            event = fabula.SaysEvent(token_list[1], text)

            return_string = "<- {}".format(event)

            return_events.append(event)

        return (return_string, return_events)
