#! /usr/bin/python

'''run_shardclient.py - Initialize and run a Shard client
   
   (c) Florian Berger <fberger@fbmd.de>
   
   Work started on 27. May 2008'''

##############################
# Imports

from optparse import OptionParser
import logging
import shard.interfaces
import shard.assetengine
import shard.presentationengine
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
                         default=50,
                         help="default 50")

option_parser.add_option("-p",  "--port",
                         type="int",
                         default=2000,
                         help="default 2000")

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

formatter = logging.Formatter("%(asctime)s %(levelname)s module %(module)s: %(funcName)s(): %(message)s",
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

    interface = shard.interfaces.ClientInterface(("localhost", options.port), logger)

    asset_engine = shard.assetengine.AssetEngine(logger)

    presentation_engine = shard.presentationengine.PresentationEngine(asset_engine, FRAMERATE, logger)

    cce = shard.clientcontrolengine.ClientControlEngine(interface, presentation_engine, logger)

    thread.start_new_thread(interface.handle_messages, ())

    # This method will return when the presentation
    # engine sets presentation_engine.exit_requested
    # to True
    #
    cce.run()

if __name__ == "__main__":
    main()
