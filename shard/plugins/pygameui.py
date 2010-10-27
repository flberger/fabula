"""2D Shard User Interface using PyGame

   Addiotional attributes:

   PygameUserInterface.clock
       Pygame frame timing clock

   PygameUserInterface.fade_surface
       A black Pygame Surface for fade effects

   (c) Florian Berger <fberger@florian-berger.de>
"""

# work started on 15. Oct 2010
#
# Partly based on the Shard PresentationEngine for the "Runaway" game done in
# October-December 2009, which in turn borrowed a lot from the PyGame-based
# CharanisMLClient developed in May 2008.

import shard.plugins.ui
import pygame
import clickndrag

class PygameUserInterface(shard.plugins.ui.UserInterface):
    """This is a Pygame implementation of an UserInterface for the Shard Client.

       Inherited from shard.plugins.ui.UserInterface:

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


       PygameUserInterface attributes:

       PygameUserInterface.clock
           An instance of pygame.time.Clock

       PygameUserInterface.fps_log_counter
           Counter to log actual fps every <framerate> frames

       PygameUserInterface.window
           An instance of clickndrag.Display. By default this is 800x600px and
           windowed.

       PygameUserInterface.window.inventory
           clickndrag Plane for the inventory. By default this is 800x100px
           with space for 8 100x100px icons and located at the bottom of the
           window.

       PygameUserInterface.window.room
           clickndrag Plane for the room. By default this is 800x500px with
           space for 8x5 tiles and located at the top of the window.

       PygameUserInterface.fade_surface
           A black pygame surface for fade effects
    """

    def __init__(self, assets, framerate, logger):
        """This method initialises the PygameUserInterface.
           assets must be an instance of shard.Assets or a subclass.
           framerate must be an integer and sets the maximum (not minimum ;-))
           frames per second the client will run at.
        """

        # Call original __init__()
        #
        shard.plugins.ui.UserInterface.__init__(self, assets, framerate, logger)

        self.logger.debug("called")

        self.logger.debug("initialising pygame")
        pygame.init()

        # Initialise the frame timing clock.
        #
        self.clock = pygame.time.Clock()
        self.fps_log_counter = self.framerate

        # Open a click'n'drag window.
        #
        self.window = clickndrag.Display((800, 600))

        # Create a black pygame surface for fade effects
        # New Surfaces are black by default in Pygame 1.x
        #
        self.fade_surface = pygame.Surface((800, 600))

        # Create inventory plane at PygameUserInterface.window.inventory
        #
        self.window.sub(clickndrag.Plane("inventory",
                                         pygame.Rect((0, 500), (800, 100))))
        # Create plane for the room.
        #
        self.window.sub(clickndrag.Plane("room",
                                         pygame.Rect((0, 0), (800, 500))))

        self.logger.debug("complete")

        return

    def update_frame_timer(self):
        """Use pygame.time.Clock.tick() to slow down to given framerate.
        """

        self.clock.tick(self.framerate)

        if self.fps_log_counter:

            self.fps_log_counter = self.fps_log_counter - 1

        else:
            self.logger.debug("{0}/{1} fps".format(int(self.clock.get_fps()),
                                                   self.framerate))
            self.fps_log_counter = self.framerate

        return

    def display_single_frame(self):
        """Update and render all click'd'drag planes.
        """

        self.window.update()
        self.window.render()

        # TODO: replace with update(dirty_rect_list)
        #
        pygame.display.flip()

        self.update_frame_timer()

        # Pump the Pygame Event Queue
        #
        pygame.event.pump()

        return

    def collect_player_input(self):
        """When overriding this method,
           you have to convert the data provided by your module into Shard 
           events, most probably instances of shard.AttemptEvent. You must
           append them to self.message_for_host which is evaluated by the
           ControlEngine.
           The UserInterface should only ever collect and send one
           single client event to prevent cheating and blocking other
           clients in the server. (hint by Alexander Marbach)
        """
        # TODO: change docstring

        events = pygame.event.get()

        for event in events:

            if event.type == pygame.QUIT:
                self.logger.debug("got pygame.QUIT")
                self.exit_requested = True

                # Quit pygame here, though there is still shutdown work to be
                # done Client and ClientInterface.
                #
                pygame.quit()

        self.window.process(events)

        # TODO: Must figure out Events here and set self.message_for_host.event_list.append(event)
        # TODO: This is weird. This should be returned instead in some way, shouldn't it?

        return

    ####################
    # Event handlers affecting presentation and management

    def process_EnterRoomEvent(self, event):
        """Fade window to black and remove subplanes of PygameUserInterface.window.room
        """

        self.logger.debug("called")

        # Only fade out if a room is already displayed.
        #
        if self.window.room.subplanes:

            self.logger.debug("room visible, fading out")

            fadestep = int(255 / self.action_frames)
            
            self.fade_surface.set_alpha(0)
            
            frames = self.action_frames

            # This is actually an exponential fade since the original surface is
            # not restored before blitting the fading surface
            #
            while frames:
                # Bypassing display_single_frame()

                self.window.rendersurface.blit(self.fade_surface, (0, 0))

                pygame.display.flip()

                self.update_frame_timer()

                # Pump the Pygame Event Queue
                #
                pygame.event.pump()

                self.fade_surface.set_alpha(self.fade_surface.get_alpha() + fadestep)

                frames = frames - 1

        # Make the window is black now
        #
        self.window.rendersurface.fill((0, 0, 0))
        pygame.display.flip()

        # Clear room
        #
        self.window.room.subplanes = {}

        return

    def process_RoomCompleteEvent(self, event):
        """Update and render the Planes of the map elements and fade in the room.
        """

        self.logger.debug("called")

        # UserInterface.process_message() has already fetched the assets, but
        # right now they are only open streams. Actually load the images here
        # and replace the asset.
        #
        for tile in self.room.tile_list:

            self.logger.debug("loading Surface from {0} for Tile {1}".format(tile.asset, tile))

            surface = pygame.image.load(tile.asset)

            tile.asset.close()

            # Convert to internal format suitable for blitting
            #
            tile.asset = surface.convert_alpha()

        self.logger.debug("creating subplanes for tiles")

        for coordinates in self.room.floor_plan:

            # Tiles are clickndrag subplanes of self.window.room, indexed by
            # the string representation of their location.
            # No need to check for existing, everything is new.
            #
            plane = clickndrag.Plane(str(coordinates),
                                     pygame.Rect((coordinates[0] * 100,
                                                  coordinates[1] * 100),
                                                 (100, 100)))

            self.window.room.sub(plane)

            surface = self.room.floor_plan[coordinates].tile.asset

            self.window.room.subplanes[str(coordinates)].image = surface

        self.logger.debug("fading in")

        fadestep = int(255 / self.action_frames)
        
        self.fade_surface.set_alpha(255)
        
        frames = self.action_frames

        while frames:
            # Bypassing display_single_frame()

            self.window.update()
            self.window.render()

            self.window.rendersurface.blit(self.fade_surface, (0, 0))

            pygame.display.flip()

            self.update_frame_timer()

            # Pump the Pygame Event Queue
            #
            pygame.event.pump()

            self.fade_surface.set_alpha(self.fade_surface.get_alpha() - fadestep)

            frames = frames - 1

        # Make sure it's all visible now
        #
        self.window.update()
        self.window.render()
        pygame.display.flip()

        self.update_frame_timer()

        # Pump the Pygame Event Queue
        #
        pygame.event.pump()

        return

#    def process_CanSpeakEvent(self, event):

#    def process_SpawnEvent(self, event):

#    def process_DeleteEvent(self, event):

    def process_ChangeMapElementEvent(self, event):
        """Fetch asset and register/replace tile.
        """

        self.logger.debug("called")

        # Assets are entirely up to the UserInterface, so we fetch the asset
        # here
        #
        try:
            # Get a file-like object from asset manager
            #
            file = self.assets.fetch(event.tile.asset_desc)

        except:
            self.display_asset_exception(event.tile.asset_desc)

        # Replace with Surface from image file
        #
        surface = pygame.image.load(file)

        file.close()

        # Convert to internal format suitable for blitting
        #
        surface = surface.convert_alpha()

        # Do we already have a tile there?
        # Tiles are clickndrag subplanes of self.window.room, indexed by their
        # location as string representation.
        #
        if str(event.location) not in self.window.room.subplanes:

            plane = clickndrag.Plane(str(event.location),
                                     pygame.Rect((event.location[0] * 100,
                                                  event.location[1] * 100),
                                                 (100, 100)))

            self.window.room.sub(plane)

        self.window.room.subplanes[str(event.location)].image = surface

        return

#    def process_PerceptionEvent(self, event):

    ####################
    # Event handlers affecting Entities

#    def process_MovesToEvent(self, event):

#    def process_ChangeStateEvent(self, event):

#    def process_DropsEvent(self, event):

#    def process_PicksUpEvent(self, event):

#    def process_SaysEvent(self, event):
