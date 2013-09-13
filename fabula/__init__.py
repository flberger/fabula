"""Fabula  - An Open Source Python Game Engine

   Copyright 2010 Florian Berger <fberger@florian-berger.de>


   Overview
   --------

   Fabula is a client-server application.

   The server side consists of instances of:

   - fabula.core.server.Server
   - fabula.plugins.Plugin
   - fabula.interfaces.Interface

   The Server manages the authoritative game state and communicates with the
   clients. The Plugin contains the game logic and controls the Server's
   reactions. The Interface manages the communication.

   fabula.plugins.serverside.DefaultGame contains a default Plugin that reads
   from configuration files.

   The client side consists of instances of:

   - fabula.core.client.Client
   - fabula.plugins.ui.UserInterface
   - fabula.interfaces.Interface

   The Client communicates with the server and mirrors the Server game state.
   The UserInterface presents the game to the player and collects player input.
   The Interface manages the communication.

   fabula.plugins.pygameui.PygameUserInterface contains a default 2D UserInterface.


   Connection Procedure
   --------------------

   Before starting Client and Server, you must create one instance of
   fabula.interfaces.Interface for each. Upon creation, these Interfaces are not
   connected.

   Once the Client.run() has been started, it will call
   UserInterface.get_connection_details() to prompt the player for a client id
   and information on how to connect to the Server Interface.

   Given this information, Client.run() will call Interface.connect() which will
   establish the actual network connection to the Server's Interface and add an
   according fabula.interfaces.MessageBuffer in Interface.connections.

   When Interface.connect() returns, Client.run() will send a fabula.InitEvent
   using the client id given by the player. The Server will reply with a series
   of Events that establish the first room.


   Communication
   -------------

   Server and Client communicate by sending Events, each using the MessageBuffer
   instance in Interface.connections.

   Events are bundled into Messages. A Message represents a set of Events that
   happen in parallel.
"""
# "Stories On A Grid"

# TODO: Could use the first sentences of the respective docstrings above (or vice versa).

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

# This file has been started on 19. May 2008, building
# on some drafts done in May 2008.
#
# Transformed into a package on 22. September 2009.

# CODING STYLE
#
# TODO: reasonable package docstring above: what is where :) PEP 257: The docstring for a module should generally list the classes, exceptions and functions (and any other objects) that are exported by the module, with a one-line summary of each.
# TODO: PEP 8: Comparisons to singletons like None should always be done with 'is' or 'is not', never the equality operators.
# TODO: PEP 8: Don't compare boolean values to True or False using ==
# TODO: give the method return value in docstring
# TODO: unify Event attributes target_identifier, trigger_identifier, item_identifier where applicable
# TODO: add a description of what is being done to "called" log messages
#
#
# CLEANUPS
#
# TODO: import fabula.xyz also imports fabula - so get rid of redundant imports
# TODO: Clean up log levels: use debug(), info(), warning(), error(), critical()
# TODO: is the default mirroring policy in Plugin OK? UserInterface also is a Plugin, after all, and it makes no sense here.
# TODO: Entity.entity_type -> Entity.type? Tile.tile_type -> Tile.type?
# TODO: nicer logging. Use the NullLogger and leave logging to the Fabula host. Use named calls to getLogger("somename") and repeat these calls whenever a Fabula logger is needed instead of passing them around.
# TODO: Remove "This method..." from docstrings, and just explain what it does.
#
#
# OPTIMISATION
#
# TODO: don't call base classes for trivial actions. Duplicate, and save calls.
# TODO: string.format() / .join() instead of "%s" % s or "s" + "s" in the whole package!
# TODO: use map() instead of "for" loops where applicable
# TODO: "avoid dots" -> prefetch functions from.long.dotted.operations, especially in loops
# TODO: most prominently: message.event_list.append -> message.append
# TODO: Room.entity_dict.keys() is scanned so often that there should be a fixed list prepared to read from
#
#
# IMPROVEMENTS
#
# TODO: multiple rooms: make anything that parses and emits locations support the (x, y, "room_identifier") syntax, and get rid of location[:2] hacks.
#
# TODO: introduce a client-specific Server timeout when an Event which requires multiple frames has been sent. Possibly send action_time in InitEvent to Server.
# TODO: readable __repr__ of fabula objects: Rack
# TODO: one should be able to evaluate Messages to True and False for if clauses testing if there are any events in the message
# TODO: per-player inventories in server... -.-
# TODO: there is no ConfirmEvent associated with TriesToManipulateEvent
# TODO: There currently is no way Plugins can directly issue Events for other clients (for example PerceptionEvents or EnterRoomEvents)
# TODO: join Tile and FloorPlanElement?
# TODO: Make Events either completely stateful (relying on preceding and following events, e.g. for room information) or stateless (all information required is encoded in the Event).
#
# TODO: support the Tiled editor, http://www.mapeditor.org/, see http://silveiraneto.net/2009/12/19/tiled-tmx-map-loader-for-pygame/
# TODO: HD support (at least 1280x720)
# TODO: real node-based rooms; no more tiles; refactor client to use mouse hit zones around node points
# TODO: abandon tile-based maps, and rather use large bitmap (GIMP XCF) or vector (Inkscape SVG) data for level backgrounds.
# TODO: also, replace tiles by graphs made of polygons, done in an bitmap (GIMP XCF) or vector (Inkscape SVG) overlay.
#
# TODO: JSON file format for all files written (from http://pound-python.org/: "When storing data, use SQLite or JSON")
# TODO: level format should be a list of JSON-encoded Events that establish the room, including fancyness as captions. Provide a tool to convert TSV to this.
#
# TODO: Use conventional names. Call maps maps, tiles tiles.
# TODO: Fabula is not event-based, it is turn-based. Reflect that in method names: next_turn(), or something like that.
#
# TODO: Fabula needs a JSON-API for the server plugin. It also needs methods to access internal data structures like room, position etc.
#
# TODO: The asset manager should be used for finding the fabula.conf file.
#
# TODO: make the current game world abstraction an named application of a more generic Fabula. Get rid of specific handlers in EventProcessor. Instead, register callbacks for each "EVENTNAME" (see above).
# TODO: Make Fabula component-based. Implement independet event handlers, 'ihandle "DropsEvent"', make a handler dict and a handle(Event) method. Strip EventProcessor down to that. Allow for custom events and handlers.
#     TODO: check test case for applicability of component-based design: replacing a method of an Entity
#     TODO: check test case for applicability of component-based design: implementing a new Event type for Entities to react to
#     TODO: check test case for applicability of component-based design: real-time method swaps in the editor
# TODO: Replace Events by ("EVENTNAME", dict). Observe that Events can already be written as URIs: eventprocessor/EVENTNAME?key=value&key=value -> but that is bad GET REST
#
# TODO: all of Fabula except pygameui should work without Pygame installed. Get rid of imports of pygameui in other modules, especially plugins.serverside
#
# TODO: finally - add event to cleanly disconnect a client session, initiated by client or server
# TODO: describe the whole connection-disconnection procedure
# TODO: allow refusal of logins by the server
#
# TODO: demos: pacman, chess
# TODO: rougue-like game, or interface to nethack. See http://www.nethack.org/ http://www.darkarts.co.za/newt http://www.zincland.com/powder/index.php?pagename=about
#
# TODO: support and test Python package managers, as pip, easyinstall etc.
# TODO: makeself binary release for Linux - http://megastep.org/makeself
# TODO: support zeroinstall - http://0install.net/
#
# TODO: The planes and surfacecatcher modules, required by pygameui, are bundled in distributions, but not part of the VCS repository. This leaves repository clones defunct, which should at least be documented.
#
# TODO: Add a skeleton for new fabula games, including default graphics, fabula.conf, planes, attempt_*.png, cancel.png, default.floorplan etc.
# TODO: automatically create file lists for inclusion from level files etc. for distribution
#
# TODO: invisible audio Entites for music
# TODO: implement API to change Entity attributes als blocking, mobile.
#
# TODO: thin clients for performance tests, bug hunting, unit tests. replace client plugin with a player of recorded scripts, for example, similar to replay interface.
# TODO: maybe it's enough to implement a replay interface for client data in the server interface.
#
# TODO: Idee von Prof. Dr. Knut Hartmann: es müsste eine Art Image mitgeschrieben werden, so dass man bei einem Fehler sofort wieder an der (oder kurz vor der) kritischen Stelle einsteigen kann, *ohne* nochmal das ganze Spiel bis dahin durchspielen muss -> ggf. Event-Log dafür benutzen! "post crash logging fast forwarder" :-)
# TODO: extended command line and GUI replay interface. Allow stopping, single or multiple step forward, stopping at step #n, obeying or discarding wait times
#
# TODO: build in in-game questionnaires for research games
#
# TODO: use a single ZIP file for all assets, instead of cluttering the main directory.
#
# TODO: optional login screen with options regarding display resolutions, sound etc.
# TODO: logoff confirmation screen for clients
#
# TODO: in standalone mode, can client and server use the same instances of entities etc.? I.e. use the same Engine instance.
#
# TODO: libGDX user interface, http://libgdx.badlogicgames.com/ : Windows, Linux, Mac OS X, Android, (iOS), Javascript/WebGL (GWT)
# TODO: cross-platform OpenGL- or Irrlicht-based client. Preferably a compiled Python module.
# TODO: HTML4+JS or HTML5 or WebGL browser client.
#
# TODO: the server should sanity check messages returned by the plugin as it does for incoming client messages, e.g. blocked positions
#
# TODO: efficient, packed UDP protocol with bookkeeping.
#
# TODO: fuzzing tool for the Fabula protocol
#
# TODO: client and server logfile gets mixed up when running in threads in one process, as in 'multiple_clients.txt' doctest. Investigage and separate by using different loggers. Fix multiple clients doctest to use threads and print to STDOUT after that.

# Fabula will not work with Python versions prior to 3.x.
#
import sys

if sys.version_info[0] != 3:
    raise Exception("Fabula needs Python 3 to work. Your Python version is: " + sys.version)

import fabula.eventprocessor
import re
import logging
import json
import configparser

############################################################
# Version Information

VERSION = "0.8.4a"

############################################################
# Events

class Event:
    """Fabula event base class.

       Event.identifier
           Must be unique for each object (player, item, NPC)
    """

    def __init__(self, identifier):
        """Event initialisation.
           This constructor must be called with an unique identifier for the
           object (player, item, NPC) which is affected by this event.
        """
        # By defining it here, the variable is
        # part of the instance object, not the
        # class object. See "Class definitions"
        # in the Python Reference Manual.
        #
        self.identifier = identifier

    def __eq__(self, other):
        """Allow the == operator to be used on Events.
           Check if the object given has the same class and the same attributes
           with the same values.
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
           Check if the object given has a different class or the different
           attributes with different values.
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
        """Official string representation suitable to recreate the Event instance.
           The attributes appear in sorted order.
        """

        # Keep order
        #
        keys = list(self.__dict__.keys())
        keys.sort()

        return representation(self, keys)

    def json(self):
        """Return a JSON representation of the Event.
        """

        return json_dump(self)

####################
# Attempt events

class AttemptEvent(Event):
    """This is the base class for attempt events by the player or NPCs.

       AttemptEvent.identifier
           identifier of the object where the attempt originates

       AttemptEvent.target_identifier
           target location of the attempt or item / NPC / player identifier
           if appropriate after server processing
    """

    def __init__(self, identifier, target_identifier):
        """Event initialisation.

           When sent by the client, target_identifier must describe the target
           location of the attempt.

           On a two-dimensional map with rectangular elements target_identifier
           is a tuple of (x, y, "room_identifier"). x and y are integer
           coordinates, with (0, 0) being the upper left corner.

           The server determines what is being looked at / picked up /
           manipulated / talked to at that location, and replaces the location
           string with an item, NPC or player identifier if appropriate.
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

       TriesToDropEvent.identifier
           identifier of the object where the attempt originates

       TriesToDropEvent.item_identifier
           item to be dropped

       TriesToDropEvent.target_identifier
           target location / item to drop on
    """

    # TODO: why are the attributes different from DropsEvent?! Unify all attepmts and confirmations.

    def __init__(self, identifier, item_identifier, target_identifier):
        """Event initialisation.
           An attempt to drop the item identified by item_identifier. When sent
           by the client, target_identifier must describe the desired location.
           On a two-dimensional map with rectangular elements target_identifier
           is a tuple of (x, y) integer coordinates, with (0, 0) being the upper
           left corner.
           Note that this attempt can turn out as a "use" action, for example
           when dropping a key on a padlock. In this case, the server replaces
           the location with an item identifier and passes that on to the story
           engine.
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

       This Event will move any Entity, regardless if the Entity.mobile flag is
       True or not.

       MovesToEvent.identifier
           identifier of the object that moves

       MovesToEvent.location
           A description as in the TriesToMoveEvent
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

       PicksUpEvent.identifier
           identifier of the Entity to pick up the item

       PicksUpEvent.item_identifier
           The item to pick up. This item should be known to the client.
    """

    def __init__(self, identifier, item_identifier):
        """Event initialisation.
           item_identifier identifies the item to pick up. This item should be
           known to the client.
        """
        self.identifier = identifier

        self.item_identifier = item_identifier

class DropsEvent(ConfirmEvent):
    """This is the server confirmation for an attempt to drop an item
       by the player or an NPC.
       This event does normally not occur when the drop action evaluates to a
       "use with" action, as described in TriesToDropEvent. In that case the
       item stays in the posession of its owner, and some other events are
       issued.

       DropsEvent.identifier
           identifier of the Entity to drop the item

       DropsEvent.item_identifier
           The item to be dropped on the map

       DropsEvent.location
           A description as in the TriesToMoveEvent
    """

    def __init__(self, identifier, item_identifier, location):
        """Event initialisation.
           item_identifier identifies the item to be dropped on the map.
           location is a description as in the TriesToMoveEvent.
        """
        self.identifier = identifier

        self.item_identifier = item_identifier

        self.location = location

class CanSpeakEvent(ConfirmEvent):
    """This is a server invitation for the player or an NPC to speak.
       Since this event requires immediate user input, it is always executed as
       the last event of a Message by the UserInterface.

       CanSpeakEvent.identifier
           identifier of the Entity invited to speak

       CanSpeakEvent.sentences
           A list of strings for the player or NPC to choose from.
           Empty for free-form input.
    """

    def __init__(self, identifier, sentences):
        """Event initialisation.
           sentences is a list of strings for the player or NPC to choose from.
           If this list is empty, the client should offer a free-form text input.
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

       PerceptionEvent.identifier
           identifier of the Entity to receive the perception

       PerceptionEvent.perception
           A string to be displayed by the client
    """

    def __init__(self, identifier, perception):
        """Event initialisation.
           perception is a string to be displayed by the client.
           Note: When used with an NPC, this could feed a memory database.
        """
        self.identifier = identifier

        self.perception = perception

class ManipulatesEvent(ConfirmEvent):
    """This is a server confirmation of an item manipulation.
       This Event normally has no visible effect; effects of a ManipulateEvent
       are usually MovesToEvents, ChangeMapElementEvents, SpawnEvents etc. The
       ManipulatesEvent simply confirms that a manipulation has happened.

       ManipulatesEvent.identifier
           identifier of the manipulating Entity

       ManipulatesEvent.item_identifier
           identifier of the item that is being manipulated
    """

    def __init__(self, identifier, item_identifier):
        """Event initialisation.
           item_identifier identifies the item that is being manipulated.
        """
        self.identifier = identifier

        self.item_identifier = item_identifier

####################
# Unclassified events without a special base class

class InitEvent(Event):
    """This event is sent by the client upon startup.
       It asks the server to send the server parameters and anything that is
       needed to update the client to the current game state - usually a number
       of ChangeMapElementEvents and SpawnEvents.
       The client interface may decide to issue this event again in case there
       has been a connection failure.

       InitEvent.identifer
           Client identifier. Must be unique for each client.
    """

    def __init__(self, identifier):
        """identifier must be unique for each client.
        """

        self.identifier = identifier

class ExitEvent(Event):
    """This Event is sent by the Client or the Server to signal that it is about to exit and that no further Events will be sent.

       Attributes:

       ExitEvent.identifer
           Client identifier. Must be unique for each client.
    """

    def __init__(self, identifier):
        """identifier must be unique for each client.
        """

        self.identifier = identifier

        return

class SaysEvent(Event):
    """This normally is a reaction to the CanSpeakEvent, to be sent by the player.
       NPCs can speak spontanously, in that case a SaysEvent is issued by he
       Story Engine. Players usually have to send an TriesToTalkToEvent before
       they are allowed to speak.

       SaysEvent.identifier
           identifier of the speaking Entity

       SaysEvent.text
           A string to be spoken by the entity
    """

    def __init__(self, identifier, text):
        """Event initialisation.
           text is a string to be spoken by the entity.
        """
        self.identifier = identifier

        self.text = text

class ChangePropertyEvent(Event):
    """This Event is issued to trigger a property change.
       Each instance of fabula.Entity has a property.

       ChangePropertyEvent.identifier
           identifier of the Entity to change property

       ChangePropertyEvent.property_key
           A string giving the name of the property.

       ChangePropertyEvent.property_value
           A string giving the value of the property.
    """

    # ChangeProperty is based on the state and ChangeState concept by Alexander Marbach.

    def __init__(self, identifier, property_key, property_value):
        """Event initialisation.
           property is a new property for the Entity identified by identifier.
           property_key and property_value must be strings.
        """
        self.identifier = identifier

        self.property_key = property_key
        self.property_value = property_value

        return

####################
# Passive events

class PassiveEvent(Event):
    """The base class for events when items or NPCs are being passed etc.

       PassiveEvent.identifier
           identifier of the Entity that has been passed etc.

       PassiveEvent.trigger_identifier
           identifier of the the entity that triggered the event
    """

    def __init__(self, identifier, trigger_identifier):
        """Event initialisation.
           The trigger_identifier identifies the entity that triggered the
           event. This makes it possible to react differently to several
           entities.
        """
        self.identifier = identifier

        self.trigger_identifier = trigger_identifier

class PassedEvent(PassiveEvent):
    """Issued by the server when an item or an NPC is being passed by the player or an NPC.
    """
    pass

class LookedAtEvent(PassiveEvent):
    """Issued by the server when an item or NPC is being looked at by the player or an NPC.
    """
    pass

class PickedUpEvent(PassiveEvent):
    """Issued by the server when an item is being picked up by the player or an NPC.
    """
    pass

class DroppedEvent(PassiveEvent):
    """Issued by the server when an item is being dropped by the player or an NPC.
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

       SpawnEvent.entity
           An instance of fabula.Entity

       SpawnEvent.location
           A description as in the TriesToMoveEvent
    """

    # TODO: why no SpawnEvent.identifier, as Event has?

    def __init__(self, entity, location):
        """Event initialisation.

           entity is an instance of fabula.Entity, having a type, identifier and
           asset.

           location is a tuple (x, y, "room_identifier") with x, y being
           2D integer coordinates.

           The server stores the relevant information and passes the entity on
           to the client.
        """
        self.entity = entity
        self.location = location

    def json(self):
        """Return a JSON representation of the SpawnEvent.
        """

        # This Event need special care because it carries an Entity that must be
        # JSON-serialized.

        json_str = '{{"class" : "{}", "entity" : {}, "location" : {}}}'

        # We pipe the whole thing back and forth through json, to get both
        # validation and pretty-printing.
        #
        # See Message.json().
        #
        # Use list() to get JSON-style square brackets for tuples.
        #
        # TODO: Use compact JSON, and indentation only in doctest
        #
        # Remove trailing whitespace
        #
        return "\n".join([line.rstrip() for line in json.dumps(json.loads(json_str.format(self.__class__.__name__,
                                                                                          self.entity.json(),
                                                                                          str(list(self.location)))),
                                                                           sort_keys = True,
                                                                           indent = 4).splitlines()])

class DeleteEvent(ServerEvent):
    """This event deletes an item or NPC from the map.
       Note that items may still persist in the players posessions.
    """
    pass

class EnterRoomEvent(ServerEvent):
    """This event announces that the player enters a new room.
       Events building the map and spawning the player, items and NPCs should
       follow. The room is done and can be used when the server issues
       RoomCompleteEvent.

       EnterRoomEvent.client_identifier
           The identifier of the client that enters the Room.

       EnterRoomEvent.room_identifier
           The identifier of the Room to be entered.
    """

    def __init__(self, client_identifier, room_identifier):
        """Event initialisation.
           client_identifier is the identifier of the client that enters the
           Room.
           room_identifier is the identifier of the Room to be entered.
        """
        self.client_identifier = client_identifier
        self.room_identifier = room_identifier

class RoomCompleteEvent(ServerEvent):
    """Issued by the server after an EnterRoomEvent when the room is populated with a tiles, a player Entity, items and NPCs.
    """

    def __init__(self):
        """This event has no parameters.
        """
        pass

class ChangeMapElementEvent(ServerEvent):
    """This event changes a single element of the two-dimensional map.
       When sent in a Message, these events are executed immediately and in
       parallel upon the rendering of the Message by the UserInterface.

       ChangeMapElementEvent.tile
           An instance of fabula.Tile

       ChangeMapElementEvent.location
           A description as in the TriesToMoveEvent
    """

    def __init__(self, tile, location):
        """Event initialisation.
           tile is a fabula map object having a type (obstacle or floor) and an
           asset.
           location is an object describing the location of the tile in the game
           world, most probably a tuple of coordinates and room identifier, but
           possibly only a string like "lobby".
           The server stores the relevant information and passes the tile and
           the location on to the client.
        """
        self.tile = tile

        self.location = location

        return

    def json(self):
        """Return a JSON representation of the ChangeMapElementEvent.
        """

        # This Event need special care because it carries a Tile that must be
        # JSON-serialized.

        # TODO: Copied from SpawnEven.json(). Maybe replace by a joining approach.

        json_str = '{{"class" : "{}", "tile" : {}, "location" : {}}}'

        # We pipe the whole thing back and forth through json, to get both
        # validation and pretty-printing.
        #
        # See Message.json().
        #
        # Use list() to get JSON-style square brackets for tuples.
        #
        # TODO: Use compact JSON, and indentation only in doctest
        #
        # Remove trailing whitespace
        #
        return "\n".join([line.rstrip() for line in json.dumps(json.loads(json_str.format(self.__class__.__name__,
                                                                                          self.tile.json(),
                                                                                          str(list(self.location)))),
                                                                          sort_keys = True,
                                                                          indent = 4).splitlines()])

class ServerParametersEvent(ServerEvent):
    """This Event is sent by the Server when an InitEvent has been received.
       It informs the client about the Server parameters.

       Attributes:

       ServerParametersEvent.client_identifier
           The client identifier to receive this Event.
           This attribute is mainly for bookkeeping purposes in the Server.

       ServerParametersEvent.action_time
           The time the Server waits between actions that do not happen instantly.
    """

    def __init__(self, client_identifier, action_time):
        """action_time is the time the Server waits between actions that do not happen instantly.
        """

        self.client_identifier = client_identifier

        self.action_time = action_time

        return

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

############################################################
# Message

class Message:
    """A Message represents a set of Events that happen in parallel.

       Attributes:

       Message.event_list
           A list of fabula.Events
    """

    def __init__(self, event_list):
        """Initialise the Message with a list of objects derived from fabula.Event.
           An empty list may be supplied.
        """

        if not isinstance(event_list, list):

            raise TypeError("argument event_list must be a list")

        # TODO: check the list elements for being instances of fabula.Event here? But then, to be consistent, we would have to implement a method to add Events which checks them as well.
        #
        self.event_list = event_list

    def __repr__(self):
        """Official string representation.
        """

        return representation(self, ("event_list",))

    def json(self):
        """Return a JSON representation of the Message.
        """

        json_str = '{{"Message": [{}]}}'.format(",".join([event.json() for event in self.event_list]))

        # We pipe the whole thing back and forth through json, to get both
        # validation and pretty-printing.
        #
        # Taken from pycms.CMS.json().
        #
        # Remove trailing whitespace
        #
        return "\n".join([line.rstrip() for line in json.dumps(json.loads(json_str), sort_keys = True, indent = 4).splitlines()])

############################################################
# Asset Entry

# Using this explicit definition instead of a tuple for readability and
# documentation.

class Asset:
    """A single asset entry.

       Attributes:

       Asset.uri
           An URI string as per [RFC 2396](https://tools.ietf.org/html/rfc2396),
           or a local filesystem path suitable to pass to open().

       Asset.data
           The asset's data. Initially None, replaced by implementation-dependet
           data when the UserInterface retrieves the asset.
    """

    def __init__(self, uri, data = None):
        """Initialise.
        """

        self.uri = uri

        self.data = data

        return

    def __repr__(self):
        """Official string representation.
        """

        return representation(self, ("uri", "data"))

    def __str__(self):
        """Informal string representation.
        """

        return "<Asset {} at {}>".format(self.__repr__(),
                                         id(self))

    def json(self):
        """Return a JSON representation of the Asset.
        """

        return json_dump(self)

    def serialisable(self):
        """Return a serialisable representation for JSON encoding.
        """

        return {"uri": self.uri, "data": self.data}

############################################################
# Entities

class Entity(fabula.eventprocessor.EventProcessor):
    """An Entity is a Fabula game object.
       This is the base class for the player, NPCs and items.
       An Entity holds information used by the Fabula game logic:

       Entity.identifier
           Must be an object whose string representation yields an unique
           identification.

       Entity.entity_type
           One of fabula.PLAYER, fabula.NPC or fabula.ITEM.

       Entity.blocking
           Boolean flag, indicating whether the Entity blocks a location for
           other Entities.

       Entity.mobile
           Boolean flag. If True, the Entity can be picked up and dropped and
           will be able to move.

       Entity.assets
           A dict, mapping strings denoting content types as per
           [RFC 2045](https://tools.ietf.org/html/rfc2045) to Asset instances.

       Entity.property_dict
           A dict mapping strings to strings, holding the application-dependent
           properties of the Entity.

       Entity.user_interface
           Pointer to the UserInterface instance. Will be filled by the
           UserInterface at runtime


       A Fabula Client should use subclasses (possibly with multiple inheritance)
       or custom attachements to instances of this class to implement the game
       objects used by the rendering engine (2D sprites, 3D models). Usually the
       Client manages a list of Entity instances. Everything concernig the
       actual graphical representation is done by the UserInterface. Since this
       is very application dependent it is not covered in the base class. Check
       the documentation and source of the UserInterface for further insight on
       how it handles game objects.
    """

    def __init__(self, identifier, entity_type, blocking, mobile, assets):
        """Initialise.

           assets is a dict to initialise Entity.asset with. It is advised
           to supply a text/plain entry such as
           {"text/plain" : Asset(None, "Entity description")}
        """

        fabula.eventprocessor.EventProcessor.__init__(self)

        # Now we have:
        # self.event_dict
        # which maps Event classes to handler methods

        self.identifier = identifier
        self.entity_type = entity_type
        self.blocking = blocking
        self.mobile = mobile
        self.assets = dict(assets)

        self.property_dict = {}

        # Will be filled by the UserInterface at runtime.
        #
        self.user_interface = None

    # EventProcessor overrides
    #
    # These are called by the UserInterface, which also has added the
    # Entity.framerate and Entity.action_frames attributes

    def process_MovesToEvent(self, event):
        """This method is called by the UserInterface.
           The Entity representation has to execute the according action over
           the course of Entity.action_frames frames. But it must du so in an
           non-blocking fashion - this method must return as soon as possible.
           So do set up counters or frame queues here. Your implementation may
           call another method once per frame, do the actual work there.
        """
        pass

    def process_ChangePropertyEvent(self, event):
        """This method is called by the UserInterface.
           The key 'event.property_key' in Entity.property_dict is set to event.property_value.
        """

        self.property_dict[event.property_key] = event.property_value

        return

    def process_DropsEvent(self, event):
        """This method is called by the UserInterface.
           The Entity representation has to execute the according action over
           the course of Entity.action_frames frames. But it must du so in an
           non-blocking fashion - this method must return as soon as possible.
           So do set up counters or frame queues here. Your implementation may
           call another method once per frame, do the actual work there.
        """
        pass

    def process_PicksUpEvent(self, event):
        """This method is called by the UserInterface.
           The Entity representation has to execute the according action over
           the course of Entity.action_frames frames. But it must du so in an
           non-blocking fashion - this method must return as soon as possible.
           So do set up counters or frame queues here. Your implementation may
           call another method once per frame, do the actual work there.
        """
        pass

    def process_SaysEvent(self, event):
        """This method is called by the UserInterface.
           The Entity representation has to execute the according action over
           the course of Entity.action_frames frames. But it must du so in an
           non-blocking fashion - this method must return as soon as possible.
           So do set up counters or frame queues here. Your implementation may
           call another method once per frame, do the actual work there.
        """
        pass

    def clone(self):
        """Return a new fabula.Entity instance, derived from this Entity.
           Useful to create an Entity object from a subclass of Entity.
        """

        return Entity(self.identifier,
                      self.entity_type,
                      self.blocking,
                      self.mobile,
                      self.assets)

    def __repr__(self):
        """Official string representation.
        """

        return representation(self, ("identifier",
                                     "entity_type",
                                     "blocking",
                                     "mobile",
                                     "assets"))

    def __str__(self):
        """Informal string representation, including property_dict and asset.
        """
        return "<{} property_dict = {}>".format(self.__repr__(),
                                                self.property_dict)

    def json(self):
        """Return a JSON representation of the Entity.
        """

        json_dict = {"class" : self.__class__.__name__}

        # Using attribute list from Entity.__repr__()
        #
        for attribute in ("identifier",
                          "entity_type",
                          "blocking",
                          "mobile",
                          "assets"):

            json_dict[attribute] = self.__dict__[attribute]

        # TODO: Use compact JSON, and indentation only in doctest

        # From the Python documentation example "Extending JSONEncoder"
        #
        class AssetEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, fabula.Asset):
                    return obj.serialisable()
                return json.JSONEncoder.default(self, obj)

        # Remove trailing whitespace
        #
        return "\n".join([line.rstrip() for line in json.dumps(json_dict, sort_keys = True, indent = 4, cls = AssetEncoder).splitlines()])

############################################################
# Entity And Tile Types

# Currently values are strings, but they are subject
# to change without notice.

PLAYER = "PLAYER"
NPC = "NPC"
ITEM = "ITEM"

FLOOR = "FLOOR"
OBSTACLE = "OBSTACLE"

# For __repr__() methods
#
_constant_representations = {PLAYER : "fabula.PLAYER",
                             NPC : "fabula.NPC",
                             ITEM : "fabula.ITEM",
                             FLOOR : "fabula.FLOOR",
                             OBSTACLE : "fabula.OBSTACLE"}

############################################################
# Tiles

class Tile:
    """A Tile is an element of a two-dimensional map.
       It is never meant to perform any active logic, so its only property is a
       type and an asset.

       Tile.tile_type
           fabula.FLOOR or fabula.OBSTACLE

       Tile.assets
           A dict, mapping strings denoting content types as per
           [RFC 2045](https://tools.ietf.org/html/rfc2045) to Asset instances.
    """

    def __init__(self, tile_type, assets):
        """Tile initialisation.
           tile_type must be fabula.FLOOR or fabula.OBSTACLE, describing whether
           the player or NPCs can move across the tile.
           asset is preferably a string with a file name or an URI of a media
           file containing the data for visualizing the tile.
        """
        self.tile_type = tile_type
        self.assets = dict(assets)

    def __eq__(self, other):
        """Allow the == operator to be used on Tiles.
           Check if the object given has the same class, the same tile_type and
           the same asset_desc.
        """

        if other.__class__ == self.__class__:

            if (other.tile_type == self.tile_type
                and other.assets == self.assets):

                return True

            else:
                return False

        else:
            return False

    def __ne__(self, other):
        """Allow the != operator to be used on Tiles.
           Check if the object given has a different class or a different
           tile_type or different asset_desc.
        """

        if other.__class__ == self.__class__:

            if (other.tile_type != self.tile_type
                or other.assets != self.assets):

                return True

            else:
                return False

        else:
            return True

    def __repr__(self):
        """Official string representation.
        """

        return representation(self, ("tile_type", "assets"))

    def __str__(self):
        """Informal string representation, including the asset.
        """

        return "<{}>".format(self.__repr__())

    def json(self):
        """Return a JSON representation of the Tile.
        """

        # NOTE: Copied from Entity.json().

        json_dict = {"class" : self.__class__.__name__}

        for attribute in ("tile_type",
                          "assets"):

            json_dict[attribute] = self.__dict__[attribute]

        # TODO: Use compact JSON, and indentation only in doctest

        # From the Python documentation example "Extending JSONEncoder"
        #
        class AssetEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, fabula.Asset):
                    return obj.serialisable()
                return json.JSONEncoder.default(self, obj)

        # Remove trailing whitespace
        #
        return "\n".join([line.rstrip() for line in json.dumps(json_dict, sort_keys = True, indent = 4, cls = AssetEncoder).splitlines()])

############################################################
# Rooms

class Room(fabula.eventprocessor.EventProcessor):
    """A Room instance saves the map as well as Entities and their locations.
       It is maintained for the current room in the Client
       and for all active rooms in the Server.

       Room.identifier
           Must be an object whose string representation yields an unique
           identification.

       Room.entity_dict
           A dict of all Entities in this room, mapping Entity identifiers to
           Entity instances.

       Room.floor_plan
           A dict mapping (x, y) 2D coordinate tuples to a FloorPlanElement instance.

       Room.entity_locations
           A dict mapping Entity identifiers to a 2D coordinate tuple.

       Room.tile_list
           A list of tiles for the current room, for easy asset fetching.

       Room.active_clients
           A dict mapping connectors from Interface.connections.keys() to the
           respective client identifier. Dict elements represent the clients who
           are currently in this room.

       Note that these dicts assume that Entity identifiers are unique.
    """

    def __init__(self, identifier):
        """Initialise a room.
           identifier must be an object whose string representation yields an
           unique identification.
        """

        fabula.eventprocessor.EventProcessor.__init__(self)

        # Now we have:
        # self.event_dict
        # mapping Event classes to handler methods though we do not need it
        # since all methods of this class are called from the outside.

        self.identifier = identifier

        # floor_plan is an attempt of an efficient storage of an arbitrary
        # two-dimensional map. To save space, only explicitly defined elements
        # are stored. This is done in a dict whose keys are tuples. Access the
        # elements using floor_plan[(x, y)]. The upper left element is
        # floor_plan[(0, 0)].
        #
        self.floor_plan = {}

        self.tile_list = []

        self.entity_dict = {}
        self.entity_locations = {}

        self.active_clients = {}

        return

    def process_ChangeMapElementEvent(self, event):
        """Update all affected dicts.

           This method assumes that event.location is (x, y, "room_identifier").
        """

        if event.location[:2] in self.floor_plan:

            self.floor_plan[event.location[:2]].tile = event.tile

        else:

            self.floor_plan[event.location[:2]] = FloorPlanElement(event.tile)

        # Avoid duplicates
        #
        if event.tile not in self.tile_list:

            self.tile_list.append(event.tile)

        return

    def process_SpawnEvent(self, event):
        """Update all affected dicts.

           This method assumes that event.location is (x, y, "room_identifier").
        """

        if event.location[:2] not in self.floor_plan:

            msg = "cannot spawn entity '{}' at undefined location {}"

            raise Exception(msg.format(event.entity.identifier,
                                       event.location))

        if event.entity.identifier in self.entity_dict:

            # This is no error, so no exception is raised.
            #
            msg = "Entity '{}', to be spawned at {}, already exists in room '{}': {}"

            fabula.LOGGER.warning(msg.format(event.entity.identifier,
                                             event.location,
                                             self.identifier,
                                             self.entity_locations))

        else:
            self.floor_plan[event.location[:2]].entities.append(event.entity)

            self.entity_dict[event.entity.identifier] = event.entity

            self.entity_locations[event.entity.identifier] = event.location[:2]

        return

    def process_MovesToEvent(self, event):
        """Update all affected dicts.
        """

        if event.identifier not in self.entity_dict:

            raise RuntimeError("cannot move unknown entity {}".format(event.identifier))

        if event.location[:2] not in self.floor_plan:

            raise RuntimeError("cannot move entity {} to undefined location {}".format(event.identifier, event.location))

        # Only process changed locations
        #
        if self.entity_locations[event.identifier] != event.location[:2]:

            # Remove old entity location
            #
            # identifier should point to the same object that is in the
            # respective FloorPlanElement list
            #
            entity = self.entity_dict[event.identifier]
            location = self.entity_locations[event.identifier]

            self.floor_plan[location].entities.remove(entity)

            # (Over)write new entity location
            #
            self.floor_plan[event.location[:2]].entities.append(entity)

            self.entity_locations[event.identifier] = event.location[:2]

        return

    def process_DeleteEvent(self, event):
        """Update all affected dicts.
        """

        try:
            entity = self.entity_dict[event.identifier]

            self.floor_plan[self.entity_locations[event.identifier]].entities.remove(entity)

            del self.entity_dict[event.identifier]

            del self.entity_locations[event.identifier]

        except KeyError:

            # Since the Entity is to be deleted anyway, we do not raise an
            # exception
            #
            fabula.LOGGER.warning("could not delete Entity '{}': Entity does not exist".format(event.identifier))

        return

    def tile_is_walkable(self, target_identifier):
        """Auxiliary method which returns True if the tile exists in Room and can be accessed by Entities.
        """

        if len(target_identifier) == 3:

            if target_identifier[2] != self.identifier:

                msg = "{} not walkable: not in Room '{}'"

                fabula.LOGGER.debug(msg.format(target_identifier,
                                               self.identifier))

                return False

            else:
                target_identifier = target_identifier[:2]

        if target_identifier not in self.floor_plan.keys():

            fabula.LOGGER.debug("{} not walkable: not in floor_plan".format(target_identifier))

            return False

        else:
            floor_plan_element = self.floor_plan[target_identifier]

            if floor_plan_element.tile.tile_type != fabula.FLOOR:

                fabula.LOGGER.debug("{} not walkable: target tile_type != fabula.FLOOR".format(target_identifier))

                return False

            else:
                occupied = False

                for entity in floor_plan_element.entities:

                    if entity.blocking:

                        occupied = True

                if occupied:

                    fabula.LOGGER.debug("{} not walkable: target occupied by blocking Entity".format(target_identifier))

                    return False

                else:

                    return True

    def __repr__(self):
        """Official string representation.
        """

        return representation(self, ("identifier",))

    def __str__(self):
        """Inofficial, informative string representation.
        """

        msg = "<Room '{}', {} Entities, {} FloorPlanElements, active_clients: {}>"

        return(msg.format(self.identifier,
                          len(self.entity_dict),
                          len(self.floor_plan),
                          list(self.active_clients.values())))

class FloorPlanElement:
    """Convenience class for floor plan elements.

       FloorPlanElement.tile
           = fabula.Tile()

       FloorPlanElement.entities
           = []
    """

    def __init__(self, tile):
        """Initialisation.
        """
        self.tile = tile
        self.entities = []

    def __repr__(self):
        """Readable and informative string representation.
        """

        return representation(self, ("tile",))

############################################################
# Rack

class Rack:
    """A Rack stores Entities removed from a room.
       An instance of Rack is used by each Engine.

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
               A fabula.Entity instance

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

        # TODO: Is it more useful to return a list of identifiers instead?

        item_list = []

        for item_identifier in self.owner_dict.keys():

            if self.owner_dict[item_identifier] == identifier:

                # Append the Entity
                #
                item_list.append(self.entity_dict[item_identifier])

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

def difference_2d(start_tuple, end_tuple):
    """Return the difference vector between a 2D start and end position.
    """

    return (end_tuple[0] - start_tuple[0],
            end_tuple[1] - start_tuple[1])

def str_is_tuple(str):
    """Return True if the string represents a (int, int[, str]) location tuple.
    """

    if re.match("^\(\d+\s*,\s*\d+(,\s*[\"'].+?[\"'])?\)$", str):

        return True

    else:
        return False

def representation(object, attributes):
    """Compute an official string representation of object. eval(representation(object)) should recreate the object.
       attributes is a list of strings giving the attributes to include.
    """

    arguments = []
    value = None

    for key in attributes:

        try:
            if object.__dict__[key] in _constant_representations.keys():

                value = _constant_representations[object.__dict__[key]]

            else:
                value = repr(object.__dict__[key])

        except TypeError:

            # Most likely an "unhashable type". Well, then, forget it.
            #
            value = repr(object.__dict__[key])

        arguments.append("{0} = {1}".format(key, value))

    arguments = ", ".join(arguments)

    return "{}.{}({})".format(object.__module__,
                              object.__class__.__name__,
                              arguments)

def json_dump(object):
    """Return a JSON representation of the object.
    """

    instance_dict = object.__dict__.copy()

    instance_dict["class"] = object.__class__.__name__

    # TODO: Use compact JSON, and indentation only in doctest
    # Remove trailing whitespace
    #
    return "\n".join([line.rstrip() for line in json.dumps(instance_dict, sort_keys = True, indent = 4).splitlines()])

def surrounding_positions(position):
    """Return a list of tuples, representing the 8 surrounding positions around the tuple given.
       The list starts with the top left position and proceeds clockwise.
    """

    # Start at top left and proceed clockwise
    #
    return [(position[0] - 1, position[1] - 1),
            (position[0], position[1] - 1),
            (position[0] + 1, position[1] - 1),
            (position[0] + 1, position[1]),
            (position[0] + 1, position[1] + 1),
            (position[0], position[1] + 1),
            (position[0] - 1, position[1] + 1),
            (position[0] - 1, position[1])]

############################################################
# Logging

# Create the logger for the whole Fabula package
#
LOGGER = logging.getLogger("fabula")

# All setup will be done in fabula.run.

# Done with logging setup.

############################################################
# Config

# Initialise parser and read config file
#
CONFIGPARSER = configparser.ConfigParser()

if not len(CONFIGPARSER.read("fabula.conf")):

    CONFIGPARSER = None
