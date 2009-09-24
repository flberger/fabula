#! /usr/bin/python

'''run_shardclient.py - Initialize and run a Shard client
   
   (c) Florian Berger <fberger@fbmd.de>
   
   Work started on 27. May 2008'''

##############################
# Imports

from optparse import OptionParser
import logging
import shard.clientinterface
import shard.assetengine
import shard.visualengine
import shard.clientcontrolengine
import thread

##############################
# Options

option_parser = OptionParser()

option_parser.add_option("-l",  "--loglevel",
                         default="d",
                         help="d(ebug) | i(nfo) | w(arning) | e(rro)r | c(ritical)")

option_parser.add_option("-f",  "--framerate",
                         type="int",
                         default=25,
                         help="default 25")

options = option_parser.parse_args()[0]

##############################
# Logging

logger = logging.getLogger()

leveldict = {"d" : logging.DEBUG,
             "i" : logging.INFO,
             "w" : logging.WARNING,
             "e" : logging.ERROR,
             "c" : logging.CRITICAL,
             }

logger.setLevel(leveldict[options.loglevel])

stderr_handler = logging.StreamHandler()
stderr_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s %(levelname)s %(module)s:%(funcName)s(): %(message)s",
                              "%Y-%m-%d %H:%M:%S")

stderr_handler.setFormatter(formatter)

logger.addHandler(stderr_handler)

##############################
# Main

FRAMERATE = options.framerate

def main():

    logger.info("Using loglevel "
                + str(options.loglevel)
                + " and framerate "
                + str(FRAMERATE)
                + ".")

    interface = shard.clientinterface.ClientInterface(logger)

    asset_engine = shard.assetengine.AssetEngine(logger)

    visual_engine = shard.visualengine.VisualEngine(asset_engine, FRAMERATE, logger)

    cce = shard.clientcontrolengine.ClientControlEngine(interface, visual_engine, logger)

    thread.start_new_thread(interface.handle_messages, ())

    cce.run()

if __name__ == "__main__":
    main()
