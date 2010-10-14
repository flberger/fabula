"""Shard Engine Plugin Base Class
"""

# Work started on 30. Sep 2009

import shard           
import shard.eventprocessor

class Plugin(shard.eventprocessor.EventProcessor):
    """Base class for plugins to be used by a shard.core.Engine.
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

           It is called with an instance of
           shard.Message. This method does
           not run in a thread. It should
           process the message quickly and
           return another instance of shard.Message
           to be processed by the host object
           and possibly to be sent to the
           remote host.

           The host is accessible as Plugin.host

           The default implementation returns
           an empty message.
        """

        self.logger.debug("processing message " + str(message.event_list))

        return self.message_for_host
