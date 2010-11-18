"""2D Shard User Interface using PyGame

   (c) Florian Berger <fberger@florian-berger.de>
"""

# work started on 15. Oct 2010
#
# Partly based on the Shard PresentationEngine for the "Runaway" game done in
# October-December 2009, which in turn borrowed a lot from the PyGame-based
# CharanisMLClient developed in May 2008.

# TODO: spawn default Entities according to OBSTACLE tiles
# TODO: make tile FLOOR/OBSTACLE editable
# TODO: obey OBSTACLE tiles when placing Entites in PygameMapEditor
#
# TODO: support Entity Surfaces > 100x100
#
# TODO: Display all assets from local folder in PygameMapEditor for visual editing

import shard.plugins.ui
import pygame
import clickndrag
import clickndrag.gui
import tkinter.filedialog
import tkinter.simpledialog
import os.path
import re

def open_image(title, logger):
    """Auxillary function to make the user open an image file.
       Returns a tuple (Surface, filename) upon success, (None, None) otherwise.
    """

    surface = None
    filename = None

    tk = tkinter.Tk()
    tk.withdraw()

    image_types = ("Image Files",
                   ".jpg .png .gif .bmp .pcx .tga .tif .lbm .pbm .xpm")

    fullpath = tkinter.filedialog.askopenfilename(filetypes = [image_types],
                                                  title = title)
    tk.destroy()

    if not fullpath:

        logger.debug("no filename selected")

    else:
        filename = os.path.basename(fullpath)

        logger.debug("open: {}".format(fullpath))

        try:
            surface = pygame.image.load(fullpath)

        except pygame.error:

            self.logger.debug("could not load image '{}'".format(fullpath))

    return (surface, filename)

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

       PygameUserInterface.big_font
       PygameUserInterface.small_font
           Pygame.font.Font instances

       PygameUserInterface.loading_surface
       PygameUserInterface.loading_surface_position
           Surface and position for a loading message

       PygameUserInterface.fps_log_counter
           Counter to log actual fps every <framerate> frames

       PygameUserInterface.spacing
           Spacing between tiles.

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

        # Spacing between tiles.
        #
        self.spacing = 100

        # Open a click'n'drag window.
        #
        self.window = clickndrag.Display((800, 600))

        # Initialise font instances.
        #
        try:
            self.big_font = pygame.font.Font("Vera.ttf", 30)
            self.small_font = pygame.font.Font("Vera.ttf", 12)
            self.logger.debug("Using font 'Vera.ttf'")

        except:
            self.logger.debug("Font 'Vera.ttf' not found, using default font '{}'".format(pygame.font.get_default_font()))
            self.big_font = pygame.font.Font(None, 40)
            self.small_font = pygame.font.Font(None, 20)

        # Create a black pygame surface for fade effects.
        # Do not use Surface.copy() since we do not want per-pixel alphas.
        #
        #self.fade_surface = self.window.image.copy()
        self.fade_surface = pygame.Surface(self.window.image.get_rect().size)
        self.fade_surface.fill((0, 0, 0))

        loading_surface = self.big_font.render("Loading, please wait...",
                                               True,
                                               (255, 255, 255))

        self.fade_surface.blit(loading_surface,
                               (int(self.fade_surface.get_width() / 2 - loading_surface.get_width() / 2),
                                int(self.fade_surface.get_height() / 2 - loading_surface.get_height() / 2)))

        # Create inventory plane at PygameUserInterface.window.inventory
        #
        self.window.sub(clickndrag.Plane("inventory",
                                         pygame.Rect((0, 500), (800, 100)),
                                         dropped_upon_callback = self.inventory_callback))

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
            self.window.display.blit(self.small_font.render("{}/{} fps  ".format(int(self.clock.get_fps()),
                                                                                 self.framerate),
                                                            True,
                                                            (255, 255, 255),
                                                            (0, 0, 0)),
                                     (700, 580))

            self.fps_log_counter = self.framerate

        return

    def display_single_frame(self):
        """Update and render all click'd'drag planes.
        """

        if not self.freeze:

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

        self.logger.debug("entering room: {}".format(event.room_identifier))

        # Only fade out if a room is already displayed.
        #
        if not self.window.room.subplanes:

            self.logger.debug("not fading out. window.room.subplanes == {}".format(self.window.room.subplanes))

        else:
            self.logger.debug("room visible, fading out")

            frames = int(self.action_frames / 4)

            fadestep = int(255 / frames)

            self.fade_surface.set_alpha(0)
            
            # This is actually an exponential fade since the original surface is
            # not restored before blitting the fading surface
            #
            while frames:
                # Bypassing display_single_frame()

                self.window.display.blit(self.fade_surface, (0, 0))

                pygame.display.flip()

                self.update_frame_timer()

                # Pump the Pygame Event Queue
                #
                pygame.event.pump()

                self.fade_surface.set_alpha(self.fade_surface.get_alpha() + fadestep)

                frames = frames - 1

        # Make sure the window is black now
        #
        self.fade_surface.set_alpha(255)
        self.window.display.blit(self.fade_surface, (0, 0))

        pygame.display.flip()

        # Clear room
        #
        self.window.room.remove()

        # No more rendering until RoomComplete
        #
        self.logger.debug("freezing")
        self.freeze = True

        return

    def process_RoomCompleteEvent(self, event):
        """Update and render the Planes of the map elements and fade in the room.
        """

        self.logger.debug("called")

        # Display the game again and accept input
        #
        self.logger.debug("unfreezing")
        self.freeze = False

        # process_ChangeMapElementEvent and process_SpawnEvent should have
        # set up everything by now, so we can simply fade in and roll.
        # Since full screen blits are very slow, use a fraction of
        # action_frames.
        #
        frames = int(self.action_frames / 4)

        fadestep = int(255 / frames)

        self.fade_surface.set_alpha(255)

        self.logger.debug("fading in over {} frames, stepping {}".format(frames, fadestep))

        while frames:
            # Bypassing display_single_frame()

            self.window.update()
            self.window.render(force = True)

            self.window.display.blit(self.fade_surface, (0, 0))

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
        self.window.render(force = True)
        pygame.display.flip()

        self.update_frame_timer()

        # Pump the Pygame Event Queue
        #
        pygame.event.pump()

        return

#    def process_CanSpeakEvent(self, event):

    def process_SpawnEvent(self, event):
        """Add a subplane to window.room, possibly fetching an asset before.
           The name of the subplane is the Entity identifier, so the subplane
           is accessible using window.room.<identifier>.
           Entity.asset points to the Plane of the Entity.
        """

        if event.entity.user_interface is None:
            # Call base class
            #
            shard.plugins.ui.UserInterface.process_SpawnEvent(self, event)

        # This is prossibly a respawn from Rack, and the Entity already has
        # an asset.
        #
        if event.entity.asset is not None:
            self.logger.debug("Entity '{}' already has an asset, updating position to {}".format(event.entity.identifier,
                                                                                                 event.location))

            event.entity.asset.rect.left = event.location[0] * self.spacing
            event.entity.asset.rect.top = event.location[1] * self.spacing

        else:
            self.logger.debug("no asset for Entity '{}', attempting to fetch".format(event.entity.identifier))

            # Assets are entirely up to the UserInterface, so we fetch the asset
            # here
            #
            try:
                # Get a file-like object from asset manager
                #
                file = self.assets.fetch(event.entity.asset_desc)

            except:
                self.display_asset_exception(event.entity.asset_desc)

            # Replace with Surface from image file
            #
            surface = pygame.image.load(file)

            file.close()

            # Convert to internal format suitable for blitting
            #
            surface = surface.convert_alpha()

            # Create Plane, name is the entity identifier
            #
            plane = clickndrag.Plane(event.entity.identifier,
                                     pygame.Rect((event.location[0] * self.spacing,
                                                  event.location[1] * self.spacing),
                                                 (100, 100)))
            plane.image = surface

            # Items can be dragged by default
            #
            if event.entity.entity_type in (shard.ITEM_BLOCK, shard.ITEM_NOBLOCK):
                plane.draggable = True

            # Finally attach the Plane as the Entity's asset
            #
            event.entity.asset = plane

        # Now there is a Plane for the Entity. Add to room.
        # This implicitly removes the Plane from the former parent plane.
        #
        self.logger.debug("adding '{}' to window.room".format(event.entity.asset.name))
        self.window.room.sub(event.entity.asset)

        return

#    def process_DeleteEvent(self, event):

    def process_ChangeMapElementEvent(self, event):
        """Fetch asset and register/replace tile.
           Tile.asset is the Pygame Surface since possibly multiple Planes must
           be derived from a single Tile.
        """

        self.logger.debug("called")

        tile_from_list = None

        # The Client should have added the Tile to self.room.tile_list
        #
        for tile in self.room.tile_list:

            # This should succeed only once
            #
            if tile == event.tile:

                # Tiles may compare equal, but the may not refer to the same
                # instance, so we use tile from tile_list.
                #
                self.logger.debug("found event.tile in self.room.tile_list")
                tile_from_list = tile

        if tile_from_list.asset is not None:

            self.logger.debug("tile already has an asset: {}".format(tile_from_list))

        else:
            # Assets are entirely up to the UserInterface, so we fetch
            # the asset here
            #
            self.logger.debug("no asset for {}, attempting to fetch".format(tile_from_list))

            try:
                # Get a file-like object from asset manager
                #
                file = self.assets.fetch(tile_from_list.asset_desc)

            except:
                self.display_asset_exception(tile_from_list.asset_desc)

            self.logger.debug("loading Surface from {}".format(file))

            surface = pygame.image.load(file)

            file.close()

            # Convert to internal format suitable for blitting
            #
            surface = surface.convert_alpha()

            tile_from_list.asset = surface

        # Now tile_from_list.asset is present

        # Do we already have a tile there?
        # Tiles are clickndrag subplanes of self.window.room, indexed by their
        # location as string representation.
        #
        if str(event.location) not in self.window.room.subplanes:

            tile_plane = clickndrag.Plane(str(event.location),
                                          pygame.Rect((event.location[0] * self.spacing,
                                                       event.location[1] * self.spacing),
                                                      (100, 100)),
                                          dropped_upon_callback = self.tile_callback)

            self.window.room.sub(tile_plane)

        # Update image regardless whether the tile existed or not
        #
        self.logger.debug("changing image for tile at {0} to {1}".format(str(event.location),
                                                                        tile_from_list.asset))
        self.window.room.subplanes[str(event.location)].image = tile_from_list.asset

        return

#    def process_PerceptionEvent(self, event):

    ####################
    # Event handlers affecting Entities

#    def process_MovesToEvent(self, event):

#    def process_ChangeStateEvent(self, event):

    def process_DropsEvent(self, event):
        """Call base class process_DropsEvent and clean up the inventory plane.
        """

        shard.plugins.ui.UserInterface.process_DropsEvent(self, event)

        for name in self.window.inventory.subplanes_list:

            plane = self.window.inventory.subplanes[name]

            # Too lazy to use a counter ;-)
            #
            plane.rect.left = self.window.inventory.subplanes_list.index(name) * 100

    def process_PicksUpEvent(self, event):
        """Move the item's Plane from window.room to window.inventory.
           Then call the base class implementation to notify the Entity.
        """

        self.logger.debug("moving Plane from window.room to window.inventory")

        # The Client has already put the item from Client.room to Client.rack.
        # We have to update the display accordingly, so move the item plane
        # from window.room to window.inventory.

        # Cache the plane
        #
        plane = self.window.room.subplanes[event.item_identifier]

        # Append at the right of the inventory.
        # Since the item is already in self.host.rack.entity_dict, the position 
        # is len - 1.
        #
        plane.rect.top = 0
        plane.rect.left = (len(self.host.rack.entity_dict) - 1) * 100

        # This will remove the plane from its current parent, window.room
        #
        self.window.inventory.sub(plane)

        # Call base class to notify the Entity
        #
        shard.plugins.ui.UserInterface.process_PicksUpEvent(self, event)

#    def process_SaysEvent(self, event):

    def inventory_callback(self, plane, dropped_plane, screen_coordinates):
        """Drop callback to issue a TriesToPickUpEvent if the item is not already in Rack.
        """

        item_identifier = dropped_plane.name

        self.logger.debug("'{}' dropped on inventory".format(item_identifier))

        if item_identifier in self.host.rack.entity_dict.keys():

            self.logger.debug("'{}' already in Rack, skipping".format(item_identifier))

        else:

            self.logger.debug("issuing TriesToPickUpEvent")

            event = shard.TriesToPickUpEvent(self.host.player_id,
                                             self.room.entity_locations[item_identifier])

            self.message_for_host.event_list.append(event)

        return

    def tile_callback(self, plane, dropped_plane, screen_coordinates):
        """Drop callback to issue a TriesToDropEvent.
        """

        name = plane.name

        # Just to be sure, check if the Plane's name matches a "(x, y)" string.
        # Taken from shard.plugins.serverside
        #
        if not re.match("^\([0-9]+\s*,\s*[0-9]+\)$", name):
            self.logger.error("plane.name does not match coordinate tuple: '{}'".format(name))

        else:
            # The target identifier is a coordinate tuple in a Room which
            # can by convention be infered from the Plane's name.
            #
            tries_to_drop_event = shard.TriesToDropEvent(self.host.player_id,
                                                         dropped_plane.name,
                                                         eval(name))

            self.message_for_host.event_list.append(tries_to_drop_event)

        return

class PygameMapEditor(PygameUserInterface):
    """A Pygame-based user interface that serves as a map editor.

       Additional PygameMapEditor attributes:

       PygameUserInterface.window.buttons
           clickndrag Plane for the buttons, 100x600px and located at the left
           border of the window.

       PygameUserInterface.window.properties
           clickndrag Plane for Entity properties, 100x600px and located at the
           right border of the window.

       PygameUserInterface.plane_cache
           A list to cache temporarily invisible planes

       PygameUserInterface.overlay_surface
           A semi-transparent red Surface to be used as an OBSTACLE indicator
           overlay
    """

    def __init__(self, assets, framerate, logger):
        """Call PygameUserInterface.__init__(), but set up different Planes.
        """

        # Call base class __init__()
        #
        PygameUserInterface.__init__(self, assets, framerate, logger)

        self.logger.debug("called")

        # Spacing is a little larger here to show grid lines.
        #
        self.spacing = 101

        # Setup a cache for planes
        #
        self.plane_cache = []

        # Open a click'n'drag window.
        #
        self.window = clickndrag.Display((1000, 600))

        # Set window name
        #
        pygame.display.set_caption("Shard Map Editor")

        # Create a black pygame surface for fade effects
        # Do not use Surface.copy() since we do not want per-pixel alphas.
        #
        self.fade_surface = pygame.Surface(self.window.image.get_rect().size)
        self.fade_surface.fill((0, 0, 0))

        loading_surface = self.big_font.render("Loading, please wait...",
                                               True,
                                               (255, 255, 255))

        self.fade_surface.blit(loading_surface,
                               (int(self.fade_surface.get_width() / 2 - loading_surface.get_width() / 2),
                                int(self.fade_surface.get_height() / 2 - loading_surface.get_height() / 2)))

        # Create a semi-transparent red Surface to be used as an OBSTACLE
        # indicator overlay
        #
        self.overlay_surface = pygame.Surface((100, 100))
        self.overlay_surface.fill((255, 0, 0))
        self.overlay_surface.set_alpha(127)

        # Create inventory plane at PygameUserInterface.window.inventory
        #
        self.window.sub(clickndrag.Plane("inventory",
                                         pygame.Rect((100, 500), (800, 100)),
                                         dropped_upon_callback = self.inventory_callback))

        # Create plane for the room.
        #
        self.window.sub(clickndrag.Plane("room",
                                         pygame.Rect((100, 0), (800, 500))))

        # Create plane for the editor buttons.
        #
        self.window.sub(clickndrag.Plane("buttons",
                                         pygame.Rect((0, 0), (100, 600))))

        self.window.buttons.image.fill((120, 120, 120))

        # Add buttons
        #
        self.window.buttons.sub(clickndrag.gui.Button("Open Image",
                                                      pygame.Rect((5, 5),
                                                                  (90, 30)),
                                                      self.open_image))

        self.window.buttons.sub(clickndrag.gui.Button("Load Room",
                                                      pygame.Rect((5, 45),
                                                                  (90, 30)),
                                                      self.load_room))

        self.window.buttons.sub(clickndrag.gui.Button("Save Room",
                                                      pygame.Rect((5, 85),
                                                                  (90, 30)),
                                                      self.save_room))

        self.window.buttons.sub(clickndrag.gui.Button("Add Item",
                                                      pygame.Rect((5, 125),
                                                                  (90, 30)),
                                                      self.add_item))

        self.window.buttons.sub(clickndrag.gui.Button("Edit Walls",
                                                      pygame.Rect((5, 165),
                                                                  (90, 30)),
                                                      self.edit_walls))

        self.window.buttons.sub(clickndrag.gui.Button("Quit",
                                                      pygame.Rect((5, 565),
                                                                  (90, 30)),
                                                      self.quit))

        # Create plane for the properties
        #
        self.window.sub(clickndrag.Plane("properties",
                                         pygame.Rect((900, 0), (100, 600))))

        self.window.properties.image.fill((120, 120, 120))

        self.logger.debug("complete")

        return

    def open_image(self, plane):
        """Button callback to prompt the user for a room background image, load it and assign it to tiles.
        """

        self.logger.debug("called")

        new_image = open_image("Open Background Image", self.logger)[0]

        if new_image is not None:

            for x in range(8):
                for y in range(5):
                    rect = pygame.Rect((x * 100, y * 100), (100, 100))

                    # TODO: catch exception for smaller images
                    #
                    self.window.room.subplanes[str((x, y))].image = new_image.subsurface(rect)

        # TODO: warn user to save the room before editing walls

    def save_room(self, plane):
        """Button callback to save the tile images, resend and save the whole Room.
        """

        self.logger.debug("called")

        tk = tkinter.Tk()
        tk.withdraw()

        fullpath = tkinter.filedialog.asksaveasfilename(filetypes = [("Shard Room Files",
                                                                      ".floorplan")],
                                                        title = "Save Tiles And Floorplan")

        tk.destroy()

        path, filename = os.path.split(fullpath)

        # Strip extension, if given
        #
        filename = os.path.splitext(filename)[0]

        if filename:

            self.logger.debug("save to: {}".format(filename))

            self.message_for_host.event_list.append(shard.EnterRoomEvent(filename))

            for x in range(8):
                for y in range(5):

                    # Save image file
                    #
                    current_file = filename + "-{0}_{1}.png".format(x, y)
                    self.logger.debug(current_file)
                    pygame.image.save(self.window.room.subplanes[str((x, y))].image,
                                      os.path.join(path, current_file))

                    # Send Tile to Server
                    #
                    tile = shard.Tile(self.room.floor_plan[(x, y)].tile.tile_type,
                                      current_file)

                    event = shard.ChangeMapElementEvent(tile, (x, y))

                    self.message_for_host.event_list.append(event)

            # Now spawn all Entities in the Server
            #
            for identifier in self.room.entity_dict.keys():

                # Create a new Entity which can be pickled by Event loggers
                #
                entity = shard.Entity(self.room.entity_dict[identifier].entity_type,
                                      identifier,
                                      self.room.entity_dict[identifier].asset_desc)

                event = shard.SpawnEvent(entity,
                                         self.room.entity_locations[identifier])

                self.message_for_host.event_list.append(event)

            self.message_for_host.event_list.append(shard.RoomCompleteEvent())

        else:
            self.logger.debug("no filename selected")

    def load_room(self, plane):
        """Button callback to issue a TriesToTalkToEvent to receive a list of rooms to load from the MapEditor Plugin.
        """
        self.logger.debug("called")

        event = shard.TriesToTalkToEvent(self.host.player_id, "load_room")

        self.message_for_host.event_list.append(event)

    def add_item(self, plane):
        """Button callback to request item identifier and image and add it to the rack.
        """

        self.logger.debug("called")

        tk = tkinter.Tk()
        tk.withdraw()

        item_identifier = tkinter.simpledialog.askstring("Add Item",
                                                         "Identifier Of New Item:")

        tk.destroy()

        if item_identifier == '' or item_identifier is None:

            self.logger.debug("no item identifer given")

        else:

            image, filename = open_image("Image Of New Item", self.logger)

            if image is not None:

                entity = shard.Entity(shard.ITEM_BLOCK,
                                      item_identifier,
                                      filename)

                self.logger.debug("appending SpawnEvent and PicksUpEvent")

                # TODO: revert to (0, 0) or another safe spawning location
                #
                self.message_for_host.event_list.append(shard.SpawnEvent(entity, (3, 3)))

                self.message_for_host.event_list.append(shard.PicksUpEvent(self.host.player_id,
                                                                           item_identifier))

    def quit(self, plane):
        """Button callback to set self.exit_requested = True
        """
        self.logger.debug("setting exit_requested = True")
        self.exit_requested = True

    def edit_walls(self, plane):
        """Button callback to switch to wall edit mode.
        """
        self.logger.debug("called")

        # Cache button planes from sidebar...
        #
        for button in self.window.buttons.subplanes.values():
            self.plane_cache.append(button)

        # ...and remove
        #
        self.window.buttons.remove()

        self.window.buttons.sub(clickndrag.gui.Label("title",
                                                     "Edit Walls",
                                                      pygame.Rect((0, 0),
                                                                  (100, 30)),
                                                      color = (120, 120, 120)))

        self.window.buttons.sub(clickndrag.gui.Button("Done",
                                                      pygame.Rect((5, 35),
                                                                  (90, 30)),
                                                      self.wall_edit_done))

        # Clear Entity planes from room, but cache them.
        # By convention the name of the Entity Plane is Entity.identifier.
        #
        for identifier in self.room.entity_dict.keys():
            self.plane_cache.append(self.window.room.subplanes[identifier])
            self.window.room.remove(identifier)

        self.logger.debug("{} Plane(s) in plane_cache now".format(len(self.plane_cache)))

        # Make Entity planes in inventory insensitive to drags
        #
        for plane in self.window.inventory.subplanes.values():
            plane.draggable = False

        # Install Tile clicked callback.
        # All Entity Planes have been removed from room, so there should be only
        # tiles left.
        #
        for plane in self.window.room.subplanes.values():
            plane.clicked_callback = self.make_tile_obstacle

        # Finally, create overlays for OBSTACLE tiles.
        # TODO: slight duplicate from make_tile_obstacle
        #
        for coordinates in self.room.floor_plan.keys():

            if self.room.floor_plan[coordinates].tile.tile_type == shard.OBSTACLE:

                overlay_plane = clickndrag.Plane(str(coordinates) + "_overlay",
                                                 pygame.Rect(self.window.room.subplanes[str(coordinates)].rect),
                                                 clicked_callback = self.make_tile_floor)

                overlay_plane.image = self.overlay_surface

                self.window.room.sub(overlay_plane)

    def make_tile_obstacle(self, plane):
        """Clicked callback which changes the Tile type to shard.OBSTACLE.
           More specific, a ChangeMapElementEvent is sent to the Server, and an
           overlay is applied to visualize the OBSTACLE type.
        """

        self.logger.debug("returning ChangeMapElementEvent and creating overlay for tile at {}".format(plane.name))

        # The name of the clicked Plane is supposed to be a string representation
        # of a coordinate tuple.
        #
        coordinates = eval(plane.name)
        asset_desc = self.room.floor_plan[coordinates].tile.asset_desc

        event = shard.ChangeMapElementEvent(shard.Tile(shard.OBSTACLE, asset_desc),
                                            coordinates)

        self.message_for_host.event_list.append(event)

        # Draw an overlay indicating the OBSTACLE type.
        # rect can be taken from the Plane that received the click, but we make
        # a copy to be on the safe side.
        #
        overlay_plane = clickndrag.Plane(str(coordinates) + "_overlay",
                                         pygame.Rect(plane.rect),
                                         clicked_callback = self.make_tile_floor)

        overlay_plane.image = self.overlay_surface

        self.window.room.sub(overlay_plane)

    def make_tile_floor(self, plane):
        """Clicked callback which changes the Tile type to shard.FLOOR.
           More specific, a ChangeMapElementEvent is sent to the Server, and the
           overlay to visualize the OBSTACLE type is deleted.
        """

        # Based on a copy-paste from make_tile_obstacle()

        self.logger.debug("returning ChangeMapElementEvent and deleting '{}'".format(plane.name))

        # The clicked Plane is  the overlay. Its name is supposed to be a string
        # representation of a coordinate tuple plus "_overlay".
        #
        coordinates = eval(plane.name.split("_overlay")[0])
        asset_desc = self.room.floor_plan[coordinates].tile.asset_desc

        event = shard.ChangeMapElementEvent(shard.Tile(shard.FLOOR, asset_desc),
                                            coordinates)

        self.message_for_host.event_list.append(event)

        # Delete the overlay indicating the OBSTACLE type.
        #
        plane.destroy()

    def wall_edit_done(self, plane):
        """Button callback which restores the editor to the state before edit_walls().
        """
        self.logger.debug("called")

        # Remove all wall marker overlays.
        # Remove Tile clicked callbacks along the way.
        # Entity Planes are not yet restored, so there should be only tiles left.
        #
        for plane in list(self.window.room.subplanes.values()):

            if plane.name.endswith("_overlay"):

                plane.destroy()

            else:
                plane.clicked_callback = None
                
        # Restore Entity Planes in room
        #
        while not isinstance(self.plane_cache[-1], clickndrag.gui.Button):
            self.window.room.sub(self.plane_cache.pop())

        # Make Entity Planes in inventory sensitive to drags
        #
        for plane in self.window.inventory.subplanes.values():
            plane.draggable = True

        self.window.buttons.remove()

        # Restore buttons, flushing plane cache
        #
        while len(self.plane_cache):
            self.window.buttons.sub(self.plane_cache.pop())

    def process_CanSpeakEvent(self, event):
        """Open the senteces as an OptionList and return a SaysEvent to the host.
        """

        self.logger.debug("called")

        rect = pygame.Rect((100, 100),
                           (300, len(event.sentences) * 30 + 30))

        self.window.room.sub(clickndrag.gui.OptionList("select_room",
                                                       rect,
                                                       event.sentences,
                                                       lambda option: self.message_for_host.event_list.append(shard.SaysEvent(self.host.player_id, option.text))))
        return

    def process_SpawnEvent(self, event):
        """Call PygameUserInterface.process_SpawnEvent and add a clicked_callback to the Entity.
        """

        PygameUserInterface.process_SpawnEvent(self, event)

        plane = self.window.room.subplanes[event.entity.identifier]

        if plane.clicked_callback is None:

            self.logger.debug("clicked_callback of '{}' is still None, adding callback".format(event.entity.identifier))
            plane.clicked_callback = self.show_properties

        return

    def show_properties(self, plane):
        """Click callback for entities which shows their properties in the properties Plane.
        """

        self.logger.debug("called")

        # Only update if not already visible
        #
        if self.window.properties.subplanes_list and self.window.properties.identifier.text == plane.name:

            self.logger.debug("properties for '{}' already displayed".format(plane.name))

        else:
            self.logger.debug("showing properties of '{}'".format(plane.name))

            self.window.properties.remove()

            if plane.name in self.room.entity_dict.keys():

                entity = self.room.entity_dict[plane.name]

            elif plane.name in self.host.rack.entity_dict.keys():

                entity = self.host.rack.entity_dict[plane.name]

            else:
                self.logger.error("entity '{}' neither in Room nor Rack, can not update property inspector".format(plane.name))

                return

            # Entity.identifier
            #
            self.window.properties.sub(clickndrag.gui.Label("identifier",
                                                            entity.identifier,
                                                            pygame.Rect((0, 0), (100, 30)),
                                                            color = (120, 120, 120)))

            # Entity.asset
            #
            asset_plane = clickndrag.Plane("asset", pygame.Rect((0, 33), (100, 100)))
            asset_plane.image = entity.asset.image

            self.window.properties.sub(asset_plane)

            # Entity.asset_desc
            #
            self.window.properties.sub(clickndrag.gui.Label("asset_desc",
                                                            entity.asset_desc,
                                                            pygame.Rect((0, 136), (100, 30)),
                                                            color = (120, 120, 120)))

            # Entity.entity_type
            #
            self.window.properties.sub(clickndrag.gui.Label("entity_type",
                                                            entity.entity_type,
                                                            pygame.Rect((0, 169), (100, 30)),
                                                            color = (120, 120, 120)))

            # Entity.state
            #
            self.window.properties.sub(clickndrag.gui.Label("state",
                                                            entity.state,
                                                            pygame.Rect((0, 202), (100, 30)),
                                                            color = (120, 120, 120)))
            return
