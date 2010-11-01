"""Server-Side Plugins for Shard

   (c) Florian Berger <fberger@florian-berger.de>
"""

# work started on 27. Oct 2010

import shard.plugins
import re

class MapEditor(shard.plugins.Plugin):
    """This is the server-side Plugin for a Shard map editor.
       Additional attributes:

       MapEditor.current_room
           name of the current room
    """

    def __init__(self, logger):
        """Initialise.
        """
        # Call base class
        #
        shard.plugins.Plugin.__init__(self, logger)

        # TODO: When handling of multiple rooms is implemented, this should go into the base class.
        # TODO: Or is that one obsolete, since the name can be guessed from host.room.identifier?
        #
        self.current_room = ''

    def process_InitEvent(self, event):
        """Send a bare room, to be populated by the user.
        """

        self.logger.debug("called")

        if self.host.room is None:

            self.logger.debug("no room sent yet, sending initial room")

            self.message_for_host.event_list.append(shard.EnterRoomEvent("edit_this"))

            tile = shard.Tile(shard.FLOOR, "tile_default.png")

            for x in range(8):
                for y in range(6):
                    event = shard.ChangeMapElementEvent(tile, (x, y))
                    self.message_for_host.event_list.append(event)

            self.message_for_host.event_list.append(shard.RoomCompleteEvent())

    def process_EnterRoomEvent(self, event):
        """Save the name of the room to be entered and forward the event to the Server to update the Room..
        """
        self.logger.debug(str(event))
        self.current_room = event.room_identifier
        self.message_for_host.event_list.append(event)

    def process_ChangeMapElementEvent(self, event):
        """Forward the event to the Server to update the Room.
        """

        self.logger.debug("called")
        self.message_for_host.event_list.append(event)

    def process_RoomCompleteEvent(self, event):
        """Save the Room to a local file, then forward the event to the Server .
        """

        self.logger.debug("called")

        roomfile = open(self.current_room + ".floorplan", "wt")

        for coordinates in self.host.room.floor_plan:

            tile = self.host.room.floor_plan[coordinates].tile

            roomfile.write("{0}\t{1}\t{2}\n".format(repr(coordinates),
                                                    tile.tile_type,
                                                    tile.asset_desc))

            # TODO: save FloorPlanElement.entities = []

        roomfile.close()

        self.logger.debug("wrote {}".format(self.current_room + ".floorplan"))

        self.message_for_host.event_list.append(event)

class DefaultGame(shard.plugins.Plugin):
    """This is an off-the-shelf server plugin, running a standard Shard game.
    """

    def process_InitEvent(self, event):
        """If there is no host.room yet, load default.floorplan and send it.
        """

        self.logger.debug("called")

        # Prevent "referenced before assignment"
        #
        roomfile = None

        if self.host.room is  not None:

            self.logger.debug("room already loaded, current room: {}".format(self.host.room.identifier))

        else:
            self.logger.debug("no room loaded yet, attempting to load 'default.floorplan'")

            try:
                roomfile = open("default.floorplan", "rt")

            except IOError:
                self.logger.error("could not open file 'default.floorplan'")

                # No need to raise SystemExit though
                #
                return

            self.message_for_host.event_list.append(shard.EnterRoomEvent("default"))

            for line in roomfile:

                # TODO: Check for 3-part tab-separated string
                #
                coordiantes_string, type, asset_desc = line.split("\t")

                coordiantes_string = coordiantes_string.strip()
                type = type.strip()
                asset_desc = asset_desc.strip()

                # Match only "(x, y)" coordinates
                #
                if re.match("^\([0-9]+\s*,\s*[0-9]+\)$", coordiantes_string):
                    coordinates = eval(coordiantes_string)

                    # TODO: Check for shard.FLOOR etc.
                    # TODO: Check asset_desc
                    #
                    tile = shard.Tile(type, asset_desc)

                    event = shard.ChangeMapElementEvent(tile, coordinates)

                    self.message_for_host.event_list.append(event)

                else:
                    self.logger.warning("non-matching coordinate string in default.floorplan: {}".format(repr(coordiantes_string)))

            self.message_for_host.event_list.append(shard.RoomCompleteEvent())

            roomfile.close()

        return
