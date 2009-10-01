"""Shard Core Engine Plugin Base Class
 
   Work started on 30. Sep 2009
"""

import shard           

class Plugin:
    """This is the base class for plugins
       to be used by an instance of
       shard.coreengine.CoreEngine.
    """

    def __init__(self, logger):
        """Initialize the plugin.
           logger is an instance of logging.Logger.
           The default implementation does nothing.
        """

        self.logger = logger

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

        return shard.Message([])
