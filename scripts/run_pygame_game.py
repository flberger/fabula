#!/usr/bin/python3

"""Pygame Client for Fabula start script

   (c) Florian Berger <fberger@florian-berger.de>
"""

# work started on 31. Oct 2010

import sys

# Add current and parent directory. One of them is supposed to contain the fabula
# package.
#
sys.path.append("../")
sys.path.append("./")

import fabula.plugins.pygameui
import fabula.plugins.serverside
import fabula.run

def main():
    app = fabula.run.App("d", timeout = 0)
    app.user_interface_class = fabula.plugins.pygameui.PygameUserInterface
    app.server_plugin_class = fabula.plugins.serverside.DefaultGame
    app.run_standalone(60, "player")

if __name__ == "__main__":

    main()
