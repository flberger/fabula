'''Shard - A Client-Server System for Interactive 
   Storytelling by means of an Adventure Game Environment

   "Stories On A Grid"

   (c) Florian Berger <fberger@fbmd.de>

   This file has been started on 19. May 2008, building
   on some drafts done in May 2008.

   This Python module contains all the classes used
   by Shard. It provides prototypes for a Client
   Interface and a Server Interface.'''

# TODO:
#
# - Some more blank lines to make the code more
#   readable without coloring.
#
# - proper logging -.-

############################################################
# Events

class Event:
    '''Shard event base class.'''

    def __init__(self, identifier):
        '''This constructor must be called with
           an unique identifier for the object
           (player, item, NPC) which is affected
           by this event.'''
        # By defining it here, the variable is
        # part of the instance object, not the
        # class object. See "Class definitions"
        # in the Python Reference Manual.
        self.identifier = identifier

####################
# Attempt events

class AttemptEvent(Event):
    '''This is the base class for attempt events
       by the player or NPCs.'''

    def __init__(self, identifier, target_identifier):
        '''When sent by the client, target_identifier
           must describe the desired direction of
           the attempt. The PyGameClient uses a 
           two-dimensional map with rectangular
           elements, so target_identifier may be one 
           of "N", "NE", "E", "SE", "S", "SW", "W", "NW".
           The server determines what is being 
           looked at / picked up / manipulated / 
           talked to in that direction, and 
           replaces the direction string with an item, 
           NPC or player identifier if appropriate.'''
        self.identifier = identifier
        self.target_identifier = target_identifier

class TriesToMoveEvent(AttemptEvent):
    '''Issued when the player or an NPC wants to move, 
       awaiting server confirmation.'''
    pass

class TriesToLookAtEvent(AttemptEvent):
    '''Issued when the player or an NPC looks at a map 
       element or an item'''
    pass

class TriesToPickUpEvent(AttemptEvent):
    '''Issued when the player or an NPC tries to pick up
       an item. Attempts to pick up NPCs are discarded 
       or answered with an error.'''
    pass

class TriesToDropEvent(AttemptEvent):
    '''The player or NPC tries to drop an item.'''

    def __init__(self, identifier, item_identifier, target_identifier):
        '''An attempt to drop the item identified by
           item_identifier. When sent by the client, 
           target_identifier must describe the 
           desired direction. The PyGameClient
           uses a two-dimensional map with rectangular
           elements, so target_identifier may be one of 
           "N", "NE", "E", "SE", "S", "SW", "W", "NW". Note 
           that this attempt can turn out as a "use" 
           action, for example when dropping a key 
           on a padlock. In this case, the server 
           replaces the direction with an item 
           identifier and passes that on to the
           story engine.'''
        self.identifier = identifier
        self.item_identifier = item_identifier
        self.target_identifier = target_identifier

class TriesToManipulateEvent(AttemptEvent):
    '''Issued when the player or an NPC tries to
       manipulate an item. NPCs cannot be manipulated.'''
    pass

class TriesToTalkToEvent(AttemptEvent):
    '''Issued when the player or an NPC wants to start 
       a conversation with another entity.
       It is not possible to talk to items.'''
    pass

####################
# Confirm events

class ConfirmEvent(Event):
    '''This is the base class for server confirmations
       of attempt events.'''
    pass

class MovesToEvent(ConfirmEvent):
    '''This is the server confirmation of a movement.'''

    def __init__(self, identifier, direction):
        '''direction is a description as in
           the TriesToMoveEvent.'''
        self.identifier = identifier
        self.direction = direction

class PicksUpEvent(ConfirmEvent):
    '''This is a server confirmation of a
       TriesToPickUpEvent issued by the player
       or an NPC.'''

    def __init__(self, identifier, item_identifier):
        '''item_identifier identifies the item to
           pick up. This item should be known to
           the client.'''
        self.identifier = identifier
        self.item_identifier = item_identifier

class DropsEvent(ConfirmEvent):
    '''This is the server confirmation for an
       attempt to drop an item by the player
       or an NPC.
       This event does normally not occur when the
       drop action evaluates to a "use with" action, 
       as described in TriesToDropEvent. I that case
       the item stays in the posession of its owner, 
       and some other events are issued.'''

    def __init__(self, identifier, item_identifier, direction):
        '''item_identifier identifies the item to be 
           dropped on the map. direction is a 
           description as in the TriesToMoveEvent.'''
        self.identifier = identifier
        self.item_identifier = item_identifier
        self.direction = direction

class CanSpeakEvent(ConfirmEvent):
    '''This is a server invitation for the player or
       an NPC to speak. Since this event requires
       immediate user input, it is always executed
       as the last event of a Message by the 
       VisualEngine.'''

    def __init__(self, identifier, sentences):
        '''sentences is a list of strings for the
           player or NPC to choose from. If this list
           is empty, the client should offer a free-form
           text input.'''
        self.identifier = identifier
        self.sentences = sentences

class AttemptFailedEvent(ConfirmEvent):
    '''This is actually not a confirmation, but the
       server announcement that the last AttemptEvent
       sent by the entity identified by identifier
       failed. This should unblock the entity and
       allow new attempts.'''
    pass

####################
# Unclassified events without a special base class

class PerceptionEvent(Event):
    '''This is a perception for the player or an NPC
       issued by the server, usually the result of 
       a TriesToLookAtEvent.'''

    def __init__(self, identifier, perception):
        '''perception is a string to be displayed
           by the client. When used with an NPC, this
           could be used to feed a memory database.'''
        self.identifier = identifier
        self.perception = perception

class SaysEvent(Event):
    '''This normally is a reaction to the CanSpeakEvent, 
       to be sent by the player. NPCs can speak spontanously, 
       in that case a SaysEvent is issued by he Story 
       Engine. Players usually have to send an 
       TriesToTalkToEvent before they are allowed to
       speak.'''

    def __init__(self, identifier, text):
        '''text is a string to be spoken by the entity.'''
        self.identifier = identifier
        self.text = text

class CustomEntityEvent(Event):
    '''Shard Game Entities (the player, NPCs, items) may
       be able to change state, graphics or animations.
       Since these may be very customized actions, they
       are not defined here. Instead, the server can
       issue a CustomEntityEvent to trigger such a 
       custom action in the entity.
       A CustomEntityEvent should feed an internal
       queue of an Entity. All CustonEntityEvents of a
       Message are passed to the Entity before the
       Message is rendered by the VisualEngine. They
       are not supplied in real time during the rendering.'''

    def __init__(self, identifier, key_value_dict):
        '''key_value_dict is a Python dictionary 
           containing the parameters of the custom
           event.'''
        self.identifier = identifier
        self.key_value_dict = key_value_dict

####################
# Passive events

class PassiveEvent(Event):
    '''The base class for events concerning items
       ot NPCs when they are being passed, looked at, 
       picked up and the like.'''

    def __init__(self, identifier, trigger_identifier):
        '''The trigger_identifier identifies the
           entity that triggered the event. This makes it
           possible to react differently to several
           entities.'''
        self.identifier = identifier
        self.trigger_identifier = trigger_identifier

class PassedEvent(PassiveEvent):
    '''Issued by the server when an item or an NPC is
       being passed by the player or an NPC.'''
    pass

class LookedAtEvent(PassiveEvent):
    '''Issued by the server when an item or NPC is
       being looked at by the player or an NPC.'''
    pass

class PickedUpEvent(PassiveEvent):
    '''Issued by the server when an item is being
       picked up by the player or an NPC.'''
    pass

class DroppedEvent(PassiveEvent):
    '''Issued by the server when an item is being
       dropped by the player or an NPC.'''
    pass

####################
# Server events

class ServerEvent(Event):
    '''Base class for various events issued by the
       server, including map and room events.'''
    pass

class SpawnEvent(ServerEvent):
    '''This event creates the player or a new item / NPC on the map.'''

    def __init__(self, entity):
        '''Entity is an instance of shard.Entity, 
           having a type, identifier, location and
           assets. The server stores the relevant
           information and passes the entity on to
           the client.'''
        self.entity = entity

class DeleteEvent(ServerEvent):
    '''This event deletes an item or NPC from the map.
       Note that items may still persist in the players
       posessions.'''
    pass

class EnterRoomEvent(ServerEvent):
    '''This event announces that the player enters a new
       room. Events building the map and spawning the
       player, items and NPCs should follow. The room 
       is done and can be used when the server issues 
       RoomCompleteEvent.'''

    def __init__(self):
        '''This event has no parameters.'''
        pass

class RoomCompleteEvent(ServerEvent):
    '''Issued by the server after an EnterRoomEvent when
       the room is populated with a map, items and NPCs.'''

    def __init__(self):
        '''This event has no parameters.'''
        pass

class ChangeMapElementEvent(ServerEvent):
    '''This event changes a single element of the 
       two-dimensional map. When sent in a Message, 
       these events are executed immediately and
       in parallel upon the rendering of the
       Message by the VisualEngine.'''
    
    def __init__(self, tile, location):
        '''tile is a shard map object having a type 
           (obstacle or floor) and an asset.
           location is an object describing the
           location of the tile in the game world, 
           most probably a tuple of coordinates, but
           possibly only a string like "lobby".
           The server stores the relevant
           information and passes the tile and the
           location on to the client.'''
        self.tile = tile
        self.location = location

####################
# Client Events

class ClientEvent(Event):
    '''This is the base class for administrative
       client events.'''

    def __init__(self):
        '''Client events have no parameters.'''
        pass

class InitEvent(ClientEvent):
    '''This event is sent once by the client upon startup.
       It asks the server to supply anything that is needed
       to update the client to the current game state -
       usually a number of ChangeMapElementEvents and SpawnEvents.
       The client interface may decide to issue this event
       again in case there has been a connection failure.'''
    pass

class MessageAppliedEvent(ClientEvent):
    '''The client sends this event when it has applied the
       last server Message, i.e. deleted NPCs, spawned
       items, moved the player etc. To stay in sync, the
       server should wait for this event before sending any
       new Messages. Currently there is no identifier for
       Messages, so if the server does not wait for the
       MessageAppliedEvent before sending new events, 
       it will not be able to determine which message is 
       confirmed by the next MessageAppliedEvent.'''
    pass

############################################################
# Message

class Message:
    '''A Message manages an ordered list of shard events.
       Messages sent by the server describe the action
       of a certain time frame. The VisualEngine has to
       decide which events happen in parallel and which 
       ones happen sequential. Instances of Message 
       expose a single Python list object as Message.event_list.'''

    def __init__(self, event_list):
        '''Initialize the Message with a list of objects
           derived from shard.Event. An empty list may
           be supplied.'''
        #CHECKME: check the list elements for being
        #         instances of shard.Event here?
        self.event_list = event_list

#    def queueAsFirstEvent(self, event):
#        '''This is a convenience method. Queue the event 
#           given as the first event to be processed, 
#           shifting other events already queued.'''
#        self.event_list = [event] + self.event_list

############################################################
# Client Interface

class ClientInterface:
    '''This is the base class for a Shard Client Interface.
       Implementations should subclass this one an override
       the default methods, which showcase a simple example.'''

    def __init__(self):
        '''Interface initialization.'''
        # EXAMPLE
        # First one cache for a client message and one
        # for a server message.
        self.client_message = Message([])
        self.server_message = Message([])

        # Please note that handle_messages() will run in
        # a background thread. NEVER attempt to change
        # data structures in handle_messages() AND other
        # methods like send_message() or grab_message()
        # unless you lock them thread-safely. A simple
        # solution is to set flags in those methods, 
        # obeying the rule that only one method may set
        # them to True and one may set them to False.
        self.server_message_available = False
        self.client_message_available = False
        
        # This list serves as a queue for client messages.
        # To be thread-safe, it is not directly accessed
        # by handle_messages()
        self.client_message_queue = []

        # This is the flag which is set when shutdown()
        # is called.
        self.shutdown_flag = False

        # And this is the one for the confirmation.
        self.shutdown_confirmed = False

        # DELETE
        self.sent_no_message_available = False

    def handle_messages(self):
        '''The task of this method is to do whatever is
           necessary to send client messages and obtain 
           server messages. It is meant to be the back end 
           of send_message() and grab_message(). Put some 
           networking code, a GUI or a random generator 
           here. 
           This method is put in a background thread 
           automatically, so it can do all sorts of 
           polling or blocking IO.
           It should regularly check whether shutdown()
           has been called, and if so, it should notify
           shutdown() in some way (so that it can return
           True), and then raise SystemExit to stop 
           the thread.'''
        # EXAMPLE
        # Set up space for some local copies
        local_client_message = Message([])
        local_server_message = Message([])

        # Just as in the main thread, a queue
        # for server messages comes in handy in case 
        # the client does not catch up fetching the 
        # messages. Since this example sends only
        # one message, we do not really need it though.
        server_message_queue = []

        # A flag for a client init request
        client_sent_init = False

        # Run thread as long as no shutdown is requested
        while not self.shutdown_flag:
            # read client message
            if self.client_message_available:
                # First do the work
                local_client_message = self.client_message

                # Then notify thread-safely by setting the flag.
                # Only handle_messages() may set it to False.
                self.client_message_available = False

                # Here we should do something useful with the
                # client message, like sending it over the
                # network. In this example, we check for the
                # init message and silently discard everything
                # else.
                for current_event in local_client_message.event_list:
                    if isinstance(current_event, InitEvent):
                        client_sent_init = True

            # When done with the client message, it is time
            # to fetch a server message and hand it over
            # to the client. In this example, we generate
            # a message ourselves once the client has
            # requested init.
            if client_sent_init:
                # Build a message
                event_list = [ EnterRoomEvent() ]
                event_list.append(SpawnEvent(Entity("PLAYER",
                                                    "player",
                                                    (0, 0),
                                                    "")))
                event_list.append(RoomCompleteEvent())
                event_list.append(PerceptionEvent("player",
                                                  "dummy server message"))

                # Append a message to the queue
                server_message_queue.append(Message(event_list))

                # Set client_sent_init to false again, so the
                # events are only set once
                client_sent_init = False
                
            # Is the client ready to read? 
            if not self.server_message_available:
                try:
                    # Pull the next one from the queue and
                    # delete it there.
                    self.server_message = server_message_queue[0]
                    del server_message_queue[0]
 
                    # Set the flag for the main thread. This is
                    # thread-safe since it may only be set to
                    # True here.
                    self.server_message_available = True

                except IndexError:
                    # No message in queue!
                    pass
            else:
                # The client has not yet grabbed the
                # last message. No problem, this check
                # is run regularly, so we'll leave it in
                # the queue.
                pass

        # Caught shutdown notification, stopping thread
        self.shutdown_confirmed = True
        raise SystemExit

    def send_message(self, message):
        '''This method is called by the client 
           ClientControlEngine with a message ready to be sent to
           the server. The Message object given is an
           an instance of shard.Message. This method
           must return immediately to avoid blocking
           the client.'''
        # EXAMPLE
        # First we put this message in the local queue.
        self.client_message_queue.append(message)

        # self.client_message_available is used as a
        # thread-safe flag. It may only be set to True
        # here and may only be set to False in
        # handle_messages().
        if not self.client_message_available:
            # Pull the next one from the queue and
            # delete it there. Note that
            # handle_messages does not access the queue.
            self.client_message = self.client_message_queue[0]
            del self.client_message_queue[0]
            self.client_message_available = True
            return
        else:
            # Uh, this is bad. The client just called
            # send_message(), but the previous message
            # has not yet been collected by 
            # handle_messages(). In this case a new 
            # thread should be spawned which
            # waits until handle_messages() is ready
            # to receive a new message. Since this is
            # a simple example implementation, we'll
            # leave the message in the queue and hope
            # for some more calls to send_message() that
            # will eventually shift it forward until
            # it can be delivered.
            return

    def grab_message(self):
        '''This method is called by the client 
           ClientControlEngine to obtain a new server message.
           It must return an instance of shard.Message, 
           and it must do so immediately to avoid
           blocking the client. If there is no new
           server message, it must return an empty
           message.'''
        # EXAMPLE
        # Set up a local copy
        local_server_message = Message([])

        # self.server_message_available is used as a 
        # thread-safe flag. It may only be set to True 
        # in handle_messages() and may only be set to
        # False here, so no locking is required.
        if self.server_message_available:
            # First grab it, so the thread does not
            # overwrite it
            local_server_message = self.server_message

            # DELETE
            print("grabserver_message: Message available, got :"
                  + str(local_server_message))

            # Now set the flag
            self.server_message_available = False

            # DELETE
            print("grabserver_message: server_message_available is now '"
                  + str(self.server_message_available) + "'.")
            self.sent_no_message_available = False
            # DELETE

            return local_server_message
        else:
            # DELETE
            if not self.sent_no_message_available:
                print("grabserver_message: no Message available "
                      + "(server_message_available False)")
                self.sent_no_message_available = True
            # DELETE

            # A Message must be returned, so create
            # an empty one
            return Message([])

    def shutdown(self):
        '''This method is called when the client is
           about to exit. It should notify 
           handle_messages() to raise SystemExit to stop 
           the thread properly. shutdown() must return 
           True when handle_messages() received the 
           notification and is about to exit.'''
        # EXAMPLE
        # Set the flag to be caught by handle_messages()
        self.shutdown_flag = True

        # Wait for confirmation (blocks interface and client!)
        while not self.shutdown_confirmed:
            pass

        return True

############################################################
# Entities

class Entity:
    '''An Entity is a Shard game object. This is the base
       class for the player, NPCs and items. An Entity
       holds information used by the Shard game logic.
       A Shard Client should use subclasses (possibly
       with multiple inheritance) or custom attachements
       to instances of this class to implement the
       game objects used by the rendering engine (2D
       sprites, 3D models). Usually the ClientControlEngine
       manages a list of Entity instances. Everything
       concernig the actual graphical representation is
       done by the VisualEngine. Since this is very
       application dependent it is not covered in the
       base class. Check the documentation and source of 
       the VisualEngine for further insight on how it 
       handles game objects.'''

    def __init__(self, entity_type, identifier, location, asset):
        '''entity_type is one of the strings "PLAYER", "NPC", 
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

           asset finally is preferably a string
           with a file name or an URI of a media
           file containing the data for visualizing
           the Entity. Do not put large objects here
           since Entities are pushed around quite a
           bit and transfered across the network.
           The VisualEngine may fetch the asset and
           attach it to the instance of the Entity.'''
        self.entity_type = entity_type
        self.identifier = identifier
        self.location = location
        self.asset = asset

        # Store current direction and movement
        # "At dawn, look to the east." -Gandalf 
        #        in Peter Jackson's "Two Towers"
        self.direction = 'E'
        self.moves = False

        # Other flags for Entity actions
        self.speaks = False
        self.picks_up = False
        self.drops = False

        # Call custom_init() for application
        # dependent setup
        self.custom_init()

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

    def custom_init(self):
        '''You should not override Entity.__init__()
           since it performs required setup. Instead, 
           override this method to perform custom
           initialization. It is called from
           Entity.__init__().'''
        return

    def process_MovesToEvent(self, event):
        '''The MovesToEvent is supplied to the
           Entity so it can update its location.
           The rationale behind this is that
           the ClientControlEngine can be entirely
           agnostic about the type of world
           and location (text, 2D, 3D).
           A call to this method does not mean
           that the VisualEngine has started
           the movement. This is rather called
           by the ClientControlEngine to signal
           where the Entity is about to move.
           See the other methods of this class.'''
        # EXAMPLE
        # Store the movement, maybe for 
        # animation purposes
        self.direction = event.direction

        # Call the 2D movement function.
        self.process_2d_direction(event.direction)

    def process_2d_direction(self, direction):
        '''This is an auxiliary default method
           called from process_MovesToEvent(). It
           implements  a movement on a 2D map 
           with rectangular elements. If you 
           override process_MovesToEvent() (to 
           include animation for example), be 
           sure to call
           self.process_2d_direction(event.direction)
           or implement the update yourself.'''
        # EXAMPLE
        # In a contract-like design, we should
        # check preconditions like
        # isinstance(Event, MovesToEvent)
        # or len(self.location) == 2.
        #
        # We use shard.DIRECTION_VECTOR which maps
        # direction strings like "NW", "SE" to
        # a 2D vector tuple

        # x coordinate
        self.location[0] = self.location[0] + DIRECTION_VECTOR[direction][0]

        # y coordinate
        self.location[1] = self.location[1] + DIRECTION_VECTOR[direction][1]

    def process_CustomEntityEvent(self, key_value_dict):
        '''This method is called by the Client with
           the key-value dict of an CustomEntityEvent
           which possibly changes the client state. 
           The interpretation of CustomEntityEvents 
           is entirely up to the Entity. The default 
           implementation does nothing, so you 
           should override it.'''
        pass

    def starts_moving(self, frames, framerate):
        '''The VisualEngine is responsible for the
           gradual movement of the Entity to the
           target, but not for the animation. It
           calls this method once to signal that
           the Entity starts moving now. Entities
           may implement a flag or some logic
           which changes their graphical 
           representation on every frame, yielding
           an animation. starts_moving() is always
           called after process_MovesToEvent(), so
           the Entity knows about the direction.
           The VisualEngine provides the number of
           frames for the movement and the framerate.
           Thus the entity can adapt to different
           frame rates by adjusting how many frames
           an image is shown. The Entity is advised
           to stop the animation once the number
           of frames given has passed, but it does
           not need to do so.
           The default implementation simply sets
           the variable self.moves to True.'''
        self.moves = True

#    def stopsMoving(self):
#        '''Called when the VisualEngine has
#           completed the movement. This should
#           trigger a stop of the movement 
#           animation. The default implementation
#           sets self.moves to False.'''
#        self.moves = False

    def starts_speaking(self, frames, framerate):
        '''The VisualEngine displays text spoken 
           by the Entity, but does not enforce any
           animation. It calls this method to 
           signal that the Entity starts speaking
           now. Entities may implement a flag or 
           some logic which changes their graphical 
           representation on every frame, yielding
           an animation.
           The VisualEngine provides the number of
           frames for the speaking action and the 
           framerate. Thus the entity can adapt to 
           different frame rates by adjusting how 
           many frames an image is shown. 
           The Entity is advised to stop the 
           animation once the number of frames 
           given has passed, but it does not need 
           to do so.
           The default implementation simply sets 
           the variable self.speaks to True.'''
        self.speaks = True

#    def stopsSpeaking(self):
#        '''Called when the VisualEngine is about
#           to erase the spoken text from the 
#           screen. This should trigger a stop of 
#           the speaking animation. The default 
#           implementation sets self.speaks
#           to False.'''
#        self.speaks = False

    def starts_picking_up(self, frames, framerate):
        '''The VisualEngine makes picked up objects
           disappear and appear in the inventory, 
           but does not enforce any animation. It 
           calls this method to signal that the 
           Entity starts picking up something now. 
           Entities may implement a flag or some 
           logic which changes their graphical 
           representation on every frame, yielding 
           an animation.
           The VisualEngine provides the number of
           frames for the action and the framerate.
           Thus the entity can adapt to different
           frame rates by adjusting how many frames
           an image is shown. The Entity is advised
           to stop the animation once the number
           of frames given has passed, but it does
           not need to do so.
           The default implementation simply sets 
           the variable self.picks_up to True.'''
        self.picks_up = True

    def starts_dropping(self, frames, framerate):
        '''The VisualEngine makes dropped objects
           disappear in the inventory and appear
           on the map, but does not enforce any 
           animation. It calls this method to 
           signal that the Entity starts picking 
           up something now. Entities may 
           implement a flag or some logic which 
           changes their graphical representation 
           on every frame, yielding an animation.
           The VisualEngine provides the number of
           frames for the action and the framerate.
           Thus the entity can adapt to different
           frame rates by adjusting how many frames
           an image is shown. The Entity is advised
           to stop the animation once the number
           of frames given has passed, but it does
           not need to do so.
           The default implementation simply sets 
           the variable self.picks_up to True.'''
        self.drops = True

############################################################
# Tiles

class Tile:
    '''A Tile is an element of a two-dimensional map.
       It is never meant to perform any active logic, 
       so its only property is a type and an asset.'''

    def __init__(self, tile_type, asset):
        '''tile_type must be a string describing the tile
           type. Currently supported are "OBSTACLE"
           and "FLOOR", describing whether the player
           or NPCs can move across the tile.
           
           asset is preferably a string with a file 
           name or an URI of a media file containing 
           the data for visualizing the tile.'''
        self.tile_type = tile_type
        self.asset = asset

############################################################
# Utilities

# Set up a DIRECTION_VECTOR for 2D movement
# processing. It is assumed that (0, 0) is
# the lower left corner
DIRECTION_VECTOR = {'N' : (0, 1) , 
                    'NE' : (1, 1) , 
                    'E' : (1, 0) , 
                    'SE' : (1, -1) , 
                    'S' : (0, -1) , 
                    'SW' : (-1, -1) , 
                    'W' : (-1, 0) , 
                    'NW' : (-1, 1) }

############################################################
# Client Control Engine

class ClientControlEngine:
    '''An instance of this class is the main engine in every
       Shard client. It connects to the Client Interface and
       to the VisualEngine, passes events and keeps track
       of Entities. It is normally instantiated in a small
       setup script "run_shardclient.py".'''

    ####################
    # Init

    def __init__(self, client_interface_instance, visual_engine_instance):
        '''The ClientControlEngine must be instantiated with an
           instance of shard.ClientInterface which handles
           the connection to the server or supplies events
           in some other way, and an instance of 
           shard.VisualEngine which graphically renders the
           game action.'''

        self.client_interface = client_interface_instance
        self.visual_engine = visual_engine_instance

        # Set up flags used by self.run()
        self.await_confirmation = False

        # A dictionary that maps event classes to functions 
        # to be called for the respective event.
        # I just love to use dicts to avoid endless
        # if... elif... clauses. :-)
        self.event_dict = {AttemptFailedEvent : self.process_AttemptFailedEvent , 
                          CanSpeakEvent : self.process_CanSpeakEvent , 
                          DropsEvent : self.process_DropsEvent , 
                          MovesToEvent : self.process_MovesToEvent , 
                          PicksUpEvent : self.process_PicksUpEvent , 
                          CustomEntityEvent : self.process_CustomEntityEvent , 
                          PerceptionEvent : self.process_PerceptionEvent , 
                          SaysEvent : self.process_SaysEvent , 
                          ChangeMapElementEvent : self.process_ChangeMapElementEvent , 
                          DeleteEvent : self.process_DeleteEvent , 
                          EnterRoomEvent : self.process_EnterRoomEvent , 
                          RoomCompleteEvent : self.process_RoomCompleteEvent , 
                          SpawnEvent : self.process_SpawnEvent }

        # self.entity_dict keeps track of all active Entites.
        # It uses the identifier as a key, assuming that is
        # is unique.
        self.entity_dict = {}

        # A dict for Entites which have been deleted, for
        # the convenience of the VisualEngine. Usually it
        # should be cleared after each rendering.
        self.deleted_entities_dict = {}

        # A list of tiles for the current room, for
        # the convenience of the VisualEngine.
        self.tile_list = []

        # self.map is an attempt of an efficient storage of
        # an arbitrary two-dimensional map. To save space, 
        # only explicitly defined elements are stored. This
        # is done in a dict of dicts, hopefully speeding up
        # the retrieval of elements by avoiding tests 
        # element-by-element. Keys are numbers. Access the
        # elemty using self.map[x][y]. The lower left element
        # is self.map[0][0].
        self.map = {}

        # The ClientControlEngine examines the events of a Server
        # Message and applies them. events for special
        # consideration for the VisualEngine are collected
        # in a Message for the VisualEngine.
        # The ClientControlEngine has to empty the Message once 
        # the VisualEngine has rendered all Events.
        self.visual_engine_message = Message([])

        # We attach custom flags to the Message to notify
        # the VisualEngine whether an EnterRoomEvent or
        # RoomCompleteEvent occured, so it does not have
        # to scan the events.
        self.visual_engine_message.has_EnterRoomEvent = False
        self.visual_engine_message.has_RoomCompleteEvent = False

        # In self.client_message we collect Client events to be
        # sent to the server in each loop.
        self.client_message = Message([])
        
        # DELETE
        self.got_empty_message = False
        print("ClientControlEngine: __init__ complete.")
        # DELETE

        # TODO: set up the inventory

    ####################
    # Main Loop

    def run(self):
        '''Main loop of the ClientControlEngine. This is
           a blocking method. It calls all the process methods
           to process events.'''

        # TODO:
        # The current implementation is too overtrustful.
        # It should check much more thoroughly if the
        # affected Entites exist at all and so on. Since
        # this is a kind of precondition or even invariant, 
        # it should be covered using a "design by contract"
        # approach to the whole thing instead of putting
        # neat "if" clauses here and there.

        # DELETE
        print("ClientControlEngine: starting main loop in run().")

        # Send InitEvent to trigger a complete update
        # from the server
        self.client_interface.send_message(Message([InitEvent()]))

        while not self.visual_engine.exit_requested:
            # grab_message must and will return a Message, but
            # it possibly has an empty event_list.
            server_message = self.client_interface.grab_message()

            # DELETE
            if len(server_message.event_list):
                print("ClientControlEngine: got server_message: \n"
                      + str(server_message.event_list))
                self.got_empty_message = False
            elif not self.got_empty_message:
                print("ClientControlEngine: got an empty server_message.")
                self.got_empty_message = True
            # DELETE

            # First handle the events in the ClientControlEngine, 
            # gathering Entities and Map Elements and preparing
            # a Message for the VisualEngine
            for current_event in server_message.event_list:
                # This is a bit of Python magic. 
                # self.event_dict is a dict which maps classes to handling
                # functions. We use the class of the event supplied as
                # a key to call the appropriate handler, and hand over
                # the event.
                self.event_dict[current_event.__class__](current_event)

            # Now that everything is set and stored, call
            # the VisualEngine to render the messages.

            # First hand over / update the necessary data.
            self.visual_engine.entity_dict = self.entity_dict
            self.visual_engine.deleted_entities_dict = self.deleted_entities_dict
            self.visual_engine.tile_list = self.tile_list
            self.visual_engine.Map = self.map

            # This call may take an almost arbitrary amount
            # of time, since there may be long actions to
            # be shown by the VisualEngine.
            # Notice: render_message() must be called regularly
            # even if the server Message and thus the
            # Visualengine_message are empty!
            self.visual_engine.render_message(self.visual_engine_message)

            # The VisualEngine returned, the Server Message has
            # been applied and rendered. Clean up.
            self.visual_engine_message = Message([])
            self.deleted_entities_dict = {}
            self.visual_engine_message.has_EnterRoomEvent = False
            self.visual_engine_message.has_RoomCompleteEvent = False

            # Up to now, we did not care whether the server Message
            # had any events at all. But we only send a 
            # MessageAppliedEvent if it had.
            if len(server_message.event_list)>0:
                self.client_message.event_list.append(MessageAppliedEvent())

            # TODO:
            # If there has been a Confirmation for a LookAt or
            # TriesToManipulate, unset "AwaitConfirmation" flag

            # If we do not await a Confirmation anymore, 
            # we evaluate the player input if any.
            # The VisualEngine might have collected some
            # player input and converted it to events.
            if (len(self.visual_engine.player_event_list)>0
                and not self.await_confirmation):
                # We queue player triggered events before 
                # MessageAppliedEvent so the server processes
                # all events before sending anything new.
                self.client_message.event_list = (self.visual_engine.player_event_list
                                                  + self.client_message.event_list)

                # Since we had player input, we now await confirmation
                self.await_confirmation = True

            # If this iteration yielded any events, send them.
            if len(self.client_message.event_list)>0:
                self.client_interface.send_message(self.client_message)

                # Clean up
                self.client_message = Message([])

            # OK, iteration done. If no exit requested, 
            # grab the next server event!

        # exit has been requested
        
        # DELETE
        print("ClientControlEngine.run: exit requested from "
              + "VisualEngine, shutting down interface...")

        # stop the Client Interface thread
        self.client_interface.shutdown()

        # DELETE
        print("ClientControlEngine.run: shutdown confirmed.")

        # TODO:
        # possibly exit cleanly from the VisualEngine here

        return

    ####################
    # Auxiliary Methods

    def process_AttemptFailedEvent(self, event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        #    ControlEngine: if there was a Confirmation and
        #    it has been applied or if there was an
        #    AttemptFailedEvent: unset "AwaitConfirmation" flag
        pass

    def process_CanSpeakEvent(self, event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        #    ControlEngine: if there was a Confirmation and
        #    it has been applied or if there was an
        #    AttemptFailedEvent: unset "AwaitConfirmation" flag

        # Pass on the event.
        self.visual_engine_message.event_list.append(event)

    def process_DropsEvent(self, event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        #
        # Remove the Entity from the Inventory
        #
        # Add it to the entity_dict, setting the
        # coordinates from direction
        #
        # Queue the DropsEvent (for Animation) and
        # a SpawnEvent for the VisualEngine
        #
        #    ControlEngine: if there was a Confirmation and
        #    it has been applied or if there was an
        #    AttemptFailedEvent: unset "AwaitConfirmation" flag
        pass

    def process_MovesToEvent(self, event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        # 
        # ControlEngine: if there was a Confirmation and it has been applied
        # or if there was an AttemptFailedEvent: unset "AwaitConfirmation" flag
        #
        # ControlEngine: pass events to Entities
        #     Entity: change location, set graphics, custom actions
        # ControlEngine: pass Message/Events to VisualEngine
        pass

    def process_PicksUpEvent(self, event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        #
        # Remove from the entity_dict
        #
        # Save in deleted_entities_dict
        #
        # Move the Entity to the Inventory
        #
        # Queue the PicksUpEvent (for Animation) and
        # a DeleteEvent for the VisualEngine
        #
        #    ControlEngine: if there was a Confirmation and
        #    it has been applied or if there was an
        #    AttemptFailedEvent: unset "AwaitConfirmation" flag
        pass

    def process_CustomEntityEvent(self, event):
        '''The key-vlaue dict of a CustomEntiyEvent 
           is just passed on to the Entity.'''
        self.entity_dict[event.identifier].process_CustomEntityEvent(event.key_value_dict)

    def process_PerceptionEvent(self, event):
        '''A perception must be displayed by the 
           VisualEngine, so it is queued in a Message passed
           from the ClientControlEngine.'''
        #    ControlEngine: if there was a Confirmation
        #    (here: for LookAt, Manipulate)
        #    and it has been applied
        #    or if there was an AttemptFailedEvent: unset
        #    "AwaitConfirmation" flag
        self.visual_engine_message.event_list.append(event)

    def process_SaysEvent(self, event):
        '''The VisualEngine usually must display the 
           spoken text. Thus the event is put in the
           event queue for the VisualEngine.
           The VisualEngine is going to notify
           the Entity once it starts speaking so it
           can provide an animation.'''
        self.visual_engine_message.event_list.append(event)

    def process_ChangeMapElementEvent(self, event):
        '''Store the tile given in self.map, 
           a dict of dicts with x- and
           y-coordinates as keys. Also save
           it for the VisualEngine.'''
        try:
            # see if a dict for the column (x coordinate)
            # already exists
            self.map[event.location[0]]
        except KeyError:
            self.map[event.location[0]] = {}

        # possibly overwrite existing tile
        self.map[event.location[0]][event.location[1]] = event.tile

        # Append the tile to a list for easy
        # fetching of the tile's asset
        self.tile_list.append(event.tile)

        # Append the event to the queue for the VisualEngine.
        self.visual_engine_message.event_list.append(event)

    def process_DeleteEvent(self, event):
        '''Save the Entity to be deleted in the
           deleted_entities_dict for the 
           VisualEngine, then remove it from the
           entity_dict.'''

        # DELETE
        # This is just a hack, see TODO for run() for details
        if event.identifier in self.entity_dict.keys():
        # DELETE

            # Save the Entity in the deleted_entities_dict
            # to notify the VisualEngine
            self.deleted_entities_dict[event.identifier] = self.entity_dict[event.identifier]

            # Now remove the Entity
            del self.entity_dict[event.identifier]

            # Append the event to the queue for the VisualEngine.
            # The VisualEngine needs the event for knowing
            # when exactly to remove the Entity.
            self.visual_engine_message.event_list.append(event)

        # DELETE
        else:
            print("process_DeleteEvent: Entity to delete does not exist.")
        # DELETE

    def process_EnterRoomEvent(self, event):
        '''An EnterRoomEvent means the server is
           about to send a new map, respawn the
           player and send items and NPCs. So
           this method  empties all data 
           structures and passes the event on to 
           the VisualEngine.'''
        # There possibly will be no more confirmation
        # for past attempts, so do not wait for them
        self.await_confirmation = False

        # All Entities in this room have to be sent.
        # No use keeping old ones around, expecially with old
        # locations.
        self.entity_dict = {}

        # Clear the dict of Entites which have been deleted.
        self.deleted_entities_dict = {}

        # Clear the list of tiles for the room.
        self.tile_list = []

        # Awaiting a new map!
        self.map = {}

        # Finally set the flag in the Message
        # for the VisualEngine and queue the event
        # so the VisualEngine knows what happend after
        # that.
        self.visual_engine_message.has_EnterRoomEvent = True
        self.visual_engine_message.event_list.append(event)

    def process_RoomCompleteEvent(self, event):
        '''RoomCompleteEvent notifies the client that
           the player, all map elements, items and
           NPCs have been transfered. By the time the
           event arrives the ClientControlEngine should
           have saved all important data in data
           structures. So the event is queued for
           the VisualEngine here.'''
        # This is a convenience flag so the VisualEngine
        # does not have to scan the event_list.
        self.visual_engine_message.has_RoomCompleteEvent = True

        # Queue the event. All events after this are
        # rendered.
        self.visual_engine_message.event_list.append(event)

    def process_SpawnEvent(self, event):
        '''Add the Entity given to the entity_dict
           and pass the SpawnEvent on to the VisualEngine.'''
        self.entity_dict[event.entity.identifier] = event.entity
        self.visual_engine_message.event_list.append(event)

############################################################
# Client Visual Engine

class VisualEngine:
    '''This is the base class for a VisualEngine for the
       Shard Client. Subclasses should override the
       appropriate methods of this class and implement a 
       graphical representation of the game and the 
       action. Shard is based on a two-dimensional map, 
       but apart from that it makes very few assumptions 
       about the graphical rendering. Thus it is 
       possible to write 2D and 3D VisualEngines and 
       even a text interface.'''

    ####################
    # Initialization

    def __init__(self, asset_engine, framerate):
        '''This method initializes the VisualEngine.
           asset_engine must be an instance of
           shard.AssetEngine or a subclass.
           framerate must be an integer and sets
           the maximum (not minimum ;-)) frames per
           second the client will run in.
           If you override this method, make sure 
           you do all these initiaizations, too.
           For your convenience there is a method
           self.custom_init() which you can savely
           override. 
           This method must not block, it has to 
           return once everything is set up.'''
        # Get framerate and asset_engine from parameters
        self.framerate = framerate
        self.asset_engine = asset_engine

        # Set how long actions like a movement from
        # Map element to Map element take, in seconds.
        self.action_time = 0.5

        # A list of events derived from player input, 
        # cleared and updated on each rendering
        self.player_event_list = []

        # Since it represents the GUI, the VisualEngine
        # is responsible for catching an
        # exit request by the user. This value is
        # checked in the ClientControlEngine main loop.
        self.exit_requested = False

        # Variables to be filled by the ClientControlEngine
        # before each call to render_message()
        self.entity_dict = {}
        self.deleted_entities_dict = {}
        self.tile_list = []
        self.map = {}

        # Are we waiting for a RoomCompleteEvent after
        # an EnterRoomEvent? Upon initialization this
        # is True, since a room has not yet been
        # transfered.
        self.waiting_for_RoomCompleteEvent = True

        # See the method for explaination.
        self.custom_init()

        return

    ####################
    # VisualEngine Main Loop

    def render_message(self, message):
        '''This is the main method of the VisualEngine.
           It is called regularly by the ClientControlEngine
           with a list of events to display (note: the
           list may be empty). It may take all the time 
           it needs to render the action, just a couple 
           or even hundreds of frames, but it must 
           return once the events have been displayed. 
           It must neither block completely nor run in 
           a thread since the ClientControlEngine has to 
           grab new events and change state between 
           calls to render_message(). Put that way, 
           render_message() is simply a part of 
           ClientControlEngine.run().
           You should normally not override this method
           unless you have to do some really advanced
           stuff. Overriding the other methods of this
           class (which in turn are called from 
           render_message()) should be just fine. See 
           the other methods and the source code for 
           details.'''
        # *sigh* Design by contract is a really nice
        # thing. We really really should do some thorough
        # checks, like for duplicate RoomCompleteEvents, 
        # duplicate CanSpeakEvents and similar stuff.
        # Below we assume that everyone behaves nicely.
        # In some weird way we could sell that as
        # "pythonic" ;-) Hey! Not a consenting adult, 
        # anyone?

        ####################
        # Initialize

        # Reset the list of events triggered by 
        # player actions
        self.player_event_list = []
        
        # Compute the number of frames per action.
        # See __init__() for details.
        action_frames = int(self.action_time * self.framerate)

        ####################
        # Check EnterRoomEvent

        # The first thing to check for is if there has
        # been an EnterRoomEvent. For our convenience, 
        # the ControlEngine has set up a flag in the
        # message, so we simply check that instead
        # of scanning the whole list.
        if message.has_EnterRoomEvent:
            # When this arrives here all data scructures
            # have already been cleared and possibly
            # populated with new Entites and a new Map.
            # So we have to ignore everything before
            # an EnterRoomEvent.

            # See the method for explaination
            self.display_EnterRoomEvent()
            
            # Set a flag that we are waiting
            # for RoomCompleteEvent
            self.waiting_for_RoomCompleteEvent = True

        ####################
        # Check RoomCompleteEvent

        # Next, as long as we are waiting for a
        # RoomCompleteEvent, nothig will be rendered
        # and no player input is accepted.
        if self.waiting_for_RoomCompleteEvent:
            # The ControlEngine has set a flag for
            # our convenience.
            if message.has_RoomCompleteEvent:
                # By the time the event arrives the 
                # ControlEngine has gathered all important
                # data and handed them over to us, so wen can
                # build a new screen.

                # Load and store assets for tiles and 
                # Entities using the asset_engine
                for current_entity in self.entity_dict.values():

                    asset_to_fetch = current_entity.asset

                    try:
                        retrieved_asset = self.asset_engine.fetch_asset(asset_to_fetch)
                    except:
                        # See the method for explaination
                        self.display_asset_exception(asset_to_fetch)

                    # After a RoomCompleteEvent all Entites
                    # are freshly created instances. We
                    # replace the string describing the
                    # asset by the data object returned
                    # by the asset_engine.
                    current_entity.asset = retrieved_asset

                for current_tile in self.tile_list:

                    asset_to_fetch = current_tile.asset

                    try:
                        retrieved_asset = self.asset_engine.fetch_asset(asset_to_fetch)
                    except:
                        # See the method for explaination
                        self.display_asset_exception(asset_to_fetch)

                    # After a RoomCompleteEvent all tiles
                    # are freshly created instances. We
                    # replace the string describing the
                    # asset by the data object returned
                    # by the asset_engine.
                    current_tile.asset = retrieved_asset

                # See the method for explaination
                self.display_RoomCompleteEvent()

                # Delete everything in the event_list up to and
                # including the RoomCompleteEvent
                while not isinstance(message.event_list[0], RoomCompleteEvent):
                    del message.event_list[0]
                
                # Arrived at RoomCompleteEvent. 
                # Delete it as well.
                del message.event_list[0]

                # No more waiting!
                self.waiting_for_RoomCompleteEvent = False

            else:
                # If there is no RoomCompleteEvent in that message, 
                # ignore everything.

                # Technically this waiting corresponds to a
                # frame, though we do not render anything.

                # See method for explaination.
                self.update_frame_timer()

                # Discard and check the next message.
                return

        ####################
        # Grouping Event List

        # If we arrive here, we are ready to render all the
        # events that are left in the event_list.

        # messages sent by the server describe the action
        # of a certain period of time. They are divided
        # into groups of parallel Events here. The division
        # is simple: group all subsequent events that do
        # not affect the same identifier.

        # TODO:
        # We could and perhaps should do some checks here
        # to prevent nonsense:
        # Added Entities may not do anything before they
        # appear.
        # Deleted Entites may act until they disappear.
        # (Get the Entity from the deletedList then, since
        # it is already deleted in the entity_dict.)

        # Make up an empty list of IDs
        collected_identifiers = []

        # make up an empty list of event lists and add an
        # empty list
        grouped_events = [[]]

        # make a buffer for the CanSpeakEvent
        buffered_CanSpeakEvent = Event("dummy_identifier")
        
        # buffer for an identifier
        identifier = ''
        
        for current_event in message.event_list:
            if isinstance(current_event, CanSpeakEvent):
                # CanSpeakEvent is taken out of the list
                # to be appended at the very end.
                # Note that this keeps only the very
                # last CanSpeakEvent. There shouldn't be
                # more than one in a message.
                buffered_CanSpeakEvent = current_event
            
            elif isinstance(current_event, ChangeMapElementEvent):
                # All these happen in parallel, no identifier
                # is recorded
                grouped_events[-1].append(current_event)

            else:
                # Now follow the events where we can
                # detect an identifier
                if isinstance(current_event, SpawnEvent):
                    identifier = current_event.entity.identifier
                else:
                    identifier = current_event.identifier

                if identifier in collected_identifiers:
                    # append an empty list to the list of
                    # event lists
                    # We've had that identifier before.
                    # Start a new event group.
                    grouped_events.append([])
                
                    # Start new
                    collected_identifiers = []
                
                else:
                    # identifier is not yet in
                    # current group
                    collected_identifiers.append(identifier)

                # Now append the event to the current group
                grouped_events[-1].append(current_event)

        # All parallel events are grouped now.            
        # Append the CanSpeakEvent if it is there.
        if isinstance(buffered_CanSpeakEvent, CanSpeakEvent):
            grouped_events.append([buffered_CanSpeakEvent])

        ####################
        # Render Groups

        # Now it's no good, we finally have to render some
        # frames!
        # grouped_events now consists of lists of parallel
        # events. MovesTo, Drops and PicksUpEvents take the
        # same number of frames to render, which is given by
        # self.action_time * self.framerate. During a 
        # SaysEvent or a PerceptionEvent, animation may even
        # stop for some time. These events are displayed last.

        for event_list in grouped_events:
            if len(event_list) == 0 :
                # No events in event_list!
                # See the method for explaination.
                self.display_static_frame()

                # Any player input?
                # See the method for explaination.
                self.collect_player_input()

                return

            # We have at least one event.

            if isinstance(event_list[0], CanSpeakEvent):
                # See the method for explaination.
                self.display_CanSpeakEvent(event_list[0])
                
                return

            # If there was no CanSpeakEvent, we are
            # still here. 

            # See the method for explaination.
            self.filter_events(event_list)

            # Now we kind of sort the remaining events.

            PerceptionEvent_list = []
            SaysEvent_list = []
            MovesToEvent_list = []
            ChangeMapElementEvent_list = []
            SpawnEvent_list = []
            DeleteEvent_list = []

            has_multiple_frame_action = False
            has_inventory_action = False

            for current_event in event_list:
                if isinstance(current_event, PerceptionEvent):
                    # Queue for later use.
                    PerceptionEvent_list.append(current_event)

                elif isinstance(current_event, SaysEvent):
                    # The Entity is notified in
                    # self.display_SaysEvents() because we
                    # do not compute the number of frames here.
                    # Queue for later use.
                    SaysEvent_list.append(current_event)

                elif isinstance(current_event, DropsEvent):
                    # This is a multiple frame action.
                    has_multiple_frame_action = True

                    # This affects the inventory.
                    has_inventory_action = True

                    # Notify the Entity that the animation is
                    # about to start. No need to queue the event.
                    self.entity_dict[current_event.identifier].starts_dropping(action_frames,
                                                                               self.framerate)

                elif isinstance(current_event, PicksUpEvent):
                    # This is a multiple frame action.
                    has_multiple_frame_action = True

                    # This affects the inventory.
                    has_inventory_action = True

                    # Notify the Entity that the animation is
                    # about to start. No need to queue the event.
                    self.entity_dict[current_event.identifier].starts_picking_up(action_frames,
                                                                                 self.framerate)

                elif isinstance(current_event, MovesToEvent):
                    # This is a multiple frame action.
                    has_multiple_frame_action = True

                    # Notify the Entity that the animation
                    # is about to start.
                    self.entity_dict[current_event.identifier].starts_moving(action_frames,
                                                                             self.framerate)

                    # Queue for later use.
                    MovesToEvent_list.append(current_event)

                elif isinstance(current_event, ChangeMapElementEvent):
                    # Queue for later use.
                    ChangeMapElementEvent_list.append(current_event)

                elif isinstance(current_event, SpawnEvent):
                    # Queue for later use.
                    SpawnEvent_list.append(current_event)

                elif isinstance(current_event, DeleteEvent):
                    # Queue for later use.
                    DeleteEvent_list.append(current_event)

            if has_multiple_frame_action:
                # See the method for explaination.
                self.display_multiple_frame_action(MovesToEvent_list)

            # See the method for explaination.
            self.display_SpawnEvents(SpawnEvent_list)

            # See the method for explaination.
            self.display_DeleteEvents(DeleteEvent_list)

            # See the method for explaination.
            self.display_ChangeMapElementEvents(ChangeMapElementEvent_list)

            if has_inventory_action:
                # See the method for explaination.
                self.update_inventory()

            # Now finally render queued blocking events.

            # See the method for explaination.
            self.display_PerceptionEvents(PerceptionEvent_list)

            # See the method for explaination.
            self.display_SaysEvents(SaysEvent_list)

            # Here we jump up to the next event_list, if any.

        # All event_lists are rendered now.

        ####################
        # Player Input

        # See the method for explaination.
        self.collect_player_input()

        ####################
        # Return to ControlEngine

        return

    ####################
    # Auxiliary Methods To Override

    # TODO:
    # Most docstrings describe 2D stuff (images).
    # Rewrite 2D-3D-agnostic.

    def custom_init(self):
        '''When creating a subclass, you should not
           override the standard __init__() method
           of the VisualEngine class. Instead place
           all your custom setup code here. You can 
           initialize your graphics module here and
           display a splash screen. Everything
           is fine, as long as you return. :-)'''
        return

    def display_EnterRoomEvent(self):
        '''This method is called when the VisualEngine
           has encoutered an EnterRoomEvent. You should
           override it, blank the screen here and display
           a waiting message since the VisualEngine is
           going to twiddle thumbs until it receives a 
           RoomCompleteEvent.'''
        return

    def display_asset_exception(self, asset):
        '''This method is called when the asset_engine
           is unable to retrieve the asset. This is a 
           serious error which prohibits continuation.
           The user should be asked to check his
           installation, file system or network
           connection.'''

        print("VisualEngine.display_asset_exception: A required asset "
              + "(image, animation, sound) could not be fetched. "
              + "The problematic asset was '"
              + str(asset)
              + "'. Sorry, but I can't go on.")

        raise SystemExit

    def display_RoomCompleteEvent(self):
        '''This method is called when everything
           is fetched and ready after a
           RoomCompleteEvent. Here you should 
           set up the main screen and display 
           some Map elements and Entities.'''
        # You'll possibly want to save the real 
        # screen coordinates of Entities in a 
        # special data structure since they do 
        # not necessarily correspond to the Map 
        # coordinates.
        return

    def update_frame_timer(self):
        '''Your graphics module might provide a
           timer which must be notified once per
           frame. Do this here and use this method
           wherever you need it. It is also called
           from render_message() when appropriate.
           This method may block execution to slow
           the VisualEngine down to a certain
           frame rate.'''
        return

    def filter_events(self, event_list):
        '''This is method is called with a list of
           parallel events before they are rendered.
           You can filter events here, for example
           if they are off-screen. This method
           must change the event_list in place.
           The default is no filtering.'''
        return

    def display_CanSpeakEvent(self, CanSpeakEvent_instance):
        '''This method is called when the VisualEngine
           needs to render a CanSpeakEvent. This is the
           last event rendered before returning to
           the ControlEngine. You have to prompt for
           appropriate user input here and add a
           corresponding SaysEvent to self.player_event_list, 
           which is evaluated by the ControlEngine.'''
        # Find a player in entity_dict
        for current_entity in self.entity_dict.values():
            if current_entity.entity_type == "PLAYER":
                self.player_event_list.append(SaysEvent(current_entity.identifier,
                                                        "display_CanSpeakEvent: dummy"))
        # Don't forget the frame counter in
        # your implementation.
        self.update_frame_timer()
        return

    def display_static_frame(self):
        '''This method is called when the VisualEngine
           decides that is need to enter a single frame
           of the current game state. There is nothing
           special going on here, so you should notify
           the Entities that there is a next frame to
           be displayed (however that is done in your 
           implementation) and update their graphics.'''
        # You might want to restrict your updates to
        # visible Entities
        pass

        self.update_frame_timer()
        return

    def collect_player_input(self):
        '''The module you use for actual graphics
           rendering most probably has a way to
           capture user input. This method is called
           when the VisualEngine has displayed a
           series of events and wants to capture
           the user's reaction. When overriding this
           method, you have to convert the data
           provided by your module into Shard 
           events, most probably instances of 
           shard.AttemptEvent. You must append them
           to self.player_event_list which is
           evaluated by the ControlEngine.
           Note that your module might provide you
           with numerous user actions if the user
           clicked and typed a lot during the
           rendering. You should create a 
           reasonable subset of those actions, 
           e.g. select only the very last user
           input action.
           The default implementation does nothing.'''
        return

    def display_multiple_frame_action(self, MovesToEvent_list):
        '''This method is called when the VisualEngine
           is ready to render Move, Drop or PickUp
           actions. All visible Entities are already
           notified about their state at this point.
           This method must render exactly
           self.action_frames frames. You have to 
           compute a movement for each Entity in the 
           list of MovesToEvent instances provided. 
           Note that this list may be empty, but even 
           then you have to render the full number of 
           frames to display PickUp and Drop animations. 
           You might get away with just changing the 
           screen coordinates and calling 
           self.display_static_frame().'''
        # Compute start and end position and movement per
        # frame for all moving Entities
 
        # This creates a copy since framerate is
        # immutable.
        i = self.action_frames

        while i:
        # for each frame:
            # move moving Entities by respective Movement
            # render a graphic for each visible entity
            # The should supply a new one on each call
            # update frame counter
            self.display_static_frame()
            i = i - 1
        return

    def display_SpawnEvents(self, event_list):
        '''This method is called with a list of
           instances of SpawnEvent to be displayed. 
           All you need to do here is adding the 
           new Enties to a list of visible Entities 
           you might have set up and render a static
           frame. Note that event_list may be empty.'''
        return           

    def display_DeleteEvents(self, event_list):
        '''This method is called with a list of 
           instances of DeleteEvent. You need
           to remove the Entites affected from
           your data structures and draw a
           frame without the deleted Entities.
           event_list may be empty. Note that
           the Entities to be removed are
           already gone in self.event_dict, 
           so use self.deleted_entities_dict
           instead.'''
        return

    def display_ChangeMapElementEvents(self, event_list):
        '''This method is called with a list of
           instances of ChangeMapElementEvent.
           There are only visible Map elements
           in the list if you hav implemented
           an according filter in self.filter_events().
           In this method you must implement a
           major redraw of the display, updating all
           Map elements and after that all Entities.
           This is only a single frame though.
           Note that event_list may be empty.'''
        return

    def update_inventory(self):
        '''We do not have to care about the object of
           a DropsEvent and PicksUpEvent since the 
           ControlEngine has generated an respective 
           SpawnEvent and DeleteEvent, which is already 
           rendered. All that is left is to update the 
           inventory visualisation. You can use that
           to enter a frame for the Entities as well.'''
        self.display_static_frame()
        return

    def display_PerceptionEvents(self, event_list):
        '''This method is called with a list of
           instances of PerceptionEvent. You
           have to provide an implementation
           whicht displays them one by one, 
           possibly awaiting user confirmation.
           event_list may be empty. Please do
           not continue animation of other
           Entities during the perception so
           there are no background actions 
           which may pass unnoticed.'''
        # Update the frame counter though.
        self.update_frame_timer()
        return           

    def display_SaysEvents(self, event_list):
        '''This method is called with a list
           of instances of SaysEvent when the
           VisualEngine is ready to display
           what Entities say. In this method
           you have to compute a number of
           frames for displaying text and
           animation for each SaysEvent 
           depending on how long the text is. 
           Once you start displaying the text, 
           you have to notify the affected 
           Entity by calling
           Entity.starts_speaking(self, frames, framerate).
           You should catch some user 
           confirmation. Please do not continue 
           animation of other Entities so there 
           are no background actions which may 
           pass unnoticed.'''
        # Don't forget the frame counter in each frame.
        self.update_frame_timer()
        return

############################################################
# Asset Engine

class AssetEngine:
    '''This is the base class for an AssetEngine.
       It is used to retrieve media data - images, 
       animations, 3D models, sound. Subclass 
       this with an Engine that actually fetches
       data - the default implementation raises
       a shard.ShardException.'''

    def fetch_asset(self, asset_identifier):
        '''This is the main method of the AssetEngine.
           It retrieves the file specified in
           asset_identifier and returns the content.
           The type of object returned is determined
           by the actual implementation of AssetEngine, 
           VisualEngine and Entity. This method is
           encouraged to do advanced operations like
           fetching and decompressing zip files, 
           format conversion and the like.
           Since fetch_asset() is a synchronous method, 
           it should cancel after a timeout and raise
           a shard.ShardException if it failes to retrieve
           the data.
           Since the AssetEngine is only created once, 
           fetch_asset() should do some asset caching
           to prevent unnecessary file or network
           access.'''
        raise ShardException("This is just a dummy fetch_asset() method. "
                        + "Please use a real implementation of AssetEngine.")

############################################################
# Exceptions

class ShardException:
    '''This is the base class of Shard-related
       exceptions. Shard Implementations should
       raise an instance of this class when 
       appropriate, providing an error description.'''

    def __init__(self, error_description):
        self.error_description = error_description

    def __repr__(self):
        # This is called and should return a
        # string representation which is shown
        return self.error_description
