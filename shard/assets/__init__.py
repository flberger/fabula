"""Shard Asset Engine
"""

# Extracted from shard.py on 22. Sep 2009

from . import ShardException

class AssetEngine:
    '''This is the base class for an AssetEngine.
       It is used to retrieve media data - images, 
       animations, 3D models, sound. Subclass 
       this with an Engine that actually fetches
       data - the default implementation raises
       a shard.ShardException.'''

    def __init__(self, logger):
        self.logger = logger

    def fetch_asset(self, asset_identifier):
        '''This is the main method of the AssetEngine.
           It retrieves the file specified in
           asset_identifier and returns the content.
           The type of object returned is determined
           by the actual implementation of AssetEngine, 
           PresentationEngine and Entity. This method is
           encouraged to do advanced operations like
           fetching and decompressing zip files, 
           format conversion and the like.
           Since fetch_asset() is a synchronous method, 
           it should cancel after a timeout and raise
           a shard.ShardException if it failes to retrieve
           the data.
           Since the AssetEngine is only created once, 
           fetch_asset() should do some asset caching
           to prevent unnecessary file or network
           access.'''

        errormessage = ("This is just a dummy fetch_asset() method. "
                        + "Please use a real implementation of AssetEngine.")

        self.logger.critical(errormessage)

        raise ShardException(errormessage)
