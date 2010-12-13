"""Shard Setup Script

   (c) Florian Berger <fberger@florian-berger.de>
"""

# work started on 10. December 2010

import distutils.core
import glob
import os.path

PACKAGE = "shard"
VERSION = "0.1.0a1"

# TODO: add scripts/Vera.ttf to package_data?
#
distutils.core.setup(name = PACKAGE,
                     version = VERSION,
                     author = "Florian Berger",
                     author_email = "fberger@florian-berger.de",
                     url = "http://florian-berger.de/software/{}/".format(PACKAGE),
                     description = "A Client-Server System for Interactive Storytelling by means of an Adventure Game Environment - 'Stories On A Grid'",
                     license = "GPL",
                     packages = [PACKAGE,
                                 "{}.core".format(PACKAGE),
                                 "{}.interfaces".format(PACKAGE),
                                 "{}.plugins".format(PACKAGE)],
                     requires = ["clickndrag",
                                 "clickndrag.gui",
                                 "pygame (>=1.9.1)"],
                     provides = [PACKAGE,
                                 "{}.core".format(PACKAGE),
                                 "{}.interfaces".format(PACKAGE),
                                 "{}.plugins".format(PACKAGE)],
                     scripts = ["scripts/run_pygame_editor.py",
                                "scripts/run_pygame_game.py"],
                     data_files = [("share/doc/{}-{}".format(PACKAGE, VERSION),
                                    glob.glob(os.path.join("doc", "*.*"))),
                                   ("share/{}".format(PACKAGE),
                                    ["scripts/100x100-gray.png",
                                     "scripts/look_at.png",
                                     "scripts/manipulate.png",
                                     "scripts/player.png",
                                     "scripts/talk_to.png"])])
