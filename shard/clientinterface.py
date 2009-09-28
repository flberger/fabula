"""Shard Client Interface

   Extracted from shard.py on 22. Sep 2009
"""

import shard
import socket
import cPickle
import shard.messagebuffer

class ClientInterface(shard.messagebuffer.MessageBuffer):
    '''This is the base class for a Shard Client Interface.
       Implementations should subclass this one an override
       the default methods, which showcase a simple example.'''

    def __init__(self, address_port_tuple, logger):
        '''Interface initialization.'''

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

        # This is a subclass of MessageBuffer, but
        # since we override __init__(), we have to
        # call setup.
        #
        self.setup()

        # Set up UDP socket
        # It wouldn't be unreasonable to also use
        # a SocketServer on the client side. But
        # since the client is only ever supposed
        # to handle one connection, direct socket
        # handling may be just right.
        #
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # The socket timeout is used for
        # socket.recv() operations, which
        # take turns with socket.sendto().
        #
        self.sock.settimeout(0.3)

        self.logger.info("complete")

    def handle_messages(self):
        '''The task of this method is to do whatever is
           necessary to send client messages and obtain 
           server messages. It is meant to be the back end 
           of send_message() and grab_message(). Put some 
           networking code, a GUI or a random generator 
           here. 
           This method is put in a background thread 
           automatically, so it can do all sorts of 
           polling or blocking IO.
           It should regularly check whether shutdown()
           has been called, and if so, it should notify
           shutdown() in some way (so that it can return
           True), and then raise SystemExit to stop 
           the thread.'''

        self.logger.debug("starting up")

        # Run thread as long as no shutdown is requested
        #
        while not self.shutdown_flag:

            if self.messages_for_remote:

                self.logger.debug("sending 1 message of " + str(len(self.messages_for_remote)))

                self.sock.sendto(cPickle.dumps(self.messages_for_remote.popleft()), 
                                 self.address_port_tuple)

            # Now listen for incoming server
            # messages for some time
            # (set in __init__()). This will
            # catch any messages received in
            # the meantime by the OS (tested).
            #
            data_received = ""

            try:

                data_received = self.sock.recv(4096)

            except socket.timeout:

                # We do not log here since this
                # happens too often
                #
                pass

            if data_received:

                # TODO: accepts data from *anywhere*

                self.logger.debug("received server message")

                self.messages_for_local.append(cPickle.loads(data_received))

        # Caught shutdown notification, stopping thread
        #
        self.logger.info("shutting down")

        self.shutdown_confirmed = True

        raise SystemExit

    def shutdown(self):
        '''This method is called when the client is
           about to exit. It should notify 
           handle_messages() to raise SystemExit to stop 
           the thread properly. shutdown() must return 
           True when handle_messages() received the 
           notification and is about to exit.'''

        self.logger.info("called")

        # Set the flag to be caught by handle_messages()
        #
        self.shutdown_flag = True

        # Wait for confirmation (blocks interface and client!)
        #
        while not self.shutdown_confirmed:
            pass

        return True
