#!/usr/bin/python3

"""Pygame Editor for Fabula start script

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

# work started on 27. Oct 2010

import sys

# Add current and parent directory. One of them is supposed to contain the fabula
# package.
#
sys.path.append("../")
sys.path.append("./")

import fabula.plugins.serverside
import fabula.interfaces
import fabula.run

def main():
    app = fabula.run.App("d", timeout = 0)

    interface = fabula.interfaces.Interface("dummy", app.logger)

    message_buffer = fabula.interfaces.MessageBuffer()
    message_buffer.messages_for_local.append(fabula.Message([fabula.InitEvent("player")]))

    interface.connections["dummy_client"] = message_buffer

    app.server_plugin_class = fabula.plugins.serverside.Editor

    app.run_server(60, interface)

if __name__ == "__main__":

    main()
