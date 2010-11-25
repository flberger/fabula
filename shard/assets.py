"""Shard Asset Manager
"""

# Extracted from shard.py on 22. Sep 2009
#
# Extension to perform actual fetches started on 18. Oct 2010, using work from
# the LocalFileAssetEngine written for the "Runaway" game in Oct-Dec 2009, which
# in turn was based on the LocalFileAssetEngine from the CharanisMLClient
# developed in May 2008.

import os.path

class Assets:
    """An assets manager which returns file-like objects for local files.
       It is used to retrieve media data - images, animations, 3D models, sound.
    """

    def __init__(self, logger):
        """Initialise.
        """

        self.logger = logger

        # TODO: Since an Assets instance is created only once, fetch() should do some asset caching (self.asset_dict) to prevent unnecessary file or network access. Problem: memory usage has to be limited. Probably use temporary files for downloaded assets?

    def fetch(self, asset_desc):
        """This method retrieves the file specified in asset_desc and returns a file-like object.
           Since fetch() is a synchronous method, it will cancel after a timeout
           and raise a Exception if it failes to retrieve the data.
           This method actually is a dispatcher to more specialised methods.
        """

        self.logger.debug("unknown asset '{}', attempting to fetch".format(asset_desc))

        if (asset_desc.startswith("http://")
            or asset_desc.startswith("ftp://")):

            return self.fetch_uri(asset_desc)

        elif os.path.exists(asset_desc):

            if asset_desc.lower().endswith(".zip"):

                return self.fetch_zip_file(asset_desc)

            else:
                # Local file, no *.zip
                #
                return self.fetch_local_file(asset_desc)

        else:
            errormessage = ("Could not open asset: '{}'".format(asset_desc))

            self.logger.critical(errormessage)

            raise Exception(errormessage)

    def fetch_uri(self, asset_desc):

        # TODO: timeout!

        errormessage = ("Assets.fetch_uri() is not implemented")

        self.logger.critical(errormessage)

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
#            self.logger.debug("retrieving %s from ZIP file %s" % (name, asset_desc))
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

        self.logger.critical(errormessage)

        raise Exception(errormessage)

    def fetch_local_file(self, asset_desc):
        """This method returns a a file-like object for the file specified.
        """

        self.logger.debug("attempting to retrieve {} from local file".format(asset_desc))

        file = open(asset_desc, mode='rb')

        self.logger.debug("returning {}".format(file))

        return file
