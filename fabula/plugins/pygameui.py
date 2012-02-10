"""2D Fabula User Interface using PyGame

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

# work started on 15. Oct 2010
#
# Partly based on the Shard PresentationEngine for the "Runaway" game done in
# October-December 2009, which in turn borrowed a lot from the PyGame-based
# CharanisMLClient developed in May 2008.

# TODO: always diplay and log full paths of saved or loaded files
# TODO: in PygameEditor, display all assets from local folder for visual editing
# TODO: ESC key should not end the game, but open a generic menu for setup and quitting the game

import fabula.plugins.ui
import pygame
import clickndrag.gui
import tkinter.filedialog
import tkinter.simpledialog

# For cx_Freeze
#
import tkinter._fix
#
# Not present in Pygame 1.9.1
#
#import pygame._view

import os

# Pixels per character, for width estimation of text renderings
#
PIX_PER_CHAR = 8

# Hardwired screen size.
#
SCREENSIZE = (800, 600)

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
    """Subclass of Plane with an extended update() method that handles movement.

       Additional attributes:

       EntityPlane.position_list
           A list of movement steps as position tuples

       EntityPlane.spritesheet
           If not None, a Pygame Surface that contains a sprite sheet. The sheet
           is assumed to consist of 4 rows. The first column contains the
           static view of the Entity in front, left, back and right view (from
           the first row down). Rows are supposed to contain movement animation
           frames: the first row a downward movement in front view, the second
           row a movement to the left in left view etc. Frames are assumed to be
           of equal width and height.

       EntityPlane.subsurface_rect_list
           A list of Pygame Rects to create subsurfaces of the sprite sheet.
    """

    def __init__(self, name, rect, draggable = False,
                                   grab = False,
                                   left_click_callback = None,
                                   right_click_callback = None,
                                   dropped_upon_callback = None,
                                   spritesheet = None):
        """Initialise.
        """

        # Call base class
        #
        clickndrag.Plane.__init__(self,
                                  name,
                                  rect,
                                  draggable = draggable,
                                  grab = grab,
                                  highlight = True,
                                  left_click_callback = left_click_callback,
                                  right_click_callback = right_click_callback,
                                  dropped_upon_callback = dropped_upon_callback)

        self.position_list = []
        self.spritesheet = spritesheet
        self.subsurface_rect_list = []

        return

    def update(self):
        """If EntityPlane.target has not yet been reached, move to the positions given in EntityPlane.position_list.
        """

        # Call base class to update() all subplanes
        #
        clickndrag.Plane.update(self)

        # Change position
        #
        if self.position_list:
            new_position = self.position_list.pop(0)
            self.rect.centerx = new_position[0]
            self.rect.bottom = new_position[1]

        # Change image
        #
        if self.subsurface_rect_list and self.spritesheet is not None:

            self.image = self.spritesheet.subsurface(self.subsurface_rect_list.pop(0))

        return

class PygameEntity(fabula.Entity):
    """Pygame-aware subclass of Entity to be used in PygameUserInterface.

       PygameEntities support the key "caption" in PygameEntity.property_dict.
       The value of PygameEntity.property_dict["caption"] will be displayed above the
       PygameEntity.

       PygameEntity.asset is supposed to be an instance of EntityPlane.

       Additional attributes:

       PygameEntity.spacing
           The spacing between tiles.

       PygameEntity.action_frames
           The number of frames per action.

       PygameEntity.caption_plane
           A clickndrag.gui.Label with the caption for this PygameEntity.
           Initially None.
    """

    def __init__(identifier, entity_type, blocking, mobile, asset_desc, spacing, action_frames):
        """Initialise.
           spacing is the spacing between tiles.
           action_frames is the number of frames per action.
        """

        # Call base class
        #
        fabula.Entity.__init__(self, identifier, entity_type, blocking, mobile, asset_desc)

        self.spacing = spacing
        self.action_frames = action_frames

        self.caption_plane = None

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

        # Animation
        #
        if self.asset.spritesheet is not None:

            # Compute direction from dx_per_frame and dy_per_frame.
            # See EntityPlane docstring for sprite sheet specifications.
            #
            # Default: down
            #
            row = 0

            if dx_per_frame < 0:

                # Left
                #
                row = 1

            elif dy_per_frame < 0:

                # Up
                #
                row = 2

            elif dx_per_frame > 0:

                # Right
                #
                row = 3

            subsurface_rect_list = []

            # TODO: most of these need only be calculated once. This should be done once the asset is fetched. Given the asset doesn't change. Nah.

            width = self.asset.spritesheet.get_width()

            offset = self.asset.rect.width

            repeat_frames = int(self.action_frames / int(width / offset))

            if repeat_frames < 1:

                repeat_frames = 1

            # That is, if there is only one column, then use no offset
            #
            if offset == width:

                offset = 0

                # Use default image all the time
                #
                repeat_frames = self.action_frames

            fabula.LOGGER.debug("repeat_frames for {} == {}".format(self.identifier,
                                                                    repeat_frames))

            repeat_count = 0

            sprite_dimensions = self.asset.rect.size

            # Omit last step
            # TODO: copied from above, can this be moved into one single iteration?
            #
            for i in range(self.action_frames - 1):

                subsurface_rect_list.append(pygame.Rect((offset, row * sprite_dimensions[1]),
                                                        sprite_dimensions))

                repeat_count = repeat_count + 1

                if repeat_count == repeat_frames:

                    offset = offset + sprite_dimensions[0]

                    if offset > width - sprite_dimensions[0]:

                        offset = self.asset.rect.width

                    repeat_count = 0

            # Append neutral image as final
            #
            subsurface_rect_list.append(pygame.Rect((0, row * sprite_dimensions[1]),
                                                    sprite_dimensions))

            self.asset.subsurface_rect_list.extend(subsurface_rect_list)

        return

    def process_ChangePropertyEvent(self, event):
        """Call base class and update caption changes.
        """

        # Call base class
        #
        fabula.Entity.process_ChangePropertyEvent(self, event)

        if self.asset is not None and event.property_key == "caption":

            # Do we already have a caption?
            #
            if self.caption_plane is not None:

                # Then only change the text.
                # Should be made visible with the next call to update().
                #
                fabula.LOGGER.debug("changing caption_plane.text to '{}'".format(event.property_value))
                self.caption_plane.text = event.property_value

            else:
                # Create a new caption Label
                # TODO: arbitrary width formula
                #
                self.caption_plane = clickndrag.gui.OutlinedText(self.identifier + "_caption",
                                                                 event.property_value)

            self.display_caption()

        return

    def display_caption(self):
        """Position the caption Plane and make it a subplane of the room.
        """

        if self.caption_plane is not None:

            fabula.LOGGER.debug("aligning caption to midtop of Entity plane: {}".format(self.asset.rect.midtop))

            self.caption_plane.rect.center = self.asset.rect.midtop

            # Sync movements to asset Plane
            #
            self.caption_plane.sync(self.asset)

            # If we make the Label a subplane of the Entity.asset Plane,
            # it will be cropped at the width of Entity.asset. This is not
            # intended. So we make it a subplane of window.room, which is
            # the parent of the asset.
            #
            self.asset.parent.sub(self.caption_plane,
                                  insert_after = self.asset.name)

        return

class PygameUserInterface(fabula.plugins.ui.UserInterface):
    """This is a Pygame implementation of an UserInterface for the Fabula Client.

       Additional attributes:

       PygameUserInterface.clock
           An instance of pygame.time.Clock

       PygameUserInterface.big_font
       PygameUserInterface.small_font
           Pygame.font.Font instances

       PygameUserInterface.fade_surface
           A black pygame surface for fade effects.

       PygameUserInterface.loading_surface
           A loading text surface to be used in process_EnterRoomEvent.

       PygameUserInterface.inventory_plane
           Plane to display the inventory

       PygameUserInterface.spacing
           Spacing between tiles.

       PygameUserInterface.scroll
           Counter for scrolling left-right. Used in display_single_frame().

       PygameUserInterface.scroll_amount
           Number of pixels to scroll per call to display_single_frame().

       PygameUserInterface.window
           An instance of clickndrag.Display. Dimensions are given by
           SCREENSIZE. By default opened in windowed mode, this can be changed
           by editing the file fabula.conf.

       PygameUserInterface.window.inventory
           clickndrag Plane for the inventory. By default this is 800x100px
           with space for 8 100x100px icons and located at the bottom of the
           window.

       PygameUserInterface.window.room
           clickndrag Plane for the room. Initially it will have a size of
           0x0 px. The final Plane is created by process_RoomCompleteEvent.

       PygameUserInterface.window.room.tiles
           clickndrag Plane which has the Tile Planes as subplanes.

       PygameUserInterface.fade_surface
           A black pygame surface for fade effects

       PygameUserInterface.attempt_icon_planes
           A list of Planes of attempt action icons.

       PygameUserInterface.right_clicked_entity
           Cache for the last right-clicked Entity.

       PygameUserInterface.osd
           An instance of PygameOSD.

       PygameUserInterface.stats
           A dict mapping names of different metrics to their current vaule.
           Updated in PygameUserInterface.update_frame_timer().
    """

    def __init__(self, assets, framerate, host, fullscreen = False):
        """This method initialises the PygameUserInterface.
           assets must be an instance of fabula.Assets or a subclass.
           framerate must be an integer and sets the maximum (not minimum ;-))
           frames per second the client will run at.
           fullscreen is a Boolean flag.
        """

        # Call original __init__()
        #
        fabula.plugins.ui.UserInterface.__init__(self,
                                                 assets,
                                                 framerate,
                                                 host,
                                                 fullscreen)

        fabula.LOGGER.debug("called")

        fabula.LOGGER.debug("initialising pygame")

        pygame.init()

        # Initialise on screen display.
        #
        self.osd = PygameOSD()

        # Statistics
        #
        self.stats = {"framerate" : self.framerate,
                      "fps" : None}

        # Initialise the frame timing clock.
        #
        self.clock = pygame.time.Clock()

        # Spacing between tiles.
        #
        self.spacing = 100

        # Counter for scrolling left-right
        #
        self.scroll = 0

        # Scroll amount, tied to framerate.
        # Scroll 2 px @ 60 fps
        #
        self.scroll_amount = int(120 / self.framerate)

        fabula.LOGGER.debug("setting scroll_amount to {}".format(self.scroll_amount))

        # Center window. Hint from the pygame-users mailing list.
        #
        os.environ["SDL_VIDEO_CENTERED"] = "1"

        # Open a click'n'drag window.
        #
        self.window = clickndrag.Display(SCREENSIZE, fullscreen)

        # Create a black pygame surface for fade effects.
        #
        self.fade_surface = self.window.image.copy()

        # Create loading text surface to be used in process_EnterRoomEvent
        #
        self.loading_surface = clickndrag.gui.BIG_FONT.render("Loading, please wait...",
                                                              True,
                                                              (255, 255, 255))

        # Create inventory plane.
        #
        self.inventory_plane = clickndrag.Plane("inventory",
                                                pygame.Rect((0, 500), (800, 100)),
                                                dropped_upon_callback = self.inventory_callback)

        self.inventory_plane.image.fill((32, 32, 32))

        # Copied from get_connection_details().
        # TODO: Again a reason for an image loading routine.
        #
        try:
            file = self.assets.fetch("inventory.png")

            surface = pygame.image.load(file)

            file.close()

            # Convert to internal format suitable for blitting.
            # Not using convert_alpha(), no RGBA support fo inventory.
            #
            surface = surface.convert()

            fabula.LOGGER.debug("using inventory.png")

            self.inventory_plane.image = surface

        except:
            fabula.LOGGER.warning("inventory.png not found, no inventory background")

        # Load the standard attempt icons
        #
        self.attempt_icon_planes = []

        for name in ("attempt_manipulate",
                     "attempt_talk_to",
                     "attempt_look_at",
                     "cancel"):

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

            # Create Plane
            #
            plane = clickndrag.Plane(name,
                                     rect,
                                     left_click_callback = self.attempt_icon_callback)

            plane.image = surface

            self.attempt_icon_planes.append(plane)

            fabula.LOGGER.debug("loaded '{}': {}".format(name, plane))

        # Cache for the last right-clicked Entity
        #
        self.right_clicked_entity = None

        # Create plane for the room.
        # This Plane is only there to collect subplanes and hence is initialised
        # with 0x0 pixels. The final Plane will be created by process_RoomCompleteEvent().
        #
        self.window.sub(clickndrag.Plane("room",
                                         pygame.Rect((0, 0), (0, 0))))

        # Create a subplane as a sort-of buffer for Tiles.
        #
        self.window.room.sub(clickndrag.Plane("tiles",
                                              pygame.Rect((0, 0), (0, 0))))

        fabula.LOGGER.debug("complete")

        return

    def get_connection_details(self, prompt_connector = True):
        """Display a splash screen, then get a connector to the Server and an identifier from the player.

           Initially, the Client Interface is not connected to the Server. This
           method should prompt the user for connection details.

           It must return a tuple (identifier, connector).

           connector will be used for Interface.connect(connector).
           identifier will be used to send InitEvent(identifier) to the server.

           If prompt_connector is False, the dialog will not ask for a connector
           and use None instead.
        """

        fabula.LOGGER.debug("called")

        # Display the splash screen
        #
        # TODO: copied from above. Maybe an image loading routine would be good.

        try:
            file = self.assets.fetch("splash.png")

            surface = pygame.image.load(file)

            file.close()

            # Convert to internal format suitable for blitting.
            # Not using convert_alpha(), no RGBA support fo splash.
            #
            surface = surface.convert()

            fabula.LOGGER.debug("displaying splash.png")

            self.window.image = surface

        except:
            fabula.LOGGER.warning("splash.png not found, not displaying splash screen")

        self.display_single_frame()

        # Use a container so we can access it from an ad-hoc function.
        # That's Python.
        #
        container_dict = {"login_name" : None,
                          "connector" : None}

        def dialog_callback(buttonplane):

            container_dict["login_name"] = buttonplane.parent.identifier.text

            if "connector" in buttonplane.parent.subplanes_list:

                # Construct tuple
                #
                container_dict["connector"] = buttonplane.parent.connector.text

                buttonplane.parent.destroy()

                return

        container = clickndrag.gui.Container("get_connection_details",
                                             padding = 5)

        # Login name prompt
        #
        container.sub(clickndrag.gui.Label("id_caption",
                                           "Login name:",
                                           pygame.Rect((0, 0),
                                                       (200, 30))))

        container.sub(clickndrag.gui.TextBox("identifier",
                                             pygame.Rect((0, 0),
                                                         (200, 30)),
                                             return_callback = None))

        # Upon clicked, register the TextBox for keyboard input
        #
        container.identifier.left_click_callback = lambda plane : self.window.key_sensitive(plane)

        # Register this one as key sensitive now
        #
        self.window.key_sensitive(container.identifier)

        # Optional connector prompt
        #
        if prompt_connector:

            container.sub(clickndrag.gui.Label("connector_caption",
                                               "Server IP",
                                               pygame.Rect((0, 0),
                                                           (200, 30))))

            container.sub(clickndrag.gui.TextBox("connector",
                                                 pygame.Rect((0, 0),
                                                             (200, 30)),
                                                 return_callback = None))

            # Provide a default
            #
            container.connector.text = "127.0.0.1"

            # Upon clicked, register the TextBox for keyboard input
            #
            container.connector.left_click_callback = lambda plane : self.window.key_sensitive(plane)

        # OK button
        #
        container.sub(clickndrag.gui.Button("OK",
                                            pygame.Rect((0, 0),
                                                        (200, 30)),
                                            dialog_callback))

        container.rect.center = self.window.rect.center

        self.window.sub(container)

        while container_dict["login_name"] is None:

            self.display_single_frame()

            self.collect_player_input()

            if self.exit_requested:

                # Return anything to get out of the loop
                #
                container_dict["login_name"] = "exit requested"

        # We are done with the splash screen if there was one. Now make sure
        # that there is no image for the window Plane left that would invisibly
        # be blitted below room and inventory planes.
        #
        self.window.image = self.window.display

        # Return connector (ip, port) using the default Fabula
        # port 0xfab == 4011.
        #
        return (container_dict["login_name"],
                (container_dict["connector"], 4011))

    def update_frame_timer(self):
        """Use pygame.time.Clock.tick() to slow down to given framerate.
           Also, update PygameUserInterface.stats.
        """

        self.clock.tick(self.framerate)

        self.stats["fps"] = int(self.clock.get_fps())

        return

    def display_single_frame(self):
        """Update and render all click'd'drag planes.
           This method also handles scrolling.
        """

        if not self.freeze:

            # Handle scrolling
            #
            if self.scroll > 0:

                self.scroll = self.scroll - self.scroll_amount

                if self.scroll < 0:

                    self.scroll = 0

                else:

                    self.window.room.rect.move_ip(self.scroll_amount, 0)

                    self._snap_room_to_display()

            elif self.scroll < 0:

                self.scroll = self.scroll + self.scroll_amount

                if self.scroll > 0:

                    self.scroll = 0

                else:

                    self.window.room.rect.move_ip( - self.scroll_amount, 0)

                    self._snap_room_to_display()

            self.window.update()
            self.window.render()

            self.osd.render(self.window.display)

            # TODO: replace with update(dirty_rect_list)
            #
            pygame.display.flip()

        self.update_frame_timer()

        # Pump the Pygame Event Queue
        #
        pygame.event.pump()

        return

    def collect_player_input(self):
        """Initiate scrolling, gather Pygame events, scan for QUIT and let the clickndrag Display evaluate the events.
        """

        # TODO: The UserInterface should only ever collect and send one single client event to prevent cheating and blocking other clients in the server. (hint by Alexander Marbach)

        # Check mouse position, and trigger window scrolling.
        # Also check whether the display window has the focus.
        # Scrolling will be done in display_single_frame().
        #
        if not self.scroll:

            mouse_position = pygame.mouse.get_pos()

            if (pygame.mouse.get_focused()
                and 0 <= mouse_position[0] <= 25
                and self.window.room.rect.left < 0):

                # Scroll to the left
                #
                self.scroll = self.spacing

            elif (pygame.mouse.get_focused()
                  and SCREENSIZE[0] - 25 <= mouse_position[0] <= SCREENSIZE[0]
                  and self.window.room.rect.right > SCREENSIZE[0]):

                # Scroll to right
                #
                self.scroll = 0 - self.spacing

        # Handle events
        #
        events = pygame.event.get()

        for event in events:

            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):

                fabula.LOGGER.info("exit request from user")
                self.exit_requested = True

                # Quit pygame here, though there is still shutdown work to be
                # done Client and ClientInterface.
                #
                pygame.quit()

            elif (event.type == pygame.KEYDOWN
                  and event.key == pygame.K_F1):

                if self.osd.is_displaying("FPS: "):

                    self.osd.remove("Framerate: ")
                    self.osd.remove("FPS: ")

                else:
                    self.osd.display("Framerate: ", self.stats, "framerate")
                    self.osd.display("FPS: ", self.stats, "fps")

        self.window.process(events)

        # TODO: Adding Events to self.message_for_host is weird. This should be returned instead in some way, shouldn't it?

        return

    ####################
    # Event handlers affecting presentation and management

    def process_EnterRoomEvent(self, event):
        """Fade window to black and remove subplanes of PygameUserInterface.window.room.
        """

        fabula.LOGGER.info("entering room: {}".format(event.room_identifier))

        fabula.LOGGER.debug("fading out")

        frames = self.action_frames

        fadestep = int(255 / frames)

        self.fade_surface.set_alpha(0)

        # This is actually an exponential fade since the original surface is
        # not restored before blitting the fading surface
        #
        while frames:
            # Bypassing display_single_frame()

            self.window.display.blit(self.fade_surface, (0, 0))

            # Blit loading message on top
            #
            self.window.display.blit(self.loading_surface,
                                     (int(self.window.display.get_width() / 2 - self.loading_surface.get_width() / 2),
                                      int(self.window.display.get_height() / 2 - self.loading_surface.get_height() / 2)))

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

        # Blit loading message on top
        #
        self.window.display.blit(self.loading_surface,
                                 (int(self.window.display.get_width() / 2 - self.loading_surface.get_width() / 2),
                                  int(self.window.display.get_height() / 2 - self.loading_surface.get_height() / 2)))

        pygame.display.flip()

        # Clear room in any case, keeping the tiles plane
        #
        for plane_name in list(self.window.room.subplanes_list):

            if plane_name is not "tiles":

                self.window.room.remove(plane_name)

        # No more rendering until RoomComplete
        #
        fabula.LOGGER.info("freezing")

        self.freeze = True

        return

    def process_RoomCompleteEvent(self, event):
        """Recreate room and tile Planes at the correct size, update and render everything and fade in the room.
           Add the inventory Plane to window if it is not yet there.
        """

        # Find out the size of the room. Tiles start at (0, 0) in the upper
        # left, so search for the rightmost and lowermost tiles.
        #
        max_right = 0
        max_bottom = 0

        for tuple in self.host.room.floor_plan.keys():

            if tuple[0] > max_right:

                max_right = tuple[0]

            if tuple[1] > max_bottom:

                max_bottom = tuple[1]

        # Create new 'room' and 'tiles' Planes based on the max size
        #
        room_plane = clickndrag.Plane("room",
                                      pygame.Rect((0, 0),
                                                  ((max_right + 1) * self.spacing,
                                                   (max_bottom + 1) * self.spacing)))

        room_plane.sub(clickndrag.Plane("tiles",
                                        pygame.Rect((0, 0),
                                                    room_plane.rect.size)))

        # Transfer all Tile Planes to the new 'tiles' Plane
        #
        for plane in list(self.window.room.tiles.subplanes.values()):

            room_plane.tiles.sub(plane)

        self.window.room.tiles.destroy()

        # Transfer all remaining subplanes of room to the new room Plane
        #
        for plane in list(self.window.room.subplanes.values()):

            room_plane.sub(plane)

        self.window.room.destroy()

        # Add new room
        #
        fabula.LOGGER.debug("recreating room plane of size {}".format(room_plane.rect.size))

        self.window.sub(room_plane)

        # Tiles are rendered on the separate Plane window.room.tiles, but
        # Entites may have been spawned in the incorrect rendering order, so
        # rearrange them.
        #
        self.reorder_room_planes()

        self.make_items_draggable()

        # Make sure inventory is present and on top
        #
        self.window.sub(self.inventory_plane)

        # Make sure the player Entity is visible. Position the room view
        # accordingly.

        try:
            player_position = list(self.host.room.entity_locations[self.host.client_id])

            # Convert to pixels, refering to the center of the tile
            #
            player_position[0] = int((player_position[0] + 0.5) * self.spacing)
            player_position[1] = int((player_position[1] + 0.5) * self.spacing)

            self.window.room.rect.left = 0 - player_position[0] + (SCREENSIZE[0] / 2)
            self.window.room.rect.top =  0 - player_position[1] + (SCREENSIZE[1] / 2)

            self._snap_room_to_display()

        except KeyError:

            msg = "cannot center window on player Entity, Entity '{}' not found in room: {}"

            fabula.LOGGER.warning(msg.format(self.host.client_id,
                                             self.host.room.entity_locations))

        # Display the game again and accept input
        #
        fabula.LOGGER.info("unfreezing")

        self.freeze = False

        # process_ChangeMapElementEvent and process_SpawnEvent should have
        # set up everything by now, so we can simply fade in and roll.
        #
        frames = self.action_frames

        fadestep = int(255 / frames)

        self.fade_surface.set_alpha(255)

        fabula.LOGGER.debug("fading in over {} frames, stepping {}".format(frames, fadestep))

        while frames:
            # Bypassing display_single_frame()

            self.window.update()
            self.window.render(force = True)

            self.window.display.blit(self.fade_surface, (0, 0))

            # Blit loading message on top
            #
            self.window.display.blit(self.loading_surface,
                                     (int(self.window.display.get_width() / 2 - self.loading_surface.get_width() / 2),
                                      int(self.window.display.get_height() / 2 - self.loading_surface.get_height() / 2)))

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

    def process_CanSpeakEvent(self, event):
        """Open the sentences as an OptionSelector and return a SaysEvent to the host.
        """

        # We blindly assume that this is for us.
        #
        fabula.LOGGER.debug("showing {}".format(event))

        option_list = clickndrag.gui.OptionSelector("select_sentence",
                                                    event.sentences,
                                                    lambda option: self.message_for_host.event_list.append(fabula.SaysEvent(self.host.client_id, option.text)),
                                                    width = 400,
                                                    lineheight = 25)

        option_list.rect.center = self.window.rect.center

        self.window.sub(option_list)

        return


    def process_SpawnEvent(self, event):
        """Add a subplane to window.room, possibly fetching an asset before.

           The name of the subplane is the Entity identifier, so the subplane
           is accessible using window.room.<identifier>.

           Entity.asset points to the Plane of the Entity.

           When a Plane has not yet been added, the Entity's class is changed
           to PygameEntity in addition.

           If the asset file name contains 'fabulasheet', this method will treat
           the image as a spritesheet. See the EntityPlane documentation for
           details.
        """

        if event.entity.user_interface is None:

            # Call base class
            #
            fabula.plugins.ui.UserInterface.process_SpawnEvent(self, event)

        # This is possibly a respawn from Rack, and the Entity already has
        # an asset.
        #
        if event.entity.asset is not None:

            msg = "Entity '{}' already has an asset, updating position to {}"
            fabula.LOGGER.info(msg.format(event.entity.identifier,
                                         event.location))

            x = event.location[0] * self.spacing + self.spacing / 2
            y = event.location[1] * self.spacing + self.spacing

            event.entity.asset.rect.centerx = x
            event.entity.asset.rect.bottom = y

            # Restore callback
            #
            event.entity.asset.dropped_upon_callback = self.entity_dropped_callback

        else:
            fabula.LOGGER.info("no asset for Entity '{}', attempting to fetch".format(event.entity.identifier))

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

            # Check for Fabula sprite sheet
            #
            spritesheet = None

            if "fabulasheet" in event.entity.asset_desc:

                msg = "sprite sheet detected for Entity '{}', asset '{}'"

                fabula.LOGGER.debug(msg.format(event.entity.identifier,
                                               event.entity.asset_desc))

                # Save orignal surface containing the sheet
                #
                spritesheet = surface

                # Spritesheet: Sheets are supposed to have 4 rows. See
                # EntityPlane docstrings.
                #
                # Computing dimensions
                #
                sprite_height = int(spritesheet.get_height() / 4)

                fabula.LOGGER.debug("assuming sprite height: {} px".format(sprite_height))

                # Spritesheet: sub-images are assumed to be squares. See
                # EntityPlane docstrings.
                #
                # Replace surface variable with a subsurface
                #
                surface = spritesheet.subsurface(pygame.Rect((0, 0),
                                                             (sprite_height,
                                                              sprite_height)))

                # Fix rect accordingly
                #
                rect.width = sprite_height
                rect.height = sprite_height

            # Place at the correct location
            #
            rect.centerx = event.location[0] * self.spacing + self.spacing / 2
            rect.bottom = event.location[1] * self.spacing + self.spacing

            # Create EntityPlane, name is the entity identifier
            #
            plane = EntityPlane(event.entity.identifier,
                                rect,
                                right_click_callback = self.entity_right_click_callback,
                                dropped_upon_callback = self.entity_dropped_callback,
                                spritesheet = spritesheet)

            plane.image = surface

            # Finally attach the Plane as the Entity's asset
            #
            event.entity.asset = plane

            # The Entity must be able to react to Events. These reactions are
            # Pygame specific and are thus not covered in the basic fabula.Entity
            # class. Thus, we exploit a Python feature here and change the
            # Entity's class at runtime to a class that supports Pygame.
            #
            if event.entity.__class__ is PygameEntity or PygameEntity in event.entity.__class__.__bases__:

                # PygameEntity already in use? Great!
                #
                pass

            elif event.entity.__class__ is fabula.Entity:

                # Oh well. Just swap.
                #
                fabula.LOGGER.debug("changing class of '{}' from {} to {}".format(event.entity.identifier,
                                                                                event.entity.__class__,
                                                                                PygameEntity))

                event.entity.__class__ = PygameEntity

            else:
                # To preserve the class, create a new class that inherits from
                # the current one and from PygameEntity.
                #
                class ExtendedEntity(event.entity.__class__, PygameEntity):

                    pass

                fabula.LOGGER.debug("changing class of '{}' from {} to bases {}".format(event.entity.identifier,
                                                                                event.entity.__class__,
                                                                                ExtendedEntity.__bases__))

                event.entity.__class__ = ExtendedEntity

            # Since we do not call PygameEntity.__init__() to prevent messing
            # up already present data, we add required attributes
            # TODO: it's easy to miss that when changing the PygameEntity.__init__()
            #
            event.entity.spacing = self.spacing
            event.entity.action_frames = self.action_frames
            event.entity.caption_plane = None

        # Now there is a Plane for the Entity. Add to room.
        # This implicitly removes the Plane from the former parent plane.
        #
        fabula.LOGGER.info("adding '{}' to window.room".format(event.entity.asset.name))
        self.window.room.sub(event.entity.asset)

        # If the PygameEntity has a caption Plane, add it as well.
        #
        event.entity.display_caption()

        return

    def process_DeleteEvent(self, event):
        """Remove the associated Plane from window.room.
        """

        # Partly taken from process_PicksUpEvent

        fabula.LOGGER.debug("deleting caption and item Plane for '{}' from window.room".format(event.identifier))

        # First remove the caption plane, if existing.
        #
        if event.identifier + "_caption" in self.window.room.subplanes_list:

            self.window.room.remove(event.identifier + "_caption")

        self.window.room.remove(event.identifier)

        return

    def process_ChangeMapElementEvent(self, event):
        """Fetch asset and register/replace tile.
           Tile.asset is the Pygame Surface since possibly multiple Planes must
           be derived from a single Tile.
        """

        fabula.LOGGER.debug("called")

        tile_from_list = None

        # The Client should have added the Tile to self.host.room.tile_list
        #
        for tile in self.host.room.tile_list:

            # This should succeed only once
            #
            if tile == event.tile:

                # Tiles may compare equal, but they may not refer to the same
                # instance, so we use tile from tile_list.
                #
                fabula.LOGGER.debug("found event.tile in self.host.room.tile_list")
                tile_from_list = tile

        if tile_from_list is None:

            fabula.LOGGER.error("could not find tile {} in tile_list of room '{}'".format(event.tile, self.host.room.identifier))
            raise Exception("could not find tile {} in tile_list of room '{}'".format(event.tile, self.host.room.identifier))

        if tile_from_list.asset is not None:

            fabula.LOGGER.debug("tile already has an asset: {}".format(tile_from_list))

        else:
            # Assets are entirely up to the UserInterface, so we fetch
            # the asset here
            #
            fabula.LOGGER.debug("no asset for {}, attempting to fetch".format(tile_from_list))

            try:
                # Get a file-like object from asset manager
                #
                file = self.assets.fetch(tile_from_list.asset_desc)

            except:
                self.display_asset_exception(tile_from_list.asset_desc)

            self.display_loading_progress(tile_from_list.asset_desc)

            fabula.LOGGER.debug("loading Surface from {}".format(file))

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
        if str(event.location) not in self.window.room.tiles.subplanes:

            tile_plane = clickndrag.Plane(str(event.location),
                                          pygame.Rect((event.location[0] * self.spacing,
                                                       event.location[1] * self.spacing),
                                                      (100, 100)),
                                          left_click_callback = self.tile_clicked_callback,
                                          dropped_upon_callback = self.tile_drop_callback)

            self.window.room.tiles.sub(tile_plane)

        # Update image regardless whether the tile existed or not
        #
        fabula.LOGGER.debug("changing image for tile at {0} to {1}".format(str(event.location),
                                                                        tile_from_list.asset))

        self.window.room.tiles.subplanes[str(event.location)].image = tile_from_list.asset

        return

    def process_PerceptionEvent(self, event):
        """Display the perception.
        """

        fabula.LOGGER.debug("called")

        # If it's not for us, ignore.
        # TODO: checking for client_id should be everywhere and be more structured
        #
        if event.identifier == self.host.client_id:

            # Using a OkBox for now.
            # Taken from PygameEditor.open_image().
            #
            perception_box = clickndrag.gui.OkBox(event.perception)
            perception_box.rect.center = self.window.rect.center
            self.window.sub(perception_box)

        else:
            fabula.LOGGER.warning("perception for '{}', not displaying".format(event.identifier))

        return

    def process_AttemptFailedEvent(self, event):
        """Flash the screen.
        """

        fabula.LOGGER.debug("called")

        # If it's not for us, ignore.
        # TODO: checking for client_id should be everywhere and be more structured
        #
        if event.identifier == self.host.client_id:

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
        """Call the base class method, re-order EntityPlanes and make EntityPlanes surrounding a new player position draggable.
        """

        fabula.LOGGER.debug("called")

        # Call base class
        #
        fabula.plugins.ui.UserInterface.process_MovesToEvent(self, event)

        # Care for overlapping
        #
        self.reorder_room_planes()

        # Care for draggability
        #
        if event.identifier == self.host.client_id:

            self.make_items_draggable()

        return

    def process_ChangePropertyEvent(self, event):
        """Call base class, update caption changes, then display a single frame to show the result.
        """

        fabula.LOGGER.debug("called")

        # Call base class
        #
        fabula.plugins.ui.UserInterface.process_ChangePropertyEvent(self, event)

        # In the case of a caption change, the asset may not have been fetched
        # when the Entity processed the property change in the Engine's loop.
        #
        entity = self.host.room.entity_dict[event.identifier]

        if entity.asset is not None \
           and event.property_key == "caption" \
           and not event.identifier + "_caption" in self.window.room.subplanes_list:

            fabula.LOGGER.debug("Entity '{}' has no caption yet, forwarding Event again".format(event.identifier))

            entity.process_ChangePropertyEvent(event)

        return

    def process_DropsEvent(self, event):
        """Call base class process_DropsEvent, clean up the inventory plane and adjust draggable flags.
        """

        fabula.LOGGER.debug("called")

        fabula.plugins.ui.UserInterface.process_DropsEvent(self, event)

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
        """Check the affected Entity, then either move the item's Plane from window.room to PygameUserInterface.inventory_plane or delete it.
           Then call the base class implementation to notify the Entity.
        """

        # The Client has already put the item from Client.room to Client.rack.
        # We have to update the display accordingly.

        # In any case, first remove the caption plane, if existing.
        #
        if event.item_identifier + "_caption" in self.window.room.subplanes_list:

            self.window.room.remove(event.item_identifier + "_caption")

        if event.identifier == self.host.client_id:

            fabula.LOGGER.debug("this affects the player entity, will move item Plane from window.room to window.inventory")

            # Cache the plane
            #
            plane = self.window.room.subplanes[event.item_identifier]

            # Append at the right of the inventory.
            #
            plane.rect.top = 0
            plane.rect.left = len(self.inventory_plane.subplanes) * 100

            # This will remove the plane from its current parent, window.room
            # Use self.inventory_plane because we do not know whether the
            # inventory is currently visible.
            #
            self.inventory_plane.sub(plane)

            # Make sure the plane is draggable
            #
            plane.draggable = True

            # Make insensitive to drops
            #
            plane.dropped_upon_callback = None

        else:
            fabula.LOGGER.debug("this does not affect the player entity, will delete item Plane from window.room")

            self.window.room.remove(event.item_identifier)

        # Call base class to notify the Entity
        #
        fabula.plugins.ui.UserInterface.process_PicksUpEvent(self, event)

    def process_SaysEvent(self, event):
        """Call the base class, then present the text to the user and wait some time.
        """

        fabula.LOGGER.debug("called")

        # Call base class
        #
        fabula.plugins.ui.UserInterface.process_SaysEvent(self, event)

        # TODO: replace with a nice speech balloon

        # Taken from process_PerceptionEvent()
        #
        says_box = clickndrag.gui.Label("{}_says".format(event.identifier),
                                        event.text,
                                        pygame.Rect((0, 0),
                                                    (len(event.text) * PIX_PER_CHAR, 30)),
                                        background_color = (250, 250, 240))

        clickndrag.gui.draw_border(says_box, (0, 0, 0))

        entity_rect = self.host.room.entity_dict[event.identifier].asset.rect

        # Display above Entity
        #
        says_box.rect.center = (entity_rect.centerx, entity_rect.top)

        # Make sure it's completely visible
        # TODO: but maybe the room is not completely visible
        #
        says_box.rect.clamp_ip(pygame.Rect((0, 0), self.window.room.rect.size))

        self.window.room.sub(says_box)

        # Display for (action_time / 8) per character, but at least for
        # 2 * action_time
        #
        frames = int(self.action_frames / 8 * len(event.text))

        if frames < 2 * self.action_frames:

            frames = 2 * self.action_frames

        for frame in range(frames):

            self.display_single_frame()

        says_box.destroy()

        return

    def reorder_room_planes(self):
        """Re-order subplanes of self.window.room from back to front by y-coordinate.
        """

        # *sigh* We dis- and reassemble the whole list.
        # Partly moved here from process_RoomCompleteEvent, which now calls
        # this method.
        #
        fabula.LOGGER.debug("rearranging subplanes of room")

        entities = []
        captions = []
        other = []

        for name in self.window.room.subplanes_list:

            if name in self.host.room.entity_dict.keys():

                entities.append(name)

            elif name.endswith("_caption"):

                captions.append(name)

            elif name == "tiles":

                # Drop the Tiles Plane for now
                #
                pass

            else:
                other.append(name)

        # Entity planes should be rendered from top to bottom, so sort by y
        # coordinate.
        #
        entities.sort(key = lambda name: self.host.room.entity_locations[name][1])

        # Finally, insert captions just after the according Entity Plane.
        #
        for name in captions:

            entities.insert(entities.index(name.split("_caption")[0]) + 1, name)

        # Observe the Tiles Plane
        #
        self.window.room.subplanes_list = ["tiles"] + entities + other

        return

    def inventory_callback(self, plane, dropped_plane, screen_coordinates):
        """Drop callback to issue a TriesToPickUpEvent if the item is not already in Rack.
        """

        item_identifier = dropped_plane.name

        fabula.LOGGER.debug("'{}' dropped on inventory".format(item_identifier))

        if item_identifier in self.host.rack.entity_dict.keys():

            fabula.LOGGER.info("'{}' already in Rack, skipping".format(item_identifier))

        else:

            fabula.LOGGER.info("issuing TriesToPickUpEvent")

            event = fabula.TriesToPickUpEvent(self.host.client_id,
                                             self.host.room.entity_locations[item_identifier])

            self.message_for_host.event_list.append(event)

        return

    def tile_clicked_callback(self, plane):
        """Clicked callback to issue a TriesToMoveEvent.
        """

        # TODO: This is so much like tile_drop_callback() that it should be unified.

        fabula.LOGGER.debug("called")

        # Just to be sure, check if the Plane's name matches a "(x, y)" string.
        #
        if not fabula.str_is_tuple(plane.name):
            fabula.LOGGER.error("plane.name does not match coordinate tuple: '{}'".format(plane.name))

        else:
            # The target identifier is a coordinate tuple in a Room which
            # can by convention be infered from the Plane's name.
            #
            event = fabula.TriesToMoveEvent(self.host.client_id,
                                           eval(plane.name))

            self.message_for_host.event_list.append(event)

        return

    def tile_drop_callback(self, plane, dropped_plane, screen_coordinates):
        """Drop callback to issue a TriesToDropEvent.
        """

        fabula.LOGGER.debug("called")

        name = plane.name

        # Just to be sure, check if the Plane's name matches a "(x, y)" string.
        #
        if not fabula.str_is_tuple(name):

            fabula.LOGGER.error("plane.name does not match coordinate tuple: '{}'".format(name))

        else:
            # The target identifier is a coordinate tuple in a Room which
            # can by convention be infered from the Plane's name.
            #
            tries_to_drop_event = fabula.TriesToDropEvent(self.host.client_id,
                                                         dropped_plane.name,
                                                         eval(name))

            self.message_for_host.event_list.append(tries_to_drop_event)

        return

    def entity_dropped_callback(self, plane, dropped_plane, coordinates):
        """Dropped upon callback for Entities.
           Adds appropriate Events to PygameUserInterface.message_for_host.
        """

        fabula.LOGGER.debug("called")

        event = fabula.TriesToDropEvent(self.host.client_id,
                                        dropped_plane.name,
                                        self.host.room.entity_locations[plane.name])

        self.message_for_host.event_list.append(event)

        return

    def entity_right_click_callback(self, plane):
        """Right click callback for Entity Plane.
        """

        fabula.LOGGER.debug("called")

        if plane.name not in self.host.room.entity_dict.keys():

            fabula.LOGGER.debug("'{}' not in Room, ignoring right click".format(plane.name))

        else:

            # One
            #
            icon_plane = self.attempt_icon_planes[0]

            icon_plane.rect.center = (plane.rect.center[0] - 35,
                                      plane.rect.center[1])

            # Sync position to Entity plane
            #
            icon_plane.sync(plane)

            # This will remove and re-add the Plane to room.
            # <3 clickndrag :-)
            #
            self.window.room.sub(icon_plane)

            # Two
            #
            icon_plane = self.attempt_icon_planes[1]

            icon_plane.rect.center = (plane.rect.center[0] + 35,
                                      plane.rect.center[1])

            icon_plane.sync(plane)

            self.window.room.sub(icon_plane)

            # Three
            #
            icon_plane = self.attempt_icon_planes[2]

            icon_plane.rect.center = (plane.rect.center[0],
                                      plane.rect.center[1] - 35)

            icon_plane.sync(plane)

            self.window.room.sub(icon_plane)

            # Four
            #
            icon_plane = self.attempt_icon_planes[3]

            icon_plane.rect.center = (plane.rect.center[0],
                                      plane.rect.center[1] + 35)

            icon_plane.sync(plane)

            self.window.room.sub(icon_plane)

            # Save Entity
            #
            self.right_clicked_entity = self.host.room.entity_dict[plane.name]

        return

    def attempt_icon_callback(self, plane):
        """General left-click callback for attempt action icons.
        """

        fabula.LOGGER.debug("called")

        event = None

        # Although we know the Entity, the server determines what if being
        # looked at. So send target identifiers instead of Entity identifiers.

        if plane.name == "attempt_manipulate":

            event = fabula.TriesToManipulateEvent(self.host.client_id,
                                                  self.host.room.entity_locations[self.right_clicked_entity.identifier])

        elif plane.name == "attempt_talk_to":

            event = fabula.TriesToTalkToEvent(self.host.client_id,
                                              self.host.room.entity_locations[self.right_clicked_entity.identifier])

        elif plane.name == "attempt_look_at":

            event = fabula.TriesToLookAtEvent(self.host.client_id,
                                              self.host.room.entity_locations[self.right_clicked_entity.identifier])

        # Remove icons in any case. This also works if the "cancel" icon was
        # clicked.
        #
        for icon_plane in self.attempt_icon_planes:

            self.window.room.remove(icon_plane)

            # Don't forget to unsync position
            #
            icon_plane.unsync()

        if event is not None:

            self.message_for_host.event_list.append(event)

        return

    def display_loading_progress(self, obj):
        """Display the string representation of the object given on the loading screen while the game is frozen.
        """

        if self.freeze:

            displaystring = str(obj).center(128)

            self.window.display.blit(clickndrag.gui.SMALL_FONT.render(displaystring,
                                                            True,
                                                            (127, 127, 127),
                                                            (0, 0, 0)),
                                     (120, 500))

            pygame.display.flip()

        return

    def make_items_draggable(self):
        """Auxiliary method to make items next to the player draggable.
        """

        if self.host.client_id in self.host.room.entity_dict.keys():

            player_location = self.host.room.entity_locations[self.host.client_id]

            surrounding_positions = fabula.surrounding_positions(player_location)

            for identifier in self.host.room.entity_locations.keys():

                entity = self.host.room.entity_dict[identifier]

                fabula.LOGGER.debug("processing Entity '{}'".format(identifier))

                if entity.entity_type == fabula.ITEM and entity.mobile:

                    if self.host.room.entity_locations[identifier] in surrounding_positions:

                        entity.asset.draggable = True

                    else:
                        entity.asset.draggable = False

                else:
                    # Make sure it's not draggable
                    #
                    entity.asset.draggable = False

        else:
            fabula.LOGGER.warning("'{}' not found in room, items are not made draggable".format(self.host.client_id))

        return

    def _snap_room_to_display(self):
        """Snap the room plane to the window plane.
        """

        if self.window.room.rect.left > 0:
           self.window.room.rect.left = 0

        if self.window.room.rect.top > 0:
           self.window.room.rect.top = 0

        if self.window.room.rect.right < SCREENSIZE[0]:
           self.window.room.rect.right = SCREENSIZE[0]

        # Mind the inventory
        #
        if self.window.room.rect.bottom < SCREENSIZE[1] - self.window.inventory.rect.height:
           self.window.room.rect.bottom = SCREENSIZE[1] - self.window.inventory.rect.height

        return

class EventEditor(clickndrag.gui.Container):
    """A clickndrag Container that implements an editor for Fabula Events.

       Additional attributes:

       EventEditor.title
           A Label for the title. EventEditor.title.name is the class name of
           the Event.

       EventEditor.ATTRIBUTE_key_value
           A Plane with the subplanes EventEditor.ATTRIBUTE_key_value.ATTRIBUTE
           (Label) and EventEditor.ATTRIBUTE_key_value.ATTRIBUTE_value (TextBox).
    """

    def __init__(self, event, display):
        """Initialise.
        """
        # This editor borrows a lot from Event.__repr__()

        # Call base class
        # We need a random and unique name - use the id of the Event.
        #
        clickndrag.gui.Container.__init__(self,
                                          str(id(event)),
                                          padding = 5)

        # Title
        #
        self.sub(clickndrag.gui.Label("title",
                                      event.__class__.__name__,
                                      pygame.Rect((0, 0), (300, 25)),
                                      background_color = clickndrag.gui.HIGHLIGHT_COLOR))

        # Show Event attributes

        # Keep order
        #
        keys = list(event.__dict__.keys())
        keys.sort()

        for key in keys:

            key_label = clickndrag.gui.Label("key_{}".format(key),
                                             "{}:".format(key),
                                             pygame.Rect((0, 0), (150, 25)))

            value_textbox = clickndrag.gui.TextBox("value_{}".format(key),
                                                   pygame.Rect((key_label.rect.width, 0),
                                                               (150, 25)))

            value_textbox.text = str(event.__dict__[key])

            # Upon clicked, register the TextBox for keyboard input
            #
            value_textbox.left_click_callback = lambda plane : display.key_sensitive(plane)

            key_value = clickndrag.Plane("keyvalue_{}".format(key),
                                         pygame.Rect((0, 0),
                                                     (300, 25)))

            key_value.sub(key_label)
            key_value.sub(value_textbox)

            self.sub(key_value)

        return

    def get_updated_event(self):
        """Return an Event that incorporates the current user changes.
        """
        # The Event is built as a string and then pumped through eval()
        # TODO: this should go to the Fabula main package
        # TODO: escape quotes in text entered by user!
        #
        class_str = "fabula.{}(".format(self.title.text)

        attribute_str_list = []

        for name in self.subplanes_list:

            if name.startswith("keyvalue_"):

                # Stripping "keyvalue_" from name to obtain key.
                #
                key = name[9:]

                value = self.subplanes[name].subplanes["value_{}".format(key)].text

                # TODO: just guessing for a list, replace with a proper check
                #
                if not fabula.str_is_tuple(value) and not (value.startswith("[") and value.endswith("]")):

                    # No coordinate tuple, no list, then it should be a string
                    #
                    value = "'{}'".format(value)

                attribute_str_list.append("{} = {}".format(key, value))

        event = eval("{}{})".format(class_str, ", ".join(attribute_str_list)))

        return event

class PygameEditor(PygameUserInterface):
    """A Pygame-based user interface that serves as a map editor.

       This Plugin is meant to be used by fabula.serverside.Editor.

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

    # TODO: PygameEditor and serverside.Editor should each care for their own data structures. So separate methods where applicable.

    def __init__(self, assets, framerate, host):
        """Call PygameUserInterface.__init__(), but set up different Planes.
        """

        # Call base class __init__()
        #
        PygameUserInterface.__init__(self, assets, framerate, host)

        fabula.LOGGER.debug("called")

        # Spacing is a little larger here to show grid lines.
        #
        self.spacing = 101

        # Setup a cache for planes
        #
        self.plane_cache = []

        # Set window name
        #
        pygame.display.set_caption("Fabula Editor")

        # Create a semi-transparent red Surface to be used as an OBSTACLE
        # indicator overlay
        #
        self.overlay_surface = pygame.Surface((100, 100))
        self.overlay_surface.fill((255, 0, 0))
        self.overlay_surface.set_alpha(127)

        # Add the inventory plane created in PygameUserInterface.__init__()
        #
        self.window.sub(self.inventory_plane)

        # Create Container for the editor buttons.
        #
        container = clickndrag.gui.Container("buttons",
                                             padding = 4,
                                             background_color = (120, 120, 120))
        self.window.sub(container)

        # Add buttons

        room = clickndrag.gui.Container("room",
                                        padding = 4,
                                        background_color = (120, 120, 120))

        room.sub(clickndrag.gui.Label("title",
                                      "Room",
                                      pygame.Rect((0, 0),
                                                  (80, 25)),
                                      background_color = (120, 120, 120)))

        room.sub(clickndrag.gui.Button("Load Room",
                                       pygame.Rect((0, 0),
                                                   (80, 25)),
                                       self.load_room))

        room.sub(clickndrag.gui.Button("Save Room",
                                       pygame.Rect((0, 0),
                                                   (80, 25)),
                                       self.save_room))

        room.sub(clickndrag.gui.Button("Add Entity",
                                       pygame.Rect((0, 0),
                                                   (80, 25)),
                                       lambda plane: self.edit_entity_attributes(self.add_entity)))

        room.sub(clickndrag.gui.Button("Edit Walls",
                                       pygame.Rect((0, 0),
                                                   (80, 25)),
                                       self.edit_walls))

        background = clickndrag.gui.Container("background",
                                              padding = 4,
                                              background_color = (120, 120, 120))

        background.sub(clickndrag.gui.Label("title",
                                            "Background",
                                            pygame.Rect((0, 0),
                                                        (80, 25)),
                                            background_color = (120, 120, 120)))

        background.sub(clickndrag.gui.Button("Open Image",
                                             pygame.Rect((0, 0),
                                                         (80, 25)),
                                             self.open_image))

        logic = clickndrag.gui.Container("logic",
                                         padding = 4,
                                         background_color = (120, 120, 120))

        logic.sub(clickndrag.gui.Label("title",
                                       "Logic",
                                       pygame.Rect((0, 0),
                                                   (80, 25)),
                                       background_color = (120, 120, 120)))

        logic.sub(clickndrag.gui.Button("Save Logic",
                                        pygame.Rect((0, 0),
                                                    (80, 25)),
                                        lambda plane : self.host.save_condition_response_dict("default.logic")))

        logic.sub(clickndrag.gui.Button("Load Logic",
                                        pygame.Rect((0, 0),
                                                    (80, 25)),
                                        lambda plane: self.host.load_condition_response_dict("default.logic")))

        logic.sub(clickndrag.gui.Button("Clear Logic",
                                        pygame.Rect((0, 0),
                                                    (80, 25)),
                                        lambda plane: self.host.clear_condition_response_dict()))

        self.window.buttons.sub(room)
        self.window.buttons.sub(background)
        self.window.buttons.sub(logic)

        self.window.buttons.sub(clickndrag.gui.Button("Quit",
                                                      pygame.Rect((0, 0),
                                                                  (80, 25)),
                                                      self.quit))

        # Create Container for the properties
        #
        container = clickndrag.gui.Container("properties",
                                             padding = 5,
                                             background_color = (120, 120, 120))
        container.rect.topleft = (700, 0)
        self.window.sub(container)

        fabula.LOGGER.debug("complete")

        return

    def open_image(self, plane):
        """Button callback to prompt the user for a room background image, load it and assign it to tiles.
        """

        fabula.LOGGER.debug("called")

        new_image, filename = load_image("Open Background Image")

        if new_image is not None:

            # TODO: hardcoded spacing
            # Cannot use self.spacing since it is deliberately larger than PygameUserInterface.spacing
            #
            spacing = 100

            image_width, image_height = new_image.get_size()

            fabula.LOGGER.debug("original dimensions of loaded image: {}x{}".format(image_width,
                                                                                   image_height))

            # Get width and height that are multiples of self.spacing
            #
            fitted_width = int(image_width / spacing) * spacing

            if image_width % spacing:

                # Add a whole spacing unit to catch the leftover pixels
                #
                fitted_width = fitted_width + spacing

            fitted_height = int(image_height / spacing) * spacing

            if image_height % spacing:

                # Add a whole spacing unit to catch the leftover pixels
                #
                fitted_height = fitted_height + spacing

            # Create a new Surface with the new size, and blit the image on it
            #
            fitted_surface = pygame.Surface((fitted_width, fitted_height))

            fitted_surface.blit(new_image, (0, 0))

            fabula.LOGGER.debug("dimensions of fitted image: {}x{}".format(fitted_width,
                                                                           fitted_height))

            for x in range(int(fitted_width / spacing)):

                for y in range(int(fitted_height / spacing)):

                    # Create new Tile and sent it to Server
                    # Cave: dummy asset description
                    #
                    tile = fabula.Tile(fabula.FLOOR,
                                       "dummy asset for ({}, {})".format(x, y))

                    rect = pygame.Rect((x * spacing, y * spacing),
                                       (spacing, spacing))

                    tile.asset = fitted_surface.subsurface(rect)

                    event = fabula.ChangeMapElementEvent(tile, (x, y))

                    self.host.message_for_host.event_list.append(event)

            self.host.message_for_host.event_list.append(fabula.RoomCompleteEvent())

        else:
            fabula.LOGGER.error("could not load image '{}'".format(filename))

        return

    def save_room(self, plane):
        """Button callback to save the tile images, resend and then save the Room to a local file.
        """

        # Observe that this method adds Events to self.host.message_for_host,
        # which is fabula.plugins.serverside.Editor.message_for_host.

        # TODO: Something goes wrong here: Loading a room and replacing the image leads to the *old* tile assets being loaded upon save.

        fabula.LOGGER.debug("called")

        tk = tkinter.Tk()
        tk.withdraw()

        fullpath = tkinter.filedialog.asksaveasfilename(filetypes = [("Fabula Room Files",
                                                                      ".floorplan")],
                                                        title = "Save Tiles And Floorplan")

        tk.destroy()

        path, filename = os.path.split(fullpath)

        # Strip extension, if given
        #
        filename = os.path.splitext(filename)[0]

        if not filename:

            fabula.LOGGER.warning("no filename selected")

        else:
            fabula.LOGGER.info("save to: {}".format(filename))

            self.host.message_for_host.event_list.append(fabula.EnterRoomEvent(self.host.client_id,
                                                                               filename))

            roomfile = open(filename + ".floorplan", "wt")

            # TODO: only save PNGs if they have actually changed
            #
            for x, y in list(self.host.room.floor_plan.keys()):

                    # Save image file
                    #
                    current_file = filename + "-{0}_{1}.png".format(x, y)
                    fabula.LOGGER.debug(current_file)
                    pygame.image.save(self.window.room.tiles.subplanes[str((x, y))].image,
                                      os.path.join(path, current_file))

                    # Send renamed Tile to Server
                    #
                    tile = fabula.Tile(self.host.room.floor_plan[(x, y)].tile.tile_type,
                                       current_file)

                    event = fabula.ChangeMapElementEvent(tile, (x, y))

                    self.host.message_for_host.event_list.append(event)

                    # Save tile in floorplan file

                    entities_string = ""

                    for entity in self.host.room.floor_plan[(x, y)].entities:

                        # TODO: make sure commas are not present in the other strings
                        #
                        argument_list = ",".join([entity.identifier,
                                                  entity.entity_type,
                                                  repr(entity.blocking),
                                                  repr(entity.mobile),
                                                  entity.asset_desc])

                        entities_string = entities_string + "\t{}".format(argument_list)

                    roomfile.write("{}\t{}\t{}{}\n".format(repr((x, y)),
                                                           tile.tile_type,
                                                           tile.asset_desc,
                                                           entities_string))

            roomfile.close()

            fabula.LOGGER.info("wrote {}".format(filename + ".floorplan"))

            # Then respawn all current Entities in the Server since
            # EnterRoomEvent will set up a new room
            #
            for identifier in self.host.room.entity_dict.keys():

                # Create a new Entity which can be pickled by Event loggers
                # TODO: still necessary?
                #
                entity = fabula.Entity(identifier,
                                       self.host.room.entity_dict[identifier].entity_type,
                                       self.host.room.entity_dict[identifier].blocking,
                                       self.host.room.entity_dict[identifier].mobile,
                                       self.host.room.entity_dict[identifier].asset_desc)

                event = fabula.SpawnEvent(entity,
                                         self.host.room.entity_locations[identifier])

                self.host.message_for_host.event_list.append(event)

            self.host.message_for_host.event_list.append(fabula.RoomCompleteEvent())

        return

    def load_room(self, plane):
        """Button callback to display a list of rooms to select from.
        """

        fabula.LOGGER.debug("called")

        room_list = []

        for filename in os.listdir(os.getcwd()):

            if filename.endswith(".floorplan"):

                room_list.append(filename.split(".floorplan")[0])

        if len(room_list):
            option_list = clickndrag.gui.OptionSelector("select_room",
                                                    room_list,
                                                    self.host.send_room_events,
                                                    lineheight = 25)

            option_list.rect.center = self.window.rect.center

            self.window.sub(option_list)

        else:
            fabula.LOGGER.warning("no floorplan files found in '{}'".format(os.getcwd()))

        return

    def edit_entity_attributes(self, callback, entity = None):
        """Open an editor to enter or edit Entity properties.
           callback will be attached to the OK button.
        """

        # TODO: edit asset description / select image

        fabula.LOGGER.debug("called")

        container = clickndrag.gui.Container("get_entity_attributes",
                                             padding = 5)

        # Identifier
        #
        container.sub(clickndrag.gui.Label("id_caption",
                                           "Identifier:",
                                           pygame.Rect((0, 0),
                                                            (200, 30))))

        if entity is not None:

            # Shouldn't change identifier of a live Entity
            #
            container.sub(clickndrag.gui.Label("identifier",
                                               entity.identifier,
                                               pygame.Rect((0, 0),
                                                                (200, 30))))

        else:
            container.sub(clickndrag.gui.TextBox("identifier",
                                                 pygame.Rect((0, 0),
                                                                (200, 30)),
                                                 return_callback = None))

            # Register text box
            #
            self.window.key_sensitive(container.identifier)


        # Type
        #
        container.sub(clickndrag.gui.Label("type_caption",
                                           "Type:",
                                           pygame.Rect((0, 0),
                                                            (200, 30))))

        if entity is not None:

            if entity.entity_type == fabula.PLAYER:

                container.sub(clickndrag.gui.Label("select_entity_type",
                                                   "PLAYER",
                                                   pygame.Rect((0, 0),
                                                                    (200, 30))))
            else:

                # Display current type at top
                #
                type_list = {fabula.ITEM: ["ITEM", "NPC"],
                             fabula.NPC: ["NPC", "ITEM"]}[entity.entity_type]

                container.sub(clickndrag.gui.OptionList("select_entity_type",
                                                        type_list,
                                                        lineheight = 25))
        else:
            container.sub(clickndrag.gui.OptionList("select_entity_type",
                                                    ["ITEM", "NPC"],
                                                    lineheight = 25))

        # Blocking
        #
        container.sub(clickndrag.gui.Label("blocking_caption",
                                           "Blocking:",
                                           pygame.Rect((0, 0),
                                                            (200, 30))))

        blocking_list = ["block", "no-block"]

        if entity is not None:

            # Display current at top
            #
            blocking_list = {True: ["block", "no-block"],
                             False: ["no-block", "block"]}[entity.blocking]

        container.sub(clickndrag.gui.OptionList("select_blocking",
                                                blocking_list,
                                                lineheight = 25))

        # Mobility
        # TODO: shouldn't be able to change mobility of PLAYER
        #
        container.sub(clickndrag.gui.Label("mobility_caption",
                                           "Mobility:",
                                           pygame.Rect((0, 0),
                                                            (200, 30))))

        mobility_list = ["mobile", "immobile"]

        if entity is not None:

            # Display current at top
            #
            mobility_list = {True: ["mobile", "immobile"],
                             False: ["immobile", "mobile"]}[entity.mobile]

        container.sub(clickndrag.gui.OptionList("select_mobile",
                                                mobility_list,
                                                lineheight = 25))

        # OK button
        #
        container.sub(clickndrag.gui.Button("OK",
                                            pygame.Rect((0, 0),
                                                        (200, 30)),
                                            callback))

        container.rect.center = self.window.rect.center

        self.window.sub(container)

        return

    def add_entity(self, buttonplane):
        """Button callback to request an image and add the Entity to the rack.
        """

        fabula.LOGGER.debug("called")

        # Get user input
        #
        entity_type = buttonplane.parent.select_entity_type.selected.text
        entity_identifier = buttonplane.parent.identifier.text
        entity_blocking = {"block": True,
                           "no-block": False}[buttonplane.parent.select_blocking.selected.text]
        entity_mobile = {"mobile": True,
                         "immobile": False}[buttonplane.parent.select_mobile.selected.text]

        # Destroy dialog
        #
        buttonplane.parent.destroy()

        # Update to clean up destroyed dialog
        #
        self.display_single_frame()

        if entity_identifier == '':

            fabula.LOGGER.warning("no item identifer given in attributes dialog, not adding Entity")

        else:

            image, filename = load_image("Image Of New Item")

            if image is not None:

                entity = fabula.Entity(identifier = entity_identifier,
                                       entity_type = {"ITEM": fabula.ITEM, "NPC": fabula.NPC}[entity_type],
                                       blocking = entity_blocking,
                                       mobile = entity_mobile,
                                       asset_desc = filename)

                fabula.LOGGER.info("adding Entity '{}'".format(entity_identifier))

                fabula.LOGGER.debug("appending SpawnEvent")

                # TODO: make sure to use a safe spawning location
                # Observe: adding to self.host.message_for_host
                #
                self.host.message_for_host.event_list.append(fabula.SpawnEvent(entity, (0, 0)))

                if entity_type == "ITEM":

                    fabula.LOGGER.debug("appending PicksUpEvent")

                    self.host.message_for_host.event_list.append(fabula.PicksUpEvent(self.host.client_id,
                                                                                     entity_identifier))

            else:
                fabula.LOGGER.warning("no image selected, not adding Entity")

        return

    def update_entity(self, buttonplane):
        """Update the properties of the Entity in self.host.entity_dict.
        """

        # TODO: there is still a lot copied from add_entity(). Wrapper?

        fabula.LOGGER.debug("called")

        # Get user input
        #
        if isinstance(buttonplane.parent.select_entity_type,
                      clickndrag.gui.OptionList):

            entity_type = buttonplane.parent.select_entity_type.selected.text

        else:
            entity_type = "PLAYER"

        entity_identifier = buttonplane.parent.identifier.text
        entity_blocking = {"block": True,
                           "no-block": False}[buttonplane.parent.select_blocking.selected.text]
        entity_mobile = {"mobile": True,
                         "immobile": False}[buttonplane.parent.select_mobile.selected.text]

        # Destroy dialog
        #
        buttonplane.parent.destroy()

        # Update to clean up destroyed dialog
        #
        self.display_single_frame()

        if entity_identifier in self.host.room.entity_dict.keys():

            fabula.LOGGER.info("updating Entity '{}'".format(entity_identifier))

            entity = self.host.room.entity_dict[entity_identifier]

            if entity_type != "PLAYER":

                # This works because we have direct access to the server via
                # self.host, which is the Server plugin.
                #
                entity.entity_type = entity_type

            entity.blocking = entity_blocking

            entity.mobile = entity_mobile

            # Update the properties Plane to show the changes
            #
            self.show_properties(entity.asset)

        else:
            fabula.LOGGER.warning("Entity '{}' not found in entity_dict".format(entity_identifier))

        return

    def quit(self, plane):
        """Button callback to set self.exit_requested = True
        """
        fabula.LOGGER.info("setting exit_requested = True")
        self.host.host.exit_requested = True

    def edit_walls(self, plane):
        """Button callback to switch to wall edit mode.
        """
        fabula.LOGGER.debug("called")

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
                                                                  (80, 25)),
                                                      background_color = (120, 120, 120)))

        self.window.buttons.sub(clickndrag.gui.Button("Done",
                                                      pygame.Rect((5, 35),
                                                                  (80, 25)),
                                                      self.wall_edit_done))

        # Clear Entity planes from room, but cache them.
        # By convention the name of the Entity Plane is Entity.identifier.
        #
        for identifier in self.host.room.entity_dict.keys():
            self.plane_cache.append(self.window.room.subplanes[identifier])
            self.window.room.remove(identifier)

        fabula.LOGGER.debug("{} Plane(s) in plane_cache now".format(len(self.plane_cache)))

        # Make Entity planes in inventory insensitive to drags
        #
        for plane in self.window.inventory.subplanes.values():
            plane.draggable = False

        # Install Tile clicked callback.
        #
        for plane in self.window.room.tiles.subplanes.values():
            plane.left_click_callback = self.make_tile_obstacle

        # Finally, create overlays for OBSTACLE tiles.
        # TODO: slight duplicate from make_tile_obstacle
        #
        for coordinates in self.host.room.floor_plan.keys():

            if self.host.room.floor_plan[coordinates].tile.tile_type == fabula.OBSTACLE:

                overlay_plane = clickndrag.Plane(str(coordinates) + "_overlay",
                                                 pygame.Rect(self.window.room.tiles.subplanes[str(coordinates)].rect),
                                                 left_click_callback = self.make_tile_floor)

                overlay_plane.image = self.overlay_surface

                self.window.room.tiles.sub(overlay_plane)

    def make_tile_obstacle(self, plane):
        """Clicked callback which changes the Tile type to fabula.OBSTACLE.
           More specific, a ChangeMapElementEvent is sent to the Server, and an
           overlay is applied to visualize the OBSTACLE type.
        """

        fabula.LOGGER.debug("returning ChangeMapElementEvent to Server and creating overlay for tile at {}".format(plane.name))

        # The name of the clicked Plane is supposed to be a string representation
        # of a coordinate tuple.
        #
        coordinates = eval(plane.name)
        asset_desc = self.host.room.floor_plan[coordinates].tile.asset_desc

        event = fabula.ChangeMapElementEvent(fabula.Tile(fabula.OBSTACLE, asset_desc),
                                             coordinates)

        self.host.message_for_host.event_list.append(event)

        # Draw an overlay indicating the OBSTACLE type.
        # rect can be taken from the Plane that received the click, but we make
        # a copy to be on the safe side.
        #
        overlay_plane = clickndrag.Plane(str(coordinates) + "_overlay",
                                         pygame.Rect(plane.rect),
                                         left_click_callback = self.make_tile_floor)

        overlay_plane.image = self.overlay_surface

        self.window.room.tiles.sub(overlay_plane)

    def make_tile_floor(self, plane):
        """Clicked callback which changes the Tile type to fabula.FLOOR.
           More specific, a ChangeMapElementEvent is sent to the Server, and the
           overlay to visualize the OBSTACLE type is deleted.
        """

        # Based on a copy-paste from make_tile_obstacle()

        fabula.LOGGER.debug("returning ChangeMapElementEvent to Server and deleting '{}'".format(plane.name))

        # The clicked Plane is the overlay. Its name is supposed to be a string
        # representation of a coordinate tuple plus "_overlay".
        #
        coordinates = eval(plane.name.split("_overlay")[0])
        asset_desc = self.host.room.floor_plan[coordinates].tile.asset_desc

        event = fabula.ChangeMapElementEvent(fabula.Tile(fabula.FLOOR, asset_desc),
                                             coordinates)

        self.host.message_for_host.event_list.append(event)

        # Delete the overlay indicating the OBSTACLE type.
        #
        plane.destroy()

    def wall_edit_done(self, plane):
        """Button callback which restores the editor to the state before edit_walls().
        """
        fabula.LOGGER.debug("called")

        # Remove all wall marker overlays.
        # Restore Tile clicked callbacks along the way.
        # Entity Planes are not yet restored, so there should be only tiles left.
        #
        for plane in list(self.window.room.tiles.subplanes.values()):

            if plane.name.endswith("_overlay"):

                plane.destroy()

            else:
                plane.left_click_callback = self.tile_clicked_callback

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

        return

    def collect_player_input(self):
        """Call base class, but initiate scrolling in any case.
        """

        PygameUserInterface.collect_player_input(self)

        # Check mouse position, and trigger window scrolling
        # Copied from PygameUserInterface.collect_player_input()
        # Pygame might have been quit, so check pygame.display.get_init().
        #
        if not self.scroll and pygame.display.get_init():

            mouse_position = pygame.mouse.get_pos()

            if 0 <= mouse_position[0] <= 25:

                # Scroll to the left
                #
                self.scroll = self.spacing

            elif SCREENSIZE[0] - 25 <= mouse_position[0] <= SCREENSIZE[0]:

                # Scroll to right
                #
                self.scroll = 0 - self.spacing

        return

    def process_SpawnEvent(self, event):
        """Call PygameUserInterface.process_SpawnEvent, add a left_click_callback to the Entity, and make the Entity asset draggable.
        """

        PygameUserInterface.process_SpawnEvent(self, event)

        plane = self.window.room.subplanes[event.entity.identifier]

        if plane.left_click_callback is None:

            fabula.LOGGER.debug("left_click_callback of '{}' is still None, adding callback".format(event.entity.identifier))
            plane.left_click_callback = self.show_properties

        self.make_items_draggable()

        return

    def process_RoomCompleteEvent(self, event):
        """Call the base class, but make sure the buttons Plane is on top.
        """

        PygameUserInterface.process_RoomCompleteEvent(self, event)

        self.window.sub(self.window.buttons)

        # Shift room to have space for the GUI
        #
        self.window.room.rect.left = 100

        return

    def show_properties(self, plane):
        """Click callback for entities to show their properties in the properties Plane.
        """

        # Always update property display.
        #
        fabula.LOGGER.debug("showing properties of '{}'".format(plane.name))

        self.window.properties.remove_all()

        if plane.name in self.host.room.entity_dict.keys():

            entity = self.host.room.entity_dict[plane.name]

        elif plane.name in self.host.rack.entity_dict.keys():

            entity = self.host.rack.entity_dict[plane.name]

        else:
            fabula.LOGGER.error("entity '{}' neither in Room nor Rack, can not update property inspector".format(plane.name))

            return

        # Entity.identifier
        #
        self.window.properties.sub(clickndrag.gui.Label("identifier",
                                                        entity.identifier,
                                                        pygame.Rect((0, 0), (80, 25)),
                                                        background_color = (120, 120, 120)))

        # Entity.asset
        #
        rect = pygame.Rect((0, 0), entity.asset.image.get_rect().size)

        asset_plane = clickndrag.Plane("asset", rect)

        asset_plane.image = entity.asset.image

        self.window.properties.sub(asset_plane)

        # Entity.asset_desc
        #
        self.window.properties.sub(clickndrag.gui.Label("asset_desc",
                                                        entity.asset_desc,
                                                        pygame.Rect((0, 0), (80, 25)),
                                                        background_color = (120, 120, 120)))

        # Entity.entity_type
        #
        self.window.properties.sub(clickndrag.gui.Label("entity_type",
                                                        entity.entity_type,
                                                        pygame.Rect((0, 0), (80, 25)),
                                                        background_color = (120, 120, 120)))

        # Entity.blocking
        #
        self.window.properties.sub(clickndrag.gui.Label("blocking",
                                                        {True: "block", False: "no-block"}[entity.blocking],
                                                        pygame.Rect((0, 0), (80, 25)),
                                                        background_color = (120, 120, 120)))

        # Entity.mobile
        #
        self.window.properties.sub(clickndrag.gui.Label("mobile",
                                                        {True: "mobile", False: "immobile"}[entity.mobile],
                                                        pygame.Rect((0, 0), (80, 25)),
                                                        background_color = (120, 120, 120)))

        # Edit
        #
        self.window.properties.sub(clickndrag.gui.Button("Edit Entity",
                                                         pygame.Rect((0, 0),
                                                                     (80, 25)),
                                                         lambda plane: self.edit_entity_attributes(self.update_entity, entity)))

        # Logic
        #
        self.window.properties.sub(clickndrag.gui.Button("Edit Logic",
                                                         pygame.Rect((0, 0),
                                                                     (80, 25)),
                                                         lambda plane : self.edit_logic(entity.identifier)))

        # Make sure it's on top
        #
        self.window.sub(self.window.properties)

        # Make it completely visible, no matter how large
        #
        self.window.properties.rect.right = SCREENSIZE[0]

        return

    def make_items_draggable(self):
        """Overriding base class: make all items always draggable.
        """

        for identifier in self.host.room.entity_locations.keys():

            if (identifier != self.host.client_id
                and self.host.room.entity_dict[identifier].asset is not None):

                self.host.room.entity_dict[identifier].asset.draggable = True

        return

    def select_event(self, event):
        """Make the user specify an response Event to an action.
        """

        fabula.LOGGER.debug("called")

        event_list = ("Attempt Failed",
                      "Perception",
                      "Says")

        # TODO: "Can Speak"
        # TODO: "Moves To"
        # TODO: "Change Map Element"
        # TODO: "Delete"
        # TODO: "Spawn"
        # TODO: ChangePropertyEvent
        # TODO: ManipulatesEvent
        # TODO: EnterRoomEvent
        # TODO: RoomCompleteEvent
        # TODO: PicksUpEvent
        # TODO: DropsEvent
        # TODO: specify multiple Events as response

        option_list = clickndrag.gui.OptionSelector("select_response",
                                                event_list,
                                                lambda option : self.edit_event(event, option),
                                                lineheight = 25)

        option_list.rect.center = self.window.rect.center

        self.window.sub(option_list)

        return

    def edit_event(self, event, option):
        """Let the user edit the attributes of the selected Event.
        """

        fabula.LOGGER.debug("called")

        if option.text == "Perception":

            # TODO: taken from update_logic(). Replace with a general Plane/Editor.
            #
            editor_window = clickndrag.gui.Container("edit_event", padding = 4)

            event_editor = EventEditor(fabula.PerceptionEvent(event.identifier, ""), self.window)

            editor_window.sub(event_editor)

            editor_window.sub(clickndrag.gui.Button("OK",
                                                    pygame.Rect((0, 0), (100, 25)),
                                                    lambda string: self.event_edit_done(event, event_editor.get_updated_event())))

            editor_window.rect.center = self.window.rect.center

            self.window.sub(editor_window)

        elif option.text == "Says":

            # TODO: copied from above, replace
            #
            editor_window = clickndrag.gui.Container("edit_event", padding = 4)

            event_editor = EventEditor(fabula.SaysEvent(event.identifier, ""), self.window)

            editor_window.sub(event_editor)

            editor_window.sub(clickndrag.gui.Button("OK",
                                                    pygame.Rect((0, 0), (100, 25)),
                                                    lambda string: self.event_edit_done(event, event_editor.get_updated_event())))

            editor_window.rect.center = self.window.rect.center

            self.window.sub(editor_window)

        elif option.text == "Attempt Failed":

            # Do nothing. AttemptFailedEvent is the default response.
            #
            pass

        else:
            fabula.LOGGER.critical("handling of '{}' not implemented".format(option.text))

        return

    def event_edit_done(self, trigger_event, response_event):
        """Button callback to call host.add_response() and destroy the Container.
        """

        fabula.LOGGER.debug("called")

        self.window.edit_event.destroy()

        self.host.add_response(trigger_event, response_event)

        return

    def edit_logic(self, identifier):
        """Display the current game logic affecting the Entity identified by identifier.
        """

        fabula.LOGGER.debug("called")

        editor_window = clickndrag.gui.Container("display_logic", padding = 4)

        editor_window.sub(clickndrag.gui.Label("title",
                                               "Logic affecting Entity '{}'".format(identifier),
                                               pygame.Rect((0, 0), (300, 25))))

        rules_container = clickndrag.gui.Container("rules", padding = 4)

        for trigger_event_str in self.host.condition_response_dict.keys():

            # Check if "identifier" is affected by a trigger or response Event
            #
            identifier_affected = False

            if identifier in trigger_event_str:

                identifier_affected = True

            else:

                for response_event in self.host.condition_response_dict[trigger_event_str]:

                    if response_event.identifier == identifier:

                        identifier_affected = True

            if identifier_affected:

                for response_event in self.host.condition_response_dict[trigger_event_str]:

                    # TODO: eval() should be preceeded by thorough checks
                    #
                    trigger_editor = EventEditor(eval(trigger_event_str),
                                                 self.window)

                    response_editor = EventEditor(response_event,
                                                  self.window)

                    # Need a unique name.
                    # See below for width - 1
                    #
                    rule_plane = clickndrag.Plane("rule_{}_{}".format(trigger_editor.name, response_editor.name),
                                                  pygame.Rect((0, 0), (trigger_editor.rect.width + response_editor.rect.width - 1, trigger_editor.rect.height)))

                    rule_plane.image.fill(clickndrag.gui.BACKGROUND_COLOR)

                    # Make them overlap to have an 1px separating line
                    #
                    response_editor.rect.left = trigger_editor.rect.width - 1

                    rule_plane.sub(trigger_editor)
                    rule_plane.sub(response_editor)

                    fabula.LOGGER.debug("Adding rule Plane '{}'".format(rule_plane.name))
                    rules_container.sub(rule_plane)

        if len(rules_container.subplanes_list):

            editor_window.sub(clickndrag.gui.ScrollingPlane("scrolling_rules",
                                                            pygame.Rect((0, 0),
                                                                        (rules_container.subplanes[rules_container.subplanes_list[0]].rect.width + 8, 400)),
                                                            rules_container))

        editor_window.sub(clickndrag.gui.Button("Update",
                                                pygame.Rect((0, 0), (100, 25)),
                                                self.update_logic))

        editor_window.rect.centerx = self.window.rect.centerx

        self.window.sub(editor_window)

        return

    def update_logic(self, plane):
        """Button callback to retrieve the updated game logic and send it to the host.
        """

        fabula.LOGGER.debug("called")

        if "scrolling_rules" in self.window.display_logic.subplanes_list:

            # ScrollingPlanes lead to long attribute traversals
            #
            rules_plane = self.window.display_logic.scrolling_rules.content.rules

            for name in rules_plane.subplanes_list:

                if name.startswith("rule_"):

                    dummy, trigger_name, response_name = name.split("_")

                    trigger_event = rules_plane.subplanes[name].subplanes[trigger_name].get_updated_event()

                    response_event = rules_plane.subplanes[name].subplanes[response_name].get_updated_event()

                    self.host.add_response(trigger_event, response_event)

        self.window.display_logic.destroy()

        return

class PygameOSD:
    """A PygameOSD instance manages an on-screen display.

       Attributes:

       PygameOSD.caption_dict_dict
           A dict, mapping caption strings to a (dict, key) tuple.

       PygameOSD.offset
           A (x, y) tuple giving the rendering offset relative to (0, 0).
    """

    def __init__(self):
        """Initialise.
        """

        self.caption_dict_dict = {}

        self.offset = (0, 0)

        return

    def display(self, caption, dictionary, key):
        """Track the value of dictionary[key], and display it after caption.
        """

        self.caption_dict_dict[caption] = (dictionary, key)

        return

    def render(self, surface):
        """Render the OSD on the Pygame Surface given.
        """

        y = self.offset[1]

        for caption in self.caption_dict_dict.keys():

            dictionary, key = self.caption_dict_dict[caption]

            text = "{} {}".format(caption, dictionary[key])

            text_plane = clickndrag.gui.OutlinedText("osd",
                                                     text)

            surface.blit(text_plane.image, (self.offset[0], y))

            y = y + text_plane.rect.height

        return

    def remove(self, caption):
        """No longer display the item identified by caption.
        """

        del self.caption_dict_dict[caption]

        return

    def is_displaying(self, key):
        """Convenience method: return True if key is a key in PygameOSD.caption_dict_dict.
        """

        if key in self.caption_dict_dict.keys():

            return True

        else:
            return False
