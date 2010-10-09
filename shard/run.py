"""Initialize and run Shard client and server

   (c) Florian Berger <fberger@florian-berger.de>
"""

# Work started on 27. May 2008
#
# Server part adapted from run_shardclient.py on 25. Sep 2009
#
# Unfied for client and server usage on 30. Sep 2009
#
# Converted from run_shard.py on 06. Oct 2009

import shard.assetengine
import shard.presentationengine
import shard.clientcoreengine
import shard.plugin
import shard.servercoreengine

import _thread
import logging
from time import sleep

class App:
    """An App instance represents a Shard client or server application.

       Attributes:

       App.logger
           Supply this to other instances of Shard classes.

       App.asset_engine_class
           Class of the asset engine to be used.
           This should be adjusted from the outside after creating
           an App instance.

       App.presentation_engine_class
           Class of the presentation engine to be used.
           This should be adjusted from the outside after creating
           an App instance.

       App.server_plugin_class
           Class of the server plugin to be used.
           This should be adjusted from the outside after creating
           an App instance.
    """

    def __init__(self, loglevel, test = False):
        """Initialise the application.

           loglevel is one of "d" (DEBUG), "i" (INFO), "w" (WARNING),
           "e" (ERROR), "c" (CRITICAL).

           When called with test = True, the core engine will receive an
           exit signal after some seconds. This feature is meant for unit tests.
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
        stderr_handler = logging.StreamHandler()

        stderr_handler.setLevel(logging.DEBUG)

        # Loglevel:
        # "\x1b\x5b\x33\x32\x6d"
        # + "%(levelname)-5s "
        # + "\x1b\x5b\x33\x39\x6d"

        stderr_formatter = logging.Formatter("\x1b\x5b\x33\x36\x6d"
                                             + "%(funcName)s() "
                                             + "\x1b\x5b\x33\x39\x6d"
                                             + "%(message)s")

        stderr_handler.setFormatter(stderr_formatter)

        # File handler
        # TODO: Different file names for client and server?
        # TODO: Checking for existing file, creating a new one?
        #
        file_handler = logging.FileHandler(filename = "shard.log",
                                           mode = "w")

        file_handler.setLevel(logging.DEBUG)

        # Loglevel:
        # + "%(levelname)-5s "

        file_formatter = logging.Formatter("%(asctime)s "
                                           + "%(filename)s [%(lineno)s] %(funcName)s() : %(message)s"
                                           ,
                                           "%Y-%m-%d %H:%M:%S")

        file_handler.setFormatter(file_formatter)

        # Add handlers
        #
        self.logger.addHandler(stderr_handler)

        self.logger.addHandler(file_handler)

        # Done with logging setup.

        self.test = test

        self.asset_engine_class = shard.assetengine.AssetEngine
        self.presentation_engine_class = shard.presentationengine.PresentationEngine
        self.server_plugin_class = shard.plugin.Plugin

    def run_client(self, framerate, interface, player_id):
        """Run a Shard client with the parameters given.
        """

        self.logger.info("running in client mode")
        self.logger.info("running with framerate {}/s".format(framerate))
        self.logger.info("player_id: {}".format(player_id))

        asset_engine = self.asset_engine_class(self.logger)

        plugin = self.presentation_engine_class(asset_engine,
                                                framerate,
                                                self.logger)

        client = shard.clientcoreengine.ClientCoreEngine(interface,
                                                         plugin,
                                                         self.logger,
                                                         player_id)

        def exit():
            from shard.interfaces import MessageBuffer
            sleep(3)
            client.interface.connections["server"] = MessageBuffer()
            plugin.exit_requested = True

        self.run(interface, client, exit)

    def run_server(self, framerate, interface):
        """Run a Shard server with the parameters given.
        """

        self.logger.info("running in server mode")
        self.logger.info("running with interval (framerate) {}/s".format(framerate))

        plugin = self.server_plugin_class(self.logger)

        server = shard.servercoreengine.ServerCoreEngine(interface,
                                                         plugin,
                                                         self.logger,
                                                         framerate)
        def exit():
            sleep(3)
            server.handle_exit(2, None)

        self.run(interface, server, exit)

    def run(self, interface, core_engine_instance, exit_function):
        """Helper method to be called from run_client() or run_server().
        """

        _thread.start_new_thread(interface.handle_messages, ())

        # Or instead, for debugging:
        #
        #interface.handle_messages()

        # Exit trigger for non-interactive unit tests
        #
        if self.test and exit_function is not None:
            _thread.start_new_thread(exit_function, ())

        # This method will block until the CoreEngine exits
        #
        core_engine_instance.run()

        # CoreEngine returned. Close logger.
        #
        logging.shutdown()
