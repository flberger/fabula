#! /usr/bin/python

"""run_shard.py - Initialize and run a Shard server or client
   
   (c) Florian Berger <fberger@fbmd.de>
   
   Work started on 27. May 2008

   Server part adapted from run_shardclient.py on 25. Sep 2009

   Unfied for client and server usage on 30. Sep 2009
"""

##############################
# Imports

from optparse import OptionParser
import logging
import shard.interfaces
import shard.servercoreengine
import shard.assetengine
import shard.presentationengine
import shard.plugin
import shard.clientcoreengine
import thread

##############################
# Options

option_parser = OptionParser()

option_parser.add_option("-l",  "--loglevel",
                         default="d",
                         help="d(ebug) | i(nfo) | w(arning) | e(rro)r | c(ritical), default: d")

option_parser.add_option("-t",  "--log-time",
                         action="store_true",
                         default=False,
                         help="append time stamps to log messages")

option_parser.add_option("-n",  "--log-name",
                         action="store_true",
                         default=False,
                         help="append module name and line to log messages")

option_parser.add_option("-m",  "--mode",
                         default="server",
                         help="client | server, default:server")

option_parser.add_option("-p",  "--port",
                         type="int",
                         default=2020,
                         help="server port, default 2020")

option_parser.add_option("-f",  "--framerate",
                         type="int",
                         default=50,
                         help="client framerate, default 50")

options = option_parser.parse_args()[0]

LOGLEVEL = options.loglevel
LOG_TIME = options.log_time
LOG_NAME = options.log_name
MODE = options.mode
PORT = options.port
FRAMERATE = options.framerate

##############################
# Logging

logger = logging.getLogger()

leveldict = {"d" : logging.DEBUG,
             "i" : logging.INFO,
             "w" : logging.WARNING,
             "e" : logging.ERROR,
             "c" : logging.CRITICAL,
             }

logger.setLevel(leveldict[LOGLEVEL])

stderr_handler = logging.StreamHandler()
stderr_handler.setLevel(logging.DEBUG)

if LOG_TIME:
    TIMESTRING = "%(asctime)s "
else:
    TIMESTRING = ""

if LOG_NAME:
    NAMESTRING = "%(filename)s l.%(lineno)s: "
else:
    NAMESTRING = ""

formatter = logging.Formatter(TIMESTRING
                              + "%(levelname)s "
                              + NAMESTRING
                              + "%(funcName)s(): %(message)s",
                              "%Y-%m-%d %H:%M:%S")

stderr_handler.setFormatter(formatter)

logger.addHandler(stderr_handler)

##############################
# Main

def main():

    logger.info("Running in " + str(MODE) + " mode")

    if MODE == "client":

        logger.info("Using framerate " + str(FRAMERATE))

        interface_class = shard.interfaces.ClientInterface

        asset_engine = shard.assetengine.AssetEngine(logger)

        plugin = shard.presentationengine.PresentationEngine(asset_engine,
                                                                    FRAMERATE,
                                                                    logger)

        coreengine_class = shard.clientcoreengine.ClientCoreEngine

    elif MODE == "server":

        interface_class = shard.interfaces.ServerInterface

        plugin = shard.plugin.Plugin(logger)

        coreengine_class = shard.servercoreengine.ServerCoreEngine

    interface = interface_class(("localhost", PORT), logger)

    coreengine_instance = coreengine_class(interface,
                                           plugin,
                                           logger)

    thread.start_new_thread(interface.handle_messages, ())

    # This method will return when the plugin
    # engine sets plugin.exit_requested
    # to True
    #
    coreengine_instance.run()

if __name__ == "__main__":
    main()
