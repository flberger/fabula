"""Initialise and run Shard client and server

   (c) Florian Berger <fberger@florian-berger.de>
"""

# Work started on 27. May 2008
#
# Server part adapted from run_shardclient.py on 25. Sep 2009
#
# Unfied for client and server usage on 30. Sep 2009
#
# Converted from run_shard.py on 06. Oct 2009

import shard.assets
import shard.core.client
import shard.core.server
import shard.plugins
import shard.plugins.ui
import shard.interfaces

import threading
import logging
from time import sleep

import sys
import traceback
import re

class ShardFileFormatter(logging.Formatter):
    """Subclass of Formatter with reasonable module information.
    """

    def __init__(self, fmt, datefmt):
        """Compile a regular expression object, then call base class __init__().
        """
        logging.Formatter.__init__(self, fmt, datefmt)

        self.module_re = re.compile("^.*shard/([^/]+/)*?([^/]+)(/__init__)*.py$")

    def format(self, record):
        """Override logging.Formatter.format()
        """
        
        # Reformat path to module information
        #
        record.pathname = "{:10}".format(self.module_re.sub(r"\2", record.pathname))

        # Fixed-length line number
        #
        record.lineno = "{:3}".format(record.lineno)

        # Call base class implementation
        #
        return logging.Formatter.format(self, record)

class App:
    """An App instance represents a Shard client or server application.

       Attributes:

       App.logger
           Supply this to other instances of Shard classes.

       App.assets_class
           Class of the asset engine to be used.
           This should be adjusted from the outside after creating
           an App instance.

       App.user_interface_class
           Class of the user interface to be used.
           This should be adjusted from the outside after creating
           an App instance.

       App.server_plugin_class
           Class of the server plugin to be used.
           This should be adjusted from the outside after creating
           an App instance.
    """

    def __init__(self, loglevel, timeout = 0):
        """Initialise the application.

           loglevel is one of "d" (DEBUG), "i" (INFO), "w" (WARNING),
           "e" (ERROR), "c" (CRITICAL).

           timeout is the number of seconds after which the engine will receive
           an exit signal. This feature is meant for unit tests. timeout = 0
           will run for an unlimited time.
        """

        ### Set up logging

        self.logger = logging.getLogger()

        leveldict = {"d" : logging.DEBUG,
                     "i" : logging.INFO,
                     "w" : logging.WARNING,
                     "e" : logging.ERROR,
                     "c" : logging.CRITICAL}

        self.logger.setLevel(leveldict[loglevel])

        # STDERR console handler
        #
        # Creating an instance without arguments defaults to STDERR.
        # 
        self.stderr_handler = logging.StreamHandler()

        self.stderr_handler.setLevel(logging.DEBUG)

        # Loglevel:
        # "\x1b\x5b\x33\x32\x6d"
        # + "%(levelname)-5s "
        # + "\x1b\x5b\x33\x39\x6d"

        # Fancy coloring for Unix terminals:
        #stderr_formatter = logging.Formatter("\x1b\x5b\x33\x36\x6d"
        #                                     + "%(funcName)s() "
        #                                     + "\x1b\x5b\x33\x39\x6d"
        #                                     + "%(message)s")
        
        stderr_formatter = logging.Formatter("%(funcName)s() %(message)s")

        self.stderr_handler.setFormatter(stderr_formatter)

        # File handler
        #
        # TODO: Different file names for client and server?
        # TODO: Checking for existing file, creating a new one?
        #
        self.file_handler = logging.FileHandler(filename = "shard.log",
                                           mode = "w")

        self.file_handler.setLevel(logging.DEBUG)

        # Loglevel:
        # + "%(levelname)-5s "

        file_formatter = ShardFileFormatter("%(asctime)s %(pathname)s [%(lineno)s] %(funcName)s() : %(message)s",
                                            "%Y-%m-%d %H:%M:%S")

        self.file_handler.setFormatter(file_formatter)

        # Add handlers
        #
        self.logger.addHandler(self.stderr_handler)
        self.logger.addHandler(self.file_handler)

        # Done with logging setup.

        self.timeout = timeout

        self.assets_class = shard.assets.Assets
        self.user_interface_class = shard.plugins.ui.UserInterface
        self.server_plugin_class = shard.plugins.Plugin

    def run_client(self, framerate, interface, player_id):
        """Run a Shard client with the parameters given.
        """

        self.logger.info("running in client mode")
        self.logger.info("running with framerate {}/s".format(framerate))
        self.logger.info("player_id: {}".format(player_id))

        assets = self.assets_class(self.logger)

        plugin = self.user_interface_class(assets,
                                           framerate,
                                           self.logger)

        client = shard.core.client.Client(interface,
                                          plugin,
                                          self.logger,
                                          player_id)

        def exit():
            """Wait for some time given in App.__init__(), then emulate a server
               connection, then emulate an exit request from the client plugin
               (user interface).
            """
            sleep(self.timeout)
            client.interface.connections["server"] = shard.interfaces.MessageBuffer()
            plugin.exit_requested = True

        self.run(interface, client, exit)

    def run_server(self, framerate, interface):
        """Run a Shard server with the parameters given.
        """

        self.logger.info("running in server mode")
        self.logger.info("running with interval (framerate) {}/s".format(framerate))

        plugin = self.server_plugin_class(self.logger)

        server = shard.core.server.Server(interface,
                                          plugin,
                                          self.logger,
                                          framerate)
        def exit():
            """Wait for some time given in App.__init__(), then call
               server.handle_exit().
            """
            sleep(self.timeout)
            server.handle_exit(2, None)

        self.run(interface, server, exit)

    def run(self, interface, engine_instance, exit_function):
        """Helper method to be called from run_client() or run_server().
        """

        interface_thread = threading.Thread(target = interface.handle_messages,
                                            name = "handle_messages")
        interface_thread.start()

        # Or instead, for debugging:
        #
        #interface.handle_messages()

        # Exit trigger for non-interactive unit tests
        #
        if self.timeout > 0 and exit_function is not None:
            exit_thread = threading.Thread(target = exit_function,
                                           name = "exit_function")
            exit_thread.start()

        # This method will block until the Engine exits
        #
        engine_instance.run()

        # Engine returned. Close logger.
        # Explicitly remove handlers to avoid multiple handlers
        # when recreating the instance.
        #
        self.logger.removeHandler(self.stderr_handler)
        self.logger.removeHandler(self.file_handler)
        logging.shutdown()

    def run_standalone(self, framerate, player_id):
        """Run Shard client and server on the local machine.
        """

        # Setting up interfaces
        #
        server_interface = shard.interfaces.Interface(None, self.logger)
        server_message_buffer = shard.interfaces.MessageBuffer()
        server_interface.connections["client_connection"] = server_message_buffer

        client_interface = shard.interfaces.Interface(None, self.logger)
        client_message_buffer = shard.interfaces.MessageBuffer()
        client_interface.connections["server_connection"] = client_message_buffer

        # Proxy for use in functions
        #
        logger = self.logger

        def handle_messages():
            """Interconnect client and server Interface.
            """

            logger.debug("starting up")

            # Run thread as long as no shutdown is requested
            #
            while not (server_interface.shutdown_flag
                       or client_interface.shutdown_flag):

                if len(server_message_buffer.messages_for_remote):
                    message = server_message_buffer.messages_for_remote.popleft()
                    client_message_buffer.messages_for_local.append(message)

                if len(client_message_buffer.messages_for_remote):
                    message = client_message_buffer.messages_for_remote.popleft()
                    server_message_buffer.messages_for_local.append(message)

            # Caught shutdown notification, stopping thread
            #
            logger.info("shutting down")

            server_interface.shutdown_confirmed = True
            client_interface.shutdown_confirmed = True

            raise SystemExit

        self.logger.info("running in standalone mode, logging client and server")
        self.logger.info("running with framerate {}/s".format(framerate))
        self.logger.info("player_id: {}".format(player_id))

        # Setting up client
        #
        assets = self.assets_class(self.logger)

        user_interface = self.user_interface_class(assets,
                                                   framerate,
                                                   self.logger)

        client = shard.core.client.Client(client_interface,
                                          user_interface,
                                          self.logger,
                                          player_id)
        # Setting up server
        #
        server_plugin = self.server_plugin_class(self.logger)

        server = shard.core.server.Server(server_interface,
                                          server_plugin,
                                          self.logger,
                                          framerate)

        # Client exit function for testing
        #
        def client_exit():
            """Wait for some time given in App.__init__(), the emulate an
               UserInterface exit request.
            """
            sleep(self.timeout)
            user_interface.exit_requested = True

        # Server exit function if client exits
        #
        def server_exit():
            client_thread.join()
            #while client_thread.is_alive():
            #    sleep(1)
            #    logger.debug(threading.enumerate())
            logger.debug("client exited, calling server.handle_exit()")
            server.handle_exit(2, None)

        # Starting threads
        #
        interface_thread = threading.Thread(target = handle_messages,
                                            name = "handle_messages")
        interface_thread.start()

        client_thread = threading.Thread(target = client.run,
                                         name = "client_thread")
        client_thread.start()

        # Exit trigger for non-interactive unit tests
        #
        if self.timeout > 0:
            client_exit_thread = threading.Thread(target = client_exit,
                                                  name = "client_exit")
            client_exit_thread.start()


        server_exit_thread = threading.Thread(target = server_exit,
                                              name = "server_exit")
        server_exit_thread.start()

        # This method will block until the server exits.
        # Cannot be put in a thread since the server installs signal handlers.
        # Strangely, tracebacks in this main thread are not printed, so they
        # are logged.
        #
        exception = ''
        try:
            server.run()
        except:
            exception = traceback.format_exc()
            self.logger.debug("exception in server.run():\n{}".format(exception))

        # Just to be sure
        #
        self.logger.info("server exited, waiting for client thread to stop")
        client_thread.join()

        self.logger.info("client thread stopped, shutting down logger")

        if exception:
            self.logger.debug("exception in server.run() was:\n{}".format(exception))

        # Engine returned. Close logger.
        # Explicitly remove handlers to avoid multiple handlers
        # when recreating the instance.
        #
        self.logger.removeHandler(self.stderr_handler)
        self.logger.removeHandler(self.file_handler)
        logging.shutdown()
