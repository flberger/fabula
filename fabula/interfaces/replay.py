"""Fabula Replay Interfaces

   Copyright 2012 Florian Berger <fberger@florian-berger.de>
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

# Work started on 05 Apr 2012
#
# Based on ReplayInterface from Shard's replay_interface.py,
# work started on 7. Dec 2009

import fabula.interfaces
import sys
import logging
from time import sleep

# Set up stdout logger
#
LOGGER = logging.getLogger("fabula.replay")

STDOUT_HANDLER = logging.StreamHandler(sys.stdout)
STDOUT_HANDLER.setLevel(logging.DEBUG)

LOGGER.addHandler(STDOUT_HANDLER)

class PythonReplayInterface(fabula.interfaces.Interface):
    """An Interface which replays Python message logs.
    """

    def handle_messages(self):
        """Read a file created by Interface.log_message(), and fill MessageBuffer.messages_for_local with these messages.
        """

        fabula.LOGGER.debug("opening file 'messages.log'")

        # Default to 'messages.log', see Interface.log_message()
        #
        message_log_file = open("messages.log", "rt")

        fabula.LOGGER.debug("reading data")

        # TODO: read and process line by line to save memory
        #
        data = message_log_file.read()

        #fabula.LOGGER.debug("data read: '{}'".format(data))

        fabula.LOGGER.debug("closing file")

        message_log_file.close()

        message_log = []

        for tab_separated in data.split("\n\n"):

            if len(tab_separated):

                # Append a tuple (float, Message)
                #
                message_log.append((float(tab_separated.split("\t")[0]),
                                    eval(tab_separated.split("\t")[1])))

        LOGGER.info("wating for first connection")
        fabula.LOGGER.info("wating for first connection")

        while not self.connections:

            # No need to run as fast as possible
            #
            sleep(1/60)

        LOGGER.info("connection found: '{}'".format(list(self.connections.keys())[0]))
        fabula.LOGGER.info("connection found: '{}'".format(list(self.connections.keys())[0]))

        message_buffer = list(self.connections.values())[0]

        # Fill MessageBuffer.messages_for_local with messages from the file.
        #
        while message_log and not self.shutdown_flag:

            time_message_tuple = message_log.pop(0)

            LOGGER.debug("sleeping {} s".format(time_message_tuple[0]))
            fabula.LOGGER.debug("sleeping {} s".format(time_message_tuple[0]))

            sleep(time_message_tuple[0])

            LOGGER.debug("adding message: {}".format(time_message_tuple[1]))
            fabula.LOGGER.debug("adding message: {}".format(time_message_tuple[1]))

            message_buffer.messages_for_local.append(time_message_tuple[1])

            LOGGER.debug("{} messages left for replay".format(len(message_log)))
            fabula.LOGGER.debug("{} messages left for replay".format(len(message_log)))

        LOGGER.info("done with replay or shutdown request")
        fabula.LOGGER.info("done with replay or shutdown request")

        # Run thread as long as no shutdown is requested
        #
        while not self.shutdown_flag:

            # No need to run as fast as possible
            #
            sleep(1/60)

        # Caught shutdown notification, stopping thread
        #
        fabula.LOGGER.info("shutting down")

        self.shutdown_confirmed = True

        raise SystemExit
