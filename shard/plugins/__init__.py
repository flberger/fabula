"""Shard Engine Plugin Base Class
"""

# Work started on 30. Sep 2009

import shard           
import shard.eventprocessor

class Plugin(shard.eventprocessor.EventProcessor):
    """Base class for plugins to be used by a shard.core.Engine.

       Attributes:

       Plugin.logger
           The host's logger

       Plugin.message_for_host
           Shard Message to be returned by Plugin.process_message()

       Plugin.host
           The host of this plugin, an instance of shard.core.Engine
    """

    def __init__(self, logger):
        """Initialise the plugin.
           logger is an instance of logging.Logger.
           The default implementation does nothing.
        """

        shard.eventprocessor.EventProcessor.__init__(self)

        self.logger = logger

        self.message_for_host = shard.Message([])

    def process_message(self, message):
        """This is the main method of a plugin.

           It is called with an instance of shard.Message. This method does not
           run in a thread. It should process the message quickly and return
           another instance of shard.Message to be processed by the host and
           possibly to be sent to the remote host.

           The default implementation calls the respective functions for the
           Events in message and returns Plugin.message_for_host.
        """

        # Clear message for host
        #
        self.message_for_host = shard.Message([])

        if message.event_list:

            self.logger.debug("processing message {}".format(message.event_list))

            for event in message.event_list:

                # event_dict from EventProcessor base class
                #
                self.event_dict[event.__class__](event)

        return self.message_for_host
