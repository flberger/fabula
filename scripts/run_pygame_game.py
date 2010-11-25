"""Pygame Client for Shard start script

   (c) Florian Berger <fberger@florian-berger.de>
"""

# work started on 31. Oct 2010

import sys

# Add current and parent directory. One of them is supposed to contain the shard
# package.
#
sys.path.append("../")
sys.path.append("./")

import shard.plugins.pygameui
import shard.plugins.serverside
import shard.run

def main():
    app = shard.run.App("d", timeout = 0)
    app.user_interface_class = shard.plugins.pygameui.PygameUserInterface
    app.server_plugin_class = shard.plugins.serverside.DefaultGame
    app.run_standalone(60, "player")

if __name__ == "__main__":

    main()
