"""Shard Message Buffer

   Work started on 28. Sep 2009

   Based on methods from ClientInterface
   and the ClienConnection class in
   ServerInterface
"""

import shard
from collections import deque

class MessageBuffer:
    """For each client connection an instance of
       this class is created. 
    """

    def __init__(self):
        """This is meant to be a base class
           to be inherited from. This default
           __init__() method simply calls
           self.setup(). You should do so,
           too, when subclassing this with a
           custom implementation.
        """

        self.setup()

    def setup(self):
        """This method sets up the internal
           queues (in this case instances
           of collections.deque)
        """

        # A hint from the Python documentation:
        # deques are a fast, thread-safe replacement
        # for queues.
        # Use deque.append(x) and deque.popleft()
        #
        self.messages_for_local = deque()
        self.messages_for_remote = deque()

    def send_message(self, message):
        """This method is called by the local
           engine with a message ready to be sent to
           the remote host. The Message object given
           is an instance of shard.Message. This method
           must return immediately to avoid blocking.
        """

        self.messages_for_remote.append(message)

        return

    def grab_message(self):
        """This method is called by the local
           engine to obtain a new buffered message
           from the remote host. It must return an
           instance of shard.Message, and it must
           do so immediately to avoid blocking. If
           there is no new message from remote, it
           must return an empty message.
        """

        if self.messages_for_local:

            return self.messages_for_local.popleft()

        else:
            # A Message must be returned, so create
            # an empty one
            #
            return shard.Message([])
