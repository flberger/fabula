"""Shard Core Engine Plugin Base Class
"""

# Work started on 30. Sep 2009

import shard           
import shard.eventprocessor

class Plugin(shard.eventprocessor.EventProcessor):
    """This is the base class for plugins
       to be used by an instance of
       shard.coreengine.CoreEngine.
    """

    def __init__(self, logger):
        """You can override this. Be sure to
           call setup_plugin() like the default
           implementation does.
        """
        self.setup_plugin(logger)

    def setup_plugin(self, logger):
        """Initialize the plugin.
           logger is an instance of logging.Logger.
           The default implementation does nothing.
        """

        self.setup_eventprocessor()

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
           The default implementation returns
           an empty message.
        """

        self.logger.debug("processing message " + str(message.event_list))

        return self.message_for_host
