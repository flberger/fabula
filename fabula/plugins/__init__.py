"""Fabula Engine Plugin Base Class

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

class Plugin(fabula.eventprocessor.EventProcessor):
    """Base class for plugins to be used by a fabula.core.Engine.

       Plugin does not override the EventProcessor handler methods, so the
       default for a Plugin is to silently discard all incoming events.

       Attributes:

       Plugin.host
           The host of this plugin, an instance of fabula.core.Engine.

       Plugin.message_for_host
           Fabula Message to be returned by Plugin.process_message().
    """

    def __init__(self, host):
        """Initialise the plugin.
           host is an instance of fabula.core.Engine.
        """

        fabula.eventprocessor.EventProcessor.__init__(self)

        self.host = host

        self.message_for_host = fabula.Message([])

    def process_message(self, message):
        """This is the main method of a plugin.

           It is called with an instance of fabula.Message. This method does not
           run in a thread. It should process the message quickly and return
           another instance of fabula.Message to be processed by the host and
           possibly to be sent to the remote host.

           The host Engine will try hard to call this method on a regular base,
           ideally once per frame. message.event_list thus might be empty.

           The default implementation calls the respective functions for the
           Events in message and returns Plugin.message_for_host.
        """

        # Clear message for host
        #
        self.message_for_host = fabula.Message([])

        if message.event_list:

            fabula.LOGGER.debug("processing message {}".format(message.event_list))

            for event in message.event_list:

                # event_dict from EventProcessor base class
                #
                self.event_dict[event.__class__](event)

        return self.message_for_host
