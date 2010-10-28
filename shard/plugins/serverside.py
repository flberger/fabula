"""Server-Side Plugins for Shard

   (c) Florian Berger <fberger@florian-berger.de>
"""

# work started on 27. Oct 2010

import shard.plugins

class MapEditor(shard.plugins.Plugin):
    """This is the server-side Plugin for a Shard map editor.
    """

    def process_InitEvent(self, event):
        """Send a bare room, to be populated by the user.
        """

        self.logger.debug("called")

        self.message_for_host.event_list.append(shard.EnterRoomEvent())

        tile = shard.Tile(shard.FLOOR, "tile_default.png")

        for x in range(8):
            for y in range(6):
                event = shard.ChangeMapElementEvent(tile, (x, y))
                self.message_for_host.event_list.append(event)

        self.message_for_host.event_list.append(shard.RoomCompleteEvent())

    def process_ChangeMapElementEvent(self, event):
        """Forward the event to the Server to update the Room.
        """

        self.logger.debug("called")
        self.message_for_host.event_list.append(event)

    def process_RoomCompleteEvent(self, event):
        """Process the event.
        """
        self.logger.debug("called")
        self.logger.debug("floor_plan: {}".format(self.host.room.floor_plan))
