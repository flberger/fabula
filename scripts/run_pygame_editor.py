#!/usr/bin/python3

"""Pygame Editor for Fabula start script

   (c) Florian Berger <fberger@florian-berger.de>
"""

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
