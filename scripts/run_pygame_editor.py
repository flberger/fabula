#!/usr/bin/python3

"""Pygame Editor for Shard start script

   (c) Florian Berger <fberger@florian-berger.de>
"""

# work started on 27. Oct 2010

import sys

# Add current and parent directory. One of them is supposed to contain the shard
# package.
#
sys.path.append("../")
sys.path.append("./")

import shard.plugins.serverside
import shard.interfaces
import shard.run

def main():
    app = shard.run.App("d", timeout = 0)

    interface = shard.interfaces.Interface("dummy", app.logger)

    message_buffer = shard.interfaces.MessageBuffer()
    message_buffer.messages_for_local.append(shard.Message([shard.InitEvent("player")]))

    interface.connections["dummy_client"] = message_buffer

    app.server_plugin_class = shard.plugins.serverside.Editor

    app.run_server(60, interface)

if __name__ == "__main__":

    main()
