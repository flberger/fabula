"""Shard Setup Script

   (c) Florian Berger <fberger@florian-berger.de>
"""

# work started on 10. December 2010

import distutils.core

# TODO: add scripts/Vera.ttf to package_data?
#
distutils.core.setup(name = "Shard",
                     version = "0.1.0a1",
                     author = "Florian Berger",
                     author_email = "fberger@florian-berger.de",
                     url = "http://florian-berger.de/software/shard/",
                     description = "A Client-Server System for Interactive Storytelling by means of an Adventure Game Environment - 'Stories On A Grid'",
                     license = "GPL",
                     packages = ["shard",
                                 "shard.core",
                                 "shard.interfaces",
                                 "shard.plugins"],
                     requires = ["clickndrag",
                                 "clickndrag.gui",
                                 "pygame (>=1.9.1)"],
                     provides = ["shard",
                                 "shard.core",
                                 "shard.interfaces",
                                 "shard.plugins"],
                     scripts = ["scripts/run_pygame_editor.py",
                                "scripts/run_pygame_game.py"],
                     package_data = {"shard" : ["doc/*",
                                                "scripts/100x100-gray.png",
                                                "scripts/look_at.png",
                                                "scripts/manipulate.png",
                                                "scripts/player.png",
                                                "scripts/talk_to.png"]})
