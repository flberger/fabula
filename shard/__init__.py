"""Shard - A Client-Server System for Interactive Storytelling by means of an Adventure Game Environment

   "Stories On A Grid"

   (c) Florian Berger <fberger@florian-berger.de>
"""

# This file has been started on 19. May 2008, building
# on some drafts done in May 2008.
#
# Transformed into a package on 22. September 2009.

# TODO: reasonable package docstring above: what is where :) PEP 257: The docstring for a module should generally list the classes, exceptions and functions (and any other objects) that are exported by the module, with a one-line summary of each.
#
# TODO: PEP 8: Comparisons to singletons like None should always be done with 'is' or 'is not', never the equality operators.
# TODO: PEP 8: Don't compare boolean values to True or False using ==
#
# TODO: import shard.xyz also imports shard - so get rid of redundant imports
#
# TODO: string.format() instead of "%s" % s or "s" + "s" in the whole package!
#
# TODO: use map() instead of "for" loops where applicable
#
# TODO: "avoid dots" -> prefetch functions from.long.dotted.operations
# TODO: most prominently: message.event_list.append -> message.append
#
# TODO: readable __repr__ of all shard objects: Room, Tile, ...
# TODO: use instance.__class__.__name__ and __module__ in repr
#
# TODO: one should be able to evaluate Messages to True and False for if clauses testing if there are any events in the message
#
# TODO: give the method return value in docstring
#
# TODO: unify Event attributes target_identifier, trigger_identifier, item_identifier where applicable
#
# TODO: per-player inventories in server... -.-
#
# TODO: there is no ConfirmEvent associated with TriesToManipulateEvent
#
# TODO: There currently is no way Plugins can directly issue Events for other clients (for example PercentionEvents or EnterRoomEvents)

import shard.eventprocessor

############################################################
# Events

class Event:
    """Shard event base class.
    """

    def __init__(self, identifier):
        """Event initialisation.
           This constructor must be called with
           an unique identifier for the object
           (player, item, NPC) which is affected
           by this event.
        """
        # By defining it here, the variable is
        # part of the instance object, not the
        # class object. See "Class definitions"
        # in the Python Reference Manual.
        #
        self.identifier = identifier

    def __eq__(self, other):
        """Allow the == operator to be used on Events.
           Check if the object given has the same
           class and the same attributes with the
           same values.
        """

        if other.__class__ == self.__class__:

            # Dicts can be compared right away (tested)
            #
            if other.__dict__ == self.__dict__:

                return True

            else:
                return False

        else:
            return False

    def __ne__(self, other):
        """Allow the != operator to be used on Events.
           Check if the object given has a different
           class or the different attributes with
           different values.
        """

        if other.__class__ == self.__class__:

            # Dicts can be compared right away (tested)
            #
            if other.__dict__ != self.__dict__:

                return True

            else:
                return False

        else:
            return True

    def __repr__(self):
        """Readable and informative string representation.
        """

        arguments = ""

        for key in self.__dict__:

            arguments = arguments + "%s = %s, " % (key, self.__dict__[key])

        arguments = arguments[:-2]

        return "<%s(%s)>" % (self.__class__, arguments)

####################
# Attempt events

class AttemptEvent(Event):
    """This is the base class for attempt events by the player or NPCs.
    """

    def __init__(self, identifier, target_identifier):
        """Event initialisation.
           When sent by the client, target_identifier
           must describe the target location of the
           attempt.
           On a two-dimensional map with rectangular
           elements target_identifier is a tuple of
           (x, y) integer coordinates, with (0, 0) being
           the upper left corner.
           The server determines what is being 
           looked at / picked up / manipulated / 
           talked to at that location, and 
           replaces the location string with an item, 
           NPC or player identifier if appropriate.
        """
        self.identifier = identifier

        self.target_identifier = target_identifier

class TriesToMoveEvent(AttemptEvent):
    """Issued when the player or an NPC wants to move, awaiting server confirmation.
    """
    pass

class TriesToLookAtEvent(AttemptEvent):
    """Issued when the player or an NPC looks at a map element or an item.
    """
    pass

class TriesToPickUpEvent(AttemptEvent):
    """Issued when the player or an NPC tries to pick up an item.
       Attempts to pick up NPCs are discarded or answered with an error.
    """
    pass

class TriesToDropEvent(AttemptEvent):
    """The player or NPC tries to drop an item.
    """

    def __init__(self, identifier, item_identifier, target_identifier):
        """Event initialisation.
           An attempt to drop the item identified by
           item_identifier. When sent by the client, 
           target_identifier must describe the 
           desired location.
           On a two-dimensional map with rectangular
           elements target_identifier is a tuple of
           (x, y) integer coordinates, with (0, 0) being
           the upper left corner.
           Note that this attempt can turn out as a
           "use" action, for example when dropping
           a key on a padlock. In this case, the
           server replaces the location with an item 
           identifier and passes that on to the
           story engine.
        """
        self.identifier = identifier

        self.item_identifier = item_identifier

        self.target_identifier = target_identifier

class TriesToManipulateEvent(AttemptEvent):
    """Issued when the player or an NPC tries to manipulate an item.
       NPCs cannot be manipulated.
    """
    pass

class TriesToTalkToEvent(AttemptEvent):
    """Issued when the player or an NPC wants to start a conversation with another entity.
       It is not possible to talk to items.
    """
    pass

####################
# Confirm events

class ConfirmEvent(Event):
    """This is the base class for server confirmations of attempt events.
    """
    pass

class MovesToEvent(ConfirmEvent):
    """This is the server confirmation of a movement.
    """

    def __init__(self, identifier, location):
        """Event initialisation.
           location is a description as in the TriesToMoveEvent.
        """
        self.identifier = identifier

        self.location = location

class PicksUpEvent(ConfirmEvent):
    """This is a server confirmation of a TriesToPickUpEvent
       issued by the player or an NPC.
    """

    def __init__(self, identifier, item_identifier):
        """Event initialisation.
           item_identifier identifies the item to
           pick up. This item should be known to
           the client.
        """
        self.identifier = identifier

        self.item_identifier = item_identifier

class DropsEvent(ConfirmEvent):
    """This is the server confirmation for an attempt to drop an item
       by the player or an NPC.
       This event does normally not occur when the
       drop action evaluates to a "use with" action, 
       as described in TriesToDropEvent. In that case
       the item stays in the posession of its owner, 
       and some other events are issued.
    """

    def __init__(self, identifier, item_identifier, location):
        """Event initialisation.
           item_identifier identifies the item to be 
           dropped on the map. location is a 
           description as in the TriesToMoveEvent.
        """
        self.identifier = identifier

        self.item_identifier = item_identifier

        self.location = location

class CanSpeakEvent(ConfirmEvent):
    """This is a server invitation for the player or an NPC to speak.
       Since this event requires immediate user input, it is always
       executed as the last event of a Message by the PresentationEngine.
    """

    def __init__(self, identifier, sentences):
        """Event initialisation.
           sentences is a list of strings for the
           player or NPC to choose from. If this list
           is empty, the client should offer a free-form
           text input.
        """
        self.identifier = identifier

        self.sentences = sentences

class AttemptFailedEvent(ConfirmEvent):
    """Server announcement that the last AttemptEvent failed.
       identifier identifies the entity which sent the AttempEvent.
       This event should unblock the entity and allow new attempts.
       Actually this is not a confirmation.
    """
    pass

class PerceptionEvent(ConfirmEvent):
    """This is a perception for the player or an NPC issued by the server,
       usually the result of a TriesToLookAtEvent. Note that a
       PerceptionEvent may be issued by the server without any
       previous attempts by the Entity affected.
    """

    def __init__(self, identifier, perception):
        """Event initialisation.
           perception is a string to be displayed
           by the client. Note: When used with an NPC,
           this could feed a memory database.
        """
        self.identifier = identifier

        self.perception = perception

class ManipulatesEvent(ConfirmEvent):
    """This is a server confirmation of an item manipulation.
       This Event normally has no visible effect; effects of
       a ManipulateEvent are usually MovesToEvents,
       ChangeMapElementEvents, SpawnEvents etc. The
       ManipulatesEvent simply confirms that a manipulation
       has happened.
    """

    def __init__(self, identifier, item_identifier):
        """Event initialisation.
           item_identifier identifies the item
           that is being manipulated.
        """
        self.identifier = identifier

        self.item_identifier = item_identifier

####################
# Unclassified events without a special base class

class SaysEvent(Event):
    """This normally is a reaction to the CanSpeakEvent, to be sent by the player.
       NPCs can speak spontanously, in that case a SaysEvent
       is issued by he Story Engine. Players usually have to
       send an TriesToTalkToEvent before they are allowed to speak.
    """

    def __init__(self, identifier, text):
        """Event initialisation.
           text is a string to be spoken by the entity.
        """
        self.identifier = identifier

        self.text = text

class ChangeStateEvent(Event):
    """This Event is issued to trigger a state change.
       Each instance of shard.Entity has a state.
    """

    # ChangeState is based on a concept by Alexander Marbach.

    def __init__(self, identifier, state):
        """Event initialisation.
           state is the new state for the Entity
           identified by identifier. In the simplest
           case state may be a number or a verbose
           string.
        """
        self.identifier = identifier

        self.state = state

####################
# Passive events

class PassiveEvent(Event):
    """The base class for events when items or NPCs are being passed, looked at, 
       picked up and the like.
    """

    def __init__(self, identifier, trigger_identifier):
        """Event initialisation.
           The trigger_identifier identifies the
           entity that triggered the event. This makes it
           possible to react differently to several
           entities.
        """
        self.identifier = identifier

        self.trigger_identifier = trigger_identifier

class PassedEvent(PassiveEvent):
    """Issued by the server when an item or an NPC is being passed
       by the player or an NPC.
    """
    pass

class LookedAtEvent(PassiveEvent):
    """Issued by the server when an item or NPC is being looked at
       by the player or an NPC.
    """
    pass

class PickedUpEvent(PassiveEvent):
    """Issued by the server when an item is being picked up
       by the player or an NPC.
    """
    pass

class DroppedEvent(PassiveEvent):
    """Issued by the server when an item is being dropped
       by the player or an NPC.
    """
    pass

####################
# Server events

class ServerEvent(Event):
    """Base class for various events issued by the server
       that are no ConfirmEvents, including map and room events.
    """
    pass

class SpawnEvent(ServerEvent):
    """This event creates the player / new item / NPC on the map.
    """

    def __init__(self, entity, location):
        """Event initialisation.
           entity is an instance of shard.Entity, 
           having a type, identifier and asset.
           location is a tuple of 2D integer
           coordinates.
           The server stores the relevant
           information and passes the entity on to
           the client.
        """
        self.entity = entity
        self.location = location

class DeleteEvent(ServerEvent):
    """This event deletes an item or NPC from the map.
       Note that items may still persist in the players
       posessions.
    """
    pass

class EnterRoomEvent(ServerEvent):
    """This event announces that the player enters a new room.
       Events building the map and spawning the player, items
       and NPCs should follow. The room is done and can be used
       when the server issues RoomCompleteEvent.
    """

    def __init__(self):
        """This event has no parameters.
        """
        pass

class RoomCompleteEvent(ServerEvent):
    """Issued by the server after an EnterRoomEvent
       when the room is populated with a map, items and NPCs.
    """

    def __init__(self):
        """This event has no parameters.
        """
        pass

class ChangeMapElementEvent(ServerEvent):
    """This event changes a single element of the two-dimensional map.
       When sent in a Message, these events are executed immediately and
       in parallel upon the rendering of the
       Message by the PresentationEngine.
    """
    
    def __init__(self, tile, location):
        """Event initialisation.
           tile is a shard map object having a type 
           (obstacle or floor) and an asset.
           location is an object describing the
           location of the tile in the game world, 
           most probably a tuple of coordinates, but
           possibly only a string like "lobby".
           The server stores the relevant
           information and passes the tile and the
           location on to the client.
        """
        self.tile = tile

        self.location = location

####################
# Client Events

# Suspended until we have more client events:
#
# class ClientEvent(Event):
#     """This is the base class for administrative
#        client events."""
#
#     def __init__(self):
#         """Client events have no parameters."""
#         pass

class InitEvent(Event):
    """This event is sent once by the client upon startup.
       It asks the server to supply anything that is needed
       to update the client to the current game state -
       usually a number of ChangeMapElementEvents and SpawnEvents.
       The client interface may decide to issue this event
       again in case there has been a connection failure.
    """

    def __init__(self, identifier):
        """identifier must be unique for each client.
        """

        self.identifier = identifier

############################################################
# Message

class Message:
    """A Message manages an ordered list of shard events.
       Messages sent by the server describe the action
       of a certain time frame. The PresentationEngine has to
       decide which events happen in parallel and which 
       ones happen sequential. Instances of Message 
       expose a single Python list object as Message.event_list.

       Attributes:

       Message.event_list
           A list of shard.Events

       Message.has_EnterRoomEvent
       Message.has_RoomCompleteEvent
           Convenience flags, initially False
    """

    def __init__(self, event_list):
        """Initialize the Message with a list of objects derived from shard.Event.
           An empty list may be supplied.
        """

        # TODO: check the list elements for being instances of shard.Event here?
        #
        self.event_list = event_list

        # We attach custom flags to the Message created in
        # setup() to notify the PresentationEngine whether
        # an EnterRoomEvent or RoomCompleteEvent occured,
        # so it does not have to scan the events.
        #
        self.has_EnterRoomEvent = False
        self.has_RoomCompleteEvent = False

    def __repr__(self):
        """Readable and informative string representation.
        """

        return str(self.event_list)

#    def queueAsFirstEvent(self, event):
#        """This is a convenience method. Queue the event 
#           given as the first event to be processed, 
#           shifting other events already queued."""
#        self.event_list = [event] + self.event_list

############################################################
# Entities

class Entity(shard.eventprocessor.EventProcessor):
    """An Entity is a Shard game object.
       This is the base class for the player, NPCs and items.
       An Entity holds information used by the Shard game logic:

       Entity.entity_type
       Entity.identifier
       Entity.asset
       Entity.state

       In addition,

       Entity.presentation_engine

       is added by and points to the PresentationEngine.

       A Shard Client should use subclasses (possibly
       with multiple inheritance) or custom attachements
       to instances of this class to implement the
       game objects used by the rendering engine (2D
       sprites, 3D models). Usually the ClientCoreEngine
       manages a list of Entity instances. Everything
       concernig the actual graphical representation is
       done by the PresentationEngine. Since this is very
       application dependent it is not covered in the
       base class. Check the documentation and source of 
       the PresentationEngine for further insight on how it 
       handles game objects.
    """

    def __init__(self, entity_type, identifier, asset):
        """This method sets up the following attributes from the values given:

           Entity.entity_type
               One of shard.PLAYER, shard.NPC, shard.ITEM_BLOCK
               or shard.ITEM_NOBLOCK.

           Entity.identifier
               Must be an object whose string representation
               yields an unique identification.

           Entity.asset
               Preferably a string with a file name or an URI
               of a media file containing the data for visualizing
               the Entity. Do not put large objects here since
               Entities are pushed around quite a bit and
               transfered across the network.
               The PresentationEngine may fetch the asset and
               attach it to the instance of the Entity.

           Entity.state
               The state the Entity is in. Defaults to None.
        """

        shard.eventprocessor.EventProcessor.__init__(self)

        # Now we have:
        # self.event_dict
        # which maps Event classes to handler methods

        self.entity_type = entity_type
        self.identifier = identifier
        self.asset = asset
        self.state = None

    # EventProcessor overrides
    #
    # These are called by the PresentationEngine,
    # which also has added the Entity.framerate
    # and Entity.action_frames attributes

    def process_MovesToEvent(self, event):
        """This method is called by the PresentationEngine.
           The Entity representation has to execute the
           according action over the course of Entity.action_frames frames.
           But it must du so in an non-blocking fashion -
           this method must return as soon as possible.
           So do set up counters or frame queues here.
           Your implementation may call another method
           once per frame, do the actual work there.
        """
        pass

    def process_ChangeStateEvent(self, event):
        """This method is called by the PresentationEngine.
           The Entity representation has to execute the
           according action over the course of Entity.action_frames frames.
           But it must du so in an non-blocking fashion -
           this method must return as soon as possible.
           So do set up counters or frame queues here.
           Your implementation may call another method
           once per frame, do the actual work there.
        """
        self.state = event.state

    def process_DropsEvent(self, event):
        """This method is called by the PresentationEngine.
           The Entity representation has to execute the
           according action over the course of Entity.action_frames frames.
           But it must du so in an non-blocking fashion -
           this method must return as soon as possible.
           So do set up counters or frame queues here.
           Your implementation may call another method
           once per frame, do the actual work there.
        """
        pass

    def process_PicksUpEvent(self, event):
        """This method is called by the PresentationEngine.
           The Entity representation has to execute the
           according action over the course of Entity.action_frames frames.
           But it must du so in an non-blocking fashion -
           this method must return as soon as possible.
           So do set up counters or frame queues here.
           Your implementation may call another method
           once per frame, do the actual work there.
        """
        pass

    def process_SaysEvent(self, event):
        """This method is called by the PresentationEngine.
           The Entity representation has to execute the
           according action over the course of Entity.action_frames frames.
           But it must du so in an non-blocking fashion -
           this method must return as soon as possible.
           So do set up counters or frame queues here.
           Your implementation may call another method
           once per frame, do the actual work there.
        """
        pass


############################################################
# Entity And Tile Types

# Currently values are strings, but they are subject
# to change without notice.

PLAYER = "PLAYER"
NPC = "NPC"
ITEM_BLOCK = "ITEM_BLOCK"
ITEM_NOBLOCK = "ITEM_NOBLOCK"

FLOOR = "FLOOR"
OBSTACLE = "OBSTACLE"

############################################################
# Tiles

class Tile:
    """A Tile is an element of a two-dimensional map.
       It is never meant to perform any active logic, 
       so its only property is a type and an asset."""

    def __init__(self, tile_type, asset):
        """Tile initialisation.
           tile_type must be shard.FLOOR or shard.OBSTACLE,
           describing whether the player or NPCs can move
           across the tile.
           asset is preferably a string with a file 
           name or an URI of a media file containing 
           the data for visualizing the tile.
        """
        self.tile_type = tile_type
        self.asset = asset

############################################################
# Rooms

class Room(shard.eventprocessor.EventProcessor):
    """A Room instance saves the map as well as Entities and their locations.
       It is maintained for the current room in the ClientCoreEngine
       and for all active rooms in the ServerCoreEngine.

       Room.entity_dict
           A dict of all Entities in this room,
           mapping Entity identifiers to Entity
           instances.

       Room.floor_plan
           A dict mapping 2D coordinate tuples
           to a FloorPlanElement instance.

       Room.entity_locations
           A dict mapping Entity identifiers to a
           2D coordinate tuple.

       Room.tile_list
           A list of tiles for the current room,
           for easy asset fetching.

       Room.active_clients
           A list of client identifiers whose
           player entities are in this room.

       Note that all these dicts assume that
       Entity identifiers are unique.
    """

    def __init__(self):
        """Initialize a room.
        """

        shard.eventprocessor.EventProcessor.__init__(self)

        # Now we have:
        # self.event_dict
        # mapping Event classes to handler methods
        # though we do not need it since all
        # methods of this class are called from
        # the outside.

        # floor_plan is an attempt of an efficient storage of
        # an arbitrary two-dimensional map. To save space, 
        # only explicitly defined elements are stored. This
        # is done in a dict whose keys are tuples. Access the
        # elements using floor_plan[(x, y)]. The upper left element
        # is floor_plan[(0, 0)].
        #
        self.floor_plan = {}

        self.tile_list = []

        self.entity_dict = {}
        self.entity_locations = {}

        self.active_clients = []

        return

    def process_ChangeMapElementEvent(self, event):
        """Update all affected dicts.
        """

        if event.location in self.floor_plan:

            self.floor_plan[event.location].tile = event.tile

        else:

            self.floor_plan[event.location] = FloorPlanElement(event.tile)

        self.tile_list.append(event.tile)

        return

    def process_SpawnEvent(self, event):
        """Update all affected dicts.
        """
        if event.location not in self.floor_plan:

            raise ShardException("cannot spawn entity %s at undefined location %s"
                                 % (event.entity.identifier, event.location))

        # If Entity is already there, just do nothing.
        # This is no error, so no exception is raised.
        # TODO: We would like to log that, but Entities have no logging access.
        #
        if event.entity.identifier not in self.entity_dict:

            self.floor_plan[event.location].entities.append(event.entity)

            self.entity_dict[event.entity.identifier] = event.entity

            self.entity_locations[event.entity.identifier] = event.location

        return

    def process_MovesToEvent(self, event):
        """Update all affected dicts.
        """

        if event.identifier not in self.entity_dict:

            raise ShardException("cannot move unknown entity %s"
                                 % event.identifier)

        if event.location not in self.floor_plan:

            raise ShardException("cannot move entity %s to undefined location %s"
                                 % (event.identifier, event.location))

        # Only process changed locations
        #
        if self.entity_locations[event.identifier] != event.location:

            # Remove old entity location
            #
            # identifier should point to the same
            # object that is in the respective
            # FloorPlanElement list
            #
            entity = self.entity_dict[event.identifier]
            location = self.entity_locations[event.identifier]

            self.floor_plan[location].entities.remove(entity)

            # (Over)write new entity location
            #
            self.floor_plan[event.location].entities.append(entity)

            self.entity_locations[event.identifier] = event.location

        return

    def process_DeleteEvent(self, event):
        """Update all affected dicts.
        """
        if event.identifier not in self.entity_dict:

            raise ShardException("cannot delete unknown entity %s"
                                 % event.identifier)

        entity = self.entity_dict[event.identifier]

        self.floor_plan[self.entity_locations[event.identifier]].entities.remove(entity)

        del self.entity_dict[event.identifier]

        del self.entity_locations[event.identifier]

        return

class FloorPlanElement:
    """Convenience class for floor plan elements.

       FloorPlanElement.tile = shard.Tile()
       FloorPlanElement.entities = []
    """
    def __init__(self, tile):
        """Initialisation.
        """
        self.tile = tile
        self.entities = []

############################################################
# Rack

class Rack:
    """A Rack stores Entities removed from a room.
       An instance of Rack is used by each CoreEngine.

       Rack.entity_dict
           Maps identifiers to Entities.

       Rack.owner_dict
           Maps item identifiers to owner identifier.
           Each item has exactly one owner.
    """

    def __init__(self):
        """Initialisation.
        """

        # entity_dict maps identifiers
        # to Entities.
        #
        self.entity_dict = {}

        # owner_dict maps item identifiers
        # to owner identifier.
        # Each item has exactly one owner.
        #
        self.owner_dict = {}

        return

    def store(self, entity, owner):
        """Store the Entity in the Rack.

           entity
               A shard.Entity instance

           owner
               Identifier of the Entity that
               issued the PicksUpEvent
        """

        self.entity_dict[entity.identifier] = entity

        self.owner_dict[entity.identifier] = owner

        return

    def items_of(self, identifier):
        """Return a list of Entities owned by identifier.
        """
        item_list = []

        for item in self.owner_dict:

            if self.owner_dict[item] == identifier:

                item_list.append(item)

        return item_list

    def retrieve(self, identifier):
        """Return and remove the Entity identified by identifier.
        """

        entity = self.entity_dict[identifier]

        del self.entity_dict[identifier]

        del self.owner_dict[identifier]

        return entity

############################################################
# Utilities

# Convenience function to compute differences
#
def difference_2d(start_tuple, end_tuple):
    """Return the difference vector between a 2D start and end position.
    """

    return (end_tuple[0] - start_tuple[0],
            end_tuple[1] - start_tuple[1])

def join_lists(first_list, second_list):
    """Returns a list which is made up of the lists given following this scheme:

       >>> join_lists([1, 2], [3, 4])
       [[3, 1], [4, 2]]

       >>> join_lists([1, 2], [[3, 4], 5])
       [[3, 4, 1], [5, 2]]

       >>> join_lists([[1, 2], 3], [[4, 5], 6])
       [[4, 5, 1, 2], [6, 3]]
    """

    if len(first_list) > len(second_list):

        longer_list = first_list
        shorter_list = second_list

    else:

        # second longer or equal
        #
        longer_list = second_list
        shorter_list = first_list

    new_list = []
    index = 0

    while index < len(shorter_list):

        if (isinstance(longer_list[index], list)
            and
            isinstance(shorter_list[index], list)):

            new_list.append(longer_list[index] + shorter_list[index])

        elif (isinstance(longer_list[index], list)
              and
              not isinstance(shorter_list[index], list)):

            new_list.append(longer_list[index] + [shorter_list[index]])

        elif (not isinstance(longer_list[index], list)
              and
              isinstance(shorter_list[index], list)):

            new_list.append([longer_list[index]] + shorter_list[index])

        else:

            new_list.append([longer_list[index], shorter_list[index]])

        index = index + 1

    # now index >= len(shorter_list)
    # Append remaining items
    #
    new_list = new_list + longer_list[index:]

    return new_list

############################################################
# Exceptions

class ShardException():
    """This is the base class of Shard-related exceptions.
       Shard Implementations should raise an instance of this
       class when appropriate, providing an error description.
    """

    def __init__(self, error_description):
        self.error_description = error_description

    def __repr__(self):
        # This is called and should return a
        # string representation which is shown
        return self.error_description
