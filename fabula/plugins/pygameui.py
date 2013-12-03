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

# TODO: Make blocking nature of SaysEvent more apparent, e.g. dimmed screen.
# TODO: Make screen resolution and tile size configurable
# TODO: always display and log full paths of saved or loaded files
# TODO: in PygameEditor, display all assets from local folder for visual editing
# TODO: Make PygameEditor Tkinter based, with multiple windows. Use planes.gui only for in-game-GUI.
# TODO: Ctrl+Q should not end the game, but open a generic menu for setup and quitting the game
# TODO: support three layers: background layer (for parallax scrolling etc.), main layer and overlay layer (for clouds, sunbeams etc.)
# TODO: actually honour input_dict["mouse"] == False, i.e. disable mouse

import fabula.plugins.ui
import pygame
import tkinter.filedialog
import tkinter.simpledialog
import datetime
import os
import planes.gui.lmr
import planes.gui.tmb
import surfacecatcher

# For cx_Freeze
#
import tkinter._fix
#
# Not present in Pygame 1.9.1
#
#import pygame._view

# Pixels per character, for width estimation of text renderings
#
PIX_PER_CHAR = 8

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

class EntityPlane(planes.Plane):
    """Subclass of Plane with an extended update() method that handles movement.

       Additional attributes:

       EntityPlane.position_list
           A list of movement steps as position tuples

       EntityPlane.spritesheet
           If not None, a Pygame Surface that contains a sprite sheet.

           The sheet is assumed to consist of 4 rows. The first column contains
           the static view of the Entity in front, left, back and right view
           (from the first row down). Rows are supposed to contain movement
           animation frames: the first row a downward movement in front view,
           the second row a movement to the left in left view etc.

           A row of movement animations will be played distributed over the
           course of UserInterface.action_time, which in turn is derived from
           a ServerParametersEvent.

           Frames are assumed to be of equal width and height.

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
        planes.Plane.__init__(self,
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
        planes.Plane.update(self)

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

       PygameEntity.assets["image/png"].data is supposed to be an instance of EntityPlane.

       Additional attributes:

       PygameEntity.spacing
           The spacing between tiles.

       PygameEntity.action_frames
           The number of frames per action.

       PygameEntity.caption_plane
           A planes.gui.Label with the caption for this PygameEntity.
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

        # TODO: blindly assuming "image/png"
        #
        if self.assets["image/png"].data.position_list:

            # Take the last queued position as current
            #
            current_x = self.assets["image/png"].data.position_list[-1][0]
            current_y = self.assets["image/png"].data.position_list[-1][1]

        else:
            # Reference point is the bottom center of the image, which is
            # positioned at the bottom center of the tile
            #
            current_x = self.assets["image/png"].data.rect.centerx
            current_y = self.assets["image/png"].data.rect.bottom

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

        self.assets["image/png"].data.position_list.extend(position_list)

        # Animation
        #
        if self.assets["image/png"].data.spritesheet is not None:

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

            width = self.assets["image/png"].data.spritesheet.get_width()

            offset = self.assets["image/png"].data.rect.width

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

            sprite_dimensions = self.assets["image/png"].data.rect.size

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

                        offset = self.assets["image/png"].data.rect.width

                    repeat_count = 0

            # Append neutral image as final
            #
            subsurface_rect_list.append(pygame.Rect((0, row * sprite_dimensions[1]),
                                                    sprite_dimensions))

            self.assets["image/png"].data.subsurface_rect_list.extend(subsurface_rect_list)

        return

    def process_ChangePropertyEvent(self, event):
        """Call base class and update caption changes.
        """

        # Call base class
        #
        fabula.Entity.process_ChangePropertyEvent(self, event)

        # TODO: blindly assuming "image/png"
        #
        if ("image/png" in self.assets.keys()
            and self.assets["image/png"].data is not None
            and event.property_key == "caption"):

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
                self.caption_plane = planes.gui.OutlinedText(self.identifier + "_caption",
                                                             event.property_value)

            self.display_caption()

        return

    def display_caption(self):
        """Position the caption Plane and make it a subplane of the room.
        """

        if self.caption_plane is not None:

            # TODO: blindly assuming "image/png"
            #
            fabula.LOGGER.debug("aligning caption to midtop of Entity plane: {}".format(self.assets["image/png"].data.rect.midtop))

            self.caption_plane.rect.center = self.assets["image/png"].data.rect.midtop

            # Sync movements to asset Plane
            #
            self.caption_plane.sync(self.assets["image/png"].data)

            # If we make the Label a subplane of the
            # Entity.assets["image/png"].data Plane, it will be cropped at the
            # width of Entity.assets["image/png"].data. This is not intended.
            # So we make it a subplane of window.room, which is the parent of
            # the asset.
            #
            self.assets["image/png"].data.parent.sub(self.caption_plane,
                                                     insert_after = self.assets["image/png"].data.name)

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

       PygameUserInterface.screensize
           A tuple (width, height), holding the size of the screen.

       PygameUserInterface.fullscreen
           A boolean flag whether to run in fullscreen or not.

       PygameUserInterface.spacing
           Spacing between tiles.

       PygameUserInterface.scroll
           Counter for scrolling left-right. Used in display_single_frame().

       PygameUserInterface.scroll_amount
           Number of pixels to scroll per call to display_single_frame().

       PygameUserInterface.fade_surface
           A black pygame surface for fade effects

       PygameUserInterface.attempt_icon_planes
           A list of Planes of attempt action icons.

       PygameUserInterface.right_clicked_entity
           Cache for the last right-clicked Entity.

       PygameUserInterface.osd
           An instance of PygameOSD. PygameOSD creates a Plane on screen which
           will be updated during the normal Plane.update() cycle.

       PygameUserInterface.stats
           A dict mapping names of different metrics to their current vaule.
           Updated in PygameUserInterface.update_frame_timer().

       PygameUserInterface.screen_dump_folder
           A string with the name of a local folder to save screen dumps to.
           This also acts as a flag: if it is different from the empty string,
           PygameUserInterface.display_single_frame() will save screen dumps
           there.

       PygameUserInterface.surfacecatcher
           An instance of surfacecatcher.SurfaceCatcher. Initially None.

       PygameUserInterface.mousescroll
           Boolen flag, indicating whether to scroll the screen when the mouse
           reaches a screen border.

       PygameUserInterface.keybindings
           A dict mapping instances of Pygame key constants to functions.
           Will be handled by
           PygameUserInterface.keybindings.collect_player_input().

       PygameUserInterface utilises the planes module for 2D bitmap rendering.
       The planes hierarchy is organised as follows:

       window +
              |
              + room +
              |      |
              |      + tiles +
              |      |       |
              |      |       + tile
              |      |       |
              |      |       + ...
              |      |
              |      + entity plane
              |      |
              |      + ...
              |
              + inventory

       The planes are attributes of PygameUserInterface:

       PygameUserInterface.window
           An instance of planes.Display. Initially None, will be created by
           PygameUserInterface._setup_display(). Dimensions are given by
           PygameUserInterface.screensize. By default opened in windowed mode,
           this can be changed by editing the file fabula.conf.

       PygameUserInterface.window.room
           planes Plane for the room. Initially it will have a size of 0x0 px.
           The final Plane is created by process_RoomCompleteEvent().

       PygameUserInterface.window.room.tiles
           planes Plane which has the Tile Planes as subplanes.

       PygameUserInterface.window.inventory
           planes Plane for the inventory. By default this is 800x100 px with
           space for 8 100x100 px icons and located at the bottom of the window.
    """

    def __init__(self, assets, framerate, host, mousescroll = False):
        """This method initialises the PygameUserInterface.

           assets must be an instance of fabula.Assets or a subclass.

           framerate must be an integer and sets the maximum (not minimum ;-))
           frames per second the client will run at.

           mousescroll is a Boolen flag, indicating whether to scroll the screen
           when the mouse reaches a screen border.
        """

        # TODO: remove mousescroll from init arguments.

        # Call original __init__()
        #
        fabula.plugins.ui.UserInterface.__init__(self,
                                                 assets,
                                                 framerate,
                                                 host)

        fabula.LOGGER.debug("called")

        fabula.LOGGER.debug("initialising pygame")

        pygame.init()

        # Statistics
        #
        self.stats = {"framerate" : self.framerate,
                      "fps" : None}

        # Initialise the frame timing clock.
        #
        self.clock = pygame.time.Clock()

        # Hardwired screen size.
        # Jakob Nielsen's [2012 recommendation](http://www.nngroup.com/articles/computer-screens-getting-bigger/)
        # is optimizing for 1440x768, but we leave some space by default.
        #
        self.screensize = (1024, 768)

        # Spacing between tiles.
        #
        self.spacing = 128

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

        self.fullscreen = False

        if fabula.CONFIGPARSER is not None and fabula.CONFIGPARSER.has_option("fabula", "fullscreen"):

            if fabula.CONFIGPARSER.get("fabula", "fullscreen").lower() in ("true", "yes", "1"):

                fabula.LOGGER.info("found fullscreen option in fabula.conf, going fullscreen")

                self.fullscreen = True

        # Will be created by _setup_display() called later
        #
        self.window = None

        # Will be created by _setup_display() called later
        #
        self.fade_surface = None

        # Create loading text surface to be used in process_EnterRoomEvent
        #
        self.loading_surface = planes.gui.FONTS.big_font.render("Loading, please wait...",
                                                                True,
                                                                (255, 255, 255))

        # Will be created by _setup_display() called later
        #
        self.inventory_plane = None

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

            # Create Rect - taken from above
            #
            rect = pygame.Rect((0, 0), surface.get_rect().size)

            # Create Plane
            #
            plane = planes.Plane(name,
                                 rect,
                                 left_click_callback = self.attempt_icon_callback)

            plane.image = surface

            self.attempt_icon_planes.append(plane)

            fabula.LOGGER.debug("loaded '{}': {}".format(name, plane))

        # Cache for the last right-clicked Entity
        #
        self.right_clicked_entity = None

        # Will be created by _setup_display() called later
        #
        self.osd = None

        # Stub for the screen recording directory
        #
        self.screen_dump_folder = ""

        self.surfacecatcher = None

        self.mousescroll = mousescroll

        self.keybindings = {}

        fabula.LOGGER.debug("complete")

        return

    def _setup_display(self):
        """Set up the planes Display, utilising PygameUserInterface.screensize and PygameUserInterface.fullscreen.
        """

        if self.window is None:

            fabula.LOGGER.info("No main window yet, creating")

            # Open a planes window.
            #
            self.window = planes.Display(self.screensize, self.fullscreen)

            # Create a black pygame surface for fade effects.
            #
            self.fade_surface = self.window.image.copy()

            # Create inventory plane.
            # TODO: Hardcoded dimensions
            #
            self.inventory_plane = planes.Plane("inventory",
                                                pygame.Rect((0, self.spacing * 5),
                                                            (self.screensize[0], self.spacing)),
                                                dropped_upon_callback = self.inventory_callback)

            self.inventory_plane.image.fill((64, 64, 64))

            # Copied from get_connection_details().
            # TODO: Again a reason for an image loading routine.
            #
            try:
                file = self.assets.fetch("inventory.png")

                surface = pygame.image.load(file)

                file.close()

                fabula.LOGGER.debug("using inventory.png")

                # Not using convert_alpha(), no RGBA support fo inventory.
                #
                self.inventory_plane.image = surface.convert()

            except:
                fabula.LOGGER.warning("inventory.png not found, no inventory background")

            # Convert already establishes planes to internal format suitable for
            # blitting.

            for plane in self.attempt_icon_planes:

                plane.image = plane.image.convert_alpha()

            # Create plane for the room.
            # This Plane is only there to collect subplanes and hence is initialised
            # with 0x0 pixels. The final Plane will be created by process_RoomCompleteEvent().
            #
            self.window.sub(planes.Plane("room",
                                         pygame.Rect((0, 0), (0, 0))))

            # Create a subplane as a sort-of buffer for Tiles.
            #
            self.window.room.sub(planes.Plane("tiles",
                                              pygame.Rect((0, 0), (0, 0))))

            # Initialise on screen display.
            #
            self.osd = PygameOSD(self.window)

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

        # TODO: Replace by Tkinter dialog box?
        #
        self._setup_display()

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

        container = planes.gui.tmb.TMBContainer("get_connection_details",
                                                    planes.gui.tmb.C_256_STYLE,
                                                    padding = 5)

        # Login name prompt
        #
        container.sub(planes.gui.Label("id_caption",
                                           "Login name:",
                                           pygame.Rect((0, 0),
                                                       (200, 30)),
                                           background_color = (128, 128, 128, 0)))

        container.sub(planes.gui.TextBox("identifier",
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

            container.sub(planes.gui.Label("connector_caption",
                                           "Server IP",
                                           pygame.Rect((0, 0),
                                                       (200, 30)),
                                           background_color = (128, 128, 128, 0)))

            container.sub(planes.gui.TextBox("connector",
                                             pygame.Rect((0, 0),
                                                         (200, 30)),
                                             return_callback = None))

            # Provide a default
            # TODO: remember older IPs somehow. Config file?
            #
            container.connector.text = "127.0.0.1"

            # Upon clicked, register the TextBox for keyboard input
            #
            container.connector.left_click_callback = lambda plane : self.window.key_sensitive(plane)

        # OK button
        #
        container.sub(planes.gui.lmr.LMRButton("OK",
                                                   50,
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

        # TODO: both clocks leave spikes of > 200 FPS through. Check if a custom implementation using time.time() (Unix) / time.clock() (MS Win) and time.sleep() is more reliable.
        #
        self.clock.tick(self.framerate)

        self.stats["fps"] = int(self.clock.get_fps())

        # Measue re-entry time
        #
        #interval = time.time() - self._timestamp
        #
        #if interval != 0:
        #
        #    fabula.LOGGER.critical("interval {:.2}, {} FPS".format(interval,
        #                                                        int(1 / interval)))
        #
        #self._timestamp = time.time()

        return

    def display_single_frame(self):
        """Update and render all planes.
           This method also handles scrolling.
        """

        # TODO: Catch some statistics. See also update_frame_timer().

        # To have an effect, this must be the first thing to be called in the
        # loop.
        #
        self.update_frame_timer()

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

            # TODO: replace with update(dirty_rect_list)
            #
            pygame.display.flip()

            # Screen dump recording
            #
            if self.screen_dump_folder:

                self.surfacecatcher.catch(self.window.display)

        # Pump the Pygame Event Queue
        #
        pygame.event.pump()

        return

    def collect_player_input(self):
        """Gather Pygame events, scan for QUIT or special keys and let the planes Display evaluate the events.

           This method will evaluate key bindings defined in the
           PygameUserInterface.keybindings dict which maps Pygame key constants
           to functions to be called when a key is pressed.
        """

        # TODO: The UserInterface should only ever collect and send one single client event to prevent cheating and blocking other clients in the server. (hint by Alexander Marbach)

        # Check mouse position, and trigger window scrolling.
        # Also check whether the display window has the focus.
        # Scrolling will be done in display_single_frame().
        #
        if self.mousescroll and not self.scroll:

            mouse_position = pygame.mouse.get_pos()

            if (pygame.mouse.get_focused()
                and 0 <= mouse_position[0] <= 25
                and self.window.room.rect.left < 0):

                # Scroll to the left
                #
                self.scroll = self.spacing

            elif (pygame.mouse.get_focused()
                  and self.screensize[0] - 25 <= mouse_position[0] <= self.screensize[0]
                  and self.window.room.rect.right > self.screensize[0]):

                # Scroll to right
                #
                self.scroll = 0 - self.spacing

        # Handle events
        #
        events = pygame.event.get()

        for event in events:

            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN
                                             and event.key == pygame.K_q
                                             and pygame.key.get_mods() & pygame.KMOD_CTRL):

                fabula.LOGGER.info("exit request from user")
                self.exit_requested = True

                if self.screen_dump_folder:

                    fabula.LOGGER.info("stopping recording screen dumps")

                    self.screen_dump_folder = ""

                    self.surfacecatcher.stop()
                    self.surfacecatcher = None

                # Quit pygame here, though there is still shutdown work to be
                # done Client and ClientInterface.
                #
                pygame.quit()

            elif (event.type == pygame.KEYDOWN
                  and event.key == pygame.K_F1):

                if "FPS: " in self.osd.caption_list:

                    self.osd.remove("Framerate: ")
                    self.osd.remove("FPS: ")

                    # Tie recording display to FPS display
                    #
                    if "Screen recorder: " in self.osd.caption_list:

                        self.osd.remove("Screen recorder: ")

                else:
                    self.osd.display("Framerate: ", self.stats, "framerate")
                    self.osd.display("FPS: ", self.stats, "fps")

                    if self.screen_dump_folder:

                        self.osd.display("Screen recorder: ",
                                         {"state" : "running"},
                                         "state")

            elif (event.type == pygame.KEYDOWN
                  and event.key == pygame.K_F2):

                if self.screen_dump_folder:

                    fabula.LOGGER.info("stopping recording screen dumps")

                    self.screen_dump_folder = ""

                    self.surfacecatcher.stop()
                    self.surfacecatcher = None

                else:
                    self.screen_dump_folder = "{}-{}".format(datetime.date.today(),
                                                             os.getpid())

                    msg = "starting to record screen dumps to folder '{}'"

                    fabula.LOGGER.info(msg.format(self.screen_dump_folder))

                    if not os.path.exists(self.screen_dump_folder):

                        os.mkdir(self.screen_dump_folder)

                    self.surfacecatcher = surfacecatcher.SurfaceCatcher(self.screen_dump_folder)

                    # Rest will be handled by display_single_frame()

            elif (self.host.room is not None
                  and self.input_dict["keyboard"]
                  and event.type == pygame.KEYDOWN
                  and event.key in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d)):

                fabula.LOGGER.debug("got key '{}' from user, returning TriesToMoveToEvent".format(event.key))

                surrounding_positions = fabula.surrounding_positions(self.host.room.entity_locations[self.host.client_id])

                event = fabula.TriesToMoveEvent(self.host.client_id,
                                                {pygame.K_w : surrounding_positions[1],
                                                 pygame.K_d : surrounding_positions[3],
                                                 pygame.K_s : surrounding_positions[5],
                                                 pygame.K_a : surrounding_positions[7],
                                                 }[event.key])

                # TODO: Adding Events to self.message_for_host is weird. This should be returned instead in some way, shouldn't it?
                #
                self.message_for_host.event_list.append(event)

            elif (self.keybindings
                  and event.type == pygame.KEYDOWN
                  and event.key in self.keybindings.keys()):

                fabula.LOGGER.debug("Key '{}' pressed, calling function from keybindings".format(event.key))

                self.keybindings[event.key]()

        self.window.process(events)

        return

    ####################
    # Event handlers affecting presentation and management

    def process_EnterRoomEvent(self, event):
        """Fade window to black and remove subplanes of PygameUserInterface.window.room.
        """

        fabula.LOGGER.info("entering room: {}".format(event.room_identifier))

        self._setup_display()

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

        # But clear all tiles nonetheless.
        #
        for plane_name in list(self.window.room.tiles.subplanes_list):

            self.window.room.tiles.remove(plane_name)

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
        room_plane = planes.Plane("room",
                                  pygame.Rect((0, 0),
                                              ((max_right + 1) * self.spacing,
                                               (max_bottom + 1) * self.spacing)))

        room_plane.sub(planes.Plane("tiles",
                                    pygame.Rect((0, 0),
                                                room_plane.rect.size)))

        # As these have no background, delete their implicitly
        # created image to save blitting time.
        #
        room_plane.del_image()

        room_plane.tiles.del_image()
        
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
            fabula.LOGGER.info("attempting to center room view on player")

            player_position = list(self.host.room.entity_locations[self.host.client_id])

            # Convert to pixels, refering to the center of the tile
            #
            player_position[0] = int((player_position[0] + 0.5) * self.spacing)
            player_position[1] = int((player_position[1] + 0.5) * self.spacing)

            self.window.room.rect.left = 0 - player_position[0] + (self.screensize[0] / 2)
            self.window.room.rect.top =  0 - player_position[1] + (self.screensize[1] / 2)

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
        """Have the user select or input text and return a SaysEvent to the host.
        """

        # If it's not for us, ignore.
        #
        if event.identifier == self.host.client_id:

            if event.sentences:

                callback = lambda option: self.message_for_host.event_list.append(fabula.SaysEvent(self.host.client_id, option.text))

                option_list = planes.gui.tmb.TMBOptionSelector("select_sentence",
                                                               event.sentences,
                                                               callback,
                                                               style = planes.gui.tmb.C_512_STYLE)

                option_list.rect.center = self.window.rect.center

                self.window.sub(option_list)

            else:
                callback = lambda text: self.message_for_host.event_list.append(fabula.SaysEvent(self.host.client_id, text))

                dialog = planes.gui.tmb.TMBGetStringDialog("You say:",
                                                           callback,
                                                           self.window)

                dialog.rect.center = self.window.rect.center

                self.window.sub(dialog)

        return


    def process_SpawnEvent(self, event):
        """Add a subplane to window.room, possibly fetching an asset before.

           The name of the subplane is the Entity identifier, so the subplane
           is accessible using window.room.<identifier>.

           Entity.assets["image/png"].data points to the Plane of the Entity.

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
        # TODO: blindly assuming "image/png"
        #
        if ("image/png" in event.entity.assets.keys()
            and event.entity.assets["image/png"].data is not None):

            msg = "Entity '{}' already has an asset, updating position to {}"
            fabula.LOGGER.info(msg.format(event.entity.identifier,
                                         event.location))

            x = event.location[0] * self.spacing + self.spacing / 2
            y = event.location[1] * self.spacing + self.spacing

            event.entity.assets["image/png"].data.rect.centerx = x
            event.entity.assets["image/png"].data.rect.bottom = y

            # Restore callback
            #
            event.entity.assets["image/png"].data.dropped_upon_callback = self.entity_dropped_callback

        else:
            fabula.LOGGER.info("no asset for Entity '{}', attempting to fetch".format(event.entity.identifier))

            # Assets are entirely up to the UserInterface, so we fetch the asset
            # here
            #
            try:
                # Get a file-like object from asset manager
                #
                file = self.assets.fetch(event.entity.assets["image/png"].uri)

            except:
                self.display_asset_exception(event.entity.assets["image/png"].uri)

            self.display_loading_progress(event.entity.assets["image/png"].uri)

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

            if "fabulasheet" in event.entity.assets["image/png"].uri:

                msg = "sprite sheet detected for Entity '{}', asset '{}'"

                fabula.LOGGER.debug(msg.format(event.entity.identifier,
                                               event.entity.assets["image/png"].uri))

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
                try:
                    surface = spritesheet.subsurface(pygame.Rect((0, 0),
                                                                 (sprite_height,
                                                                  sprite_height)))

                except ValueError:

                    msg = "Error: could not create subsurface from spritesheet"

                    fabula.LOGGER.critical(msg)

                    raise RuntimeError(msg)

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
            event.entity.assets["image/png"].data = plane

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
        fabula.LOGGER.info("adding '{}' to window.room".format(event.entity.assets["image/png"].data.name))
        self.window.room.sub(event.entity.assets["image/png"].data)

        # If the PygameEntity has a caption Plane, add it as well.
        #
        event.entity.display_caption()

        # Finally - this may be a draggable item.
        # Check only when we are not in the middle of establishing a Room.
        #
        if self.freeze == False:

            self.make_items_draggable()

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
           Tile.assets["image/png"].data is the Pygame Surface since possibly
           multiple Planes must be derived from a single Tile.
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
            raise RuntimeError("could not find tile {} in tile_list of room '{}'".format(event.tile, self.host.room.identifier))

        # TODO: blindly assuming "image/png"
        #
        if ("image/png" in tile_from_list.assets.keys()
            and tile_from_list.assets["image/png"].data is not None):

            fabula.LOGGER.debug("tile already has an asset: {}".format(tile_from_list))

        else:
            # Assets are entirely up to the UserInterface, so we fetch
            # the asset here
            #
            fabula.LOGGER.debug("no asset for {}, attempting to fetch".format(tile_from_list))

            try:
                # Get a file-like object from asset manager
                #
                file = self.assets.fetch(tile_from_list.assets["image/png"].uri)

            except:
                self.display_asset_exception(tile_from_list.assets["image/png"].uri)

            self.display_loading_progress(tile_from_list.assets["image/png"].uri)

            fabula.LOGGER.debug("loading Surface from {}".format(file))

            surface = pygame.image.load(file)

            file.close()

            # Convert to internal format suitable for blitting
            #
            surface = surface.convert_alpha()

            tile_from_list.assets["image/png"].data = surface

        # Now tile_from_list.assets["image/png"].data is present

        # Do we already have a tile there?
        # Tiles are planes subplanes of self.window.room, indexed by their
        # location as string representation.
        #
        if str(event.location) not in self.window.room.tiles.subplanes:

            tile_plane = planes.Plane(str(event.location),
                                      pygame.Rect((event.location[0] * self.spacing,
                                                   event.location[1] * self.spacing),
                                                  (100, 100)),
                                      left_click_callback = self.tile_clicked_callback,
                                      dropped_upon_callback = self.tile_drop_callback)

            self.window.room.tiles.sub(tile_plane)

        # Update image regardless whether the tile existed or not
        #
        fabula.LOGGER.debug("changing image for tile at {0} to {1}".format(str(event.location),
                                                                           tile_from_list.assets["image/png"].data))

        self.window.room.tiles.subplanes[str(event.location)].image = tile_from_list.assets["image/png"].data

        return

    def process_PerceptionEvent(self, event):
        """Display the perception.
        """

        fabula.LOGGER.debug("called")

        # If it's not for us, ignore.
        # TODO: checking for client_id should be everywhere and be more structured
        #
        if event.identifier == self.host.client_id:

            # Choose container width depending on text length
            # Copied from process_SaysEvent().
            #
            container_style = planes.gui.tmb.C_256_STYLE

            if len(event.perception) * PIX_PER_CHAR > 200:

                container_style = planes.gui.tmb.C_512_STYLE

            perception_box = planes.gui.tmb.TMBFadingContainer("perception",
                                                                   self._chars_to_frames(event.perception),
                                                                   self.action_frames,
                                                                   style = container_style)
            lines = event.perception.split("\n")

            for line_no in range(len(lines)):

                perception_box.sub(planes.gui.Label("perception_line_{0}".format(line_no),
                                   lines[line_no],
                                   pygame.Rect((0, 0), (512, 30)),
                                   background_color = (128, 128, 128, 0)))

            perception_box.rect.centerx = self.window.rect.centerx

            # Stay away from the window center
            #
            perception_box.rect.centery = int(self.window.rect.height / 5)

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

            # Flash very short...
            #
            frames = int(self.action_frames / 10)

            # ...but make sure it flashes
            #
            if frames < 1:
                frames = 1

            flash_plane = planes.Plane("flash",
                                       pygame.Rect((0, 0),
                                                   self.window.rect.size))

            flash_plane.image.fill((250, 250, 250))

            self.window.sub(flash_plane)

            while frames:
                self.display_single_frame()
                frames = frames - 1

            # Mark Entity Plane as changed to trigger redraw of the room
            #
            #self.window.room.subplanes[event.identifier].last_rect = None

            self.window.remove(flash_plane)
            
            self.display_single_frame()

        return

    ####################
    # Event handlers affecting Entities

    def process_MovesToEvent(self, event):
        """Call the base class method, re-order EntityPlanes and make EntityPlanes surrounding a new player position draggable.
        """

        fabula.LOGGER.debug("called")

        # Call base class.
        # This will forward the Event to the affected Entity.
        #
        fabula.plugins.ui.UserInterface.process_MovesToEvent(self, event)

        # Care for overlapping
        #
        self.reorder_room_planes()

        # And if it is the player...
        #
        if event.identifier == self.host.client_id:

            # Care for draggability
            #
            self.make_items_draggable()

            # Check whether the player has moved one Tile away or closer from
            # the window border, and if so, initiate scrolling.
            # Actual scrolling will be done in display_single_frame().
            #
            if not self.scroll:

                left_border_x = int((0 - self.window.room.rect.left) / self.spacing)

                right_border_x = left_border_x + int(self.screensize[0] / self.spacing) - 1

                if (event.location[0] <= left_border_x + 1
                    and self.window.room.rect.left < 0):

                    # Scroll to the left
                    #
                    self.scroll = self.spacing

                elif (event.location[0] >= right_border_x - 1
                      and self.window.room.rect.right > self.screensize[0]):

                    # Scroll to the right
                    #
                    self.scroll = 0 - self.spacing

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

        # TODO: blindly assuming "image/png"
        #
        if ("image/png" in entity.assets.keys()
            and entity.assets["image/png"].data is not None
            and event.property_key == "caption"
            and not event.identifier + "_caption" in self.window.room.subplanes_list):

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
        # This will forward the event to the Entity.
        #
        fabula.plugins.ui.UserInterface.process_SaysEvent(self, event)

        says_box = None

        # Choose mode of presentation by text length
        # TODO: threshold should be configurable somewhere
        #
        if len(event.text) <= 10:

            # Small container
            #
            says_box = planes.gui.tmb.TMBContainer("{}_says".format(event.identifier),
                                                   planes.gui.tmb.C_256_STYLE)

            says_box.sub(planes.gui.Label("text",
                                          event.text,
                                          pygame.Rect((0, 0),
                                                      (len(event.text) * PIX_PER_CHAR, 30)),
                                          background_color = (128, 128, 128, 0)))

            # Display above Entity
            # TODO: blindly assuming "image/png"
            #
            entity_rect = self.host.room.entity_dict[event.identifier].assets["image/png"].data.rect

            # Lower a bit, to make sure to touch the Entity.
            #
            says_box.rect.midbottom = (entity_rect.centerx,
                                       entity_rect.top + 10)

            # Make sure it's completely visible
            #
            says_box.rect.clamp_ip(pygame.Rect((0, 0), self.window.rect.size))

            # To actually align with the Entity coordinates, this must be a
            # subplane of the room.
            #
            self.window.room.sub(says_box)

        else:
            # Large container
            #
            says_box = planes.gui.tmb.TMBContainer("{}_says".format(event.identifier),
                                                   planes.gui.tmb.C_512_STYLE)

            # Additional speaker string
            #
            speaker_str = "{}:".format(event.identifier)

            says_box.sub(planes.gui.Label("speaker",
                                          speaker_str,
                                          pygame.Rect((0, 0),
                                                      (len(speaker_str) * PIX_PER_CHAR, 30)),
                                          background_color = (128, 128, 128, 0)))

            says_box.sub(planes.gui.Label("text",
                                          event.text,
                                          pygame.Rect((0, 0),
                                                      (len(event.text) * PIX_PER_CHAR, 30)),
                                          background_color = (128, 128, 128, 0)))

            # Display at the bottom of the screen
            #
            says_box.rect.midbottom = (self.window.rect.centerx,
                                       self.window.rect.bottom - self.inventory_plane.rect.height)

            # This is just being put in the window, on top.
            #
            self.window.sub(says_box)

        first_part = int(self._chars_to_frames(event.text) * 0.95)
        second_part = self._chars_to_frames(event.text) - first_part

        # The first can be closed on ESC
        #
        while first_part:

            self.display_single_frame()

            if pygame.key.get_pressed()[pygame.K_ESCAPE]:

                first_part = 0

            else:

                first_part -= 1

        # The second half can not be canceled
        #
        while second_part:

            self.display_single_frame()

            second_part -= 1

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

        # NOTE: there might be a difference in what self.host.room.entity_dict
        # and self.window.room.subplanes think is in the current room, e.g.
        # when we are in the middle of a transition, as self.host.room is
        # managed in the Engine, and self.window.room here.
        #
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

            if name.split("_caption")[0] in entities:

                entities.insert(entities.index(name.split("_caption")[0]) + 1, name)

            else:

                msg = "Entity '{}' not found in Room, not inserting caption plane '{}'"

                fabula.LOGGER.warning(msg.format(name.split("_caption")[0], name))

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

            fabula.LOGGER.warning("'{}' already in Rack, skipping".format(item_identifier))

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

        target_identifier = None

        if plane.name in self.host.room.entity_dict.keys():

            # Although we know the Entity, the server determines what if being
            # looked at. So send target identifiers instead of Entity
            # identifiers.
            #
            target_identifier = self.host.room.entity_locations[plane.name]

        elif plane.name in self.host.rack.entity_dict.keys():

            host_plane = self.inventory_plane

            # Use the identifier, as the Rack has no location
            #
            target_identifier = plane.name

        else:

            fabula.LOGGER.error("Entity '{}' neither in rack nor room".format(plane.name))

            raise RuntimeError("Entity '{}' neither in rack nor room".format(plane.name))

        event = fabula.TriesToDropEvent(self.host.client_id,
                                        dropped_plane.name,
                                        target_identifier)

        self.message_for_host.event_list.append(event)

        return

    def entity_right_click_callback(self, plane):
        """Right click callback for Entity Plane.
        """

        fabula.LOGGER.debug("called")

        host_plane = None

        if plane.name in self.host.room.entity_dict.keys():

            host_plane = self.window.room

            # Save Entity
            #
            self.right_clicked_entity = self.host.room.entity_dict[plane.name]

        elif plane.name in self.host.rack.entity_dict.keys():

            host_plane = self.inventory_plane

            # Save Entity
            #
            self.right_clicked_entity = self.host.rack.entity_dict[plane.name]

        else:

            fabula.LOGGER.error("No Entity named '{}' in rack or room".format(plane.name))

            raise RuntimeError("No Entity named '{}' in rack or room".format(plane.name))

        # One
        #
        icon_plane = self.attempt_icon_planes[0]

        icon_plane.rect.center = (plane.rect.center[0] - 35,
                                  plane.rect.center[1])

        # Sync position to Entity plane
        #
        icon_plane.sync(plane)

        # This will remove and re-add the Plane to room.
        # <3 planes :-)
        #
        host_plane.sub(icon_plane)

        # Two
        #
        icon_plane = self.attempt_icon_planes[1]

        icon_plane.rect.center = (plane.rect.center[0] + 35,
                                  plane.rect.center[1])

        icon_plane.sync(plane)

        host_plane.sub(icon_plane)

        # Three
        #
        icon_plane = self.attempt_icon_planes[2]

        icon_plane.rect.center = (plane.rect.center[0],
                                  plane.rect.center[1] - 35)

        icon_plane.sync(plane)

        host_plane.sub(icon_plane)

        # Four
        #
        icon_plane = self.attempt_icon_planes[3]

        icon_plane.rect.center = (plane.rect.center[0],
                                  plane.rect.center[1] + 35)

        icon_plane.sync(plane)

        host_plane.sub(icon_plane)

        return

    def attempt_icon_callback(self, plane):
        """General left-click callback for attempt action icons.
        """

        fabula.LOGGER.debug("called")

        host_plane = None

        event = None

        target_identifier = None

        if self.right_clicked_entity.identifier in self.host.room.entity_dict.keys():

            host_plane = self.window.room

            # Although we know the Entity, the server determines what if being
            # looked at. So send target identifiers instead of Entity
            # identifiers.
            #
            target_identifier = self.host.room.entity_locations[self.right_clicked_entity.identifier]

        elif self.right_clicked_entity.identifier in self.host.rack.entity_dict.keys():

            host_plane = self.inventory_plane

            # Use the identifier, as the Rack has no location
            #
            target_identifier = self.right_clicked_entity.identifier

        else:

            fabula.LOGGER.error("Cached right click Entity '{}' neither in rack nor room".format(self.right_clicked_entity.identifier))

            raise RuntimeError("Cached right click Entity '{}' neither in rack nor room".format(self.right_clicked_entity.identifier))

        if plane.name == "attempt_manipulate":

            event = fabula.TriesToManipulateEvent(self.host.client_id,
                                                  target_identifier)

        elif plane.name == "attempt_talk_to":

            event = fabula.TriesToTalkToEvent(self.host.client_id,
                                              target_identifier)

        elif plane.name == "attempt_look_at":

            event = fabula.TriesToLookAtEvent(self.host.client_id,
                                              target_identifier)

        # Remove icons in any case. This also works if the "cancel" icon was
        # clicked.
        #
        for icon_plane in self.attempt_icon_planes:

            host_plane.remove(icon_plane)

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

            # Center for easy overwriting of Surfaces
            #
            displaystring = str(obj).center(128)

            surface = planes.gui.FONTS.small_font.render(displaystring,
                                                         True,
                                                         (127, 127, 127),
                                                         (0, 0, 0))

            self.window.display.blit(surface, (self.window.rect.width / 2 - surface.get_rect().width / 2,
                                               500))

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

                # Catch a common error.
                # TODO: Why does this happen?
                # TODO: blindly assuming "image/png"
                #
                if ("image/png" in entity.assets.keys()
                    and entity.assets["image/png"].data is None):

                    msg = "asset of Entity '{}' is None, cannot change draggable flag: {}"

                    fabula.LOGGER.warning(msg.format(entity.identifier, entity))

                else:

                    if entity.entity_type == fabula.ITEM and entity.mobile:

                            if self.host.room.entity_locations[identifier] in surrounding_positions:

                                entity.assets["image/png"].data.draggable = True

                            else:
                                entity.assets["image/png"].data.draggable = False

                    else:
                        # Make sure it's not draggable
                        #
                        entity.assets["image/png"].data.draggable = False

        else:
            fabula.LOGGER.warning("'{}' not found in room, items are not made draggable".format(self.host.client_id))

        return

    def _snap_room_to_display(self):
        """Snap the room plane to the window plane.
        """

        if self.window.room.rect.left > 0:

            fabula.LOGGER.debug("snapping window.room.rect.left from {} to 0".format(self.window.room.rect.left))

            self.window.room.rect.left = 0

        if self.window.room.rect.top > 0:

            fabula.LOGGER.debug("snapping window.room.rect.top from {} to 0".format(self.window.room.rect.top))

            self.window.room.rect.top = 0

        if self.window.room.rect.right < self.screensize[0]:

            fabula.LOGGER.debug("snapping window.room.rect.right from {} to {}".format(self.window.room.rect.right,
                                                                                       self.screensize[0]))

            self.window.room.rect.right = self.screensize[0]

        # Mind the inventory
        #
        if self.window.room.rect.bottom < self.screensize[1] - self.window.inventory.rect.height:

            fabula.LOGGER.debug("snapping window.room.rect.bottom")

            self.window.room.rect.bottom = self.screensize[1] - self.window.inventory.rect.height

        return

    def _chars_to_frames(self, characters):
        """Auxiliary method to compute how many frames to display a string.
           characters is the string to display.
        """

        # Display for (action_time / 7) per character, but at least for
        # 2.5 * action_time
        #
        frames = int(self.action_frames / 7 * len(characters))

        if frames < 2.5 * self.action_frames:

            frames = int(2.5 * self.action_frames)

        return frames

class EventEditor(planes.gui.Container):
    """A planes Container that implements an editor for Fabula Events.

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
        planes.gui.Container.__init__(self,
                                          str(id(event)),
                                          padding = 5,
                                          background_color = (128, 128, 128, 0))

        # Title
        #
        self.sub(planes.gui.Label("title",
                                      event.__class__.__name__,
                                      pygame.Rect((0, 0), (300, 25)),
                                      background_color = planes.gui.HIGHLIGHT_COLOR))

        # Show Event attributes

        # Keep order
        #
        keys = list(event.__dict__.keys())
        keys.sort()

        for key in keys:

            key_label = planes.gui.Label("key_{}".format(key),
                                             "{}:".format(key),
                                             pygame.Rect((0, 0), (150, 25)),
                                             background_color = (64, 64, 64, 0),
                                             text_color = (250, 250, 250))

            value_textbox = planes.gui.TextBox("value_{}".format(key),
                                                   pygame.Rect((key_label.rect.width, 0),
                                                               (150, 25)))

            value_textbox.text = str(event.__dict__[key])

            # Upon clicked, register the TextBox for keyboard input
            #
            value_textbox.left_click_callback = lambda plane : display.key_sensitive(plane)

            key_value = planes.Plane("keyvalue_{}".format(key),
                                         pygame.Rect((0, 0),
                                                     (300, 25)))

            # Make Plane transparent
            #
            key_value.image = pygame.Surface(key_value.rect.size,
                                             flags = pygame.SRCALPHA)

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

       PygameEditor.window.buttons
           planes Plane for the buttons, 100x600px and located at the left
           border of the window.

       PygameEditor.window.properties
           planes Plane for Entity properties, 100x600px and located at the
           right border of the window.

       PygameEditor.plane_cache
           A list to cache temporarily invisible planes

       PygameEditor.overlay_surface
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
        self.spacing += 1

        # Setup a cache for planes
        #
        self.plane_cache = []

        # Create planes Display
        #
        self._setup_display()

        # Set window name
        #
        pygame.display.set_caption("Fabula Editor")

        # Create a semi-transparent red Surface to be used as an OBSTACLE
        # indicator overlay
        #
        self.overlay_surface = pygame.Surface((self.spacing, self.spacing))
        self.overlay_surface.fill((255, 0, 0))
        self.overlay_surface.set_alpha(127)

        # Add the inventory plane created in PygameUserInterface.__init__()
        #
        self.window.sub(self.inventory_plane)

        # Create Container for the editor buttons.
        #
        container = planes.gui.Container("buttons",
                                         padding = 4,
                                         background_color = (64, 64, 64))
        self.window.sub(container)

        # Add buttons

        room = planes.gui.Container("room",
                                    padding = 4,
                                    background_color = (64, 64, 64))

        room.sub(planes.gui.Label("title",
                                  "Room",
                                  pygame.Rect((0, 0),
                                              (80, 25)),
                                  background_color = (64, 64, 64),
                                  text_color = (250, 250, 250)))

        room.sub(planes.gui.Button("Load Room",
                                   pygame.Rect((0, 0), (80, 25)),
                                   self.load_room))

        room.sub(planes.gui.Button("Save Room",
                                   pygame.Rect((0, 0), (80, 25)),
                                   self.save_room))

        room.sub(planes.gui.Button("Add Entity",
                                   pygame.Rect((0, 0), (80, 25)),
                                   lambda plane: self.edit_entity_attributes(self.add_entity)))

        room.sub(planes.gui.Button("Edit Walls",
                                   pygame.Rect((0, 0), (80, 25)),
                                   self.edit_walls))

        background = planes.gui.Container("background",
                                          padding = 4,
                                          background_color = (64, 64, 64))

        background.sub(planes.gui.Label("title",
                                        "Background",
                                        pygame.Rect((0, 0),
                                                    (80, 25)),
                                        background_color = (64, 64, 64),
                                        text_color = (250, 250, 250)))

        background.sub(planes.gui.Button("Open Image",
                                         pygame.Rect((0, 0), (80, 25)),
                                         self.open_image))

        logic = planes.gui.Container("logic",
                                     padding = 4,
                                     background_color = (64, 64, 64))

        logic.sub(planes.gui.Label("title",
                                   "Logic",
                                   pygame.Rect((0, 0),
                                               (80, 25)),
                                   background_color = (64, 64, 64),
                                   text_color = (250, 250, 250)))

        logic.sub(planes.gui.Button("Save Logic",
                                    pygame.Rect((0, 0), (80, 25)),
                                    lambda plane : self.host.save_condition_response_dict("default.logic")))

        logic.sub(planes.gui.Button("Load Logic",
                                    pygame.Rect((0, 0), (80, 25)),
                                    lambda plane: self.host.load_condition_response_dict("default.logic")))

        logic.sub(planes.gui.Button("Clear Logic",
                                    pygame.Rect((0, 0), (80, 25)),
                                    lambda plane: self.host.clear_condition_response_dict()))

        self.window.buttons.sub(room)
        self.window.buttons.sub(background)
        self.window.buttons.sub(logic)

        self.window.buttons.sub(planes.gui.Button("Quit",
                                                  pygame.Rect((0, 0), (80, 25)),
                                                  self.quit))

        # Create Container for the properties
        #
        container = planes.gui.Container("properties",
                                         padding = 5,
                                         background_color = (64, 64, 64))

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

            # TODO: hardcoded spacing, assuming 1 was added
            #
            spacing = self.spacing - 1

            image_width, image_height = new_image.get_size()

            msg = "original dimensions of loaded image: {}x{}"

            fabula.LOGGER.debug(msg.format(image_width, image_height))

            # Get width and height that are multiples of self.spacing
            #
            fitted_width = int(image_width / spacing) * spacing

            if image_width % spacing:

                # Add a whole spacing unit to catch the leftover pixels
                #
                fitted_width = fitted_width + spacing

                fabula.LOGGER.debug("width does not fit spacing, adding {}px".format(spacing))

            fitted_height = int(image_height / spacing) * spacing

            if image_height % spacing:

                # Add a whole spacing unit to catch the leftover pixels
                #
                fitted_height = fitted_height + spacing

                fabula.LOGGER.debug("height does not fit spacing, adding {}px".format(spacing))

            # Create a new Surface with the new size, and blit the image on it
            #
            fitted_surface = pygame.Surface((fitted_width, fitted_height))

            fitted_surface.blit(new_image, (0, 0))

            fabula.LOGGER.debug("dimensions of fitted image: {}x{}".format(fitted_width,
                                                                           fitted_height))

            # We have to re-enter the current room for the UI to display the
            # Tiles properly.
            self.host.message_for_host.event_list.append(fabula.EnterRoomEvent(self.host.client_id,
                                                                               self.host.room.identifier))

            for x in range(int(fitted_width / spacing)):

                for y in range(int(fitted_height / spacing)):

                    # Cave: dummy asset description
                    # Create new Tile and sent it to Server
                    #
                    tile = fabula.Tile(fabula.FLOOR,
                                       {"image/png": fabula.Asset("dummy asset for ({}, {})".format(x, y))})

                    rect = pygame.Rect((x * spacing, y * spacing),
                                       (spacing, spacing))

                    # TODO: blindly assuming "image/png"
                    #
                    tile.assets["image/png"].data = fitted_surface.subsurface(rect)

                    event = fabula.ChangeMapElementEvent(tile, (x, y, self.host.room.identifier))

                    self.host.message_for_host.event_list.append(event)

            # Respawn current Entities. To achieve that, we recreate the room
            # and filter out all ChangeMapElementEvents.
            #
            self.host.message_for_host.event_list.extend([event for event in self.host.host._generate_room_rack_events(self.host.room.identifier) if not isinstance(event, fabula.ChangeMapElementEvent)])

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
            fabula.LOGGER.info("save to: '{}'".format(filename))

            # NOTE: Using filename as new room identifier
            #
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
                    pygame.image.save(self.window.room.tiles.subplanes[str((x, y, self.host.room.identifier))].image,
                                      os.path.join(path, current_file))

                    # Send renamed Tile to Server
                    # TODO: blindly assuming "image/png"
                    #
                    tile = fabula.Tile(self.host.room.floor_plan[(x, y)].tile.tile_type,
                                       {"image/png": fabula.Asset(current_file)})

                    # NOTE: Using filename as new room identifier
                    #
                    event = fabula.ChangeMapElementEvent(tile, (x, y, filename))

                    self.host.message_for_host.event_list.append(event)

                    # Save tile in floorplan file

                    entities_string = ""

                    # NOTE: enclosing saved strings in quotes, to be compatible with spreadsheet applications.

                    for entity in self.host.room.floor_plan[(x, y)].entities:

                        # TODO: make sure commas are not present in the other strings
                        # TODO: blindly assuming "image/png"
                        #
                        argument_list = ",".join([entity.identifier,
                                                  entity.entity_type,
                                                  repr(entity.blocking),
                                                  repr(entity.mobile),
                                                  entity.assets["image/png"].uri])

                        entities_string = entities_string + '\t"{}"'.format(argument_list)

                    roomfile.write('"{}"\t"{}, {}"{}\n'.format(repr((x, y)),
                                                                 tile.tile_type,
                                                                 tile.assets["image/png"].uri,
                                                                 entities_string))

            roomfile.close()

            fabula.LOGGER.info("wrote '{}'".format(filename + ".floorplan"))

            # Then respawn all current Entities in the Server since
            # EnterRoomEvent will set up a new room
            #
            for event in self.host.host._generate_room_rack_events(self.host.room.identifier):

                if not isinstance(event, fabula.ChangeMapElementEvent):

                    if ("location" in event.__dict__.keys()
                        and len(event.location) == 3):

                        event.location = (event.location[0],
                                          event.location[1],
                                          filename)

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
            option_list = planes.gui.OptionSelector("select_room",
                                                        room_list,
                                                        self.host.send_room_events,
                                                        background_color = (64, 64, 64))

            option_list.rect.center = self.window.rect.center

            self.window.sub(option_list)

        else:
            fabula.LOGGER.warning("no floorplan files found in '{}'".format(os.getcwd()))

            self.window.sub(planes.gui.OkBox("No room files in current directory."))

        return

    def edit_entity_attributes(self, callback, entity = None):
        """Open an editor to enter or edit Entity properties.
           callback will be attached to the OK button.
        """

        # TODO: edit asset description / select image

        fabula.LOGGER.debug("called")

        container = planes.gui.Container("get_entity_attributes",
                                             padding = 5,
                                             background_color = (64, 64, 64))

        # Identifier
        #
        container.sub(planes.gui.Label("id_caption",
                                           "Identifier:",
                                           pygame.Rect((0, 0),
                                                            (200, 30)),
                                           background_color = (64, 64, 64),
                                           text_color = (250, 250, 250)))

        if entity is not None:

            # Shouldn't change identifier of a live Entity
            #
            container.sub(planes.gui.Label("identifier",
                                               entity.identifier,
                                               pygame.Rect((0, 0),
                                                                (200, 30)),
                                               background_color = (64, 64, 64),
                                               text_color = (250, 250, 250)))

        else:
            container.sub(planes.gui.TextBox("identifier",
                                                 pygame.Rect((0, 0),
                                                                (200, 30)),
                                                 return_callback = None))

            # Register text box
            #
            self.window.key_sensitive(container.identifier)


        # Type
        #
        container.sub(planes.gui.Label("type_caption",
                                           "Type:",
                                           pygame.Rect((0, 0),
                                                            (200, 30)),
                                           background_color = (64, 64, 64),
                                           text_color = (250, 250, 250)))

        if entity is not None:

            if entity.entity_type == fabula.PLAYER:

                container.sub(planes.gui.Label("select_entity_type",
                                                   "PLAYER",
                                                   pygame.Rect((0, 0),
                                                                    (200, 30)),
                                                   background_color = (64, 64, 64),
                                                   text_color = (250, 250, 250)))
            else:

                # Display current type at top
                #
                type_list = {fabula.ITEM: ["ITEM", "NPC"],
                             fabula.NPC: ["NPC", "ITEM"]}[entity.entity_type]

                container.sub(planes.gui.OptionList("select_entity_type",
                                                        type_list,
                                                        width = 200))
        else:
            container.sub(planes.gui.OptionList("select_entity_type",
                                                    ["ITEM", "NPC"],
                                                    width = 200))

        # Blocking
        #
        container.sub(planes.gui.Label("blocking_caption",
                                           "Blocking:",
                                           pygame.Rect((0, 0),
                                                            (200, 30)),
                                           background_color = (64, 64, 64),
                                           text_color = (250, 250, 250)))

        blocking_list = ["block", "no-block"]

        if entity is not None:

            # Display current at top
            #
            blocking_list = {True: ["block", "no-block"],
                             False: ["no-block", "block"]}[entity.blocking]

        container.sub(planes.gui.OptionList("select_blocking",
                                                blocking_list,
                                                width = 200))

        # Mobility
        # TODO: shouldn't be able to change mobility of PLAYER
        #
        container.sub(planes.gui.Label("mobility_caption",
                                           "Mobility:",
                                           pygame.Rect((0, 0),
                                                            (200, 30)),
                                           background_color = (64, 64, 64),
                                           text_color = (250, 250, 250)))

        mobility_list = ["mobile", "immobile"]

        if entity is not None:

            # Display current at top
            #
            mobility_list = {True: ["mobile", "immobile"],
                             False: ["immobile", "mobile"]}[entity.mobile]

        container.sub(planes.gui.OptionList("select_mobile",
                                                mobility_list,
                                                width = 200))

        # OK button
        #
        container.sub(planes.gui.Button("OK",
                                            pygame.Rect((0, 0), (80, 25)),
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

                # TODO: blindly assuming "image/png"
                #
                entity = fabula.Entity(identifier = entity_identifier,
                                       entity_type = {"ITEM": fabula.ITEM, "NPC": fabula.NPC}[entity_type],
                                       blocking = entity_blocking,
                                       mobile = entity_mobile,
                                       assets = {"image/png": fabula.Asset(filename)})

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
                      planes.gui.OptionList):

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
            # TODO: blindly assuming "image/png"
            #
            self.show_properties(entity.assets["image/png"].data)

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

        self.window.buttons.sub(planes.gui.Label("title",
                                                     "Edit Walls",
                                                      pygame.Rect((0, 0),
                                                                  (80, 25)),
                                                      background_color = (120, 120, 120)))

        self.window.buttons.sub(planes.gui.Button("Done",
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

                overlay_plane = planes.Plane(str(coordinates) + "_overlay",
                                                 pygame.Rect(self.window.room.tiles.subplanes[str(coordinates + (self.host.room.identifier, ))].rect),
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
        # TODO: blindly assuming "image/png"
        #
        coordinates = eval(plane.name)

        # NOTE: floor_plan uses (x, y) tuples
        #
        uri = self.host.room.floor_plan[coordinates[:2]].tile.assets["image/png"].uri
        data = self.host.room.floor_plan[coordinates[:2]].tile.assets["image/png"].data

        event = fabula.ChangeMapElementEvent(fabula.Tile(fabula.OBSTACLE, {"image/png": fabula.Asset(uri, data = data)}),
                                             coordinates)

        self.host.message_for_host.event_list.append(event)

        # Draw an overlay indicating the OBSTACLE type.
        # rect can be taken from the Plane that received the click, but we make
        # a copy to be on the safe side.
        #
        overlay_plane = planes.Plane(str(coordinates) + "_overlay",
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
        # TODO: blindly assuming "image/png"
        #
        coordinates = eval(plane.name.split("_overlay")[0])
        uri = self.host.room.floor_plan[coordinates].tile.assets["image/png"].uri
        data = self.host.room.floor_plan[coordinates].tile.assets["image/png"].data

        event = fabula.ChangeMapElementEvent(fabula.Tile(fabula.FLOOR, {"image/png": fabula.Asset(uri, data = data)}),
                                             coordinates + (self.host.room.identifier, ))

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
        while not isinstance(self.plane_cache[-1], planes.gui.Button):
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

            elif self.screensize[0] - 25 <= mouse_position[0] <= self.screensize[0]:

                # Scroll to right
                #
                self.scroll = 0 - self.spacing

            # TODO: this is ugly, as it's processed too often. Remove once we have an Tkinter GUI.
            #
            if pygame.key.get_pressed()[pygame.K_F10]:

                for plane_name in ("buttons", "properties"):

                    if plane_name in self.window.subplanes_list:

                        self.plane_cache.append(self.window.subplanes[plane_name])
                        self.window.remove(plane_name)

                    else:
                        for plane in self.plane_cache:

                            if plane.name == plane_name:

                                self.plane_cache.remove(plane)

                                self.window.sub(plane)

                                break

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
        self.window.room.rect.left = self.spacing

        return

    def show_properties(self, plane):
        """Click callback for entities to show their properties in the properties Plane.
        """

        # Is the property plane currently visible?
        #
        if "properties" not in self.window.subplanes_list:

            fabula.LOGGER.debug("properties not visible, not updating plane")

            return

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
        self.window.properties.sub(planes.gui.Label("identifier",
                                                    entity.identifier,
                                                    pygame.Rect((0, 0), (80, 25)),
                                                    background_color = (64, 64, 64),
                                                    text_color = (250, 250, 250)))

        # Entity.assets
        # TODO: blindly assuming "image/png"
        #
        rect = pygame.Rect((0, 0), entity.assets["image/png"].data.image.get_rect().size)

        asset_plane = planes.Plane("asset", rect)

        asset_plane.image = entity.assets["image/png"].data.image

        self.window.properties.sub(asset_plane)

        # Entity.asset_desc
        #
        self.window.properties.sub(planes.gui.Label("asset_desc",
                                                    entity.assets["image/png"].uri,
                                                    pygame.Rect((0, 0), (80, 25)),
                                                    background_color = (64, 64, 64),
                                                    text_color = (250, 250, 250)))

        # Entity.entity_type
        #
        self.window.properties.sub(planes.gui.Label("entity_type",
                                                    entity.entity_type,
                                                    pygame.Rect((0, 0), (80, 25)),
                                                    background_color = (64, 64, 64),
                                                    text_color = (250, 250, 250)))

        # Entity.blocking
        #
        self.window.properties.sub(planes.gui.Label("blocking",
                                                    {True: "block", False: "no-block"}[entity.blocking],
                                                    pygame.Rect((0, 0), (80, 25)),
                                                    background_color = (64, 64, 64),
                                                    text_color = (250, 250, 250)))

        # Entity.mobile
        #
        self.window.properties.sub(planes.gui.Label("mobile",
                                                    {True: "mobile", False: "immobile"}[entity.mobile],
                                                    pygame.Rect((0, 0), (80, 25)),
                                                    background_color = (64, 64, 64),
                                                    text_color = (250, 250, 250)))

        # Edit
        #
        self.window.properties.sub(planes.gui.Button("Edit Entity",
                                                     pygame.Rect((0, 0),
                                                                 (80, 25)),
                                                     lambda plane: self.edit_entity_attributes(self.update_entity, entity)))

        # Logic
        #
        self.window.properties.sub(planes.gui.Button("Edit Logic",
                                                     pygame.Rect((0, 0),
                                                                 (80, 25)),
                                                     lambda plane : self.edit_logic(entity.identifier)))

        # Make sure it's on top
        #
        self.window.sub(self.window.properties)

        # Make it completely visible, no matter how large
        #
        self.window.properties.rect.right = self.screensize[0]

        return

    def make_items_draggable(self):
        """Overriding base class: make all items always draggable.
        """

        for identifier in self.host.room.entity_locations.keys():

            # TODO: blindly assuming "image/png"
            #
            if (identifier != self.host.client_id
                and "image/png" in self.host.room.entity_dict[identifier].assets.keys()
                and self.host.room.entity_dict[identifier].assets["image/png"].data is not None):

                self.host.room.entity_dict[identifier].assets["image/png"].data.draggable = True

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

        option_list = planes.gui.OptionSelector("select_response",
                                                    event_list,
                                                    lambda option : self.edit_event(event, option),
                                                    background_color = (64, 64, 64))

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
            editor_window = planes.gui.Container("edit_event",
                                                     padding = 4,
                                                     background_color = (64, 64, 64))

            event_editor = EventEditor(fabula.PerceptionEvent(event.identifier, ""), self.window)

            editor_window.sub(event_editor)

            editor_window.sub(planes.gui.Button("OK",
                                                    pygame.Rect((0, 0), (50, 25)),
                                                    lambda string: self.event_edit_done(event, event_editor.get_updated_event())))

            editor_window.rect.center = self.window.rect.center

            self.window.sub(editor_window)

        elif option.text == "Says":

            # TODO: copied from above, replace
            #
            editor_window = planes.gui.Container("edit_event",
                                                     padding = 4,
                                                     background_color = (64, 64, 64))

            event_editor = EventEditor(fabula.SaysEvent(event.identifier, ""), self.window)

            editor_window.sub(event_editor)

            editor_window.sub(planes.gui.Button("OK",
                                                    pygame.Rect((0, 0), (50, 25)),
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

        editor_window = planes.gui.Container("display_logic",
                                                 padding = 4,
                                                 background_color = (64, 64, 64))

        editor_window.sub(planes.gui.Label("title",
                                               "Logic affecting Entity '{}'".format(identifier),
                                               pygame.Rect((0, 0), (300, 25)),
                                               background_color = (64, 64, 64),
                                               text_color = (250, 250, 250)))

        rules_container = planes.gui.Container("rules",
                                                   padding = 4,
                                                   background_color = (64, 64, 64))

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
                    rule_plane = planes.Plane("rule_{}_{}".format(trigger_editor.name, response_editor.name),
                                                  pygame.Rect((0, 0), (trigger_editor.rect.width + response_editor.rect.width - 1, trigger_editor.rect.height)))

                    rule_plane.image.fill((64, 64, 64))

                    # Make them overlap to have an 1px separating line
                    #
                    response_editor.rect.left = trigger_editor.rect.width - 1

                    rule_plane.sub(trigger_editor)
                    rule_plane.sub(response_editor)

                    fabula.LOGGER.debug("Adding rule Plane '{}'".format(rule_plane.name))
                    rules_container.sub(rule_plane)

        if len(rules_container.subplanes_list):

            editor_window.sub(planes.gui.ScrollingPlane("scrolling_rules",
                                                            pygame.Rect((0, 0),
                                                                        (rules_container.subplanes[rules_container.subplanes_list[0]].rect.width + 8, 400)),
                                                            rules_container))

        editor_window.sub(planes.gui.Button("Update",
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

       PygameOSD.caption_list
           A list of active captions which also serve as identifiers for
           OSDText instances.

       PygameOSD.offset
           A (x, y) tuple giving the rendering offset relative to (0, 0).

       PygameOSD.display_plane
           An instance of planes.Display.

       PygameOSD.font
           A pygame.fonts.Font instance.

       PygameOSD.text_color
           A list [R, G, B] giving the text color. Change this list in place
           to change the text color.
    """

    def __init__(self, display_plane, font = None, text_color = None):
        """Initialise.

           display_plane is an instance of planes.Display.

           If present, font is a pygame.fonts.Font instance.

           If present, text_color must be a list [R, G, B] giving the text
           color. Change PygameOSD.text_color in place to change the text color.
        """

        self.display_plane = display_plane

        self.caption_list = []

        self.offset = (0, 0)

        self.font = font

        self.text_color = text_color

        if self.text_color is None:

            self.text_color = [255, 255, 255]

        # Proxy for access from inside the class
        #
        text_color_proxy = self.text_color

        class OSDText(planes.gui.OutlinedText):
            """Subclass that updates the text from a dict value in update().

               Additional attributes:

               OSDText.caption
               OSDText.dictionary
               OSDText.key
                   Data to update the text.
            """

            def __init__(self, name,
                               caption,
                               dictionary,
                               key,
                               text_color = text_color_proxy,
                               font = None):
                """Call base class and register caption, dictionary and key.
                """

                planes.gui.OutlinedText.__init__(self, name, "",
                                                 text_color = text_color,
                                                 font = font)

                self.caption = caption
                self.dictionary = dictionary
                self.key = key

                self.update()

                return

            def update(self):
                """Update text, then call base class to display.
                """

                value = ""

                try:

                    value = self.dictionary[self.key]

                except KeyError:

                    value = "not available"

                self.text =  "{} {}".format(self.caption, value)

                # OutlinedText is centered. We don't want that.
                #
                x, y = self.rect.topleft

                planes.gui.OutlinedText.update(self)

                # Restore
                #
                self.rect.topleft = (x, y)

                return

        self.OSDText = OSDText

        return

    def display(self, caption, dictionary, key):
        """Create a PygameOSD.OSDText instance and register it as a subplane of display_plane.
        """

        # Use caption as Plane name
        #
        osdtext = self.OSDText(caption, caption, dictionary, key, font = self.font)

        osdtext.rect.left = self.offset[0]

        y = self.offset[1]

        for existing_caption in self.caption_list:

            y += self.display_plane.subplanes[existing_caption].rect.height

        osdtext.rect.top = y

        self.display_plane.sub(osdtext)

        self.caption_list.append(caption)

        fabula.LOGGER.debug("displaying caption '{}' at ({}, {})".format(caption,
                                                                         osdtext.rect.left,
                                                                         osdtext.rect.top))

        return

    def remove(self, caption):
        """No longer display the item identified by caption.
        """

        self.display_plane.remove(caption)

        self.caption_list.remove(caption)

        return
