"""Server-Side Plugins for Shard

   (c) Florian Berger <fberger@florian-berger.de>
"""

# work started on 27. Oct 2010

import shard.plugins

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
        #
        self.current_room = ''

    def process_InitEvent(self, event):
        """Send a bare room, to be populated by the user.
        """

        self.logger.debug("called")

        self.message_for_host.event_list.append(shard.EnterRoomEvent("edit_this"))

        tile = shard.Tile(shard.FLOOR, "tile_default.png")

        for x in range(8):
            for y in range(6):
                event = shard.ChangeMapElementEvent(tile, (x, y))
                self.message_for_host.event_list.append(event)

        self.message_for_host.event_list.append(shard.RoomCompleteEvent())

    def process_EnterRoomEvent(self, event):
        """Save the name of the room to be entered.
        """
        self.logger.debug("entering room: {}".format(event.name))
        self.current_room = event.name

    def process_ChangeMapElementEvent(self, event):
        """Forward the event to the Server to update the Room.
        """

        self.logger.debug("called")
        self.message_for_host.event_list.append(event)

    def process_RoomCompleteEvent(self, event):
        """Process the event.
        """
        self.logger.debug("called")
        self.logger.debug("floor_plan for room '{0}': {1}".format(self.current_room,
                                                                  self.host.room.floor_plan))
