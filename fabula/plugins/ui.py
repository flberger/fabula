"""Fabula User Interface

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

# Extracted from shard.py on 22. Sep 2009
#
# Renamed from VisualEngine to PresentationEngine on 29. Sep 2009
#
# Renamed from PresentationEngine to UserInterface on 14. Oct 2010

import fabula
import fabula.plugins
import time

class UserInterface(fabula.plugins.Plugin):
    """This is the base class for an UserInterface for the Fabula Client.
       Subclasses should override the appropriate methods of this class
       and implement a graphical representation of the game and the
       action. Fabula is based on a two-dimensional map, but apart from
       that it makes very few assumptions about the graphical rendering.
       Thus it is possible to write 2D and 3D UserInterfaces and
       even a text interface.

       Attributes:

       UserInterface.framerate
       UserInterface.assets
           framerate and assets manager

       UserInterface.action_frames
           The number of frames per action. This can only be set when a
           ServerParametersEvent has been received, so it is initially None.

       UserInterface.exit_requested
           The UserInterface is responsible for catching an exit request by the
           user. This value is checked in the Client main loop.

       UserInterface.freeze
           Flag whether to stop displaying the game and collect input.
           False upon initialisation.

       UserInterface.room
           Variables to be filled by the Client before each call to
           process_message()

       UserInterface.direction_vector_dict
           Convenience dict converting symbolic directions to a vector
    """

    ####################
    # Initialization

    def __init__(self, assets, framerate, host, fullscreen = False):
        """This method initialises the UserInterface.
           assets must be an instance of fabula.Assets or a subclass.
           framerate must be an integer and sets the maximum (not minimum ;-))
           frames per second the client will run in.
           fullscreen is a Boolean flag that indicates whether the game should
           run in a window or use the full screen. Its effect is implementation
           dependent.
        """

        # First set up the plugin
        #
        fabula.plugins.Plugin.__init__(self, host)

        # Get framerate and assets from parameters
        #
        self.framerate = framerate
        self.assets = assets

        # See docstring
        #
        self.action_frames = None

        # Since it represents the GUI, the UserInterface
        # is responsible for catching an
        # exit request by the user. This value is
        # checked in the Client main loop.
        # TODO: maybe return self.exit_requested along with client events in a tuple
        #
        self.exit_requested = False

        # Flag whether to stop displaying the game and collect input
        #
        self.freeze = False

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

        fabula.LOGGER.debug("complete")

        return

    def get_connection_details(self):
        """Get a connector to the Server and an identifier from the player.

           Initially, the Client Interface is not connected to the Server. This
           method should prompt the user for connection details.

           It must return a tuple (identifier, connector).

           connector will be used for Interface.connect(connector).
           identifier will be used to send InitEvent(identifier) to the server.

           The default implementation returns ("player", "dummy_connector") for
           testing purposes.
        """

        fabula.LOGGER.warning('this is a dummy implementation, returning ("player", "dummy_connector")')

        return ("player", "dummy_connector")

    ####################
    # UserInterface Main Method

    def process_message(self, message):
        """This is the main method of the UserInterface.

           You should normally not override this method unless you have to do
           some really advanced stuff. Overriding the other methods of this
           class (which in turn are called from process_message()) should be
           just fine. See the other methods and the source code for details.

           This method is called regularly by Client.run() with a Message to
           display (note: the Event list may be empty). It may take all the time
           it needs to render the action, just a couple or even hundreds of
           frames, but it must return once the events have been displayed. It
           must neither block completely nor run in a thread since the Client
           has to grab new events and change state between calls to
           process_message().
        """
        # TODO: update docstring

        # *sigh* Design by contract is a really nice thing. We really really
        # should do some thorough checks, like for duplicate RoomCompleteEvents,
        # duplicate CanSpeakEvents and similar stuff. Below we assume that
        # everyone behaves nicely. In some weird way we could sell that as
        # "pythonic" ;-) Hey! Not a consenting adult, anyone?

        # We used to check for EnterRoomEvent and RoomCompleteEvent here and
        # discard all inbetween since UserInterface.process_RoomCompleteEvent
        # was expected to infer the game state, fetch assets and setup the whole
        # thing. Instead we now treat the setup Events - ChangeMapEvent,
        # SpawnEvent - like any other event, which is much more in line with
        # Fabula plugin design. UserInterface.process_EnterRoomEvent is expected
        # to stall the game display.
        #
        # We also used to queue subsequent events and let a countdown pass
        # between them. This is gone in the UserInterface: the Server has the
        # timing authority, we render everything as soon as we get it.
        #
        # And this finally means that we can just call the base class.

        ####################
        # Render Events

        # Now it's no good, we finally have to render some frames!
        # MovesTo, Drops and PicksUpEvents take the same number of frames to
        # render, which is given by self.host.action_time * self.framerate. During a
        # SaysEvent or a PerceptionEvent, animation may even stop for some time.

        # Results are added to self.message_for_host
        #
        fabula.plugins.Plugin.process_message(self, message)

        # Mandatory render a frame
        #
        self.display_single_frame()

        # All Events are rendered now.

        ####################
        # Player Input

        # See the method for explanation.
        #
        self.collect_player_input()

        ####################
        # Return to Client

        return self.message_for_host

    # TODO: Most docstrings describe 2D stuff (images). Rewrite 2D-3D-agnostic.

    def process_ServerParametersEvent(self, event, **kwargs):
        """Compute action_frames from event.action_time and UserInterface.framerate.
        """

        self.action_frames = int(event.action_time * self.framerate)

        msg = "{} s action_time from server * {} fps framerate = {} action_frames"

        fabula.LOGGER.debug(msg.format(event.action_time,
                                     self.framerate,
                                     self.action_frames))

        return

    def display_asset_exception(self, asset):
        """Called when assets is unable to retrieve the asset.
           This is a serious error which usually prohibits continuation.
           The user should be asked to check his installation, file system
           or network connection.
           The default implementation logs the error and raises an Exception.
        """

        fabula.LOGGER.critical("Asset could not be fetched: {}. Aborting.".format(asset))

        raise Exception("Asset could not be fetched: {}. Aborting.".format(asset))

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
        """Called when the UserInterface needs to render a single frame of the current game state.
           There is nothing special going on here, so you should notify the
           Entities that there is a next frame to be displayed (whichever way
           that is done in your implementation) and update their graphics.
           You might want to check the UserInterface.freeze flag whether to
           display the game and accept input.
        """

        # You might want to restrict your updates to
        # visible Entities
        #
        pass

        self.update_frame_timer()

        return

    def collect_player_input(self):
        """Called when the UserInterface wants to capture the user's reaction.

           The module you use for actual graphics rendering most probably has a
           way to capture user input. When overriding this method, you have to
           convert the data provided by your module into Fabula events, most
           probably instances of fabula.AttemptEvent. You must append them to
           self.message_for_host which is evaluated by the ControlEngine.

           Note that your module might provide you with numerous user actions if
           the user clicked and typed a lot during the rendering. You should
           create a reasonable subset of those actions, e.g. select only the
           very last user input action.

           The UserInterface should only ever collect and send one single client
           event to prevent cheating and blocking other clients in the server.
           (hint by Alexander Marbach)

           The default implementation pretending player wants to quit and sets
           UserInterface.exit_requested to True.
        """

        fabula.LOGGER.warning("pretending player wants to quit")

        self.exit_requested = True

        return

    ####################
    # Event handlers affecting presentation and management

    def process_EnterRoomEvent(self, event):
        """Called when the UserInterface has encountered an EnterRoomEvent.
           You should override it, blank the screen here and display a waiting
           message since the UserInterface is going to twiddle thumbs until
           it receives a RoomCompleteEvent.
           The default implementation sets UserInterface.freeze = True.
        """

        fabula.LOGGER.info("entering room: {}".format(event.room_identifier))

        fabula.LOGGER.info("freezing")
        self.freeze = True
        # TODO: make sure the user can interact with the game (close etc.) even if frozen

        return

    def process_RoomCompleteEvent(self, event):
        """Called when everything is fetched and ready after a RoomCompleteEvent.
           Here you should set up the main screen and display some Map elements
           and Entities.
           The default implementation sets UserInterface.freeze = False.
        """

        fabula.LOGGER.debug("called")

        fabula.LOGGER.info("unfreezing")
        self.freeze = False

        return

    def process_CanSpeakEvent(self, event):
        """Called when the UserInterface needs to render a CanSpeakEvent.
           You have to prompt for appropriate user input here and add a
           corresponding SaysEvent to self.message_for_host, which is
           evaluated by the ControlEngine. The default implementation
           makes the player say "blah".
        """

        # TODO: Make sure that this is the last event rendered before returning to the ControlEngine?

        fabula.LOGGER.debug("called")

        event = fabula.SaysEvent(self.player_id, "blah")

        self.message_for_host.event_list.append(event)

        return

    def process_SpawnEvent(self, event):
        """This method is called with an instance of SpawnEvent to be displayed.
           You should supply the Entity with self.user_interface as done
           in the default implementation. Then add the new Enties to a list of
           visible Entities you might have set up and render a static frame.
        """

        fabula.LOGGER.debug("adding pointer to UserInterface to Entity '{}'".format(event.entity.identifier))

        event.entity.user_interface = self

        return

    def process_DeleteEvent(self, event):
        """This method is called with an instance of DeleteEvent.
           You need to remove the Entites affected from your data structures.
           Note that the Entities to be removed are already gone in
           self.host.room.
           The default implementation does nothing.
        """

        fabula.LOGGER.debug("called")

        return

    def process_ChangeMapElementEvent(self, event):
        """Called with an instance of ChangeMapElementEvent.
           In this method you must implement a major redraw of the display,
           updating all Map elements and after that all Entities.
           This is only a single frame though.
           Note that event may be empty.
           The default implementation does nothing.
        """

        fabula.LOGGER.debug("called")

        return

    def process_PerceptionEvent(self, event):
        """Called with an instance of PerceptionEvent.
           You have to provide an implementation whicht displays it, possibly
           awaiting user confirmation. event.event_list may be empty. Please do
           not continue animation of other Entities during the perception so
           there are no background actions which may pass unnoticed.
           The default implementation does nothing.
        """

        fabula.LOGGER.debug("called")

        return

    ####################
    # Event handlers affecting Entities

    def process_MovesToEvent(self, event):
        """Let the Entity handle the Event.
        """

        fabula.LOGGER.debug("forwarding Event to Entity and displaying a single frame")

        self.host.room.entity_dict[event.identifier].process_MovesToEvent(event)

        return

    def process_ChangePropertyEvent(self, event):
        """Entity has already handled the Event.
        """

        fabula.LOGGER.debug("Entity '{}' has already handled the Event".format(event.identifier))

        return

    def process_DropsEvent(self, event):
        """Pass the Event to the dropping Entity and spawn the dropped Entity.
        """

        fabula.LOGGER.debug("passing Event to '{}'".format(event.identifier))

        self.host.room.entity_dict[event.identifier].process_DropsEvent(event)

        # Spawn the dropped Entity
        #
        fabula.LOGGER.info("spawning '{}' in room".format(event.item_identifier))

        entity = self.host.room.entity_dict[event.item_identifier]

        self.process_SpawnEvent(fabula.SpawnEvent(entity, event.location))

        return

    def process_PicksUpEvent(self, event):
        """Let the Entity picking up the item handle the Event.
           The Client has already put the item Entity from Client.room into
           client.rack.
        """

        fabula.LOGGER.debug("notifying Entity '{}'".format(event.identifier))

        try:

            self.host.room.entity_dict[event.identifier].process_PicksUpEvent(event)

        except:

            fabula.LOGGER.error("Entity '{}' not found in host.room.entity_dict, cannot forward PicksUpEvent".format(event.identifier))

        return

    def process_SaysEvent(self, event):
        """Called with an instance of SaysEvent.
           In this method you have to compute a number of frames for displaying
           text and animation for each SaysEvent depending on how long the text
           is. Once you start displaying the text, you have to notify the
           affected Entity. You should catch some user confirmation. Consider
           not to continue animation of other Entities so there are no
           background actions which may pass unnoticed.
        """

        try:
            self.host.room.entity_dict[event.identifier].process_SaysEvent(event)

            fabula.LOGGER.debug("forwarded SaysEvent({}, '{}')".format(event.identifier,
                                                                     event.text))

        except KeyError:

            # Entity has been deleted by an upcoming DeleteEvent
            #
            self.host.rack.entity_dict[event.identifier].process_SaysEvent(event)

            fabula.LOGGER.warning("forwarded SaysEvent({}, '{}') to deleted entity".format(event.identifier,
                                                                                       event.text))

        return
