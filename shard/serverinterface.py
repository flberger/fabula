"""Shard Server Interface

   Work started on 24. Sep 2009
"""

import shard.messagebuffer
import shard.interface
import cPickle
import SocketServer

class ServerInterface(shard.interface.Interface):
    '''This is the base class for a Shard Server Interface.
       Implementations should subclass this one an override
       the default methods, which do nothing.'''

    def __init__(self, address_port_tuple, logger):
        '''Interface initialization.'''

        # First call setup_interface() from the
        # base class
        #
        self.setup_interface(address_port_tuple, logger)

        # client_connections is a dict of
        # shard.messagebuffer.MessageBuffer
        # instances, indexed by (address, port) tuples.
        #
        self.client_connections = {}

        self.logger.debug("complete")

    def handle_messages(self):
        '''The task of this method is to do whatever is
           necessary to send server messages and obtain 
           client messages. It is meant to be the back end 
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

        client_connections_proxy = self.client_connections
        logger_proxy = self.logger

        # We define the class here to be able
        # to access variables of the ServerInterface
        # instance.
        #
        class ShardRequestHandler(SocketServer.BaseRequestHandler):

            def handle(self):

                logger_proxy.debug("called")

                # Test for new client,
                # i.e. not (address, port) tuple in keys
                #
                if not self.client_address in client_connections_proxy:

                    # New client. Create a new
                    # shard.messagebuffer.MessageBuffer
                    # and add it to the dict
                    #
                    client_connections_proxy[self.client_address] = shard.messagebuffer.MessageBuffer()

                    logger_proxy.info("adding new client: "
                                      + str(self.client_address))

                # Append the message.
                # (inbetween steps to avoid a loong line ;-) )
                #
                message = cPickle.loads(self.request[0])

                messagebuffer = client_connections_proxy[self.client_address]

                messagebuffer.messages_for_local.append(message)

                # End of handle() method.

        # End of class.

        server = SocketServer.UDPServer(self.address_port_tuple, ShardRequestHandler)

        # Server timeout, so server.handle_request()
        # doesn't wait forever, which would prevent
        # shutdown.
        #
        server.timeout = 0.1

        # Run thread as long as no shutdown is requested
        #
        while not self.shutdown_flag:

            # TODO: several threads for send and receive

            # wait at most server.timeout seconds
            # until a request comes in:
            #
            server.handle_request()

            # Flush server event queues.
            # Iterate over dict keys:
            #
            for address_port_tuple in self.client_connections:

                messagebuffer = self.client_connections[address_port_tuple]

                if messagebuffer.messages_for_remote:

                    self.logger.debug("sending 1 message of "
                                      + str(len(messagebuffer.messages_for_remote))
                                      + " to client "
                                      + str(address_port_tuple))

                    server.socket.sendto(cPickle.dumps(messagebuffer.messages_for_remote.popleft()), 
                                         address_port_tuple)

        # Caught shutdown notification, stopping thread
        #
        self.logger.info("shutting down")

        self.shutdown_confirmed = True

        raise SystemExit
