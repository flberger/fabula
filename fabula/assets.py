"""Fabula Asset Manager

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

# Extracted from shard.py on 22. Sep 2009
#
# Extension to perform actual fetches started on 18. Oct 2010, using work from
# the LocalFileAssetEngine written for the "Runaway" game in Oct-Dec 2009, which
# in turn was based on the LocalFileAssetEngine from the CharanisMLClient
# developed in May 2008.

import fabula
import os.path
import glob
import site
import sys

class Assets:
    """An assets manager which returns file-like objects for local files.
       It is used to retrieve media data - images, animations, 3D models, sound.
    """

    def __init__(self):
        """Initialise.
        """

        # TODO: Since an Assets instance is created only once, fetch() should do some asset caching (self.asset_dict) to prevent unnecessary file or network access. Problem: memory usage has to be limited. Probably use temporary files for downloaded assets?
        # TODO: Add a function to cache an object associated with an asset description.

        return

    def fetch(self, asset_desc):
        """This method retrieves the file specified in asset_desc and returns a file-like object.
           Since fetch() is a synchronous method, it will cancel after a timeout
           and raise a Exception if it failes to retrieve the data.
           This method actually is a dispatcher to more specialised methods.
        """

        fabula.LOGGER.debug("unknown asset '{}', attempting to fetch".format(asset_desc))

        if (asset_desc.startswith("http://") or asset_desc.startswith("ftp://")):

            return self.fetch_uri(asset_desc)

        elif asset_desc.lower().endswith(".zip"):

            return self.fetch_zip_file(asset_desc)

        else:

            return self.fetch_local_file(asset_desc)

    def fetch_uri(self, asset_desc):

        # TODO: timeout!

        errormessage = ("Assets.fetch_uri() is not implemented")

        fabula.LOGGER.critical(errormessage)

        raise Exception(errormessage)

    def fetch_zip_file(self, asset_desc):
        """This method reads a ZIP file and returns a dict with the asset_desc minus extension as keys and a PyGame surface as values.
           The file name must contain only one dot right before the extension.
           You are strongly advised to call Surface.convert() for each surface
           once you have set up your display.
        """

#        surface_dict = {}
#        zip_file = zipfile.ZipFile(asset_desc, 'r')
#
#        for name in zip_file.namelist():
#
#            fabula.LOGGER.info("retrieving %s from ZIP file %s" % (name, asset_desc))
#
#            string_io = StringIO.StringIO(zip_file.read(name))
#
#            # Dict key is file name cut behind the
#            # first dot.
#            #
#            # Using load(fileobject, namehint)
#            #
#            surface_dict[name.split('.')[0]] = pygame.image.load(string_io, name)
#
#        zip_file.close()
#
#        return surface_dict

        errormessage = ("Assets.fetch_zip_file() is not implemented")

        fabula.LOGGER.critical(errormessage)

        raise Exception(errormessage)

    def fetch_local_file(self, asset_desc):
        """This method returns a a file-like object for the file specified.
        """

        # TODO: check the script base directory?

        if os.path.exists(asset_desc):

            pass

        # Look in script base directory
        #
        elif os.path.exists(os.path.join(sys.path[0], asset_desc)):

            asset_desc = os.path.join(sys.path[0], asset_desc)

        # Look in parent directory
        #
        elif os.path.exists(os.path.join(os.path.abspath(".."), asset_desc)):

            asset_desc = os.path.join(os.path.abspath(".."), asset_desc)

        # Look in subdirectories
        #
        elif glob.glob("./*/" + asset_desc):

            # Take first match
            #
            asset_desc = os.path.abspath(glob.glob("./*/" + asset_desc)[0])

        # Look in sibling directories
        #
        elif glob.glob("../*/" + asset_desc):

            # Take first match
            #
            asset_desc = os.path.abspath(glob.glob("../*/" + asset_desc)[0])

        # Look in user base directory
        #
        elif os.path.exists(os.path.join(site.USER_BASE, "share", "fabula", asset_desc)):

            asset_desc = os.path.join(site.USER_BASE, "share", "fabula", asset_desc)

        else:

            # Up to now, nothing has been found.
            #
            found = False

            # Check prefixes
            #
            for prefix in site.PREFIXES:

                if os.path.exists(os.path.join(prefix, "share", "fabula", asset_desc)):

                    asset_desc = os.path.join(prefix, "share", "fabula", asset_desc)

                    found = True

            if not found:

                errormessage = "Could not open asset: '{}'".format(asset_desc)

                fabula.LOGGER.critical(errormessage)

                raise Exception(errormessage)

                return

        fabula.LOGGER.info("attempting to retrieve '{}' from local file".format(asset_desc))

        file = open(asset_desc, mode='rb')

        fabula.LOGGER.debug("returning {}".format(file))

        return file
