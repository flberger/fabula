"""Shard User Interface
"""

# Extracted from shard.py on 22. Sep 2009
#
# Renamed from VisualEngine to PresentationEngine on 29. Sep 2009
#
# Renamed from PresentationEngine to UserInterface on 14. Oct 2010

import shard
import shard.plugin
import time

class UserInterface(shard.plugin.Plugin):
    """This is the base class for an UserInterface for the Shard Client.
       Subclasses should override the appropriate methods of this class
       and implement a graphical representation of the game and the 
       action. Shard is based on a two-dimensional map, but apart from
       that it makes very few assumptions about the graphical rendering.
       Thus it is possible to write 2D and 3D UserInterfaces and 
       even a text interface.

       Attributes:

       UserInterface.action_time
           Set how long actions like a movement from Map element to Map element
           take, in seconds.

       UserInterface.framerate
       UserInterface.assets
           framerate and assets manager

       UserInterface.action_frames
           The number of frames per action.

       UserInterface.action_countdown
           A copy of action_frames used in UserInterface.process_message().

       UserInterface.event_queue
           A queue for Events of a Message to be rendered later.
           UserInterface.action_countdown will be counted down between
           processing the Events.

       UserInterface.exit_requested
           The UserInterface is responsible for catching an exit request by the
           user. This value is checked in the Client main loop.

       UserInterface.room
           Variables to be filled by the Client before each call to
           process_message()

       UserInterface.direction_vector_dict
           Convenience dict converting symbolic directions to a vector

       UserInterface.waiting_for_RoomCompleteEvent
           Flag, True after initialisation
    """

    ####################
    # Initialization

    def __init__(self, assets, framerate, logger):
        """This method initialises the UserInterface.
           assets must be an instance of shard.Assets or a subclass.
           framerate must be an integer and sets the maximum (not minimum ;-))
           frames per second the client will run in.
        """

        # First set up the plugin
        #
        shard.plugin.Plugin.__init__(self, logger)

        # Set how long actions like a movement from
        # Map element to Map element take, in seconds.
        #
        self.action_time = 0.5

        # Get framerate and assets from parameters
        #
        self.framerate = framerate
        self.assets = assets

        # Compute the number of frames per action.
        #
        self.action_frames = int(self.action_time * self.framerate)

        # A copy to count down.
        # Creates a copy since action_frames is immutable.
        # 
        self.action_countdown = self.action_frames

        # A queue for Events of a Message to be
        # rendered later. self.action_countdown
        # will be counted down between processing
        # the Events.
        #
        self.event_queue = []

        # Since it represents the GUI, the UserInterface
        # is responsible for catching an
        # exit request by the user. This value is
        # checked in the Client main loop.
        # TODO: maybe return self.exit_requested along with client events in a tuple
        #
        self.exit_requested = False

        # Variables to be filled by the Client
        # before each call to process_message()
        #
        self.room = shard.Room()

        # Convenience dict converting symbolic
        # directions to a vector
        #
        self.direction_vector_dict = {"^" : (0, -1),
                                      ">" : (1, 0),
                                      "v" : (0, 1),
                                      "<" : (-1, 0),
                                      (0, -1) : "^",
                                      (1, 0) : ">",
                                      (0, 1) : "v",
                                      (-1, 0) : "<"}

        # Are we waiting for a RoomCompleteEvent after
        # an EnterRoomEvent? Upon initialization this
        # is True, since a room has not yet been
        # transfered.
        #
        self.waiting_for_RoomCompleteEvent = True

        self.logger.info("complete, now waiting for RoomCompleteEvent")

        return

    ####################
    # UserInterface Main Method

    def process_message(self,
                        message,
                        room,
                        player_id):
        """This is the main method of the UserInterface.
           You should normally not override this method unless you have to do
           some really advanced stuff. Overriding the other methods of this
           class (which in turn are called from process_message()) should be
           just fine. See the other methods and the source code for details.
           This method is called regularly by the Client with a list of events
           to display (note: the list may be empty). It may take all the time it
           needs to render the action, just a couple or even hundreds of frames,
           but it must return once the events have been displayed. 
           It must neither block completely nor run in a thread since the Client
           has to grab new events and change state between calls to
           process_message(). Put that way, process_message() is simply a part
           of Client.run().
        """

        # TODO: do we still need to give room and player_id? The should be accessible via Plugin.host, and we can set up proxies here for faster access

        # *sigh* Design by contract is a really nice
        # thing. We really really should do some thorough
        # checks, like for duplicate RoomCompleteEvents, 
        # duplicate CanSpeakEvents and similar stuff.
        # Below we assume that everyone behaves nicely.
        # In some weird way we could sell that as
        # "pythonic" ;-) Hey! Not a consenting adult, 
        # anyone?

        ####################
        # Initialise

        self.room = room

        # TODO: Do we need to transfer player_id on every call?
        #
        self.player_id = player_id

        # Reset the list of events triggered by 
        # player actions
        #
        self.message_for_host = shard.Message([])

        # Proxy for faster access
        #
        event_list = message.event_list

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
            # populated with new Entities and a new map.
            # So we have to ignore everything before
            # an EnterRoomEvent.

            for event in event_list:

                if isinstance(event, shard.EnterRoomEvent):

                    # See the method for explaination
                    #
                    self.process_EnterRoomEvent(event)

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

                self.logger.debug("got RoomCompleteEvent")

                # TODO: That original design - handling Events before RoomComplete here or not at all, then deleting - can probably be discarded and replaced by an ordinary Plugin behaviour: process all Events with the according methods.

                # By the time the event arrives the ControlEngine has gathered
                # all important data and handed them over to us, so wen can
                # build a new screen.

                # Load and store assets for Tiles and Entities using the assets
                #
                entity_tile_list = list(self.room.entity_dict.values()) + list(self.room.tile_list)

                for element in entity_tile_list:

                    # Fetch if not already done so
                    #
                    if element.asset is None:

                        try:
                            retrieved_asset = self.assets.fetch(element.asset_desc)

                        except:
                            # See the method for explaination
                            #
                            self.display_asset_exception(element.asset_desc)

                        element.asset = retrieved_asset

                # Delete everything in the event_list up to and
                # including the RoomCompleteEvent
                #
                while not isinstance(event_list[0], shard.RoomCompleteEvent):
                    del event_list[0]
                
                # Arrived at RoomCompleteEvent.
                # See the method for explaination
                #
                self.process_RoomCompleteEvent(event_list[0])

                # Delete it as well.
                #
                del event_list[0]

                # No more waiting!
                #
                self.waiting_for_RoomCompleteEvent = False

            else:
                # If there is no RoomCompleteEvent in that message, 
                # ignore everything.

                # Technically this waiting corresponds to a
                # frame, though we do not render anything.

                # TODO: Well, we completely lock out the user here. If the server is down, he will not be able to interact with the application (quit, for examlpe).

                # See method for explaination.
                #
                self.update_frame_timer()

                # Discard and check the next message.
                #
                return self.message_for_host

        ####################
        # Countdown and rendering waiting Events

        self.action_countdown = self.action_countdown - 1

        if self.action_countdown == 0:

            if len(self.event_queue):

                self.logger.debug("countdown passed, event_queue now: %s" % self.event_queue)

                list_item = self.event_queue.pop(0)

                if isinstance(list_item, list):

                    for event in list_item:

                        self.event_dict[event.__class__](event)

                else:

                    self.event_dict[list_item.__class__](list_item)

            self.action_countdown = self.action_frames

        ####################
        # Render Events

        # Now it's no good, we finally have to render some
        # frames!
        # MovesTo, Drops and PicksUpEvents take the
        # same number of frames to render, which is given by
        # self.action_time * self.framerate. During a 
        # SaysEvent or a PerceptionEvent, animation may even
        # stop for some time. These events are displayed last.

        if not len(event_list):

            # No events in event_list!
            # See the method for explaination.
            #
            self.display_single_frame()

        elif len(event_list) == 1:

            # We have exacly one event.
            # Process at once.
            #
            self.event_dict[event_list[0].__class__](event_list[0])

        else:

            # More than one Event.
            #
            self.logger.debug("queueing %s events for later rendering"
                              % len(event_list))

            # Parallelise subsequent ChangeMapElementEvents
            #
            event_list_parallel = []
            change_map_list = []

            for event in event_list:

                if isinstance(event, shard.ChangeMapElementEvent):

                    change_map_list.append(event)

                else:

                    # If a change_map_list has been built,
                    # the sequence is broken now. Append
                    # the list and the event.
                    #
                    if len(change_map_list) == 1:

                        # Append the single event as-is.
                        #
                        event_list_parallel.append(change_map_list[0])

                        change_map_list = []

                    elif len(change_map_list) > 1:

                        event_list_parallel.append(change_map_list)

                        change_map_list = []

                    event_list_parallel.append(event)

            # In case the last Event was an
            # ChangeMapElementEvent: append
            #
            # TODO: Exact duplicate
            #
            if len(change_map_list) == 1:

                # Append the single event as-is.
                #
                event_list_parallel.append(change_map_list[0])

                change_map_list = []

            elif len(change_map_list) > 1:

                event_list_parallel.append(change_map_list)

                change_map_list = []

            self.logger.debug("event queue: %s, parallel events: %s"
                              % (self.event_queue, event_list_parallel))

            # Join with event_queue
            #
            self.event_queue = shard.join_lists(self.event_queue,
                                                event_list_parallel)

            self.logger.debug("joined event queue: %s"
                              % self.event_queue)

            # Render first Event at once
            #
            list_item = self.event_queue.pop(0)

            if isinstance(list_item, list):

                for event in list_item:

                    self.event_dict[event.__class__](event)

            else:

                self.event_dict[list_item.__class__](list_item)

        # All Events are rendered now.

        ####################
        # Player Input

        # See the method for explaination.
        #
        self.collect_player_input()

        ####################
        # Return to ControlEngine

        return self.message_for_host

    # TODO: Most docstrings describe 2D stuff (images). Rewrite 2D-3D-agnostic.

    def display_asset_exception(self, asset):
        """Called when the assets is unable to retrieve the asset.
           This is a serious error which usually prohibits continuation.
           The user should be asked to check his installation, file system
           or network connection.
        """

        self.logger.critical("Asset could not be fetched: %s. Aborting."
                             % asset)

        raise SystemExit

    def update_frame_timer(self):
        """You might have to notify a timer once per frame.
           Do this here and use this method wherever you need it.
           It is also called from process_message() when appropriate.
           This method may block execution to slow the UserInterface
           down to a certain frame rate. The default implementation waits
           1.0/self.framerate seconds.
        """

        time.sleep(1.0/self.framerate)

        return

    def display_single_frame(self):
        """Called when the UserInterface needs to render a single frame
           of the current game state. There is nothing special going on here,
           so you should notify the Entities that there is a next frame to be
           displayed (whichever way that is done in your implementation) and
           update their graphics.
        """

        # You might want to restrict your updates to
        # visible Entities
        #
        pass

        self.update_frame_timer()

        return

    def collect_player_input(self):
        """Called when the UserInterface wants to capture the user's reaction.
           The module you use for actual graphics rendering most probably
           has a way to capture user input. When overriding this method,
           you have to convert the data provided by your module into Shard 
           events, most probably instances of shard.AttemptEvent. You must
           append them to self.message_for_host which is evaluated by the
           ControlEngine.
           Note that your module might provide you with numerous user
           actions if the user clicked and typed a lot during the rendering.
           You should create a reasonable subset of those actions, e.g.
           select only the very last user input action.
           The UserInterface should only ever collect and send one
           single client event to prevent cheating and blocking other
           clients in the server. (hint by Alexander Marbach)
           The default implementation reads user input from the console.
        """

        self.logger.debug("called")

        user_input = raw_input("Quit? (y/n):")

        if user_input == "y":

            self.exit_requested = True

        return

    # TODO: remove following method if applicable
    #
    #def display_multiple_frame_action(self, MovesToEvent_list):
    #    """Called when the UserInterface is ready to render Move, Drop or PickUp actions.
    #       All visible Entities are already
    #       notified about their state at this point.
    #       This method must render exactly
    #       self.action_frames frames. You have to 
    #       compute a movement for each Entity in the 
    #       list of MovesToEvent instances provided. 
    #       Note that this list may be empty, but even 
    #       then you have to render the full number of 
    #       frames to display PickUp and Drop animations. 
    #       You might get away with just changing the 
    #       screen coordinates and calling 
    #       self.display_single_frame()."""
    #
    #    self.logger.debug("called")
    #
    #    # Compute start and end position and movement per
    #    # frame for all moving Entities
    #
    #    # This creates a copy since framerate is
    #    # immutable.
    #    #
    #    i = self.action_frames
    #
    #    # for each frame:
    #    #
    #    while i:
    #        # - move moving Entities by respective Movement
    #        # - render a graphic for each visible entity
    #        #   The should supply a new one on each call
    #        # - update frame counter
    #        #
    #        self.display_single_frame()
    #        i = i - 1
    #    return

    ####################
    # Event handlers affecting presentation and management

    def process_EnterRoomEvent(self, event):
        """Called when the UserInterface has encoutered an EnterRoomEvent.
           You should override it, blank the screen here and display a waiting
           message since the UserInterface is going to twiddle thumbs until
           it receives a RoomCompleteEvent.
        """

        self.logger.debug("called")

        self.display_single_frame()

        return

    def process_RoomCompleteEvent(self, event):
        """Called when everything is fetched and ready after a RoomCompleteEvent.
           Here you should set up the main screen and display some Map
           elements and Entities.
        """

        self.logger.debug("called")

        self.display_single_frame()

        return

    def process_CanSpeakEvent(self, event):
        """Called when the UserInterface needs to render a CanSpeakEvent.
           You have to prompt for appropriate user input here and add a
           corresponding SaysEvent to self.message_for_host, which is
           evaluated by the ControlEngine. The default implementation
           makes the player say "blah". 
        """

        # TODO: Make sure that this is the last event rendered before returning to the ControlEngine?

        self.logger.debug("called")

        event = shard.SaysEvent(self.player_id, "blah")

        self.message_for_host.event_list.append(event)

        self.display_single_frame()

        return

    def process_SpawnEvent(self, event):
        """This method is called with an instance of SpawnEvent to be displayed.
           You should supply the Entity with self.user_interface as done
           in the default implementation. Then add the new Enties to a list of
           visible Entities you might have set up and render a static frame.
        """

        self.logger.debug("called")

        event.entity.user_interface = self

        self.display_single_frame()

        return           

    def process_DeleteEvent(self, event):
        """This method is called with an instance of DeleteEvent.
           You need to remove the Entites affected from your data
           structures and draw a frame without the deleted Entities.
           Note that the Entities to be removed are already gone
           in self.room.
        """

        self.logger.debug("called")

        self.display_single_frame()

        return

    def process_ChangeMapElementEvent(self, event):
        """Called with an instance of ChangeMapElementEvent.
           In this method you must implement a major redraw of the display,
           updating all Map elements and after that all Entities.
           This is only a single frame though.
           Note that event may be empty.
        """

        self.logger.debug("called")

        self.display_single_frame()

        return

    def process_PerceptionEvent(self, event):
        """Called with a list of instances of PerceptionEvent.
           You have to provide an implementation whicht displays them
           one by one, possibly awaiting user confirmation.
           event_list may be empty. Please do not continue animation
           of other Entities during the perception so there are no
           background actions which may pass unnoticed.
        """

        self.logger.debug("called")

        self.display_single_frame()

        return           

    ####################
    # Event handlers affecting Entities

    def process_MovesToEvent(self, event):
        """Let the Entity handle the Event.
        """

        self.logger.debug("called")

        self.room.entity_dict[event.identifier].process_MovesToEvent(event)

        self.display_single_frame()

        return           

    def process_ChangeStateEvent(self, event):
        """Entity has already handled the Event.
           Display a single frame to show the result.
        """

        self.logger.debug("called")

        self.display_single_frame()

        return           

    def process_DropsEvent(self, event):
        """Let the Entity handle the Event.
        """

        self.logger.debug("called")

        self.room.entity_dict[event.identifier].process_DropsEvent(event)

        self.display_single_frame()

        return           

    def process_PicksUpEvent(self, event):
        """Remove the target from all data structures,
           then let the Entity handle the Event.
           Possibly update an inventory display.
        """

        self.logger.debug("called")

        self.room.entity_dict[event.identifier].process_PicksUpEvent(event)

        self.display_single_frame()

        return           

    def process_SaysEvent(self, event):
        """Called with an instance of SaysEvent
           when the UserInterface is ready to display what Entities say.
           In this method you have to compute a number of frames for
           displaying text and animation for each SaysEvent depending
           on how long the text is. Once you start displaying the text,
           you have to notify the affected Entity. You should catch
           some user confirmation. Consider not to continue  animation
           of other Entities so there are no background actions which may
           pass unnoticed.
        """

        try:
            self.room.entity_dict[event.identifier].process_SaysEvent(event)

            self.logger.debug("forwarded SaysEvent(%s, '%s')"
                             % (event.identifier, event.text))

        except KeyError:

            # Entity has been deleted by an
            # upcoming DeleteEvent
            #
            self.host.rack.entity_dict[event.identifier].process_SaysEvent(event)

            self.logger.debug("forwarded SaysEvent(%s, '%s') to deleted entity"
                             % (event.identifier, event.text))

        self.display_single_frame()

        return

    ####################
    # Auxiliary methods

    def group_events(self, message):
        """Returns a list of lists of parallel events.
           The division is simple: group all subsequent events
           that do not affect the same identifier.
        """

        # This method used to be a mandatory part
        # of process_message().
        # TODO: Kept for reference. Can possibly be removed.

        ####################
        # Grouping Event List

        # If we arrive here, we are ready to render all the
        # events that are left in the event_list.

        # TODO:
        # We could and perhaps should do some checks here
        # to prevent nonsense:
        # Added Entities may not do anything before they
        # appear.
        # Deleted Entites may act until they disappear.
        # (Get the Entity from the deletedList then, since
        # it is already deleted in the entity_dict.)

        # Make up an empty list of IDs
        #
        collected_identifiers = []

        # make up an empty list of event lists and add an
        # empty list
        #
        grouped_events = [[]]

        # make a buffer for the CanSpeakEvent
        #
        buffered_CanSpeakEvent = shard.Event("dummy_identifier")

        # buffer for an identifier
        #
        identifier = ''
        
        for current_event in message.event_list:

            if isinstance(current_event, shard.CanSpeakEvent):

                # CanSpeakEvent is taken out of the list
                # to be appended at the very end.
                # Note that this keeps only the very
                # last CanSpeakEvent. There shouldn't be
                # more than one in a message.
                #
                buffered_CanSpeakEvent = current_event
            
            elif isinstance(current_event, shard.ChangeMapElementEvent):

                # All these happen in parallel, no identifier
                # is recorded
                #
                grouped_events[-1].append(current_event)

            else:
                # Now follow the events where we can
                # detect an identifier
                #
                if isinstance(current_event, shard.SpawnEvent):

                    identifier = current_event.entity.identifier

                else:
                    identifier = current_event.identifier

                if identifier in collected_identifiers:

                    # append an empty list to the list of
                    # event lists
                    # We've had that identifier before.
                    # Start a new event group.
                    #
                    grouped_events.append([])
                
                    # Start new
                    #
                    collected_identifiers = []
                
                else:
                    # identifier is not yet in
                    # current group
                    #
                    collected_identifiers.append(identifier)

                # Now append the event to the current group
                #
                grouped_events[-1].append(current_event)

        # All parallel events are grouped now.            
        # Append the CanSpeakEvent if it is there.
        #
        if isinstance(buffered_CanSpeakEvent, shard.CanSpeakEvent):

            grouped_events.append([buffered_CanSpeakEvent])

        return grouped_events
