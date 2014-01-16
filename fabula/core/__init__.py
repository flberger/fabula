"""Fabula Engine Base Class

   Based on former implementations of the ClientControlEngine

   Copyright 2010 Florian Berger <mail@florian-berger.de>
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

# Work started on 30. Sep 2009

import fabula
import fabula.eventprocessor
import logging
from time import sleep

class Engine(fabula.eventprocessor.EventProcessor):
    """Common base class for Fabula server and client engines.
       Most likely you will want to override all of the methods when subclassing
       Engine, so the use of this class is providing a structure for Engines.

       Attributes:

       Engine.interface

       Engine.message_logger
           An instance of logging.Logger that Engine.run() should log
           incoming messages to.

       Engine.plugin
           This is None upon initialisation and must be set to an instance of
           fabula.plugins.Plugin using Engine.set_plugin().

       Engine.message_for_plugin

       Engine.message_for_remote

       Engine.rack
           An instance of fabula.Rack.
    """

    def __init__(self, interface_instance, sublogger_name):
        """Set up Engine attributes.

           Arguments:

           interface_instance
               An instance of a subclass of fabula.interfaces.Interface to
               communicate with the remote host.

           sublogger_name
               A string. Engine.message_logger will be created by
               calling logging.getLogger("fabula." + sublogger_name)
        """

        # First setup base class
        #
        fabula.eventprocessor.EventProcessor.__init__(self)

        self.interface = interface_instance

        # The logging module uses a funny dotted naming hierarchy
        # for subloggers.
        #
        self.message_logger = logging.getLogger("fabula." + sublogger_name)

        # Raw message logs are not supposed to clutter the fabula
        # main logger.
        #
        self.message_logger.propagate = False

        self.plugin = None

        # The Engine examines the events of a received
        # Message and applies them. Events for special
        # consideration for the PluginEngine are collected
        # in a Message for the PluginEngine.
        # The Engine has to empty the Message once
        # the PluginEngine has processed all Events.
        #
        self.message_for_plugin = fabula.Message([])

        # In self.message_for_remote we collect events to be
        # sent to the remote host in each loop.
        #
        self.message_for_remote = fabula.Message([])

        # self.rack serves as a storage for deleted Entities
        # because there may be the need to respawn them.
        #
        self.rack = fabula.Rack()

        fabula.LOGGER.debug("complete")

        return

    def set_plugin(self, plugin_instance):
        """Set the Plugin which controls or presents the game.
           plugin_instance must be an instance of fabula.plugins.Plugin.
        """

        fabula.LOGGER.info("setting plugin to {}".format(plugin_instance))

        self.plugin = plugin_instance

        return

    def run(self):
        """This is the main loop of an Engine. Put all the business logic here.

           This is a blocking method which should call all the process methods
           to process events, and then call the plugin.

           This method should log incoming messages to the logger
           instance Engine.message_logger.

           The default implementation waits for self.plugin.exit_requested to be True.
        """

        fabula.LOGGER.info("starting")

        # You will probably want to run until the
        # plugin engine decides that the game is
        # over.
        #
        while not self.plugin.exit_requested:

            # No need to run as fast as possible
            #
            sleep(1/30)

        # exit has been requested

        fabula.LOGGER.info("exit requested from Plugin, shutting down interface...")

        # stop the Interface thread
        #
        self.interface.shutdown()

        fabula.LOGGER.info("shutdown confirmed.")

        # TODO: possibly exit cleanly from the Plugin here

        return

    def process_TriesToMoveEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_TriesToLookAtEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_TriesToPickUpEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_TriesToDropEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_TriesToManipulateEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_TriesToTalkToEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_ManipulatesEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_CanSpeakEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_AttemptFailedEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_PerceptionEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_SaysEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_PassedEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_LookedAtEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_PickedUpEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_DroppedEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_EnterRoomEvent(self, event, **kwargs):
        """The default implementation simply forwards the Event.
           On the client side, an EnterRoomEvent means that the server is about
           to send a new map, respawn the player and send items and NPCs.
           On the server side, things may be a little more complicated. In a
           single player scenario the server might replace the current room or
           save it to be able to return to it later. In a multiplayer
           environment however the server has to set up another room to manage
           in parallel to the established rooms.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_RoomCompleteEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_InitEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_ServerParametersEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        fabula.LOGGER.debug("called")

        kwargs["message"].event_list.append(event)

        return
