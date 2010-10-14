"""Shard Asset Manager
"""

# Extracted from shard.py on 22. Sep 2009

from shard import ShardException

class Assets:
    '''This is the base class for an assets manager.
       It is used to retrieve media data - images, animations, 3D models, sound.
       Subclass this with an Engine that actually fetches data - the default
       implementation raises a shard.ShardException.
    '''

    def __init__(self, logger):
        """Initialise.
        """

        self.logger = logger

    def fetch(self, asset_identifier):
        '''This method retrieves the file specified in asset_identifier and returns the content.
           The type of object returned is determined by the actual
           implementation of Assets, UserInterface and Entity. This method
           is encouraged to do advanced operations like fetching and
           decompressing zip files, format conversion and the like.
           Since fetch() is a synchronous method, it should cancel after a
           timeout and raise a shard.ShardException if it failes to retrieve the
           data.
           Since an Assets instance is created only once, fetch() should
           do some asset caching to prevent unnecessary file or network access.
        '''

        errormessage = ("This is just a dummy fetch() method. "
                        + "Please use a real implementation of Assets.")

        self.logger.critical(errormessage)

        raise ShardException(errormessage)
