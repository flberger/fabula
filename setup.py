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

import sys

# Fabula will not work with Python versions prior to 3.x.
#
if sys.version_info[0] != 3:
    raise Exception("fabula needs Python 3 to work. Your Python version is: " + sys.version)

import glob
import os.path
import fabula

# Fallback
#
from distutils.core import setup

SCRIPTS = glob.glob(os.path.join("scripts", "*.py"))

EXECUTABLES = []

try:
    import cx_Freeze

    setup = cx_Freeze.setup

    # Collect all Python scripts in the 'script' directory
    #
    EXECUTABLES = [cx_Freeze.Executable(path) for path in SCRIPTS]

except ImportError:

    print("Warning: the cx_Freeze module could not be imported. You will not be able to build binary packages.")

PACKAGE = "fabula"

INCLUDE_FILES = [os.path.join("scripts", "100x100-gray.png"),
                 os.path.join("scripts", "attempt_look_at.png"),
                 os.path.join("scripts", "attempt_manipulate.png"),
                 os.path.join("scripts", "attempt_talk_to.png"),
                 os.path.join("scripts", "cancel.png"),
                 os.path.join("scripts", "splash.png"),
                 os.path.join("scripts", "inventory.png"),
                 os.path.join("scripts", "fabula.conf")]

# Include clickndrag resources
#
import fabula.plugins.pygameui as pygamui

INCLUDE_FILES.extend(glob.glob(os.path.join("fabula",
                                            "plugins",
                                            "pygameui",
                                            "clickndrag",
                                            "gui",
                                            "resources",
                                            "*.png")))

INCLUDE_FILES.extend(glob.glob(os.path.join("fabula",
                                            "plugins",
                                            "pygameui",
                                            "clickndrag",
                                            "gui",
                                            "resources",
                                            "*.ttf")))

# Include default room
#
INCLUDE_FILES.extend([os.path.join("scripts", "default.floorplan"),
                      os.path.join("scripts", "default.logic"),
                      os.path.join("scripts", "apple.png"),
                      os.path.join("scripts", "axe.png"),
                      os.path.join("scripts", "key.png"),
                      os.path.join("scripts", "player-fabulasheet.png"),
                      os.path.join("scripts", "potion.png"),
                      os.path.join("scripts", "shield.png"),
                      os.path.join("scripts", "sword.png"),
                      os.path.join("scripts", "tree_large.png"),
                      os.path.join("scripts", "tree_small.png")])

INCLUDE_FILES.extend(glob.glob(os.path.join("scripts", "default-*.png")))

if sys.platform == "win32":
    INCLUDE_FILES.append(os.path.join(sys.prefix, "tcl", "tcl8.5"))
    INCLUDE_FILES.append(os.path.join(sys.prefix, "tcl", "tk8.5"))

# For most operations, cx_Freeze.setup() is a wrapper for distutils.core.setup().
# The syntax for the "include_files" option to "build_exe" is [(src, target), ...]
#
setup(name = PACKAGE,
      version = fabula.VERSION,
      author = "Florian Berger",
      author_email = "fberger@florian-berger.de",
      url = "http://fabula-engine.org/",
      description = "An Open Source Python Game Engine suitable for adventure, role-playing and strategy games and digital interactive storytelling.",
      license = "GPL",
      packages = [PACKAGE,
                  "{}.core".format(PACKAGE),
                  "{}.interfaces".format(PACKAGE),
                  "{}.plugins".format(PACKAGE),
                  "{}.plugins.pygameui".format(PACKAGE),
                  "{}.plugins.pygameui.clickndrag".format(PACKAGE),
                  "{}.plugins.pygameui.clickndrag.gui".format(PACKAGE)],
      py_modules = [],
      requires = ["pygame (>=1.9.1)"],
      provides = [PACKAGE,
                  "{}.core".format(PACKAGE),
                  "{}.interfaces".format(PACKAGE),
                  "{}.plugins".format(PACKAGE),
                  "{}.plugins.pygameui".format(PACKAGE),
                  "{}.plugins.pygameui.clickndrag".format(PACKAGE),
                  "{}.plugins.pygameui.clickndrag.gui".format(PACKAGE)],
      package_data = {},
      scripts = SCRIPTS,
      data_files = [(os.path.join("share", "doc", "{}-{}").format(PACKAGE, fabula.VERSION),
                     glob.glob(os.path.join("doc", "*.*")) + ["README", "NEWS"]),
                    (os.path.join("share", "{}").format(PACKAGE),
                     INCLUDE_FILES)],
      executables = EXECUTABLES,
      options = {"build_exe" :
                 {"include_files" :
                  [(path, os.path.basename(path)) for path in INCLUDE_FILES]
                 }
                })
