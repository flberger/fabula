"""2D Shard User Interface using PyGame

   (c) Florian Berger <fberger@florian-berger.de>
"""

# work started on 15. Oct 2010
#
# Partly based on the Shard PresentationEngine for the "Runaway" game done in
# October-December 2009, which in turn borrowed a lot from the PyGame-based
# CharanisMLClient developed in May 2008.

# TODO: in PygameEditor, display all assets from local folder for visual editing
#
# TODO: render order top-down, following lines

import shard.plugins.ui
import pygame
import clickndrag.gui
import tkinter.filedialog
import tkinter.simpledialog
import os
import re

def load_image(title):
    """Auxiliary function to make the user open an image file.
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

    if fullpath:

        filename = os.path.basename(fullpath)

        try:
            surface = pygame.image.load(fullpath)

        except pygame.error:

            # This will return None
            #
            pass

    return (surface, filename)

class EntityPlane(clickndrag.Plane):
    """Subclass of Plane with an update() method that handles movement.

       Additional attributes:

       EntityPlane.position_list
           A list of movement steps as position tuples
    """

    def __init__(self, name, rect, draggable = False,
                                   grab = False,
                                   clicked_callback = None,
                                   dropped_upon_callback = None):
        """Initialise.
        """

        # Call base class
        #
        clickndrag.Plane.__init__(self, name, rect, draggable,
                                                    grab,
                                                    clicked_callback,
                                                    dropped_upon_callback)

        self.position_list = []

        return

    def update(self):
        """If EntityPlane.target has not yet been reached, move to the positions given in EntityPlane.position_list.
        """

        if self.position_list:
            new_position = self.position_list.pop(0)
            self.rect.centerx = new_position[0]
            self.rect.bottom = new_position[1]

        return

class PygameEntity(shard.Entity):
    """Pygame-aware subclass of Entity to be used in PygameUserInterface.

       Additional attributes:

       PygameEntity.spacing
           The spacing between tiles.

       PygameEntity.action_frames
           The number of frames per action.
    """

    def __init__(entity_type, identifier, asset_desc, spacing, action_frames):
        """Initialise.
           spacing is the spacing between tiles.
           action_frames is the number of frames per action.
        """

        # Call base class
        #
        shard.Entity.__init__(self, entity_type, identifier, asset_desc)

        self.spacing = spacing
        self.action_frames = action_frames

        return

    def process_MovesToEvent(self, event):
        """Instruct the EntityPlane with the movement.
        """

        if self.asset.position_list:

            # Take the last queued position as current
            #
            current_x = self.asset.position_list[-1][0]
            current_y = self.asset.position_list[-1][1]

        else:
            # Reference point is the bottom center of the image, which is
            # positioned at the bottom center of the tile
            #
            current_x = self.asset.rect.centerx
            current_y = self.asset.rect.bottom

        future_x = event.location[0] * self.spacing + int(self.spacing / 2)
        future_y = event.location[1] * self.spacing + self.spacing

        dx_per_frame = (future_x - current_x) / self.action_frames
        dy_per_frame = (future_y - current_y) / self.action_frames

        position_list = []

        # Re-using current_x, current_y retrieved above.
        # But omit last step.
        #
        for i in range(self.action_frames - 1):

            current_x = current_x + dx_per_frame
            current_y = current_y + dy_per_frame

            # Round now to distribute the error
            #
            position_list.append((int(current_x), int(current_y)))

        # Append final position to make sure it's being hit.
        #
        position_list.append((future_x, future_y))

        self.asset.position_list.extend(position_list)

        return

class PygameUserInterface(shard.plugins.ui.UserInterface):
    """This is a Pygame implementation of an UserInterface for the Shard Client.

       Additional attributes:

       PygameUserInterface.clock
           An instance of pygame.time.Clock

       PygameUserInterface.big_font
       PygameUserInterface.small_font
           Pygame.font.Font instances

       PygameUserInterface.loading_surface
       PygameUserInterface.loading_surface_position
           Surface and position for a loading message

       PygameUserInterface.inventory_plane
           Plane to display the inventory

       PygameUserInterface.room_plane
           Plane to display the room

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

    def __init__(self, assets, framerate, host):
        """This method initialises the PygameUserInterface.
           assets must be an instance of shard.Assets or a subclass.
           framerate must be an integer and sets the maximum (not minimum ;-))
           frames per second the client will run at.
        """

        # Call original __init__()
        #
        shard.plugins.ui.UserInterface.__init__(self, assets, framerate, host)

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
        # TODO: Use Assets to fetch the font
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

        # Create inventory plane.
        #
        self.inventory_plane = clickndrag.Plane("inventory",
                                                pygame.Rect((0, 500), (800, 100)),
                                                dropped_upon_callback = self.inventory_callback)

        self.window.sub(self.inventory_plane)

        self.window.inventory.image.fill((32, 32, 32))

        # Add the standard action icons to the inventory
        #
        for name, x in (("look_at", 0), ("manipulate", 100), ("talk_to", 200)):

            # Partly copied from process_SpawnEvent
            #
            try:
                file = self.assets.fetch(name + ".png")

            except:
                self.display_asset_exception(name + ".png")

            surface = pygame.image.load(file)

            file.close()

            # Convert to internal format suitable for blitting
            #
            surface = surface.convert_alpha()

            # Create Rect - taken from above
            #
            rect = pygame.Rect((0, 0), surface.get_rect().size)

            rect.topleft = (x, 0)

            # Create Plane
            #
            plane = clickndrag.Plane(name, rect, draggable = True)

            plane.image = surface

            self.logger.debug("adding {} to inventory".format(plane))

            # Finally create subplane
            #
            self.window.inventory.sub(plane)

        # Create plane for the room.
        #
        self.room_plane = clickndrag.Plane("room",
                                           pygame.Rect((0, 0), (800, 500)))

        self.window.sub(self.room_plane)

        self.logger.debug("complete")

        return

    def update_frame_timer(self):
        """Use pygame.time.Clock.tick() to slow down to given framerate.
        """

        self.clock.tick(self.framerate)

        if self.fps_log_counter:

            self.fps_log_counter = self.fps_log_counter - 1

        else:
            self.fps_log_counter = self.framerate

            if not self.freeze:

                fps_string = "{}/{} fps  ".format(int(self.clock.get_fps()),
                                                  self.framerate)

                self.window.display.blit(self.small_font.render(fps_string, True,
                                                                (127, 127, 127),
                                                                (32, 32, 32)),
                                         (700, 575))

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
        """Gather Pygame events, scan for QUIT and let the clickndrag Display evaluate the events.
        """

        # The UserInterface should only ever collect and send one
        # single client event to prevent cheating and blocking other
        # clients in the server. (hint by Alexander Marbach)

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

        # TODO: Adding Events to self.message_for_host is weird. This should be returned instead in some way, shouldn't it?

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

            frames = self.action_frames

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
        self.window.room.remove_all()

        # No more rendering until RoomComplete
        #
        self.logger.debug("freezing")
        self.freeze = True

        return

    def process_RoomCompleteEvent(self, event):
        """Update and render the Planes of the map elements and fade in the room.
        """

        self.logger.debug("rearranging tile and entity planes")

        # Entities may have been spawned inbetween ChangeMapElementEvents, but
        # clickndrag requires their Planes to be the last ones in
        # window.room.subplanes_list to be rendered on top of the tiles. So,
        # check if there are any entites in the wrong place and correct.

        tiles = []
        entities = []

        for name in self.window.room.subplanes_list:

            # By convention, a tile's plane name is the string representation of
            # the coordinates, so it starts with a brace.
            #
            if name.startswith("("):
                tiles.append(name)
            else:
                entities.append(name)

        self.window.room.subplanes_list = tiles + entities

        # Make items next to player draggable
        #
        self.make_items_draggable()

        # Display the game again and accept input
        #
        self.logger.debug("unfreezing")
        self.freeze = False

        # process_ChangeMapElementEvent and process_SpawnEvent should have
        # set up everything by now, so we can simply fade in and roll.
        # Since full screen blits are very slow, use a fraction of
        # action_frames.
        #
        frames = self.action_frames

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
           When a Plane has not yet been added, the Entity's class is changed
           to PygameEntity in addition.
        """

        if event.entity.user_interface is None:
            # Call base class
            #
            shard.plugins.ui.UserInterface.process_SpawnEvent(self, event)

        # This is possibly a respawn from Rack, and the Entity already has
        # an asset.
        #
        if event.entity.asset is not None:

            msg = "Entity '{}' already has an asset, updating position to {}"
            self.logger.debug(msg.format(event.entity.identifier,
                                         event.location))

            x = event.location[0] * self.spacing + self.spacing / 2
            y = event.location[1] * self.spacing + self.spacing

            event.entity.asset.rect.centerx = x
            event.entity.asset.rect.bottom = y

            # Restore callback
            #
            event.entity.asset.dropped_upon_callback = self.entity_dropped_callback

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

            self.display_loading_progress(event.entity.asset_desc)

            # Replace with Surface from image file
            #
            surface = pygame.image.load(file)

            file.close()

            # Convert to internal format suitable for blitting
            #
            surface = surface.convert_alpha()

            # Create Rect - taken from above
            #
            rect = pygame.Rect((0, 0), surface.get_rect().size)

            rect.centerx = event.location[0] * self.spacing + self.spacing / 2
            rect.bottom = event.location[1] * self.spacing + self.spacing

            # Create EntityPlane, name is the entity identifier
            #
            plane = EntityPlane(event.entity.identifier,
                                rect,
                                dropped_upon_callback = self.entity_dropped_callback)

            plane.image = surface

            # Finally attach the Plane as the Entity's asset
            #
            event.entity.asset = plane

            # The Entity must be able to react to Events. These reactions are
            # Pygame specific and are thus not covered in the basic shard.Entity
            # class. Thus, we exploit a Python feature here and change the
            # Entity's class at runtime to a subclass that supports Pygame.
            #
            event.entity.__class__ = PygameEntity

            # Since we do not call PygameEntity.__init__() to prevent messing
            # up already present data, we add required attributes
            #
            event.entity.spacing = self.spacing
            event.entity.action_frames = self.action_frames

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

        if tile_from_list is None:

            self.logger.error("could not find tile {} in tile_list of room '{}'".format(event.tile, self.room.identifier))
            raise Exception("could not find tile {} in tile_list of room '{}'".format(event.tile, self.room.identifier))

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

            self.display_loading_progress(tile_from_list.asset_desc)

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
                                          clicked_callback = self.tile_clicked_callback,
                                          dropped_upon_callback = self.tile_drop_callback)

            self.window.room.sub(tile_plane)

        # Update image regardless whether the tile existed or not
        #
        self.logger.debug("changing image for tile at {0} to {1}".format(str(event.location),
                                                                        tile_from_list.asset))
        self.window.room.subplanes[str(event.location)].image = tile_from_list.asset

        return

    def process_PerceptionEvent(self, event):
        """Display the perception.
        """

        self.logger.debug("called")

        # Using a OkBox for now.
        # Taken from PygameEditor.open_image().
        #
        perception_box = clickndrag.gui.OkBox(event.perception)
        perception_box.rect.center = pygame.Rect((0, 0), self.window.room.rect.size).center
        self.window.room.sub(perception_box)

        return

    def process_AttemptFailedEvent(self, event):
        """Flash the screen.
        """

        self.logger.debug("called")

        # Flash very short
        #
        frames = int(self.action_frames / 10)

        self.window.room.rendersurface.fill((250, 250, 250))
        self.window.room.last_rect = None

        while frames:
            self.display_single_frame()
            frames = frames - 1

        # Mark Entity Plane as changed to trigger redraw of the room
        #
        self.window.room.subplanes[event.identifier].last_rect = None

        self.display_single_frame()

        return

    ####################
    # Event handlers affecting Entities

    def process_MovesToEvent(self, event):
        """Make EntityPlanes surrounding the new position draggable and call the base class method.
        """

        self.logger.debug("called")

        # Call base class
        #
        shard.plugins.ui.UserInterface.process_MovesToEvent(self, event)

        # TODO: use actual player identifier
        #
        if event.identifier == "player":
            self.make_items_draggable()

        return

#    def process_ChangeStateEvent(self, event):

    def process_DropsEvent(self, event):
        """Call base class process_DropsEvent, clean up the inventory plane and adjust draggable flags.
        """

        self.logger.debug("called")

        shard.plugins.ui.UserInterface.process_DropsEvent(self, event)

        for name in self.window.inventory.subplanes_list:

            plane = self.window.inventory.subplanes[name]

            # Too lazy to use a counter ;-)
            #
            plane.rect.left = self.window.inventory.subplanes_list.index(name) * 100

        # Make items next to player draggable
        #
        self.make_items_draggable()

        return

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
        # + 300 for the standard action icons.
        #
        plane.rect.top = 0
        plane.rect.left = (len(self.host.rack.entity_dict) - 1) * 100 + 300

        # This will remove the plane from its current parent, window.room
        #
        self.window.inventory.sub(plane)

        # Make sure the plane is draggable
        #
        plane.draggable = True

        # Make insensitive to drops
        #
        plane.dropped_upon_callback = None

        # Call base class to notify the Entity
        #
        shard.plugins.ui.UserInterface.process_PicksUpEvent(self, event)

#    def process_SaysEvent(self, event):

    def inventory_callback(self, plane, dropped_plane, screen_coordinates):
        """Drop callback to issue a TriesToPickUpEvent if the item is not already in Rack.
        """

        item_identifier = dropped_plane.name

        self.logger.debug("'{}' dropped on inventory".format(item_identifier))

        # Ignore drops of standard actions
        #
        if dropped_plane.name in ("look_at", "manipulate", "talk_to"):

            self.logger.debug("ignoring drop of action icon")

        elif item_identifier in self.host.rack.entity_dict.keys():

            self.logger.debug("'{}' already in Rack, skipping".format(item_identifier))

        else:

            self.logger.debug("issuing TriesToPickUpEvent")

            event = shard.TriesToPickUpEvent(self.host.player_id,
                                             self.room.entity_locations[item_identifier])

            self.message_for_host.event_list.append(event)

        return

    def tile_clicked_callback(self, plane):
        """Clicked callback to issue a TriesToMoveEvent.
        """

        # TODO: This is so much like tile_drop_callback() that it should be unified.

        self.logger.debug("called")

        # Just to be sure, check if the Plane's name matches a "(x, y)" string.
        # Taken from shard.plugins.serverside
        #
        if not re.match("^\([0-9]+\s*,\s*[0-9]+\)$", plane.name):
            self.logger.error("plane.name does not match coordinate tuple: '{}'".format(plane.name))

        else:
            # The target identifier is a coordinate tuple in a Room which
            # can by convention be infered from the Plane's name.
            #
            event = shard.TriesToMoveEvent(self.host.player_id,
                                           eval(plane.name))

            self.message_for_host.event_list.append(event)

        return

    def tile_drop_callback(self, plane, dropped_plane, screen_coordinates):
        """Drop callback to issue a TriesToDropEvent.
        """

        self.logger.debug("called")

        name = plane.name

        # Ignore drops of standard actions
        #
        if dropped_plane.name in ("look_at", "manipulate", "talk_to"):

            self.logger.debug("ignoring drop of action icon")

        # Just to be sure, check if the Plane's name matches a "(x, y)" string.
        # Taken from shard.plugins.serverside
        #
        elif not re.match("^\([0-9]+\s*,\s*[0-9]+\)$", name):

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

    def entity_dropped_callback(self, plane, dropped_plane, coordinates):
        """Dropped upon callback for Entities.
           Adds appropriate Events to PygameUserInterface.message_for_host.
        """

        self.logger.debug("called")

        # Although we know the Entity, the server determines what if being
        # looked at. So send target identifiers instead of Entity identifiers.

        if dropped_plane.name == "look_at":

            event = shard.TriesToLookAtEvent(self.host.player_id,
                                             self.host.room.entity_locations[plane.name])

        elif dropped_plane.name == "manipulate":

            event = shard.TriesToManipulateEvent(self.host.player_id,
                                                 self.host.room.entity_locations[plane.name])

        elif dropped_plane.name == "talk_to":

            event = shard.TriesToTalkToEvent(self.host.player_id,
                                             self.host.room.entity_locations[plane.name])

        else:
            event = shard.TriesToDropEvent(self.host.player_id,
                                           dropped_plane.name,
                                           self.host.room.entity_locations[plane.name])

        self.message_for_host.event_list.append(event)

        return

    def display_loading_progress(self, obj):
        """Display the string representation of the object given on the loading screen while the game is frozen.
        """

        if self.freeze:

            displaystring = str(obj).center(32)

            self.window.display.blit(self.small_font.render(displaystring,
                                                            True,
                                                            (127, 127, 127),
                                                            (0, 0, 0)),
                                     (300, 500))

            pygame.display.flip()

        return

    def make_items_draggable(self):
        """Auxiliary method to make items next to the player draggable.
        """

        # TODO: use actual player identifier
        #
        if "player" in self.host.room.entity_dict.keys():

            player_location = self.host.room.entity_locations["player"]

            surrounding_positions = [(player_location[0] - 1, player_location[1]),
                                     (player_location[0], player_location[1] - 1),
                                     (player_location[0] + 1, player_location[1]),
                                     (player_location[0], player_location[1] + 1)]

            for identifier in self.host.room.entity_locations.keys():

                if self.host.room.entity_locations[identifier] in surrounding_positions:

                    self.host.room.entity_dict[identifier].asset.draggable = True

                else:
                    self.host.room.entity_dict[identifier].asset.draggable = False

        else:
            self.logger.warning("'{}' not found in room, items are not made draggable".format("player"))

        return

class PygameEditor(PygameUserInterface):
    """A Pygame-based user interface that serves as a map editor.

       This Plugin is meant to be used by shard.serverside.Editor.

       Additional PygameEditor attributes:

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

    def __init__(self, assets, framerate, host):
        """Call PygameUserInterface.__init__(), but set up different Planes.
        """

        # Call base class __init__()
        #
        PygameUserInterface.__init__(self, assets, framerate, host)

        self.logger.debug("called")

        # Spacing is a little larger here to show grid lines.
        #
        self.spacing = 101

        # Setup a cache for planes
        #
        self.plane_cache = []

        # Re-open the click'n'drag window.
        #
        self.window = clickndrag.Display((1000, 600))
        self.window.image.fill((16, 16, 16))

        # Set window name
        #
        pygame.display.set_caption("Shard Editor")

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

        # Add the inventory plane created in PygameUserInterface.__init__()
        #
        self.inventory_plane.rect.left = 100

        self.window.sub(self.inventory_plane)

        # Add the room plane created in PygameUserInterface.__init__()
        #
        self.room_plane.rect.left = 100

        self.window.sub(self.room_plane)

        # Create Container for the editor buttons.
        #
        container = clickndrag.gui.Container("buttons",
                                             padding = 5,
                                             color = (120, 120, 120))
        container.rect.topleft = (0, 0)
        self.window.sub(container)

        # Add buttons
        #
        self.window.buttons.sub(clickndrag.gui.Button("Open Image",
                                                      pygame.Rect((0, 0),
                                                                  (88, 30)),
                                                      self.open_image))

        self.window.buttons.sub(clickndrag.gui.Button("Load Room",
                                                      pygame.Rect((0, 0),
                                                                  (88, 30)),
                                                      self.load_room))

        self.window.buttons.sub(clickndrag.gui.Button("Save Room",
                                                      pygame.Rect((0, 0),
                                                                  (88, 30)),
                                                      self.save_room))

        self.window.buttons.sub(clickndrag.gui.Button("Add Item",
                                                      pygame.Rect((0, 0),
                                                                  (88, 30)),
                                                      self.add_item))

        self.window.buttons.sub(clickndrag.gui.Button("Edit Walls",
                                                      pygame.Rect((0, 0),
                                                                  (88, 30)),
                                                      self.edit_walls))

        self.window.buttons.sub(clickndrag.gui.Button("Save Logic",
                                                      pygame.Rect((0, 0),
                                                                  (88, 30)),
                                                      lambda plane : self.logger.debug("no callback for '{}'".format(plane.name))))

        self.window.buttons.sub(clickndrag.gui.Button("Quit",
                                                      pygame.Rect((0, 0),
                                                                  (88, 30)),
                                                      self.quit))

        # Create Container for the properties
        #
        container = clickndrag.gui.Container("properties",
                                             color = (120, 120, 120))
        container.rect.topleft = (900, 0)
        self.window.sub(container)

        self.logger.debug("complete")

        return

    def open_image(self, plane):
        """Button callback to prompt the user for a room background image, load it and assign it to tiles.
        """

        self.logger.debug("called")

        new_image, filename = load_image("Open Background Image")

        if new_image is not None:

            for x in range(8):
                for y in range(5):
                    rect = pygame.Rect((x * 100, y * 100), (100, 100))

                    # TODO: catch exception for smaller images
                    #
                    self.window.room.subplanes[str((x, y))].image = new_image.subsurface(rect)

            # Warn user
            #
            warning_box = clickndrag.gui.OkBox("Please save the room before editing walls.")
            warning_box.rect.center = pygame.Rect((0, 0), self.window.room.rect.size).center
            self.window.room.sub(warning_box)

        else:
            self.logger.error("could not load image '{}'".format(filename))

        return

    def save_room(self, plane):
        """Button callback to save the tile images, resend and then save the Room to a local file.
        """

        # Observe that this method adds Events to self.host.message_for_host,
        # which is shard.plugins.serverside.Editor.message_for_host.

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

        if not filename:

            self.logger.debug("no filename selected")

        else:
            self.logger.debug("save to: {}".format(filename))

            self.host.message_for_host.event_list.append(shard.EnterRoomEvent(filename))

            roomfile = open(filename + ".floorplan", "wt")

            # TODO: only save PNGs if they have actually changed
            #
            for x in range(8):
                for y in range(5):

                    # Save image file
                    #
                    current_file = filename + "-{0}_{1}.png".format(x, y)
                    self.logger.debug(current_file)
                    pygame.image.save(self.window.room.subplanes[str((x, y))].image,
                                      os.path.join(path, current_file))

                    # Send renamed Tile to Server
                    #
                    tile = shard.Tile(self.host.room.floor_plan[(x, y)].tile.tile_type,
                                      current_file)

                    event = shard.ChangeMapElementEvent(tile, (x, y))

                    self.host.message_for_host.event_list.append(event)

                    # Save tile in floorplan file

                    entities_string = ""

                    for entity in self.host.room.floor_plan[(x, y)].entities:

                        # TODO: make sure commas are not present in the other strings
                        #
                        entities_string = entities_string + "\t{},{},{}".format(entity.entity_type,
                                                                                entity.identifier,
                                                                                entity.asset_desc)

                    roomfile.write("{}\t{}\t{}{}\n".format(repr((x, y)),
                                                           tile.tile_type,
                                                           tile.asset_desc,
                                                           entities_string))

            roomfile.close()

            self.logger.debug("wrote {}".format(filename + ".floorplan"))

            # Then respawn all current Entities in the Server since
            # EnterRoomEvent will set up a new room
            #
            for identifier in self.host.room.entity_dict.keys():

                # Create a new Entity which can be pickled by Event loggers
                # TODO: still necessary?
                #
                entity = shard.Entity(self.host.room.entity_dict[identifier].entity_type,
                                      identifier,
                                      self.host.room.entity_dict[identifier].asset_desc)

                event = shard.SpawnEvent(entity,
                                         self.host.room.entity_locations[identifier])

                self.host.message_for_host.event_list.append(event)

            self.host.message_for_host.event_list.append(shard.RoomCompleteEvent())

        return

    def load_room(self, plane):
        """Button callback to display a list of rooms to select from.
        """

        self.logger.debug("called")

        room_list = []

        for filename in os.listdir(os.getcwd()):

            if filename.endswith(".floorplan"):

                room_list.append(filename.split(".floorplan")[0])

        option_list = clickndrag.gui.OptionList("select_room",
                                                room_list,
                                                self.host.send_room_events)

        self.window.room.sub(option_list)

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

            image, filename = load_image("Image Of New Item")

            if image is not None:

                entity = shard.Entity(shard.ITEM_BLOCK,
                                      item_identifier,
                                      filename)

                self.logger.debug("appending SpawnEvent and PicksUpEvent")

                # TODO: make sure to use a safe spawning location
                # Observe: adding to self.host.message_for_host
                #
                self.host.message_for_host.event_list.append(shard.SpawnEvent(entity, (0, 0)))

                self.host.message_for_host.event_list.append(shard.PicksUpEvent(self.host.player_id,
                                                                                item_identifier))

        return

    def quit(self, plane):
        """Button callback to set self.exit_requested = True
        """
        self.logger.debug("setting exit_requested = True")
        self.host.host.exit_requested = True

    def edit_walls(self, plane):
        """Button callback to switch to wall edit mode.
        """
        self.logger.debug("called")

        # Cache button planes from sidebar...
        # Use subplanes_list to keep order
        #
        for name in self.window.buttons.subplanes_list:
            self.plane_cache.append(self.window.buttons.subplanes[name])

        # ...and remove
        #
        self.window.buttons.remove_all()

        self.window.buttons.sub(clickndrag.gui.Label("title",
                                                     "Edit Walls",
                                                      pygame.Rect((0, 0),
                                                                  (88, 30)),
                                                      color = (120, 120, 120)))

        self.window.buttons.sub(clickndrag.gui.Button("Done",
                                                      pygame.Rect((5, 35),
                                                                  (88, 30)),
                                                      self.wall_edit_done))

        # Clear Entity planes from room, but cache them.
        # By convention the name of the Entity Plane is Entity.identifier.
        #
        for identifier in self.host.room.entity_dict.keys():
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
        for coordinates in self.host.room.floor_plan.keys():

            if self.host.room.floor_plan[coordinates].tile.tile_type == shard.OBSTACLE:

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

        self.logger.debug("returning ChangeMapElementEvent to Server and creating overlay for tile at {}".format(plane.name))

        # The name of the clicked Plane is supposed to be a string representation
        # of a coordinate tuple.
        #
        coordinates = eval(plane.name)
        asset_desc = self.host.room.floor_plan[coordinates].tile.asset_desc

        event = shard.ChangeMapElementEvent(shard.Tile(shard.OBSTACLE, asset_desc),
                                            coordinates)

        self.host.message_for_host.event_list.append(event)

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

        self.logger.debug("returning ChangeMapElementEvent to Server and deleting '{}'".format(plane.name))

        # The clicked Plane is the overlay. Its name is supposed to be a string
        # representation of a coordinate tuple plus "_overlay".
        #
        coordinates = eval(plane.name.split("_overlay")[0])
        asset_desc = self.host.room.floor_plan[coordinates].tile.asset_desc

        event = shard.ChangeMapElementEvent(shard.Tile(shard.FLOOR, asset_desc),
                                            coordinates)

        self.host.message_for_host.event_list.append(event)

        # Delete the overlay indicating the OBSTACLE type.
        #
        plane.destroy()

    def wall_edit_done(self, plane):
        """Button callback which restores the editor to the state before edit_walls().
        """
        self.logger.debug("called")

        # Remove all wall marker overlays.
        # Restore Tile clicked callbacks along the way.
        # Entity Planes are not yet restored, so there should be only tiles left.
        #
        for plane in list(self.window.room.subplanes.values()):

            if plane.name.endswith("_overlay"):

                plane.destroy()

            else:
                plane.clicked_callback = self.tile_clicked_callback

        # Restore Entity Planes in room
        #
        while not isinstance(self.plane_cache[-1], clickndrag.gui.Button):
            self.window.room.sub(self.plane_cache.pop())

        # Make Entity Planes in inventory sensitive to drags
        #
        for plane in self.window.inventory.subplanes.values():
            plane.draggable = True

        self.window.buttons.remove_all()

        # Restore buttons, flushing plane cache
        #
        while len(self.plane_cache):
            self.window.buttons.sub(self.plane_cache.pop(0))

    def process_CanSpeakEvent(self, event):
        """Open the senteces as an OptionList and return a SaysEvent to the host.
        """

        self.logger.debug("called")

        self.window.room.sub(clickndrag.gui.OptionList("select_room",
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

            self.window.properties.remove_all()

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
                                                            pygame.Rect((0, 0), (98, 30)),
                                                            color = (120, 120, 120)))

            # Entity.asset
            #
            rect = pygame.Rect((0, 0), (98, entity.asset.image.get_rect().height))

            asset_plane = clickndrag.Plane("asset", rect)

            asset_plane.image = entity.asset.image

            self.window.properties.sub(asset_plane)

            # Entity.asset_desc
            #
            self.window.properties.sub(clickndrag.gui.Label("asset_desc",
                                                            entity.asset_desc,
                                                            pygame.Rect((0, 0), (98, 30)),
                                                            color = (120, 120, 120)))

            # Entity.entity_type
            #
            self.window.properties.sub(clickndrag.gui.Label("entity_type",
                                                            entity.entity_type,
                                                            pygame.Rect((0, 0), (98, 30)),
                                                            color = (120, 120, 120)))

            # Entity.state
            #
            self.window.properties.sub(clickndrag.gui.Label("state",
                                                            entity.state,
                                                            pygame.Rect((0, 0), (98, 30)),
                                                            color = (120, 120, 120)))
            return

    def make_items_draggable(self):
        """Overriding base class: make all items always draggable.
        """

        for identifier in self.host.room.entity_locations.keys():

            if identifier != self.host.player_id:

                self.host.room.entity_dict[identifier].asset.draggable = True

        return

    def select_event(self, event):
        """Make the user specify an response Event to an action.
        """

        self.logger.debug("called")

        event_list = ("Can Speak",
                      "Moves To",
                      "Perception",
                      "Says",
                      "Change Map Element",
                      "Delete",
                      "Spawn",
                      "Attempt Failed")

        # TODO: ChangeStateEvent, ManipulatesEvent, EnterRoomEvent, RoomCompleteEvent, PicksUpEvent, DropsEvent
        # TODO: specify multiple Events as response

        option_list = clickndrag.gui.OptionList("select_response",
                                                event_list,
                                                lambda option: self.edit_event(event, option))

        self.window.room.sub(option_list)

        return

    def edit_event(self, event, option):
        """Let the user edit the attributes of the selected Event.
        """

        self.logger.debug("called")

        if option.text == "Perception":

            container = clickndrag.gui.Container("edit_event",
                                                 padding = 5)

            container.sub(clickndrag.gui.Label("title",
                                               "Edit {}".format(option.text),
                                               pygame.Rect((0, 0), (200, 30))))

            textbox = clickndrag.gui.TextBox("textbox",
                                             pygame.Rect((0, 0), (200, 30)))

            self.window.key_sensitive(textbox)

            container.sub(textbox)

            container.sub(clickndrag.gui.Button("OK",
                                                pygame.Rect((0, 0), (90, 30)),
                                                lambda plane: self.event_edit_done(event, shard.PerceptionEvent(event.identifier, textbox.text))))

            self.window.room.sub(container)

        elif option.text == "Attempt Failed":

            # Do nothing. AttemptFailedEvent is the default response.
            #
            pass

        else:
            self.logger.critical("handling of '{}' not implemented".format(option.text))

        return

    def event_edit_done(self, trigger_event, response_event):
        """Button callback to call host.add_response() and destroy the Container.
        """

        self.logger.debug("called")

        self.host.add_response(trigger_event, response_event)

        self.window.room.edit_event.destroy()

        return