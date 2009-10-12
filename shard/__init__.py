"""Shard - A Client-Server System for Interactive 
   Storytelling by means of an Adventure Game Environment

   "Stories On A Grid"

   (c) Florian Berger <fberger@fbmd.de>
"""

# This file has been started on 19. May 2008, building
# on some drafts done in May 2008.
#
# Transformed into a package on 22. September 2009.

# TODO: reasonable package docstring above: what is where :)
# TODO: "%s" % s instead of "s" + "s" in the whole package!
# TODO: use map() instead of "for" loops

############################################################
# Events

class Event:
    """Shard event base class.
    """

    def __init__(self, identifier):
        """This constructor must be called with
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

####################
# Attempt events

class AttemptEvent(Event):
    """This is the base class for attempt events
       by the player or NPCs.
    """

    def __init__(self, identifier, target_identifier):
        """When sent by the client, target_identifier
           must describe the desired direction of
           the attempt.
           On a two-dimensional map with rectangular
           elements target_identifier may be one 
           of "N", "NE", "E", "SE", "S", "SW", "W", "NW".
           The server determines what is being 
           looked at / picked up / manipulated / 
           talked to in that direction, and 
           replaces the direction string with an item, 
           NPC or player identifier if appropriate.
        """
        self.identifier = identifier

        self.target_identifier = target_identifier

class TriesToMoveEvent(AttemptEvent):
    """Issued when the player or an NPC wants to move, 
       awaiting server confirmation.
    """
    pass

class TriesToLookAtEvent(AttemptEvent):
    """Issued when the player or an NPC looks at a map 
       element or an item
    """
    pass

class TriesToPickUpEvent(AttemptEvent):
    """Issued when the player or an NPC tries to pick up
       an item. Attempts to pick up NPCs are discarded 
       or answered with an error.
    """
    pass

class TriesToDropEvent(AttemptEvent):
    """The player or NPC tries to drop an item.
    """

    def __init__(self, identifier, item_identifier, target_identifier):
        """An attempt to drop the item identified by
           item_identifier. When sent by the client, 
           target_identifier must describe the 
           desired direction.
           On a two-dimensional map with rectangular
           elements target_identifier may be one of 
           "N", "NE", "E", "SE", "S", "SW", "W", "NW".
           Note that this attempt can turn out as a
           "use" action, for example when dropping
           a key on a padlock. In this case, the
           server replaces the direction with an item 
           identifier and passes that on to the
           story engine.
        """
        self.identifier = identifier

        self.item_identifier = item_identifier

        self.target_identifier = target_identifier

class TriesToManipulateEvent(AttemptEvent):
    """Issued when the player or an NPC tries to
       manipulate an item. NPCs cannot be manipulated.
    """
    pass

class TriesToTalkToEvent(AttemptEvent):
    """Issued when the player or an NPC wants to start 
       a conversation with another entity.
       It is not possible to talk to items.
    """
    pass

####################
# Confirm events

class ConfirmEvent(Event):
    """This is the base class for server confirmations
       of attempt events.
    """
    pass

class MovesToEvent(ConfirmEvent):
    """This is the server confirmation of a movement.
    """

    def __init__(self, identifier, direction):
        """direction is a description as in
           the TriesToMoveEvent.
        """
        self.identifier = identifier

        self.direction = direction

class PicksUpEvent(ConfirmEvent):
    """This is a server confirmation of a
       TriesToPickUpEvent issued by the player
       or an NPC.
    """

    def __init__(self, identifier, item_identifier):
        """item_identifier identifies the item to
           pick up. This item should be known to
           the client.
        """
        self.identifier = identifier

        self.item_identifier = item_identifier

class DropsEvent(ConfirmEvent):
    """This is the server confirmation for an
       attempt to drop an item by the player
       or an NPC.
       This event does normally not occur when the
       drop action evaluates to a "use with" action, 
       as described in TriesToDropEvent. In that case
       the item stays in the posession of its owner, 
       and some other events are issued.
    """

    def __init__(self, identifier, item_identifier, direction):
        """item_identifier identifies the item to be 
           dropped on the map. direction is a 
           description as in the TriesToMoveEvent.
        """
        self.identifier = identifier

        self.item_identifier = item_identifier

        self.direction = direction

class CanSpeakEvent(ConfirmEvent):
    """This is a server invitation for the player or
       an NPC to speak. Since this event requires
       immediate user input, it is always executed
       as the last event of a Message by the 
       PresentationEngine.
    """

    def __init__(self, identifier, sentences):
        """sentences is a list of strings for the
           player or NPC to choose from. If this list
           is empty, the client should offer a free-form
           text input.
        """
        self.identifier = identifier

        self.sentences = sentences

class AttemptFailedEvent(ConfirmEvent):
    """This is actually not a confirmation, but the
       server announcement that the last AttemptEvent
       sent by the entity identified by identifier
       failed. This should unblock the entity and
       allow new attempts.
    """
    pass

class PerceptionEvent(ConfirmEvent):
    """This is a perception for the player or an NPC
       issued by the server, usually the result of 
       a TriesToLookAtEvent. Note that a PerceptionEvent
       may be issued by the server without any previous
       attempts by the Entity affected.
    """

    def __init__(self, identifier, perception):
        """perception is a string to be displayed
           by the client. Note: When used with an NPC,
           this could feed a memory database.
        """
        self.identifier = identifier

        self.perception = perception

####################
# Unclassified events without a special base class

class SaysEvent(Event):
    """This normally is a reaction to the CanSpeakEvent, 
       to be sent by the player. NPCs can speak spontanously, 
       in that case a SaysEvent is issued by he Story 
       Engine. Players usually have to send an 
       TriesToTalkToEvent before they are allowed to
       speak.
    """

    def __init__(self, identifier, text):
        """text is a string to be spoken by the entity.
        """
        self.identifier = identifier

        self.text = text

class ChangeStateEvent(Event):
    """Each instance of shard.Entity has a state.
       This Event is issued to trigger a state
       change.
    """

    # ChangeState is based on a concept by Alexander Marbach.

    def __init__(self, identifier, state):
        """state is the new state for the Entity
           identified by identifier. In the simplest
           case state may be a number or a verbose
           string.
        """
        self.identifier = identifier

        self.state = state

####################
# Passive events

class PassiveEvent(Event):
    """The base class for events concerning items
       ot NPCs when they are being passed, looked at, 
       picked up and the like.
    """

    def __init__(self, identifier, trigger_identifier):
        """The trigger_identifier identifies the
           entity that triggered the event. This makes it
           possible to react differently to several
           entities.
        """
        self.identifier = identifier

        self.trigger_identifier = trigger_identifier

class PassedEvent(PassiveEvent):
    """Issued by the server when an item or an NPC is
       being passed by the player or an NPC.
    """
    pass

class LookedAtEvent(PassiveEvent):
    """Issued by the server when an item or NPC is
       being looked at by the player or an NPC.
    """
    pass

class PickedUpEvent(PassiveEvent):
    """Issued by the server when an item is being
       picked up by the player or an NPC.
    """
    pass

class DroppedEvent(PassiveEvent):
    """Issued by the server when an item is being
       dropped by the player or an NPC.
    """
    pass

####################
# Server events

class ServerEvent(Event):
    """Base class for various events issued by the
       server that are no ConfirmEvents, including
       map and room events.
    """
    pass

class SpawnEvent(ServerEvent):
    """This event creates the player / new item / NPC on the map.
    """

    def __init__(self, entity):
        """Entity is an instance of shard.Entity, 
           having a type, identifier, location and
           assets. The server stores the relevant
           information and passes the entity on to
           the client.
        """
        self.entity = entity

class DeleteEvent(ServerEvent):
    """This event deletes an item or NPC from the map.
       Note that items may still persist in the players
       posessions.
    """
    pass

class EnterRoomEvent(ServerEvent):
    """This event announces that the player enters a new
       room. Events building the map and spawning the
       player, items and NPCs should follow. The room 
       is done and can be used when the server issues 
       RoomCompleteEvent.
    """

    def __init__(self):
        """This event has no parameters.
        """
        pass

class RoomCompleteEvent(ServerEvent):
    """Issued by the server after an EnterRoomEvent when
       the room is populated with a map, items and NPCs.
    """

    def __init__(self):
        """This event has no parameters.
        """
        pass

class ChangeMapElementEvent(ServerEvent):
    """This event changes a single element of the 
       two-dimensional map. When sent in a Message, 
       these events are executed immediately and
       in parallel upon the rendering of the
       Message by the PresentationEngine.
    """
    
    def __init__(self, tile, location):
        """tile is a shard map object having a type 
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
       expose a single Python list object as Message.event_list."""

    def __init__(self, event_list):
        """Initialize the Message with a list of objects
           derived from shard.Event. An empty list may
           be supplied."""
        #CHECKME: check the list elements for being
        #         instances of shard.Event here?
        self.event_list = event_list

#    def queueAsFirstEvent(self, event):
#        """This is a convenience method. Queue the event 
#           given as the first event to be processed, 
#           shifting other events already queued."""
#        self.event_list = [event] + self.event_list

############################################################
# Entities

class Entity:
    """An Entity is a Shard game object. This is the base
       class for the player, NPCs and items. An Entity
       holds information used by the Shard game logic.
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
       handles game objects."""

    def __init__(self, entity_type, identifier, location, asset):
        """You are welcome to override this method, but
           be sure to call setup() as done by the default
           implementation of this method.
        """

        self.setup(entity_type, identifier, location, asset)

    def setup(self, entity_type, identifier, location, asset):
        """entity_type is one of the strings "PLAYER", "NPC", 
           "ITEM".

           identifier must be an object whose string 
           representation yields an unique 
           identification.

           location is an object describing the
           location of the Entity in the game world, 
           most probably a tuple of coordinates, but
           possibly only a string like "lobby". The
           location should not be too precise when
           using coordinates, since it is not
           incremented during movement. It should
           rather store where the entity will be
           once the next movement is complete.

           asset is preferably a string
           with a file name or an URI of a media
           file containing the data for visualizing
           the Entity. Do not put large objects here
           since Entities are pushed around quite a
           bit and transfered across the network.
           The PresentationEngine may fetch the asset and
           attach it to the instance of the Entity.

           logger finally is an instance of logging.Logger.
        """

        self.entity_type = entity_type
        self.identifier = identifier
        self.location = location
        self.asset = asset

        # Store current direction and movement
        # "At dawn, look to the east." -Gandalf 
        #        in Peter Jackson's "Two Towers"
        #
        self.direction = 'E'
        self.moves = False

        # Other flags for Entity actions
        #
        self.speaks = False
        self.picks_up = False
        self.drops = False

    # TODO:
    # Entities should be notified about all attempts
    # or actions to be able to display an according
    # image or animation:
    # lookAt, 
    # Manipulate, 
    # They also need to know the direction (to turn
    # in the right one).
    # AttemptFailed should also be passed to the
    # Entity so it can switch to a neutral image.

    def process_MovesToEvent(self, event):
        """The MovesToEvent is supplied to the
           Entity so it can update its location.
           The rationale behind this is that
           the ClientCoreEngine can be entirely
           agnostic about the type of world
           and location (text, 2D, 3D).
           A call to this method does not mean
           that the PresentationEngine has started
           the movement. This is rather called
           by the ClientCoreEngine to signal
           where the Entity is about to move.
           See the other methods of this class."""

        # In a contract-like design, we should
        # check preconditions like
        # isinstance(Event, MovesToEvent)
        # or len(self.location) == 2.
        
        # EXAMPLE
        #
        # Store the movement, maybe for 
        # animation purposes
        #
        self.direction = event.direction

        # We use shard.DIRECTION_VECTOR which maps
        # direction strings like "NW", "SE" to
        # a 2D vector tuple

        new_x = (self.location[0]
                 + DIRECTION_VECTOR[event.direction][0])

        new_y = (self.location[1]
                 + DIRECTION_VECTOR[event.direction][1])

        self.location = (new_x, new_y)

    def change_state(self, state, frames=None, framerate=None):
        """Called when the state of the Entity is
           changed from outside.
           The PresentationEngine is responsible for the
           gradual movement of the Entity to the
           target, the display of text spoken 
           by the Entity, making picked up objects
           disappear and appear in the inventory, 
           but not for any Entity animation.
           Instead, the PresentationEngine will
           call this method with the following states:
           "MOVING"
           "SPEAKING"
           "PICKING_UP"
           "DROPPING"
           to signal that the Entity starts the action
           now. Entities may implement a flag or some
           logic which changes their graphical 
           representation on every frame, yielding
           an animation.
           process_ChangeStateEvent() is always
           called after process_MovesToEvent() etc.,
           so the Entity already knows about the result
           of the action.
           The PresentationEngine may provide the number
           of frames for the movement and the framerate.
           Thus the entity can adapt to different
           frame rates by adjusting how many frames
           an image is shown. The Entity is advised
           to stop the animation once the number
           of frames given has passed, but it does
           not need to do so.
           The default implementation sets Entity.state
           to the state given.
        """

        # ChangeState is based on a concept by Alexander Marbach.

        self.state = state

############################################################
# Tiles

class Tile:
    """A Tile is an element of a two-dimensional map.
       It is never meant to perform any active logic, 
       so its only property is a type and an asset."""

    def __init__(self, tile_type, asset):
        """tile_type must be a string describing the tile
           type. Currently supported are "OBSTACLE"
           and "FLOOR", describing whether the player
           or NPCs can move across the tile.
           
           asset is preferably a string with a file 
           name or an URI of a media file containing 
           the data for visualizing the tile."""
        self.tile_type = tile_type
        self.asset = asset

############################################################
# Utilities

# Set up a DIRECTION_VECTOR for 2D movement
# processing. It is assumed that (0, 0) is
# the upper left corner
#
DIRECTION_VECTOR = {'N' : (0, -1),
                    'NE' : (1, -1),
                    'E' : (1, 0),
                    'SE' : (1, 1),
                    'S' : (0, 1),
                    'SW' : (-1, 1),
                    'W' : (-1, 0),
                    'NW' : (-1, -1)
                   }

############################################################
# Exceptions

class ShardException():
    """This is the base class of Shard-related
       exceptions. Shard Implementations should
       raise an instance of this class when 
       appropriate, providing an error description."""

    def __init__(self, error_description):
        self.error_description = error_description

    def __repr__(self):
        # This is called and should return a
        # string representation which is shown
        return self.error_description
