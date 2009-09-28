"""Shard Interface Base Class

   Work started on 28. Sep 2009

   Based on former client- and server
   interface implementations
"""

class Interface:
    """This is a base class for Shard interfaces
       which handle all the network traffic. A
       custom implementation using Shard will
       likely have an client- and a server side
       interface.
    """

    def __init__(self, address_port_tuple, logger):
        """Most likey you will want to override
           this method. Be sure to call
           self.setup_interface() with the
           appropriate arguments in your
           implementation. This is also what
           the default implementation does.
        """

        setup_interface(address_port_tuple, logger)

    def setup_interface(self, address_port_tuple, logger):
        """An interface is initialized with an
           ("address", port) tuple holding the
           server's address and port, and an
           instance of logging.Logger. Be sure
           to call this method from __init__()
           when subclassing.
        """

        self.address_port_tuple = address_port_tuple

        # Attach logger
        #
        self.logger = logger

        # This is the flag which is set when shutdown()
        # is called.
        #
        self.shutdown_flag = False

        # And this is the one for the confirmation.
        #
        self.shutdown_confirmed = False

    def handle_messages(self):
        """This is the main method of an interface
           class. It must transfer all the messages
           between local and remote host. This
           method is put in a background thread by
           the startup script, so your implementation
           can do all sorts of polling or blocking IO.
           It should regularly check whether shutdown()
           has been called (checking self.shutdown_flag),
           and if so, it should notify shutdown() by
           setting self.shutdown_confirmed to true (so
           that method can return True itself), and then
           raise SystemExit to stop the thread.
           The default implementation does nothing, but
           will handle the shutdown as described.
        """

        # Run thread as long as no shutdown is requested
        #
        while not self.shutdown_flag:
            pass

        # Caught shutdown notification, stopping thread
        #
        self.logger.info("shutting down")

        self.shutdown_confirmed = True

        raise SystemExit

    def shutdown(self):
        """This method is called when the engine is
           about to exit. It notifies handle_messages()
           to raise SystemExit to stop the thread
           properly by setting self.shutdown_flag.
           shutdown() will return True when
           handle_messages() received the notification
           and is about to exit.
        """

        self.logger.info("called")

        # Set the flag to be caught by handle_messages()
        #
        self.shutdown_flag = True

        # Wait for confirmation (blocks interface and client!)
        #
        while not self.shutdown_confirmed:
            pass

        return True
