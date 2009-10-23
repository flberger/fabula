"""shard.run - Initialize and run Shard client and server

   (c) Florian Berger <fberger@fbmd.de>
"""

# Work started on 27. May 2008
#
# Server part adapted from run_shardclient.py on 25. Sep 2009
#
# Unfied for client and server usage on 30. Sep 2009
#
# Converted from run_shard.py on 06. Oct 2009

import shard.interfaces
import shard.clientcoreengine
import shard.servercoreengine

import thread
import logging

def run(mode,
        address_port_tuple,
        framerate,
        plugin_class,
        asset_engine_class,
        loglevel,
        log_time,
        log_name):

    # Set up logging

    logger = logging.getLogger()

    leveldict = {"d" : logging.DEBUG,
                 "i" : logging.INFO,
                 "w" : logging.WARNING,
                 "e" : logging.ERROR,
                 "c" : logging.CRITICAL}

    logger.setLevel(leveldict[loglevel])

    stderr_handler = logging.StreamHandler()
    stderr_handler.setLevel(logging.DEBUG)

    if log_time:
        timestring = "%(asctime)s "
    else:
        timestring = ""

    if log_name:
        namestring = "%(filename)s l.%(lineno)s: "
    else:
        namestring = ""

    formatter = logging.Formatter(timestring
                                  + "%(levelname)s "
                                  + namestring
                                  + "%(funcName)s(): %(message)s",
                                  "%Y-%m-%d %H:%M:%S")

    stderr_handler.setFormatter(formatter)

    logger.addHandler(stderr_handler)

    logger.info("Running in " + str(mode) + " mode")

    # Set up mode specific objects

    if mode == "client":

        logger.info("Using framerate " + str(framerate))

        # TODO: hardwired TCP protocol
        #
        interface_class = shard.interfaces.TCPClientInterface

        asset_engine = asset_engine_class(logger)

        plugin = plugin_class(asset_engine, framerate, logger)

        core_engine_class = shard.clientcoreengine.ClientCoreEngine

    elif mode == "server":

        # TODO: hardwired TCP protocol
        #
        interface_class = shard.interfaces.TCPServerInterface

        plugin = plugin_class(logger)

        core_engine_class = shard.servercoreengine.ServerCoreEngine

    interface = interface_class(address_port_tuple, logger)

    core_engine_instance = core_engine_class(interface,
                                             plugin,
                                             logger)

    thread.start_new_thread(interface.handle_messages, ())

    # Or instead, for debugging:
    #
    #interface.handle_messages()

    # This method will return when the plugin
    # engine sets plugin.exit_requested
    # to True
    #
    core_engine_instance.run()
