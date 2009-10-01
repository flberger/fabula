"""Shard Presentation Engine

   Extracted from shard.py on 22. Sep 2009

   Renamed from VisualEngine to PresentationEngine on 29. Sep 2009
"""

import shard
import shard.plugin
import time

class PresentationEngine(shard.plugin.Plugin):
    """This is the base class for a PresentationEngine for the
       Shard Client. Subclasses should override the
       appropriate methods of this class and implement a 
       graphical representation of the game and the 
       action. Shard is based on a two-dimensional map, 
       but apart from that it makes very few assumptions 
       about the graphical rendering. Thus it is 
       possible to write 2D and 3D PresentationEngines and 
       even a text interface."""

    ####################
    # Initialization

    def __init__(self, asset_engine, framerate, logger):
        """Initialize the PresentationEngine. You are
           welcome to override this method, but make
           sure to call self.setup_presentation_engine()
           with the appropriate arguments to properly
           initialize internals.
           This is what the default implementation does.
           This method must not block, it has to 
           return once everything is set up.
        """

        self.setup_presentation_engine(asset_engine, framerate, logger)

    def setup_presentation_engine(self, asset_engine, framerate, logger):
        """This method initializes the PresentationEngine.
           asset_engine must be an instance of
           shard.AssetEngine or a subclass.
           framerate must be an integer and sets
           the maximum (not minimum ;-)) frames per
           second the client will run in.
        """

        # Attach logger
        #
        self.logger = logger

        # Get framerate and asset_engine from parameters
        #
        self.framerate = framerate
        self.asset_engine = asset_engine

        # Set how long actions like a movement from
        # Map element to Map element take, in seconds.
        #
        self.action_time = 0.5

        # A list of events derived from player input, 
        # cleared and updated on each rendering
        #
        self.player_event_list = []

        # Since it represents the GUI, the PresentationEngine
        # is responsible for catching an
        # exit request by the user. This value is
        # checked in the ClientCoreEngine main loop.
        # TODO: maybe return self.exit_requested along with client events in a tuple
        #
        self.exit_requested = False

        # Variables to be filled by the ClientCoreEngine
        # before each call to process_message()
        #
        self.entity_dict = {}
        self.deleted_entities_dict = {}
        self.tile_list = []
        self.map = {}

        # Are we waiting for a RoomCompleteEvent after
        # an EnterRoomEvent? Upon initialization this
        # is True, since a room has not yet been
        # transfered.
        #
        self.waiting_for_RoomCompleteEvent = True

        self.logger.info("complete")
        self.logger.info("now waiting for RoomCompleteEvent")

        return

    ####################
    # PresentationEngine Main Loop

    def process_message(self,
                        message,
                        entity_dict,
                        deleted_entities_dict,
                        tile_list,
                        map):
        """This is the main method of the PresentationEngine.
           It is called regularly by the ClientCoreEngine
           with a list of events to display (note: the
           list may be empty). It may take all the time 
           it needs to render the action, just a couple 
           or even hundreds of frames, but it must 
           return once the events have been displayed. 
           It must neither block completely nor run in 
           a thread since the ClientCoreEngine has to 
           grab new events and change state between 
           calls to process_message(). Put that way, 
           process_message() is simply a part of 
           ClientCoreEngine.run().
           You should normally not override this method
           unless you have to do some really advanced
           stuff. Overriding the other methods of this
           class (which in turn are called from 
           process_message()) should be just fine. See 
           the other methods and the source code for 
           details."""

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

        self.entity_dict = entity_dict
        self.deleted_entities_dict = deleted_entities_dict
        self.tile_list = tile_list
        self.map = map

        # Reset the list of events triggered by 
        # player actions
        self.player_event_list = []
        
        # Compute the number of frames per action.
        # See __init__() for details.
        self.action_frames = int(self.action_time * self.framerate)

        ####################
        # Check EnterRoomEvent

        # The first thing to check for is if there has
        # been an EnterRoomEvent. For our convenience, 
        # the ControlEngine has set up a flag in the
        # message, so we simply check that instead
        # of scanning the whole list.
        #
        if message.has_EnterRoomEvent:

            # When this arrives here all data scructures
            # have already been cleared and possibly
            # populated with new Entites and a new Map.
            # So we have to ignore everything before
            # an EnterRoomEvent.

            # See the method for explaination
            #
            self.display_EnterRoomEvent()
            
            # Set a flag that we are waiting
            # for RoomCompleteEvent
            #
            self.logger.info("now waiting for RoomCompleteEvent")

            self.waiting_for_RoomCompleteEvent = True

        ####################
        # Check RoomCompleteEvent

        # Next, as long as we are waiting for a
        # RoomCompleteEvent, nothig will be rendered
        # and no player input is accepted.
        #
        if self.waiting_for_RoomCompleteEvent:

            # The ControlEngine has set a flag for
            # our convenience.
            #
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
                while not isinstance(message.event_list[0], shard.RoomCompleteEvent):
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
                #
                return shard.Message(self.player_event_list)

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
        buffered_CanSpeakEvent = shard.Event("dummy_identifier")
        
        # buffer for an identifier
        identifier = ''
        
        for current_event in message.event_list:
            if isinstance(current_event, shard.CanSpeakEvent):
                # CanSpeakEvent is taken out of the list
                # to be appended at the very end.
                # Note that this keeps only the very
                # last CanSpeakEvent. There shouldn't be
                # more than one in a message.
                buffered_CanSpeakEvent = current_event
            
            elif isinstance(current_event, shard.ChangeMapElementEvent):
                # All these happen in parallel, no identifier
                # is recorded
                grouped_events[-1].append(current_event)

            else:
                # Now follow the events where we can
                # detect an identifier
                if isinstance(current_event, shard.SpawnEvent):
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
        if isinstance(buffered_CanSpeakEvent, shard.CanSpeakEvent):
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

                return shard.Message(self.player_event_list)

            # We have at least one event.

            if isinstance(event_list[0], shard.CanSpeakEvent):
                # See the method for explaination.
                self.display_CanSpeakEvent(event_list[0])
                
                return shard.Message(self.player_event_list)

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
                if isinstance(current_event, shard.PerceptionEvent):
                    # Queue for later use.
                    PerceptionEvent_list.append(current_event)

                elif isinstance(current_event, shard.SaysEvent):
                    # The Entity is notified in
                    # self.display_SaysEvents() because we
                    # do not compute the number of frames here.
                    # Queue for later use.
                    SaysEvent_list.append(current_event)

                elif isinstance(current_event, shard.DropsEvent):
                    # This is a multiple frame action.
                    has_multiple_frame_action = True

                    # This affects the inventory.
                    has_inventory_action = True

                    # Notify the Entity that the animation is
                    # about to start. No need to queue the event.
                    self.entity_dict[current_event.identifier].starts_dropping(self.action_frames,
                                                                               self.framerate)

                elif isinstance(current_event, shard.PicksUpEvent):
                    # This is a multiple frame action.
                    has_multiple_frame_action = True

                    # This affects the inventory.
                    has_inventory_action = True

                    # Notify the Entity that the animation is
                    # about to start. No need to queue the event.
                    self.entity_dict[current_event.identifier].starts_picking_up(self.action_frames,
                                                                                 self.framerate)

                elif isinstance(current_event, shard.MovesToEvent):
                    # This is a multiple frame action.
                    has_multiple_frame_action = True

                    # Notify the Entity that the animation
                    # is about to start.
                    self.entity_dict[current_event.identifier].starts_moving(self.action_frames,
                                                                             self.framerate)

                    # Queue for later use.
                    MovesToEvent_list.append(current_event)

                elif isinstance(current_event, shard.ChangeMapElementEvent):
                    # Queue for later use.
                    ChangeMapElementEvent_list.append(current_event)

                elif isinstance(current_event, shard.SpawnEvent):
                    # Queue for later use.
                    SpawnEvent_list.append(current_event)

                elif isinstance(current_event, shard.DeleteEvent):
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

        return shard.Message(self.player_event_list)

    ####################
    # Auxiliary Methods To Override

    # TODO:
    # Most docstrings describe 2D stuff (images).
    # Rewrite 2D-3D-agnostic.

    def display_EnterRoomEvent(self):
        """This method is called when the PresentationEngine
           has encoutered an EnterRoomEvent. You should
           override it, blank the screen here and display
           a waiting message since the PresentationEngine is
           going to twiddle thumbs until it receives a 
           RoomCompleteEvent."""

        self.logger.info("called")

        return

    def display_asset_exception(self, asset):
        """This method is called when the asset_engine
           is unable to retrieve the asset. This is a 
           serious error which prohibits continuation.
           The user should be asked to check his
           installation, file system or network
           connection."""

        self.logger.critical("A required asset (image, animation,"
              + " sound) could not be fetched. The problematic asset was '"
              + str(asset)
              + "'. Sorry, but I can't go on.")

        raise SystemExit

    def display_RoomCompleteEvent(self):
        """This method is called when everything
           is fetched and ready after a
           RoomCompleteEvent. Here you should 
           set up the main screen and display 
           some Map elements and Entities."""

        self.logger.info("called")

        # You'll possibly want to save the real 
        # screen coordinates of Entities in a 
        # special data structure since they do 
        # not necessarily correspond to the Map 
        # coordinates.
        #
        return

    def update_frame_timer(self):
        """Your graphics module might provide a
           timer which must be notified once per
           frame. Do this here and use this method
           wherever you need it. It is also called
           from process_message() when appropriate.
           This method may block execution to slow
           the PresentationEngine down to a certain
           frame rate.
           The default implementation waits
           1.0/self.framerate seconds.
        """

        time.sleep(1.0/self.framerate)

        return

    def filter_events(self, event_list):
        """This is method is called with a list of
           parallel events before they are rendered.
           You can filter events here, for example
           if they are off-screen. This method
           must change the event_list in place.
           The default is no filtering."""
        return

    def display_CanSpeakEvent(self, CanSpeakEvent_instance):
        """This method is called when the PresentationEngine
           needs to render a CanSpeakEvent. This is the
           last event rendered before returning to
           the ControlEngine. You have to prompt for
           appropriate user input here and add a
           corresponding SaysEvent to self.player_event_list, 
           which is evaluated by the ControlEngine."""

        self.logger.info("called")

        # Find a player in entity_dict
        #
        for current_entity in self.entity_dict.values():
            if current_entity.entity_type == "PLAYER":
                self.player_event_list.append(shard.SaysEvent(current_entity.identifier,
                                                              "display_CanSpeakEvent: dummy"))
        # Don't forget the frame counter in
        # your implementation.
        #
        self.update_frame_timer()

        return

    def display_static_frame(self):
        """This method is called when the PresentationEngine
           decides that is need to enter a single frame
           of the current game state. There is nothing
           special going on here, so you should notify
           the Entities that there is a next frame to
           be displayed (however that is done in your 
           implementation) and update their graphics."""

        # You might want to restrict your updates to
        # visible Entities
        #
        pass

        self.update_frame_timer()

        return

    def collect_player_input(self):
        """The module you use for actual graphics
           rendering most probably has a way to
           capture user input. This method is called
           when the PresentationEngine has displayed a
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
           The default implementation reads
           user input from the console.
        """

        user_input = raw_input("Quit? (y/n):")

        if user_input == "y":
            self.exit_requested = True

        return

    def display_multiple_frame_action(self, MovesToEvent_list):
        """This method is called when the PresentationEngine
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
           self.display_static_frame()."""
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
        """This method is called with a list of
           instances of SpawnEvent to be displayed. 
           All you need to do here is adding the 
           new Enties to a list of visible Entities 
           you might have set up and render a static
           frame. Note that event_list may be empty."""

        self.logger.info("called")

        return           

    def display_DeleteEvents(self, event_list):
        """This method is called with a list of 
           instances of DeleteEvent. You need
           to remove the Entites affected from
           your data structures and draw a
           frame without the deleted Entities.
           event_list may be empty. Note that
           the Entities to be removed are
           already gone in self.event_dict, 
           so use self.deleted_entities_dict
           instead."""

        self.logger.info("called")

        return

    def display_ChangeMapElementEvents(self, event_list):
        """This method is called with a list of
           instances of ChangeMapElementEvent.
           There are only visible Map elements
           in the list if you hav implemented
           an according filter in self.filter_events().
           In this method you must implement a
           major redraw of the display, updating all
           Map elements and after that all Entities.
           This is only a single frame though.
           Note that event_list may be empty."""

        self.logger.info("called")

        return

    def update_inventory(self):
        """We do not have to care about the object of
           a DropsEvent and PicksUpEvent since the 
           ControlEngine has generated an respective 
           SpawnEvent and DeleteEvent, which is already 
           rendered. All that is left is to update the 
           inventory visualisation. You can use that
           to enter a frame for the Entities as well."""
        self.display_static_frame()
        return

    def display_PerceptionEvents(self, event_list):
        """This method is called with a list of
           instances of PerceptionEvent. You
           have to provide an implementation
           whicht displays them one by one, 
           possibly awaiting user confirmation.
           event_list may be empty. Please do
           not continue animation of other
           Entities during the perception so
           there are no background actions 
           which may pass unnoticed."""

        self.logger.info("called")

        # Update the frame counter though.
        #
        self.update_frame_timer()

        return           

    def display_SaysEvents(self, event_list):
        """This method is called with a list
           of instances of SaysEvent when the
           PresentationEngine is ready to display
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
           pass unnoticed."""

        self.logger.info("called")

        # Don't forget the frame counter in each frame.
        #
        self.update_frame_timer()

        return
