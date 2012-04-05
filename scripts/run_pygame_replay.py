#!/usr/bin/python3

"""Pygame Replay Client for Fabula start script

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

import sys

# Add current and parent directory. One of them is supposed to contain the fabula
# package.
#
sys.path.append("../")
sys.path.append("./")

import fabula.plugins.pygameui
import fabula.plugins.ui
import fabula.interfaces.replay
import fabula.run

class ReplayPygameUserInterface(fabula.plugins.pygameui.PygameUserInterface):
    """A PygameUserInterface that does not display CanSpeakEvents.
    """

    def process_CanSpeakEvent(self, event):
        """Silently discard the CanSpeakEvent.
        """

        fabula.LOGGER.info("discarding '{}' in replay".format(event))

        return

if __name__ == "__main__":

    app = fabula.run.App(timeout = 0)
    app.user_interface_class = ReplayPygameUserInterface
    app.run_client(30, fabula.interfaces.replay.PythonReplayInterface)
