'''run_shardclient.py - Initialize and run a Shard client
   
   (c) Florian Berger <fberger@fbmd.de>
   
   Work started on 27. May 2008'''

import logging
import shard.clientinterface
import shard.assetengine
import shard.visualengine
import shard.clientcontrolengine
import thread

logger = logging.getLogger()
stderr_handler = logging.StreamHandler()
stderr_handler.setLevel(logging.DEBUG)
logger.addHandler(stderr_handler)

FRAMERATE = 25

interface = shard.clientinterface.ClientInterface(logger)

asset_engine = shard.assetengine.AssetEngine(logger)

visual_engine = shard.visualengine.VisualEngine(asset_engine, FRAMERATE, logger)

cce = shard.clientcontrolengine.ClientControlEngine(interface, visual_engine, logger)

thread.start_new_thread(interface.handleEvents, ())

cce.run()
