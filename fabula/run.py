"""Initialise and run Fabula client and server

   Copyright 2010 Florian Berger <fberger@florian-berger.de>
"""

# This file is part of Fabula.
#
# Fabula is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Fabula is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fabula.  If not, see <http://www.gnu.org/licenses/>.

# Work started on 27. May 2008
#
# Server part adapted from run_shardclient.py on 25. Sep 2009
#
# Unfied for client and server usage on 30. Sep 2009
#
# Converted from run_shard.py on 06. Oct 2009

import fabula.assets
import fabula.core.client
import fabula.core.server
import fabula.plugins.ui
import fabula.interfaces

import threading
import logging
from time import sleep
import traceback
import re
import configparser

class App:
    """An App instance represents a Fabula client or server application.

       Attributes:

       App.parser
           An instance of configparser.ConfigParser reading from fabula.conf, or
           None if the file is not found.

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

    def __init__(self, timeout = 0):
        """Initialise the application.

           timeout is the number of seconds after which the engine will receive
           an exit signal. This feature is meant for unit tests. timeout = 0
           will run for an unlimited time.
        """

        # Initialise parser and read config file
        #
        self.parser = configparser.ConfigParser()

        if not len(self.parser.read("fabula.conf")):

            self.parser = None

        # Set up logger level
        #
        if self.parser is not None and self.parser.has_option("fabula", "loglevel"):

            leveldict = {"debug" : logging.DEBUG,
                         "info" : logging.INFO,
                         "warning" : logging.WARNING,
                         "error" : logging.ERROR,
                         "critical" : logging.CRITICAL}

            if self.parser.get("fabula", "loglevel") in leveldict.keys():

                fabula.LOGGER.setLevel(leveldict[self.parser.get("fabula", "loglevel")])

                fabula.LOGGER.info("found loglevel option in fabula.conf, setting loglevel to '{}'".format(self.parser.get("fabula", "loglevel")))

        else:

            fabula.LOGGER.setLevel(logging.ERROR)

        self.timeout = timeout

        self.assets_class = fabula.assets.Assets
        self.user_interface_class = fabula.plugins.ui.UserInterface
        self.server_plugin_class = fabula.plugins.Plugin

    def run_client(self, framerate, interface):
        """Run a Fabula client with the parameters given.
        """

        fabula.LOGGER.info("running in client mode")
        fabula.LOGGER.info("running with framerate {}/s".format(framerate))

        assets = self.assets_class()

        client = fabula.core.client.Client(interface)

        fullscreen = False

        if self.parser is not None and self.parser.has_option("fabula", "fullscreen"):

            if self.parser.get("fabula", "fullscreen").lower() in ("true", "yes", "1"):

                fabula.LOGGER.info("found fullscreen option in fabula.conf, going fullscreen")

                fullscreen = True

        plugin = self.user_interface_class(assets,
                                           framerate,
                                           client,
                                           fullscreen)

        client.set_plugin(plugin)

        def exit():
            """Wait for some time given in App.__init__(), then emulate a server
               connection, then emulate an exit request from the client plugin
               (user interface).
            """
            sleep(self.timeout)
            client.interface.connections["server"] = fabula.interfaces.MessageBuffer()
            plugin.exit_requested = True

        self.run(interface, client, exit)

    def run_server(self, framerate, interface, action_time):
        """Run a Fabula server with the parameters given.
        """

        fabula.LOGGER.info("running in server mode")
        fabula.LOGGER.info("running with interval (framerate) {}/s".format(framerate))

        # Since the Server will run in the main thread, signal handlers can
        # be installed.
        #
        server = fabula.core.server.Server(interface,
                                          framerate,
                                          action_time,
                                          threadsafe = False)

        plugin = self.server_plugin_class(server)

        server.set_plugin(plugin)

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
        fabula.LOGGER.removeHandler(fabula.STDERR_HANDLER)
        fabula.LOGGER.removeHandler(fabula.FILE_HANDLER)
        logging.shutdown()

    def run_standalone(self, framerate, action_time):
        """Run Fabula client and server on the local machine.
        """

        fabula.LOGGER.info("running in standalone mode, logging client and server")
        fabula.LOGGER.info("running with framerate {}/s".format(framerate))

        # Setting up interfaces
        #
        server_interface = fabula.interfaces.StandaloneInterface(framerate)

        client_interface = fabula.interfaces.StandaloneInterface(framerate)

        server_interface.connect("client")
        client_interface.connect("server")

        # Setting up client
        #
        assets = self.assets_class()

        client = fabula.core.client.Client(client_interface)

        # TODO: copied from above
        #
        fullscreen = False

        if self.parser is not None and self.parser.has_option("fabula", "fullscreen"):

            if self.parser.get("fabula", "fullscreen").lower() in ("true", "yes", "1"):

                fabula.LOGGER.info("found fullscreen option in fabula.conf, going fullscreen")

                fullscreen = True

        user_interface = self.user_interface_class(assets,
                                                   framerate,
                                                   client,
                                                   fullscreen)

        client.set_plugin(user_interface)

        # Setting up server
        #
        server = fabula.core.server.Server(server_interface,
                                           framerate,
                                           action_time,
                                           threadsafe = True)

        server_plugin = self.server_plugin_class(server)

        server.set_plugin(server_plugin)

        # Client exit function for testing
        #
        def client_exit():
            """Wait for some time given in App.__init__(), the emulate an
               UserInterface exit request.
            """
            sleep(self.timeout)
            user_interface.exit_requested = True

        # Starting threads
        # Interconnecting client and server Interfaces here
        #
        client_interface_thread = threading.Thread(target = client_interface.handle_messages,
                                                   name = "client_handle_messages",
                                                   args = (server_interface.connections["client"],))

        client_interface_thread.start()

        server_interface_thread = threading.Thread(target = server_interface.handle_messages,
                                                   name = "server_handle_messages",
                                                   args = (client_interface.connections["server"],))

        server_interface_thread.start()

        # Client must run in main thread to be able to interact properly
        # with the OS (think Pygame events). So we put the server in a thread.
        #
        server_thread = threading.Thread(target = server.run,
                                         name = "server_thread")
        server_thread.start()

        # Exit trigger for non-interactive unit tests
        #
        if self.timeout > 0:
            client_exit_thread = threading.Thread(target = client_exit,
                                                  name = "client_exit")
            client_exit_thread.start()

        # This method will block until the client exits.
        # Strangely, tracebacks in this main thread are not printed, so they
        # are logged.
        #
        exception = ''

        try:
            client.run()

        except:
            exception = traceback.format_exc()
            fabula.LOGGER.info("exception in client.run():\n{}".format(exception))

        fabula.LOGGER.info("client exited, calling server.handle_exit()")
        server.handle_exit(2, None)

        fabula.LOGGER.info("waiting for server thread to stop")
        server_thread.join()

        fabula.LOGGER.info("server thread stopped, shutting down logger")

        if exception:
            fabula.LOGGER.info("exception in client.run() was:\n{}".format(exception))

        fabula.LOGGER.info("log file written to fabula.log")

        # Engine returned. Close logger.
        # Explicitly remove handlers to avoid multiple handlers
        # when recreating the instance.
        #
        fabula.LOGGER.removeHandler(fabula.STDERR_HANDLER)
        fabula.LOGGER.removeHandler(fabula.FILE_HANDLER)
        logging.shutdown()
