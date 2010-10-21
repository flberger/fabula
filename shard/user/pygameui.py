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

import shard.user
import pygame
import clickndrag

class PygameUserInterface(shard.user.UserInterface):
    """This is a Pygame implementation of an UserInterface for the Shard Client.

       Inherited from shard.user.UserInterface:

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

       PygameUserInterface.window
           An instance of clickndrag.Display

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
        shard.user.UserInterface.__init__(self, assets, framerate, logger)

        pygame.init()

        # Initialize the frame timing clock.
        #
        self.clock = pygame.time.Clock()

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

        self.logger.debug("complete")

        return

    def update_frame_timer(self):
        """Use pygame.time.Clock.tick() to slow down to given framerate.
        """

        self.clock.tick(self.framerate)

        return

    def display_single_frame(self):
        """Update and render all click'd'drag planes.
        """

        # Pump the Pygame Event Queue
        #
        pygame.event.pump()

        self.window.update()
        self.window.render()

        # TODO: replace with update(dirty_rect_list)
        #
        pygame.display.flip()

        self.update_frame_timer()

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

        screen.process(events)

        # TODO: Must figure out Events here and set self.message_for_host.event_list.append(event)
        # TODO: This is weird. This should be returned instead in some way, shouldn't it?

        return

    ####################
    # Event handlers affecting presentation and management

    def process_EnterRoomEvent(self, event):
        """Fade display window to black.
        """

        self.logger.debug("called")

        fadestep = int(255 / self.action_frames)
        
        self.fade_surface.set_alpha(0)
        
        frames = self.action_frames

        # This is actually an exponential fade since the original surface is
        # not restored before blitting the fading surface
        #
        while frames:
            # Bypassing display_single_frame()

            # Pump the Pygame Event Queue
            #
            pygame.event.pump()

            self.window.rendersurface.blit(self.fade_surface)

            pygame.display.flip()

            self.update_frame_timer()

            self.fade_surface.set_alpha(self.fade_surface.get_alpha + fadestep)

            frames = frames - 1

        # Make sure it's black now
        #
        self.window.rendersurface.fill((0, 0, 0))
        pygame.display.flip()

        return

#    def process_RoomCompleteEvent(self, event):

#    def process_CanSpeakEvent(self, event):

#    def process_SpawnEvent(self, event):

#    def process_DeleteEvent(self, event):

    def process_ChangeMapElementEvent(self, event):
        """Called with a list of instances of ChangeMapElementEvent.
           In this method you must implement a major redraw of the display,
           updating all Map elements and after that all Entities.
           This is only a single frame though.
           Note that event may be empty.
        """

        self.logger.debug("called")

        # Assets are entirely up to the UserInterface, so we fetch the asset
        # here
        #
        try:
            #!!!
            event.tile.asset = self.assets.fetch(event.tile.asset)

        except:
            self.display_asset_exception(event.tile.asset)

        event.tile.asset = event.tile.asset.convert_alpha()
        
        # pygame convert surface if applicable
        # clear tile area because of possible alpha
        # blit/redraw
        # self.display_single_frame()

        return

#    def process_PerceptionEvent(self, event):

    ####################
    # Event handlers affecting Entities

#    def process_MovesToEvent(self, event):

#    def process_ChangeStateEvent(self, event):

#    def process_DropsEvent(self, event):

#    def process_PicksUpEvent(self, event):

#    def process_SaysEvent(self, event):
