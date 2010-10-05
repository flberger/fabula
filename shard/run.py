"""shard.run - Initialize and run Shard client and server

   (c) Florian Berger <fberger@florian-berger.de>
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
        player_id,
        framerate,
        plugin_class,
        asset_engine_class,
        loglevel):

    ### Set up logging

    logger = logging.getLogger()

    leveldict = {"d" : logging.DEBUG,
                 "i" : logging.INFO,
                 "w" : logging.WARNING,
                 "e" : logging.ERROR,
                 "c" : logging.CRITICAL}

    logger.setLevel(leveldict[loglevel])

    # STDERR console handler
    #
    # Creating an instance without arguments
    # defaults to STDERR.
    # 
    stderr_handler = logging.StreamHandler()

    stderr_handler.setLevel(logging.DEBUG)

    # Loglevel:
    # "\x1b\x5b\x33\x32\x6d"
    # + "%(levelname)-5s "
    # + "\x1b\x5b\x33\x39\x6d"

    stderr_formatter = logging.Formatter("\x1b\x5b\x33\x36\x6d"
                                         + "%(funcName)s() "
                                         + "\x1b\x5b\x33\x39\x6d"
                                         + "%(message)s")

    stderr_handler.setFormatter(stderr_formatter)

    # File handler
    #
    if player_id != None:

        file_name = "%s-%s.log" % (mode, player_id)

    else:

        file_name = "%s.log" % mode

    file_handler = logging.FileHandler(filename = file_name,
                                       mode = "w")

    file_handler.setLevel(logging.DEBUG)

    # Loglevel:
    # + "%(levelname)-5s "

    file_formatter = logging.Formatter("%(asctime)s "
                                       + "%(filename)s [%(lineno)s] %(funcName)s() : %(message)s"
                                       ,
                                       "%Y-%m-%d %H:%M:%S")

    file_handler.setFormatter(file_formatter)

    # Add handlers
    #
    logger.addHandler(stderr_handler)

    logger.addHandler(file_handler)

    logger.info("running in %s mode" % mode)

    # Set up mode specific objects

    if mode == "client":

        logger.info("running with framerate %s/s" % framerate)

        logger.info("player_id: %s" % player_id)

        # TODO: hardwired TCP protocol
        #
        interface = shard.interfaces.TCPInterface(address_port_tuple,
                                                  logger,
                                                  interface_type = mode,
                                                  send_interval = 0.3)

        asset_engine = asset_engine_class(logger)

        plugin = plugin_class(asset_engine, framerate, logger)

        core_engine_instance = shard.clientcoreengine.ClientCoreEngine(player_id,
                                                                       interface,
                                                                       plugin,
                                                                       logger)

    elif mode == "server":

        logger.info("running with interval (framerate) %s/s" % framerate)

        # TODO: hardwired TCP protocol
        #
        interface = shard.interfaces.TCPInterface(address_port_tuple,
                                                  logger,
                                                  interface_type = mode,
                                                  send_interval = 0.1)

        plugin = plugin_class(logger)

        core_engine_instance = shard.servercoreengine.ServerCoreEngine(framerate,
                                                                       interface,
                                                                       plugin,
                                                                       logger)

    # endif :-)

    thread.start_new_thread(interface.handle_messages, ())

    # Or instead, for debugging:
    #
    #interface.handle_messages()

    # This method will return when the plugin
    # engine sets plugin.exit_requested
    # to True
    #
    core_engine_instance.run()

    # CoreEngine returned.
    # Close logger.
    #
    logging.shutdown()
