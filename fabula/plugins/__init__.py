"""Fabula Engine Plugin Base Class
"""

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

       Plugin.logger
           The host's logger.

       Plugin.message_for_host
           Fabula Message to be returned by Plugin.process_message().
    """

    def __init__(self, host):
        """Initialise the plugin.
           host is an instance of fabula.core.Engine.
        """

        fabula.eventprocessor.EventProcessor.__init__(self)

        self.host = host

        self.logger = host.logger

        self.message_for_host = fabula.Message([])

    def process_message(self, message):
        """This is the main method of a plugin.

           It is called with an instance of fabula.Message. This method does not
           run in a thread. It should process the message quickly and return
           another instance of fabula.Message to be processed by the host and
           possibly to be sent to the remote host.

           The default implementation calls the respective functions for the
           Events in message and returns Plugin.message_for_host.
        """

        # Clear message for host
        #
        self.message_for_host = fabula.Message([])

        if message.event_list:

            self.logger.debug("processing message {}".format(message.event_list))

            for event in message.event_list:

                # event_dict from EventProcessor base class
                #
                self.event_dict[event.__class__](event)

        return self.message_for_host
