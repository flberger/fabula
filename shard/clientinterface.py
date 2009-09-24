"""Shard Client Interface

   Extracted from shard.py on 22. Sep 2009
"""

import shard

class ClientInterface:
    '''This is the base class for a Shard Client Interface.
       Implementations should subclass this one an override
       the default methods, which showcase a simple example.'''

    def __init__(self, logger):
        '''Interface initialization.'''

        # Attach logger
        self.logger = logger

        # EXAMPLE
        # First one cache for a client message and one
        # for a server message.
        self.client_message = shard.Message([])
        self.server_message = shard.Message([])

        # Please note that handle_messages() will run in
        # a background thread. NEVER attempt to change
        # data structures in handle_messages() AND other
        # methods like send_message() or grab_message()
        # unless you lock them thread-safely. A simple
        # solution is to set flags in those methods, 
        # obeying the rule that only one method may set
        # them to True and one may set them to False.
        self.server_message_available = False
        self.client_message_available = False
        
        # This list serves as a queue for client messages.
        # To be thread-safe, it is not directly accessed
        # by handle_messages()
        self.client_message_queue = []

        # This is the flag which is set when shutdown()
        # is called.
        self.shutdown_flag = False

        # And this is the one for the confirmation.
        self.shutdown_confirmed = False

        self.sent_no_message_available = False

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
        # EXAMPLE
        # Set up space for some local copies
        local_client_message = shard.Message([])
        local_server_message = shard.Message([])

        # Just as in the main thread, a queue
        # for server messages comes in handy in case 
        # the client does not catch up fetching the 
        # messages. Since this example sends only
        # one message, we do not really need it though.
        server_message_queue = []

        # A flag for a client init request
        client_sent_init = False

        # Run thread as long as no shutdown is requested
        while not self.shutdown_flag:
            # read client message
            if self.client_message_available:
                # First do the work
                local_client_message = self.client_message

                # Then notify thread-safely by setting the flag.
                # Only handle_messages() may set it to False.
                self.client_message_available = False

                # Here we should do something useful with the
                # client message, like sending it over the
                # network. In this example, we check for the
                # init message and silently discard everything
                # else.
                for current_event in local_client_message.event_list:
                    if isinstance(current_event, shard.InitEvent):
                        client_sent_init = True

            # When done with the client message, it is time
            # to fetch a server message and hand it over
            # to the client. In this example, we generate
            # a message ourselves once the client has
            # requested init.
            if client_sent_init:
                # Build a message
                event_list = [shard.EnterRoomEvent()]
                event_list.append(shard.SpawnEvent(shard.Entity("PLAYER",
                                                                "player",
                                                                (0, 0),
                                                                "")))
                event_list.append(shard.RoomCompleteEvent())
                event_list.append(shard.PerceptionEvent("player",
                                                        "dummy server message"))

                # Append a message to the queue
                server_message_queue.append(shard.Message(event_list))

                # Set client_sent_init to false again, so the
                # events are only set once
                client_sent_init = False
                
            # Is the client ready to read? 
            if not self.server_message_available:
                try:
                    # Pull the next one from the queue and
                    # delete it there.
                    self.server_message = server_message_queue[0]
                    del server_message_queue[0]
 
                    # Set the flag for the main thread. This is
                    # thread-safe since it may only be set to
                    # True here.
                    self.server_message_available = True

                except IndexError:
                    # No message in queue!
                    pass
            else:
                # The client has not yet grabbed the
                # last message. No problem, this check
                # is run regularly, so we'll leave it in
                # the queue.
                pass

        # Caught shutdown notification, stopping thread
        self.shutdown_confirmed = True
        raise SystemExit

    def send_message(self, message):
        '''This method is called by the client 
           ClientControlEngine with a message ready to be sent to
           the server. The Message object given is an
           an instance of shard.Message. This method
           must return immediately to avoid blocking
           the client.'''
        # EXAMPLE
        # First we put this message in the local queue.
        self.client_message_queue.append(message)

        # self.client_message_available is used as a
        # thread-safe flag. It may only be set to True
        # here and may only be set to False in
        # handle_messages().
        if not self.client_message_available:
            # Pull the next one from the queue and
            # delete it there. Note that
            # handle_messages does not access the queue.
            self.client_message = self.client_message_queue[0]
            del self.client_message_queue[0]
            self.client_message_available = True
            return
        else:
            # Uh, this is bad. The client just called
            # send_message(), but the previous message
            # has not yet been collected by 
            # handle_messages(). In this case a new 
            # thread should be spawned which
            # waits until handle_messages() is ready
            # to receive a new message. Since this is
            # a simple example implementation, we'll
            # leave the message in the queue and hope
            # for some more calls to send_message() that
            # will eventually shift it forward until
            # it can be delivered.
            return

    def grab_message(self):
        '''This method is called by the client 
           ClientControlEngine to obtain a new server message.
           It must return an instance of shard.Message, 
           and it must do so immediately to avoid
           blocking the client. If there is no new
           server message, it must return an empty
           message.'''
        # EXAMPLE
        # Set up a local copy
        local_server_message = shard.Message([])

        # self.server_message_available is used as a 
        # thread-safe flag. It may only be set to True 
        # in handle_messages() and may only be set to
        # False here, so no locking is required.
        if self.server_message_available:
            # First grab it, so the thread does not
            # overwrite it
            local_server_message = self.server_message

            self.logger.info("grabserver_message: Message available, got :"
                  + str(local_server_message))

            # Now set the flag
            self.server_message_available = False

            self.logger.info("grabserver_message: server_message_available is now '"
                  + str(self.server_message_available) + "'.")
            self.sent_no_message_available = False

            return local_server_message
        else:
            if not self.sent_no_message_available:
                self.logger.info("grabserver_message: no Message available "
                      + "(server_message_available False)")
                self.sent_no_message_available = True

            # A Message must be returned, so create
            # an empty one
            return shard.Message([])

    def shutdown(self):
        '''This method is called when the client is
           about to exit. It should notify 
           handle_messages() to raise SystemExit to stop 
           the thread properly. shutdown() must return 
           True when handle_messages() received the 
           notification and is about to exit.'''
        # EXAMPLE
        # Set the flag to be caught by handle_messages()
        self.shutdown_flag = True

        # Wait for confirmation (blocks interface and client!)
        while not self.shutdown_confirmed:
            pass

        return True

