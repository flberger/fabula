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

import sys
import traceback
import re

class FabulaFileFormatter(logging.Formatter):
    """Subclass of Formatter with reasonable module information.
    """

    def __init__(self, fmt, datefmt):
        """Compile a regular expression object, then call base class __init__().
        """
        logging.Formatter.__init__(self, fmt, datefmt)

        self.module_re = re.compile("^.*fabula/([^/]+/)*?([^/]+)(/__init__)*.py$")

    def format(self, record):
        """Override logging.Formatter.format()
        """

        # Reformat path to module information
        #
        record.pathname = "{:10}".format(self.module_re.sub(r"\2", record.pathname))

        # Fixed-length line number
        #
        #record.lineno = "{:3}".format(record.lineno)

        # Call base class implementation
        #
        return logging.Formatter.format(self, record)

class App:
    """An App instance represents a Fabula client or server application.

       Attributes:

       App.logger
           Supply this to other instances of Fabula classes.

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
        self.file_handler = logging.FileHandler(filename = "fabula.log",
                                           mode = "w")

        self.file_handler.setLevel(logging.DEBUG)

        # Loglevel:
        # + "%(levelname)-5s "

        file_formatter = FabulaFileFormatter("%(asctime)s  %(pathname)s %(funcName)s() --- %(message)s (l.%(lineno)s)",
                                            "%Y-%m-%d %H:%M:%S")

        self.file_handler.setFormatter(file_formatter)

        # Add handlers
        #
        self.logger.addHandler(self.stderr_handler)
        self.logger.addHandler(self.file_handler)

        # Done with logging setup.

        self.timeout = timeout

        self.assets_class = fabula.assets.Assets
        self.user_interface_class = fabula.plugins.ui.UserInterface
        self.server_plugin_class = fabula.plugins.Plugin

    def run_client(self, framerate, interface, fullscreen = False):
        """Run a Fabula client with the parameters given.
        """

        self.logger.info("running in client mode")
        self.logger.info("running with framerate {}/s".format(framerate))

        assets = self.assets_class(self.logger)

        client = fabula.core.client.Client(interface,
                                           self.logger)

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

        self.logger.info("running in server mode")
        self.logger.info("running with interval (framerate) {}/s".format(framerate))

        # Since the Server will run in the main thread, signal handlers can
        # be installed.
        #
        server = fabula.core.server.Server(interface,
                                          self.logger,
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
        self.logger.removeHandler(self.stderr_handler)
        self.logger.removeHandler(self.file_handler)
        logging.shutdown()

    def run_standalone(self, framerate, action_time, fullscreen = False):
        """Run Fabula client and server on the local machine.
        """

        self.logger.info("running in standalone mode, logging client and server")
        self.logger.info("running with framerate {}/s".format(framerate))

        # Setting up interfaces
        #
        server_interface = fabula.interfaces.StandaloneInterface(self.logger,
                                                                 framerate)

        client_interface = fabula.interfaces.StandaloneInterface(self.logger,
                                                                 framerate)

        server_interface.connect("client")
        client_interface.connect("server")

        # Setting up client
        #
        assets = self.assets_class(self.logger)

        client = fabula.core.client.Client(client_interface,
                                           self.logger)

        user_interface = self.user_interface_class(assets,
                                                   framerate,
                                                   client,
                                                   fullscreen)

        client.set_plugin(user_interface)

        # Setting up server
        #
        server = fabula.core.server.Server(server_interface,
                                           self.logger,
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
            self.logger.debug("exception in client.run():\n{}".format(exception))

        self.logger.debug("client exited, calling server.handle_exit()")
        server.handle_exit(2, None)

        self.logger.debug("waiting for server thread to stop")
        server_thread.join()

        self.logger.info("server thread stopped, shutting down logger")

        if exception:
            self.logger.debug("exception in client.run() was:\n{}".format(exception))

        self.logger.info("log file written to fabula.log")

        # Engine returned. Close logger.
        # Explicitly remove handlers to avoid multiple handlers
        # when recreating the instance.
        #
        self.logger.removeHandler(self.stderr_handler)
        self.logger.removeHandler(self.file_handler)
        logging.shutdown()
