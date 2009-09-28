#! /usr/bin/python

'''run_shardserver.py - Initialize and run a Shard server
   
   (c) Florian Berger <fberger@fbmd.de>
   
   Adapted from run_shardclient.py on 25. Sep 2009
'''

##############################
# Imports

from optparse import OptionParser
import logging
import shard.interfaces
import shard.servercoreengine
import thread

##############################
# Options

option_parser = OptionParser()

option_parser.add_option("-l",  "--loglevel",
                         default="d",
                         help="d(ebug) | i(nfo) | w(arning) | e(rro)r | c(ritical)")

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

def main():

    logger.info("Using loglevel "
                + str(options.loglevel)
                + ".")

    interface = shard.interfaces.ServerInterface(("localhost", options.port), logger)

    sce = shard.servercoreengine.ServerCoreEngine(interface, logger)

    thread.start_new_thread(interface.handle_messages, ())

    sce.run()

if __name__ == "__main__":
    main()
