'''Shard - A Client-Server System for Interactive 
   Storytelling by means of an Adventure Game Environment

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
    '''Shard Event base class.'''

    def __init__(self,Identifier):
        '''This constructor must be called with
           an unique identifier for the object
           (player, item, NPC) which is affected
           by this event.'''
        # By defining it here, the variable is
        # part of the instance object, not the
        # class object. See "Class definitions"
        # in the Python Reference Manual.
        self.Identifier = Identifier

####################
# Attempt events

class AttemptEvent(Event):
    '''This is the base class for attempt events
       by the player or NPCs.'''

    def __init__(self,Identifier,TargetIdentifier):
        '''When sent by the client, TargetIdentifier
           must describe the desired direction of
           the attempt. The PyGameClient uses a 
           two-dimensional map with rectangular
           elements, so TargetIdentifier may be one 
           of "N","NE","E","SE","S","SW","W","NW".
           The server determines what is being 
           looked at / picked up / manipulated / 
           talked to in that direction, and 
           replaces the direction string with an item, 
           NPC or player identifier if appropriate.'''
        self.Identifier       = Identifier
        self.TargetIdentifier = TargetIdentifier

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

    def __init__(self,Identifier,ItemIdentifier,TargetIdentifier):
        '''An attempt to drop the item identified by
           ItemIdentifier. When sent by the client,
           TargetIdentifier must describe the 
           desired direction. The PyGameClient
           uses a two-dimensional map with rectangular
           elements, so TargetIdentifier may be one of 
           "N","NE","E","SE","S","SW","W","NW". Note 
           that this attempt can turn out as a "use" 
           action, for example when dropping a key 
           on a padlock. In this case, the server 
           replaces the direction with an item 
           identifier and passes that on to the
           story engine.'''
        self.Identifier       = Identifier
        self.ItemIdentifier   = ItemIdentifier
        self.TargetIdentifier = TargetIdentifier

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

    def __init__(self,Identifier,Direction):
        '''Direction is a description as in
           the TriesToMoveEvent.'''
        self.Identifier = Identifier
        self.Direction  = Direction

class PicksUpEvent(ConfirmEvent):
    '''This is a server confirmation of a
       TriesToPickUpEvent issued by the player
       or an NPC.'''

    def __init__(self,Identifier,ItemIdentifier):
        '''ItemIdentifier identifies the item to
           pick up. This item should be known to
           the client.'''
        self.Identifier     = Identifier
        self.ItemIdentifier = ItemIdentifier

class DropsEvent(ConfirmEvent):
    '''This is the server confirmation for an
       attempt to drop an item by the player
       or an NPC.
       This event does normally not occur when the
       drop action evaluates to a "use with" action,
       as described in TriesToDropEvent. I that case
       the item stays in the posession of its owner,
       and some other events are issued.'''

    def __init__(self,Identifier,ItemIdentifier,Direction):
        '''ItemIdentifier identifies the item to be 
           dropped on the map. Direction is a 
           description as in the TriesToMoveEvent.'''
        self.Identifier     = Identifier
        self.ItemIdentifier = ItemIdentifier
        self.Direction      = Direction

class CanSpeakEvent(ConfirmEvent):
    '''This is a server invitation for the player or
       an NPC to speak. Since this Event requires
       immediate user input, it is always executed
       as the last Event of a Message by the 
       VisualEngine.'''

    def __init__(self,Identifier,Sentences):
        '''Sentences is a list of strings for the
           player or NPC to choose from. If this list
           is empty, the client should offer a free-form
           text input.'''
        self.Identifier = Identifier
        self.Sentences  = Sentences

class AttemptFailedEvent(ConfirmEvent):
    '''This is actually not a confirmation, but the
       server announcement that the last AttemptEvent
       sent by the entity identified by Identifier
       failed. This should unblock the entity and
       allow new attempts.'''
    pass

####################
# Unclassified events without a special base class

class PerceptionEvent(Event):
    '''This is a perception for the player or an NPC
       issued by the server, usually the result of 
       a TriesToLookAtEvent.'''

    def __init__(self,Identifier,Perception):
        '''Perception is a string to be displayed
           by the client. When used with an NPC, this
           could be used to feed a memory database.'''
        self.Identifier = Identifier
        self.Perception = Perception

class SaysEvent(Event):
    '''This normally is a reaction to the CanSpeakEvent,
       to be sent by the player. NPCs can speak spontanously,
       in that case a SaysEvent is issued by he Story 
       Engine. Players usually have to send an 
       TriesToTalkToEvent before they are allowed to
       speak.'''

    def __init__(self,Identifier,Text):
        '''Text is a string to be spoken by the entity.'''
        self.Identifier = Identifier
        self.Text       = Text

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

    def __init__(self,Identifier,KeyValueDict):
        '''KeyValueDict is a Python dictionary 
           containing the parameters of the custom
           event.'''
        self.Identifier   = Identifier
        self.KeyValueDict = KeyValueDict

####################
# Passive events

class PassiveEvent(Event):
    '''The base class for events concerning items
       ot NPCs when they are being passed, looked at,
       picked up and the like.'''

    def __init__(self,Identifier,TriggerIdentifier):
        '''The TriggerIdentifier identifies the
           entity that triggered the event. This makes it
           possible to react differently to several
           entities.'''
        self.Identifier        = Identifier
        self.TriggerIdentifier = TriggerIdentifier

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

    def __init__(self,Entity):
        '''Entity is an instance of shard.Entity,
           having a type, identifier, location and
           assets. The server stores the relevant
           information and passes the entity on to
           the client.'''
        self.Entity = Entity

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
       these Events are executed immediately and
       in parallel upon the rendering of the
       Message by the VisualEngine.'''
    
    def __init__(self,Tile,Location):
        '''Tile is a shard map object having a type 
           (obstacle or floor) and an asset.
           Location is an object describing the
           location of the Tile in the game world,
           most probably a tuple of coordinates, but
           possibly only a string like "lobby".
           The server stores the relevant
           information and passes the Tile and the
           Location on to the client.'''
        self.Tile     = Tile
        self.Location = Location

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
       decide which Events happen in parallel and which 
       ones happen sequential. Instances of Message 
       expose a single Python list object as Message.EventList.'''

    def __init__(self,EventList):
        '''Initialize the Message with a list of objects
           derived from shard.Event. An empty list may
           be supplied.'''
        #CHECKME: check the list elements for being
        #         instances of shard.Event here?
        self.EventList = EventList

#    def queueAsFirstEvent(self,Event):
#        '''This is a convenience method. Queue the event 
#           given as the first event to be processed, 
#           shifting other events already queued.'''
#        self.EventList = [Event] + self.Eventlist

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
        self.ClientMessage = Message([])
        self.ServerMessage = Message([])

        # Please note that handleMessages() will run in
        # a background thread. NEVER attempt to change
        # data structures in handleMessages() AND other
        # methods like sendMessage() or grabMessage()
        # unless you lock them thread-safely. A simple
        # solution is to set flags in those methods,
        # obeying the rule that only one method may set
        # them to True and one may set them to False.
        self.ServerMessageAvailable = False
        self.ClientMessageAvailable = False
        
        # This list serves as a queue for client messages.
        # To be thread-safe, it is not directly accessed
        # by handleMessages()
        self.ClientMessageQueue = []

        # This is the flag which is set when shutdown()
        # is called.
        self.ShutdownFlag = False

        # And this is the one for the confirmation.
        self.ShutdownConfirmed = False

        # DELETE
        self.SentNoMessageAvailable = False

    def handleMessages(self):
        '''The task of this method is to do whatever is
           necessary to send client messages and obtain 
           server messages. It is meant to be the back end 
           of sendMessage() and grabMessage(). Put some 
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
        LocalClientMessage = Message([])
        LocalServerMessage = Message([])

        # Just as in the main thread, a queue
        # for server messages comes in handy in case 
        # the client does not catch up fetching the 
        # messages. Since this example sends only
        # one message, we do not really need it though.
        ServerMessageQueue = []

        # A flag for a client init request
        ClientSentInit = False

        # Run thread as long as no shutdown is requested
        while not self.ShutdownFlag:
            # read client message
            if self.ClientMessageAvailable:
                # First do the work
                LocalClientMessage = self.ClientMessage

                # Then notify thread-safely by setting the flag.
                # Only handleMessages() may set it to False.
                self.ClientMessageAvailable = False

                # Here we should do something useful with the
                # client message, like sending it over the
                # network. In this example, we check for the
                # init message and silently discard everything
                # else.
                for CurrentEvent in LocalClientMessage.EventList:
                    if isinstance(CurrentEvent,InitEvent):
                        ClientSentInit = True

            # When done with the client message, it is time
            # to fetch a server message and hand it over
            # to the client. In this example, we generate
            # a message ourselves once the client has
            # requested init.
            if ClientSentInit:
                # Build a message
                EventList = [ EnterRoomEvent() ]
                EventList.append( SpawnEvent( Entity("PLAYER","player",(0,0),"") ) )
                EventList.append( RoomCompleteEvent() )
                EventList.append( PerceptionEvent("player","A fake server message generated by the Client Interface.") )

                # Append a message to the queue
                ServerMessageQueue.append( Message(EventList) )

                # Set ClientSentInit to false again, so the
                # events are only set once
                ClientSentInit = False
                
            # Is the client ready to read? 
            if not self.ServerMessageAvailable:
                try:
                    # Pull the next one from the queue and
                    # delete it there.
                    self.ServerMessage = ServerMessageQueue[0]
                    del ServerMessageQueue[0]
 
                    # Set the flag for the main thread. This is
                    # thread-safe since it may only be set to
                    # True here.
                    self.ServerMessageAvailable = True

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
        self.ShutdownConfirmed = True
        raise SystemExit

    def sendMessage(self,Message):
        '''This method is called by the client 
           ClientControlEngine with a message ready to be sent to
           the server. The Message object given is an
           an instance of shard.Message. This method
           must return immediately to avoid blocking
           the client.'''
        # EXAMPLE
        # First we put this message in the local queue.
        self.ClientMessageQueue.append(Message)

        # self.ClientMessageAvailable is used as a
        # thread-safe flag. It may only be set to True
        # here and may only be set to False in
        # handlemessages().
        if not self.ClientMessageAvailable:
            # Pull the next one from the queue and
            # delete it there. Note that
            # handleMessages does not access the queue.
            self.ClientMessage = self.ClientMessageQueue[0]
            del self.ClientMessageQueue[0]
            self.ClientMessageAvailable = True
            return
        else:
            # Uh, this is bad. The client just called
            # sendMessage(), but the previous message
            # has not yet been collected by 
            # handleMessages(). In this case a new 
            # thread should be spawned which
            # waits until handleMessages() is ready
            # to receive a new message. Since this is
            # a simple example implementation, we'll
            # leave the message in the queue and hope
            # for some more calls to sendMessage() that
            # will eventually shift it forward until
            # it can be delivered.
            return

    def grabMessage(self):
        '''This method is called by the client 
           ClientControlEngine to obtain a new server message.
           It must return an instance of shard.Message,
           and it must do so immediately to avoid
           blocking the client. If there is no new
           server message, it must return an empty
           message.'''
        # EXAMPLE
        # Set up a local copy
        LocalServerMessage = Message([])

        # self.ServerMessageAvailable is used as a 
        # thread-safe flag. It may only be set to True 
        # in handleMessages() and may only be set to
        # False here, so no locking is required.
        if self.ServerMessageAvailable:
            # First grab it, so the thread does not
            # overwrite it
            LocalServerMessage = self.ServerMessage

            # DELETE
            print( "grabServerMessage: Message available, got :"+str(LocalServerMessage) )

            # Now set the flag
            self.ServerMessageAvailable = False

            # DELETE
            print( "grabServerMessage: ServerMessageAvailable is now '"+str(self.ServerMessageAvailable)+"'.")
            self.SentNoMessageAvailable = False
            # DELETE

            return LocalServerMessage
        else:
            # DELETE
            if not self.SentNoMessageAvailable:
                print( "grabServerMessage: no Message available (ServerMessageAvailable False).")
                self.SentNoMessageAvailable = True
            # DELETE

            # A Message must be returned, so create
            # an empty one
            return Message([])

    def shutdown(self):
        '''This method is called when the client is
           about to exit. It should notify 
           handleMessages() to raise SystemExit to stop 
           the thread properly. shutdown() must return 
           True when handleMessages() received the 
           notification and is about to exit.'''
        # EXAMPLE
        # Set the flag to be caught by handleMessages()
        self.ShutdownFlag = True

        # Wait for confirmation (blocks interface and client!)
        while not self.ShutdownConfirmed:
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

    def __init__(self,Type,Identifier,Location,Asset):
        '''Type is one of the strings "PLAYER", "NPC",
           "ITEM".

           Identifier must be an object whose string 
           representation yields an unique 
           identification.

           Location is an object describing the
           location of the Entity in the game world,
           most probably a tuple of coordinates, but
           possibly only a string like "lobby". The
           Location should not be too precise when
           using coordinates, since it is not
           incremented during movement. It should
           rather store where the entity will be
           once the next movement is complete.

           Asset finally is preferably a string
           with a file name or an URI of a media
           file containing the data for visualizing
           the Entity. Do not put large objects here
           since Entities are pushed around quite a
           bit and transfered across the network.
           The VisualEngine may fetch the asset and
           attach it to the instance of the Entity.'''
        self.Type       = Type
        self.Identifier = Identifier
        self.Location   = Location
        self.Asset      = Asset

        # Store current direction and movement
        # "At dawn, look to the east." -Gandalf 
        #        in Peter Jackson's "Two Towers"
        self.Direction = 'E'
        self.Moves     = False

        # Other flags for Entity actions
        self.Speaks  = False
        self.PicksUp = False
        self.Drops   = False

        # Call customInit() for application
        # dependent setup
        self.customInit()

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

    def customInit(self):
        '''You should not override Entity.__init__()
           since it performs required setup. Instead,
           override this method to perform custom
           initialization. It is called from
           Entity.__init__().'''
        return

    def processMovesToEvent(self,Event):
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
        self.Direction = Event.Direction

        # Call the 2D movement function.
        self.process2dDirection(Event.Direction)

    def process2dDirection(self,Direction):
        '''This is an auxiliary default method
           called from processMovesToEvent(). It
           implements  a movement on a 2D map 
           with rectangular elements. If you 
           override processMovesToEvent() (to 
           include animation for example), be 
           sure to call
           self.process2dDirection(Event.Direction)
           or implement the update yourself.'''
        # EXAMPLE
        # In a contract-like design, we should
        # check preconditions like
        # isinstance(Event,MovesToEvent)
        # or len(self.Location) == 2.
        #
        # We use shard.DirectionVector which maps
        # direction strings like "NW", "SE" to
        # a 2D vector tuple

        # x coordinate
        self.Location[0] = self.Location[0] + DirectionVector[Direction][0]

        # y coordinate
        self.Location[1] = self.Location[1] + DirectionVector[Direction][1]

    def processCustomEntityEvent(self,KeyValueDict):
        '''This method is called by the Client with
           the key-value dict of an CustomEntityEvent
           which possibly changes the client state. 
           The interpretation of CustomEntityEvents 
           is entirely up to the Entity. The default 
           implementation does nothing, so you 
           should override it.'''
        pass

    def startsMoving(self,Frames,Framerate):
        '''The VisualEngine is responsible for the
           gradual movement of the Entity to the
           target, but not for the animation. It
           calls this method once to signal that
           the Entity starts moving now. Entities
           may implement a flag or some logic
           which changes their graphical 
           representation on every frame, yielding
           an animation. startsMoving() is always
           called after processMovesToEvent(), so
           the Entity knows about the direction.
           The VisualEngine provides the number of
           frames for the movement and the Framerate.
           Thus the entity can adapt to different
           frame rates by adjusting how many frames
           an image is shown. The Entity is advised
           to stop the animation once the number
           of Frames given has passed, but it does
           not need to do so.
           The default implementation simply sets
           the variable self.Moves to True.'''
        self.Moves = True

#    def stopsMoving(self):
#        '''Called when the VisualEngine has
#           completed the movement. This should
#           trigger a stop of the movement 
#           animation. The default implementation
#           sets self.Moves to False.'''
#        self.Moves = False

    def startsSpeaking(self,Frames,Framerate):
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
           Framerate. Thus the entity can adapt to 
           different frame rates by adjusting how 
           many frames an image is shown. 
           The Entity is advised to stop the 
           animation once the number of Frames 
           given has passed, but it does not need 
           to do so.
           The default implementation simply sets 
           the variable self.Speaks to True.'''
        self.Speaks = True

#    def stopsSpeaking(self):
#        '''Called when the VisualEngine is about
#           to erase the spoken text from the 
#           screen. This should trigger a stop of 
#           the speaking animation. The default 
#           implementation sets self.Speaks
#           to False.'''
#        self.Speaks = False

    def startsPickingUp(self,Frames,Framerate):
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
           frames for the action and the Framerate.
           Thus the entity can adapt to different
           frame rates by adjusting how many frames
           an image is shown. The Entity is advised
           to stop the animation once the number
           of Frames given has passed, but it does
           not need to do so.
           The default implementation simply sets 
           the variable self.PicksUp to True.'''
        self.PicksUp = True

    def startsDropping(self,Frames,Framerate):
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
           frames for the action and the Framerate.
           Thus the entity can adapt to different
           frame rates by adjusting how many frames
           an image is shown. The Entity is advised
           to stop the animation once the number
           of Frames given has passed, but it does
           not need to do so.
           The default implementation simply sets 
           the variable self.PicksUp to True.'''
        self.Drops = True

############################################################
# Tiles

class Tile:
    '''A Tile is an element of a two-dimensional map.
       It is never meant to perform any active logic,
       so its only property is a Type and an Asset.'''

    def __init__(self,Type,Asset):
        '''Type must be a string describing the Tile
           type. Currently supported are "OBSTACLE"
           and "FLOOR", describing whether the player
           or NPCs can move across the Tile.
           
           Asset is preferably a string with a file 
           name or an URI of a media file containing 
           the data for visualizing the Tile.'''
        self.Type  = Type
        self.Asset = Asset

############################################################
# Utilities

# Set up a DirectionVector for 2D movement
# processing. It is assumed that (0,0) is
# the lower left corner
DirectionVector = { 'N'  : ( 0, 1) ,
                    'NE' : ( 1, 1) ,
                    'E'  : ( 1, 0) ,
                    'SE' : ( 1,-1) ,
                    'S'  : ( 0,-1) ,
                    'SW' : (-1,-1) ,
                    'W'  : (-1, 0) ,
                    'NW' : (-1, 1) }

############################################################
# Client Control Engine

class ClientControlEngine:
    '''An instance of this class is the main engine in every
       Shard client. It connects to the Client Interface and
       to the VisualEngine, passes Events and keeps track
       of Entities. It is normally instantiated in a small
       setup script "run_shardclient.py".'''

    ####################
    # Init

    def __init__(self,ClientInterfaceInstance,VisualEngineInstance):
        '''The ClientControlEngine must be instantiated with an
           instance of shard.ClientInterface which handles
           the connection to the server or supplies events
           in some other way, and an instance of 
           shard.VisualEngine which graphically renders the
           game action.'''

        self.ClientInterface = ClientInterfaceInstance
        self.VisualEngine    = VisualEngineInstance

        # Set up flags used by self.run()
        self.AwaitConfirmation = False

        # A dictionary that maps Event classes to functions 
        # to be called for the respective event.
        # I just love to use dicts to avoid endless
        # if... elif... clauses. :-)
        self.EventDict = {AttemptFailedEvent : self.processAttemptFailedEvent ,
                          CanSpeakEvent      : self.processCanSpeakEvent ,
                          DropsEvent         : self.processDropsEvent ,
                          MovesToEvent       : self.processMovesToEvent ,
                          PicksUpEvent       : self.processPicksUpEvent ,
                          CustomEntityEvent  : self.processCustomEntityEvent ,
                          PerceptionEvent    : self.processPerceptionEvent ,
                          SaysEvent          : self.processSaysEvent ,
                          ChangeMapElementEvent : self.processChangeMapElementEvent ,
                          DeleteEvent        : self.processDeleteEvent ,
                          EnterRoomEvent     : self.processEnterRoomEvent ,
                          RoomCompleteEvent  : self.processRoomCompleteEvent ,
                          SpawnEvent         : self.processSpawnEvent }

        # self.EntityDict keeps track of all active Entites.
        # It uses the Identifier as a key, assuming that is
        # is unique.
        self.EntityDict = {}

        # A dict for Entites which have been deleted, for
        # the convenience of the VisualEngine. Usually it
        # should be cleared after each rendering.
        self.DeletedEntitiesDict = {}

        # A list of Tiles for the current room, for
        # the convenience of the VisualEngine.
        self.TileList = []

        # self.Map is an attempt of an efficient storage of
        # an arbitrary two-dimensional map. To save space,
        # only explicitly defined elements are stored. This
        # is done in a dict of dicts, hopefully speeding up
        # the retrieval of elements by avoiding tests 
        # element-by-element. Keys are numbers. Access the
        # elemty using self.Map[x][y]. The lower left element
        # is self.Map[0][0].
        self.Map = {}

        # The ClientControlEngine examines the Events of a Server
        # Message and applies them. Events for special
        # consideration for the VisualEngine are collected
        # in a Message for the VisualEngine.
        # The ClientControlEngine has to empty the Message once 
        # the VisualEngine has rendered all Events.
        self.VisualEngineMessage = Message([])

        # We attach custom flags to the Message to notify
        # the VisualEngine whether an EnterRoomEvent or
        # RoomCompleteEvent occured, so it does not have
        # to scan the Events.
        self.VisualEngineMessage.HasEnterRoomEvent    = False
        self.VisualEngineMessage.HasRoomCompleteEvent = False

        # In self.ClientMessage we collect Client Events to be
        # sent to the server in each loop.
        self.ClientMessage = Message([])
        
        # DELETE
        self.GotEmptyMessage = False
        print("ClientControlEngine: __init__ complete.")
        # DELETE

        # TODO: set up the inventory

    ####################
    # Main Loop

    def run(self):
        '''Main loop of the ClientControlEngine. This is
           a blocking method. It calls all the process methods
           to process Events.'''

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
        self.ClientInterface.sendMessage( Message( [InitEvent()] ) )

        while not self.VisualEngine.ExitRequested:
            # grabMessage must and will return a Message, but
            # it possibly has an empty EventList.
            ServerMessage = self.ClientInterface.grabMessage()

            # DELETE
            if len(ServerMessage.EventList):
                print( "ClientControlEngine: got ServerMessage: \n"+str(ServerMessage.EventList) )
                self.GotEmptyMessage = False
            elif not self.GotEmptyMessage:
                print("ClientControlEngine: got an empty ServerMessage.")
                self.GotEmptyMessage = True
            # DELETE

            # First handle the events in the ClientControlEngine,
            # gathering Entities and Map Elements and preparing
            # a Message for the VisualEngine
            for CurrentEvent in ServerMessage.EventList:
                # This is a bit of Python magic. 
                # self.EventDict is a dict which maps classes to handling
                # functions. We use the class of the Event supplied as
                # a key to call the appropriate handler, and hand over
                # the Event.
                self.EventDict[CurrentEvent.__class__](CurrentEvent)

            # Now that everything is set and stored, call
            # the VisualEngine to render the messages.

            # First hand over / update the necessary data.
            self.VisualEngine.EntityDict          = self.EntityDict
            self.VisualEngine.DeletedEntitiesDict = self.DeletedEntitiesDict
            self.VisualEngine.TileList            = self.TileList
            self.VisualEngine.Map                 = self.Map

            # This call may take an almost arbitrary amount
            # of time, since there may be long actions to
            # be shown by the VisualEngine.
            # Notice: renderMessage() must be called regularly
            # even if the server Message and thus the
            # VisualEngineMessage are empty!
            self.VisualEngine.renderMessage(self.VisualEngineMessage)

            # The VisualEngine returned, the Server Message has
            # been applied and rendered. Clean up.
            self.VisualEngineMessage = Message([])
            self.DeletedEntitiesDict = {}
            self.VisualEngineMessage.HasEnterRoomEvent    = False
            self.VisualEngineMessage.HasRoomCompleteEvent = False

            # Up to now, we did not care whether the server Message
            # had any events at all. But we only send a 
            # MessageAppliedEvent if it had.
            if len(ServerMessage.EventList)>0:
                self.ClientMessage.EventList.append( MessageAppliedEvent() )

            # TODO:
            # If there has been a Confirmation for a LookAt or TriesToManipulate,
            # unset "AwaitConfirmation" flag

            # If we do not await a Confirmation anymore,
            # we evaluate the player input if any.
            # The VisualEngine might have collected some
            # player input and converted it to events.
            if len(self.VisualEngine.PlayerEventList)>0 and not self.AwaitConfirmation:
                # We queue player triggered Events before 
                # MessageAppliedEvent so the server processes
                # all Events before sending anything new.
                self.ClientMessage.EventList = \
                    self.VisualEngine.PlayerEventList + self.ClientMessage.EventList

                # Since we had player input, we now await confirmation
                self.AwaitConfirmation = True

            # If this iteration yielded any Events, send them.
            if len(self.ClientMessage.EventList)>0:
                self.ClientInterface.sendMessage(self.ClientMessage)

                # Clean up
                self.ClientMessage = Message([])

            # OK, iteration done. If no exit requested,
            # grab the next server event!

        # exit has been requested
        
        # DELETE
        print("ClientControlEngine.run: exit requested from VisualEngine, shutting down interface...")

        # stop the Client Interface thread
        self.ClientInterface.shutdown()

        # DELETE
        print("ClientControlEngine.run: shutdown confirmed.")

        # TODO:
        # possibly exit cleanly from the VisualEngine here

        return

    ####################
    # Auxiliary Methods

    def processAttemptFailedEvent(self,Event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        #    ControlEngine: if there was a Confirmation and it has been applied
        #    or if there was an AttemptFailedEvent: unset "AwaitConfirmation" flag
        pass

    def processCanSpeakEvent(self,Event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        #    ControlEngine: if there was a Confirmation and it has been applied
        #    or if there was an AttemptFailedEvent: unset "AwaitConfirmation" flag

        # Pass on the Event.
        self.VisualEngineMessage.EventList.append(Event)

    def processDropsEvent(self,Event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        # Remove the Entity from the Inventory
        # Add it to the EntityDict, setting the coordinates from direction
        # Queue the DropsEvent (for Animation) and a SpawnEvent for the VisualEngine
        #
        #    ControlEngine: if there was a Confirmation and it has been applied
        #    or if there was an AttemptFailedEvent: unset "AwaitConfirmation" flag
        pass

    def processMovesToEvent(self,Event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        # 
        # ControlEngine: if there was a Confirmation and it has been applied
        # or if there was an AttemptFailedEvent: unset "AwaitConfirmation" flag
        #
        # ControlEngine: pass Events to Entities
        #     Entity: change Location, set graphics, custom actions
        # ControlEngine: pass Message/Events to VisualEngine
        pass

    def processPicksUpEvent(self,Event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        # Remove from the EntityDict
        # Save in DeletedEntitiesDict
        # Move the Entity to the Inventory
        # Queue the PicksUpEvent (for Animation) and a DeleteEvent for the VisualEngine
        #
        #    ControlEngine: if there was a Confirmation and it has been applied
        #    or if there was an AttemptFailedEvent: unset "AwaitConfirmation" flag
        pass

    def processCustomEntityEvent(self,Event):
        '''The key-vlaue dict of a CustomEntiyEvent 
           is just passed on to the Entity.'''
        self.EntityDict[Event.Identifier].processCustomEntityEvent(Event.KeyValueDict)

    def processPerceptionEvent(self,Event):
        '''A Perception must be displayed by the 
           VisualEngine, so it is queued in a Message passed
           from the ClientControlEngine.'''
        #    ControlEngine: if there was a Confirmation (here: for LookAt,Manipulate)
        #    and it has been applied
        #    or if there was an AttemptFailedEvent: unset "AwaitConfirmation" flag
        self.VisualEngineMessage.EventList.append(Event)

    def processSaysEvent(self,Event):
        '''The VisualEngine usually must display the 
           spoken Text. Thus the Event is put in the
           Event queue for the VisualEngine.
           The VisualEngine is going to notify
           the Entity once it starts speaking so it
           can provide an animation.'''
        self.VisualEngineMessage.EventList.append(Event)

    def processChangeMapElementEvent(self,Event):
        '''Store the Tile given in self.Map,
           a dict of dicts with x- and
           y-coordinates as keys. Also save
           it for the VisualEngine.'''
        try:
            # see if a dict for the column (x coordinate)
            # already exists
            self.Map[Event.Location[0]]
        except KeyError:
            self.Map[Event.Location[0]] = {}

        # possibly overwrite existing Tile
        self.Map[Event.Location[0]][Event.Location[1]] = Event.Tile

        # Append the Tile to a list for easy
        # fetching of the Tile's asset
        self.TileList.append(Event.Tile)

        # Append the Event to the queue for the VisualEngine.
        self.VisualEngineMessage.EventList.append(Event)

    def processDeleteEvent(self,Event):
        '''Save the Entity to be deleted in the
           DeletedEntitiesDict for the 
           VisualEngine, then remove it from the
           EntityDict.'''

        # DELETE
        # This is just a hack, see TODO for run() for details
        if Event.Identifier in self.EntityDict.keys():
        # DELETE

            # Save the Entity in the DeletedEntitiesDict
            # to notify the VisualEngine
            self.DeletedEntitiesDict[Event.Identifier] = self.EntityDict[Event.Identifier]

            # Now remove the Entity
            del self.EntityDict[Event.Identifier]

            # Append the Event to the queue for the VisualEngine.
            # The VisualEngine needs the event for knowing
            # when exactly to remove the Entity.
            self.VisualEngineMessage.EventList.append(Event)

        # DELETE
        else:
            print("processDeleteEvent: Entity to delete does not exist.")
        # DELETE

    def processEnterRoomEvent(self,Event):
        '''An EnterRoomEvent means the server is
           about to send a new map, respawn the
           player and send items and NPCs. So
           this method  empties all data 
           structures and passes the Event on to 
           the VisualEngine.'''
        # There possibly will be no more confirmation
        # for past attempts, so do not wait for them
        self.AwaitConfirmation = False

        # All Entities in this room have to be sent.
        # No use keeping old ones around, expecially with old
        # locations.
        self.EntityDict = {}

        # Clear the dict of Entites which have been deleted.
        self.DeletedEntitiesDict = {}

        # Clear the list of Tiles for the room.
        self.TileList = []

        # Awaiting a new map!
        self.Map = {}

        # Finally set the flag in the Message
        # for the VisualEngine and queue the Event
        # so the VisualEngine knows what happend after
        # that.
        self.VisualEngineMessage.HasEnterRoomEvent = True
        self.VisualEngineMessage.EventList.append(Event)

    def processRoomCompleteEvent(self,Event):
        '''RoomCompleteEvent notifies the client that
           the player, all map elements, items and
           NPCs have been transfered. By the time the
           Event arrives the ClientControlEngine should
           have saved all important data in data
           structures. So the Event is queued for
           the VisualEngine here.'''
        # This is a convenience flag so the VisualEngine
        # does not have to scan the EventList.
        self.VisualEngineMessage.HasRoomCompleteEvent = True

        # Queue the Event. All Events after this are
        # rendered.
        self.VisualEngineMessage.EventList.append(Event)

    def processSpawnEvent(self,Event):
        '''Add the Entity given to the EntityDict
           and pass the SpawnEvent on to the VisualEngine.'''
        self.EntityDict[Event.Entity.Identifier] = Event.Entity
        self.VisualEngineMessage.EventList.append(Event)

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

    def __init__(self,AssetEngine,Framerate):
        '''This method initializes the VisualEngine.
           AssetEngine must be an instance of
           shard.AssetEngine or a subclass.
           Framerate must be an integer and sets
           the maximum (not minimum ;-) ) Frames per
           second the client will run in.
           If you override this method, make sure 
           you do all these initiaizations, too.
           For your convenience there is a method
           self.customInit() which you can savely
           override. 
           This method must not block, it has to 
           return once everything is set up.'''
        # Get Framerate and AssetEngine from parameters
        self.Framerate = Framerate
        self.AssetEngine = AssetEngine

        # Set how long actions like a movement from
        # Map element to Map element take, in seconds.
        self.ActionTime = 0.5

        # A list of Events derived from player input,
        # cleared and updated on each rendering
        self.PlayerEventList = []

        # Since it represents the GUI, the VisualEngine
        # is responsible for catching an
        # exit request by the user. This value is
        # checked in the ClientControlEngine main loop.
        self.ExitRequested = False

        # Variables to be filled by the ClientControlEngine
        # before each call to renderMessage()
        self.EntityDict          = {}
        self.DeletedEntitiesDict = {}
        self.TileList            = []
        self.Map                 = {}

        # Are we waiting for a RoomCompleteEvent after
        # an EnterRoomEvent? Upon initialization this
        # is True, since a room has not yet been
        # transfered.
        self.WaitingForRoomCompleteEvent = True

        # See the method for explaination.
        self.customInit()

        return

    ####################
    # VisualEngine Main Loop

    def renderMessage(self,Message):
        '''This is the main method of the VisualEngine.
           It is called regularly by the ClientControlEngine
           with a list of Events to display (note: the
           list may be empty). It may take all the time 
           it needs to render the action, just a couple 
           or even hundreds of frames, but it must 
           return once the Events have been displayed. 
           It must neither block completely nor run in 
           a thread since the ClientControlEngine has to 
           grab new Events and change state between 
           calls to renderMessage(). Put that way, 
           renderMessage() is simply a part of 
           ClientControlEngine.run().
           You should normally not override this method
           unless you have to do some really advanced
           stuff. Overriding the other methods of this
           class (which in turn are called from 
           renderMessage() ) should be just fine. See 
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

        # Reset the list of Events triggered by 
        # player actions
        self.PlayerEventList = []
        
        # Compute the number of frames per action.
        # See __init__() for details.
        ActionFrames = int( self.ActionTime * self.Framerate )

        ####################
        # Check EnterRoomEvent

        # The first thing to check for is if there has
        # been an EnterRoomEvent. For our convenience,
        # the ControlEngine has set up a flag in the
        # message, so we simply check that instead
        # of scanning the whole list.
        if Message.HasEnterRoomEvent:
            # When this arrives here all data scructures
            # have already been cleared and possibly
            # populated with new Entites and a new Map.
            # So we have to ignore everything before
            # an EnterRoomEvent.

            # See the method for explaination
            self.displayEnterRoomEvent()
            
            # Set a flag that we are waiting
            # for RoomCompleteEvent
            self.WaitingForRoomCompleteEvent = True

        ####################
        # Check RoomCompleteEvent

        # Next, as long as we are waiting for a
        # RoomCompleteEvent, nothig will be rendered
        # and no player input is accepted.
        if self.WaitingForRoomCompleteEvent:
            # The ControlEngine has set a flag for
            # our convenience.
            if Message.HasRoomCompleteEvent:
                # By the time the Event arrives the 
                # ControlEngine has gathered all important
                # data and handed them over to us, so wen can
                # build a new screen.

                # Load and store Assets for Tiles and 
                # Entities using the AssetEngine
                for CurrentEntity in self.EntityDict.values():

                    AssetToFetch = CurrentEntity.Asset

                    try:
                        RetrievedAsset = self.AssetEngine.fetchAsset(AssetToFetch)
                    except:
                        # See the method for explaination
                        self.displayAssetException(AssetToFetch)

                    # After a RoomCompleteEvent all Entites
                    # are freshly created instances. We
                    # replace the string describing the
                    # asset by the data object returned
                    # by the AssetEngine.
                    CurrentEntity.Asset = RetrievedAsset

                for CurrentTile in self.TileList:

                    AssetToFetch = CurrentTile.Asset

                    try:
                        RetrievedAsset = self.AssetEngine.fetchAsset(AssetToFetch)
                    except:
                        # See the method for explaination
                        self.displayAssetException(AssetToFetch)

                    # After a RoomCompleteEvent all Tiles
                    # are freshly created instances. We
                    # replace the string describing the
                    # asset by the data object returned
                    # by the AssetEngine.
                    CurrentTile.Asset = RetrievedAsset

                # See the method for explaination
                self.displayRoomCompleteEvent()

                # Delete everything in the EventList up to and
                # including the RoomCompleteEvent
                while not isinstance(Message.EventList[0],RoomCompleteEvent):
                    del Message.EventList[0]
                
                # Arrived at RoomCompleteEvent. 
                # Delete it as well.
                del Message.EventList[0]

                # No more waiting!
                self.WaitingForRoomCompleteEvent = False

            else:
                # If there is no RoomCompleteEvent in that Message,
                # ignore everything.

                # Technically this waiting corresponds to a
                # frame, though we do not render anything.

                # See method for explaination.
                self.updateFrameTimer()

                # Discard and check the next Message.
                return

        ####################
        # Grouping Event List

        # If we arrive here, we are ready to render all the
        # Events that are left in the EventList.

        # Messages sent by the server describe the action
        # of a certain period of time. They are divided
        # into groups of parallel Events here. The division
        # is simple: group all subsequent Events that do
        # not affect the same identifier.

        # TODO:
        # We could and perhaps should do some checks here
        # to prevent nonsense:
        # Added Entities may not do anything before they
        # appear.
        # Deleted Entites may act until they disappear.
        # (Get the Entity from the deletedList then, since
        # it is already deleted in the EntityDict.)

        # Make up an empty list of IDs
        CollectedIdentifiers = []

        # make up an empty list of event lists and add an
        # empty list
        GroupedEvents = [[]]

        # make a buffer for the CanSpeakEvent
        BufferedCanSpeakEvent = Event("DummyIdentifier")
        
        # buffer for an Identifier
        Identifier = ''
        
        for CurrentEvent in Message.EventList:
            if isinstance(CurrentEvent,CanSpeakEvent):
                # CanSpeakEvent is taken out of the list
                # to be appended at the very end.
                # Note that this keeps only the very
                # last CanSpeakEvent. There shouldn't be
                # more than one in a message.
                BufferedCanSpeakEvent = CurrentEvent
            
            elif isinstance(CurrentEvent,ChangeMapElementEvent):
                # All these happen in parallel, no Identifier
                # is recorded
                GroupedEvents[-1].append(CurrentEvent)

            else:
                # Now follow the Events where we can
                # detect an Identifier
                if isinstance(CurrentEvent,SpawnEvent):
                    Identifier = CurrentEvent.Entity.Identifier
                else:
                    Identifier = CurrentEvent.Identifier

                if Identifier in CollectedIdentifiers:
                    # append an empty list to the list of
                    # event lists
                    # We've had that Identifier before.
                    # Start a new Event group.
                    GroupedEvents.append([])
                
                    # Start new
                    CollectedIdentifiers = []
                
                else:
                    # Identifier is not yet in
                    # current group
                    CollectedIdentifiers.append(Identifier)

                # Now append the Event to the current group
                GroupedEvents[-1].append(CurrentEvent)

        # All parallel Events are grouped now.            
        # Append the CanSpeakEvent if it is there.
        if isinstance(BufferedCanSpeakEvent,CanSpeakEvent):
            GroupedEvents.append( [BufferedCanSpeakEvent] )

        ####################
        # Render Groups

        # Now it's no good, we finally have to render some
        # frames!
        # GroupedEvents now consists of lists of parallel
        # Events. MovesTo, Drops and PicksUpEvents take the
        # same number of frames to render, which is given by
        # self.ActionTime * self.Framerate. During a 
        # SaysEvent or a PerceptionEvent, animation may even
        # stop for some time. These Events are displayed last.

        for EventList in GroupedEvents:
            if len(EventList) == 0 :
                # No Events in EventList!
                # See the method for explaination.
                self.displayStaticFrame()

                # Any player input?
                # See the method for explaination.
                self.collectPlayerInput()

                return

            # We have at least one Event.

            if isinstance(EventList[0],CanSpeakEvent):
                # See the method for explaination.
                self.displayCanSpeakEvent(EventList[0])
                
                return

            # If there was no CanSpeakEvent, we are
            # still here. 

            # See the method for explaination.
            self.filterEvents(EventList)

            # Now we kind of sort the remaining Events.

            PerceptionEventList    = []
            SaysEventList          = []
            MovesToEventList       = []
            ChangeMapElementEventList = []
            SpawnEventList         = []
            DeleteEventList        = []

            HasMultipleFrameAction = False
            HasInventoryAction     = False

            for CurrentEvent in EventList:
                if isinstance(CurrentEvent,PerceptionEvent):
                    # Queue for later use.
                    PerceptionEventList.append(CurrentEvent)

                elif isinstance(CurrentEvent,SaysEvent):
                    # The Entity is notified in
                    # self.displaySaysEvents() because we
                    # do not compute the number of frames here.
                    # Queue for later use.
                    SaysEventList.append(CurrentEvent)

                elif isinstance(CurrentEvent,DropsEvent):
                    # This is a multiple frame action.
                    HasMultipleFrameAction = True

                    # This affects the inventory.
                    HasInventoryAction = True

                    # Notify the Entity that the animation is
                    # about to start. No need to queue the Event.
                    self.EntityDict[CurrentEvent.Identifier].startsDropping(ActionFrames,self.Framerate)

                elif isinstance(CurrentEvent,PicksUpEvent):
                    # This is a multiple frame action.
                    HasMultipleFrameAction = True

                    # This affects the inventory.
                    HasInventoryAction = True

                    # Notify the Entity that the animation is
                    # about to start. No need to queue the Event.
                    self.EntityDict[CurrentEvent.Identifier].startsPickingUp(ActionFrames,self.Framerate)

                elif isinstance(CurrentEvent,MovesToEvent):
                    # This is a multiple frame action.
                    HasMultipleFrameAction = True

                    # Notify the Entity that the animation
                    # is about to start.
                    self.EntityDict[CurrentEvent.Identifier].startsMoving(ActionFrames,self.Framerate)

                    # Queue for later use.
                    MovesToEventList.append(CurrentEvent)

                elif isinstance(CurrentEvent,ChangeMapElementEvent):
                    # Queue for later use.
                    ChangeMapElementEventList.append(CurrentEvent)

                elif isinstance(CurrentEvent,SpawnEvent):
                    # Queue for later use.
                    SpawnEventList.append(CurrentEvent)

                elif isinstance(CurrentEvent,DeleteEvent):
                    # Queue for later use.
                    DeleteEventList.append(CurrentEvent)

            if HasMultipleFrameAction:
                # See the method for explaination.
                self.displayMultipleFrameAction(MovesToEventList)

            # See the method for explaination.
            self.displaySpawnEvents(SpawnEventList)

            # See the method for explaination.
            self.displayDeleteEvents(DeleteEventList)

            # See the method for explaination.
            self.displayChangeMapElementEvents(ChangeMapElementEventList)

            if HasInventoryAction:
                # See the method for explaination.
                self.updateInventory()

            # Now finally render queued blocking events.

            # See the method for explaination.
            self.displayPerceptionEvents(PerceptionEventList)

            # See the method for explaination.
            self.displaySaysEvents(SaysEventList)

            # Here we jump up to the next EventList, if any.

        # All EventLists are rendered now.

        ####################
        # Player Input

        # See the method for explaination.
        self.collectPlayerInput()

        ####################
        # Return to ControlEngine

        return

    ####################
    # Auxiliary Methods To Override

    # TODO:
    # Most docstrings describe 2D stuff (images).
    # Rewrite 2D-3D-agnostic.

    def customInit(self):
        '''When creating a subclass, you should not
           override the standard __init__() method
           of the VisualEngine class. Instead place
           all your custom setup code here. You can 
           initialize your graphics module here and
           display a splash screen. Everything
           is fine, as long as you return. :-)'''
        return

    def displayEnterRoomEvent(self):
        '''This method is called when the VisualEngine
           has encoutered an EnterRoomEvent. You should
           override it, blank the screen here and display
           a waiting message since the VisualEngine is
           going to twiddle thumbs until it receives a 
           RoomCompleteEvent.'''
        return

    def displayAssetException(self,Asset):
        '''This method is called when the AssetEngine
           is unable to retrieve the asset. This is a 
           serious error which prohibits continuation.
           The user should be asked to check his
           installation, file system or network
           connection.'''

        print("VisualEngine.displayAssetException: " \
              + "A required asset (image, animation, sound) could not be fetched. " \
              + "The problematic asset was '" + str(Asset) + "'. Sorry, but I can't go on.")

        raise SystemExit

    def displayRoomCompleteEvent(self):
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

    def updateFrameTimer(self):
        '''Your graphics module might provide a
           timer which must be notified once per
           frame. Do this here and use this method
           wherever you need it. It is also called
           from renderMessage() when appropriate.
           This method may block execution to slow
           the VisualEngine down to a certain
           frame rate.'''
        return

    def filterEvents(self,EventList):
        '''This is method is called with a list of
           parallel Events before they are rendered.
           You can filter Events here, for example
           if they are off-screen. This method
           must change the EventList in place.
           The default is no filtering.'''
        return

    def displayCanSpeakEvent(self,CanSpeakEventInstance):
        '''This method is called when the VisualEngine
           needs to render a CanSpeakEvent. This is the
           last Event rendered before returning to
           the ControlEngine. You have to prompt for
           appropriate user input here and add a
           corresponding SaysEvent to self.PlayerEventList,
           which is evaluated by the ControlEngine.'''
        # Find a player in EntityDict
        for CurrentEntity in self.EntityDict.values():
            if CurrentEntity.Type == "PLAYER":
                self.PlayerEventList.append( SaysEvent(CurrentEntity.Identifier,"Please override displayCanSpeakEvent in the VisualEngine.") )
        # Don't forget the frame counter in
        # your implementation.
        self.updateFrameTimer()
        return

    def displayStaticFrame(self):
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

        self.updateFrameTimer()
        return

    def collectPlayerInput(self):
        '''The module you use for actual graphics
           rendering most probably has a way to
           capture user input. This method is called
           when the VisualEngine has displayed a
           series of Events and wants to capture
           the user's reaction. When overriding this
           method, you have to convert the data
           provided by your module into Shard 
           Events, most probably instances of 
           shard.AttemptEvent. You must append them
           to self.PlayerEventList which is
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

    def displayMultipleFrameAction(self,MovesToEventList):
        '''This method is called when the VisualEngine
           is ready to render Move, Drop or PickUp
           actions. All visible Entities are already
           notified about their state at this point.
           This method must render exactly
           self.ActionFrames frames. You have to 
           compute a movement for each Entity in the 
           list of MovesToEvent instances provided. 
           Note that this list may be empty, but even 
           then you have to render the full number of 
           frames to display PickUp and Drop animations. 
           You might get away with just changing the 
           screen coordinates and calling 
           self.displayStaticFrame().'''
        # Compute start and end position and movement per
        # frame for all moving Entities
 
        # This creates a copy since Framerate is
        # immutable.
        Counter = self.ActionFrames

        while Counter:
        # for each frame:
            # move moving Entities by respective Movement
            # render a graphic for each visible entity
            # The should supply a new one on each call
            # update frame counter
            self.displayStaticFrame()
            Counter = Counter - 1
        return

    def displaySpawnEvents(self,EventList):
        '''This method is called with a list of
           instances of SpawnEvent to be displayed. 
           All you need to do here is adding the 
           new Enties to a list of visible Entities 
           you might have set up and render a static
           frame. Note that EventList may be empty.'''
        return           

    def displayDeleteEvents(self,EventList):
        '''This method is called with a list of 
           instances of DeleteEvent. You need
           to remove the Entites affected from
           your data structures and draw a
           frame without the deleted Entities.
           EventList may be empty. Note that
           the Entities to be removed are
           already gone in self.EventDict,
           so use self.DeletedEntitiesDict
           instead.'''
        return

    def displayChangeMapElementEvents(self,EventList):
        '''This method is called with a list of
           instances of ChangeMapElementEvent.
           There are only visible Map elements
           in the list if you hav implemented
           an according filter in self.filterEvents().
           In this method you must implement a
           major redraw of the display, updating all
           Map elements and after that all Entities.
           This is only a single frame though.
           Note that EventList may be empty.'''
        return

    def updateInventory(self):
        '''We do not have to care about the object of
           a DropsEvent and PicksUpEvent since the 
           ControlEngine has generated an respective 
           SpawnEvent and DeleteEvent, which is already 
           rendered. All that is left is to update the 
           inventory visualisation. You can use that
           to enter a frame for the Entities as well.'''
        self.displayStaticFrame()
        return

    def displayPerceptionEvents(self,EventList):
        '''This method is called with a list of
           instances of PerceptionEvent. You
           have to provide an implementation
           whicht displays them one by one,
           possibly awaiting user confirmation.
           EventList may be empty. Please do
           not continue animation of other
           Entities during the Perception so
           there are no background actions 
           which may pass unnoticed.'''
        # Update the frame counter though.
        self.updateFrameTimer()
        return           

    def displaySaysEvents(self,EventList):
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
           Entity.startsSpeaking(self,Frames,Framerate).
           You should catch some user 
           confirmation. Please do not continue 
           animation of other Entities so there 
           are no background actions which may 
           pass unnoticed.'''
        # Don't forget the frame counter in each frame.
        self.updateFrameTimer()
        return

############################################################
# Asset Engine

class AssetEngine:
    '''This is the base class for an AssetEngine.
       It is used to retrieve media data - images,
       animations, 3D models, sound. Subclass 
       this with an Engine that actually fetches
       data - the default implementation raises
       a shard.Exception.'''

    def fetchAsset(self,AssetIdentifier):
        '''This is the main method of the AssetEngine.
           It retrieves the file specified in
           AssetIdentifier and returns the content.
           The type of object returned is determined
           by the actual implementation of AssetEngine,
           VisualEngine and Entity. This method is
           encouraged to do advanced operations like
           fetching and decompressing zip files,
           format conversion and the like.
           Since fetchAsset() is a synchronous method,
           it should cancel after a timeout and raise
           a shard.Exception if it failes to retrieve
           the data.
           Since the AssetEngine is only created once,
           fetchAsset() should do some Asset caching
           to prevent unnecessary file or network
           access.'''
        raise Exception("This is just a dummy fetchAsset() method. Please use a real implementation of AssetEngine.")

############################################################
# Exceptions

class Exception:
    '''This is the base class of Shard-related
       exceptions. Shard Implementations should
       raise an instance of this class when 
       appropriate, providing an error description.'''

    def __init__(self,ErrorDescription):
        self.ErrorDescription = ErrorDescription

    def __repr__(self):
        # This is called and should return a
        # string representation which is shown
        return self.ErrorDescription
