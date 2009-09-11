'''run_shardclient.py - Initialize and run a Shard client
   
   (c) Florian Berger <fberger@fbmd.de>
   
   Work started on 27. May 2008'''

import shard
import thread
import an_interface

InterfaceInstance = an_interface.AnInterface()

VisualEngineInstance = shard.VisualEngine()

ClientControlEngineInstance = shard.ClientControlEngine(InterfaceInstance,VisualEngineInstance)

thread.start_new_thread(InterfaceInstance.handleEvents,())

ClientControlEngineInstance.run()
