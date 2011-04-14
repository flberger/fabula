"""Fabula Setup Script

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

# work started on 10. December 2010

# Fabula will not work with Python versions prior to 3.x.
#
import sys

if sys.version_info[0] != 3:
    raise Exception("fabula needs Python 3 to work. Your Python version is: " + sys.version)

# Imported by cx_Freeze
#
#import distutils.core
import cx_Freeze
import glob
import os.path

PACKAGE = "fabula"
VERSION = "0.5.0"

INCLUDE_FILES = [os.path.join("scripts", "100x100-gray.png"),
                 os.path.join("scripts", "attempt_look_at.png"),
                 os.path.join("scripts", "attempt_manipulate.png"),
                 os.path.join("scripts", "attempt_talk_to.png"),
                 os.path.join("scripts", "cancel.png"),
                 os.path.join("scripts", "player.png"),
                 os.path.join("scripts", "splash.png"),
                 os.path.join("scripts", "inventory.png"),
                 os.path.join("scripts", "fabula.conf"),
                 os.path.join("clickndrag", "Vera.ttf"),
                 os.path.join("clickndrag", "VeraBd.ttf")]

# Include default room
#
INCLUDE_FILES.extend([os.path.join("scripts", "default.floorplan"),
                      os.path.join("scripts", "default.logic"),
                      os.path.join("scripts", "gem.png"),
                      os.path.join("scripts", "key.png")])

INCLUDE_FILES.extend(glob.glob(os.path.join("scripts", "default-*.png")))

if sys.platform == "win32":
    INCLUDE_FILES.append(os.path.join(sys.prefix, "tcl", "tcl8.5"))
    INCLUDE_FILES.append(os.path.join(sys.prefix, "tcl", "tk8.5"))

# For most operations, cx_Freeze.setup() is a wrapper for distutils.core.setup().
# The syntax for the "include_files" option to "build_exe" is [(src, target), ...]
#
cx_Freeze.setup(name = PACKAGE,
                version = VERSION,
                author = "Florian Berger",
                author_email = "fberger@florian-berger.de",
                url = "http://florian-berger.de/software/{}/".format(PACKAGE),
                description = "An Open Source Python Game Engine suitable for adventure, role-playing and strategy games and digital interactive storytelling.",
                license = "GPL",
                packages = [PACKAGE,
                            "{}.core".format(PACKAGE),
                            "{}.interfaces".format(PACKAGE),
                            "{}.plugins".format(PACKAGE),
                            "clickndrag"],
                requires = ["pygame (>=1.9.1)"],
                provides = [PACKAGE,
                            "{}.core".format(PACKAGE),
                            "{}.interfaces".format(PACKAGE),
                            "{}.plugins".format(PACKAGE),
                            "clickndrag"],
                package_data = {"clickndrag" : ["Vera.ttf", "VeraBd.ttf"]},
                scripts = [os.path.join("scripts", "run_pygame_editor.py"),
                           os.path.join("scripts", "run_pygame_game.py")],
                data_files = [(os.path.join("share", "doc", "{}-{}").format(PACKAGE, VERSION),
                               glob.glob(os.path.join("doc", "*.*")) + ["README", "NEWS"]),
                              (os.path.join("share", "{}").format(PACKAGE),
                               INCLUDE_FILES)],
                executables = [cx_Freeze.Executable(os.path.join("scripts", "run_pygame_editor.py")),
                               cx_Freeze.Executable(os.path.join("scripts", "run_pygame_game.py"))],
                options = {"build_exe" :
                           {"include_files" :
                            [(path, os.path.basename(path)) for path in INCLUDE_FILES]
                           }
                          })
