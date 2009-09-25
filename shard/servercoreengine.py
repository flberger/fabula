""" Shard Server Core Engine

    Started with a complete dummy
    implementation on 25. Sep 2009
"""

import shard

class ServerCoreEngine:
    "Dummy!"

    def __init__(self, server_interface_instance, logger):
        "dummy, currently"

        # Attach logger
        #
        self.logger = logger

        self.server_interface = server_interface_instance

    def run(self):
        "Dummy implementation of main method"

        import time

        while not self.server_interface.client_connections:
            self.logger.debug("no client connections. waiting 5s.")
            time.sleep(5)

        self.logger.debug("got a connection. Sending room events.")

        message = shard.Message([shard.EnterRoomEvent(), shard.RoomCompleteEvent()])

        for connection in self.server_interface.client_connections.values():
            connection.send_message(message)

        while True:
            for address_port_tuple in self.server_interface.client_connections:

                message = self.server_interface.client_connections[address_port_tuple].grab_message()

                if message.event_list:

                    self.logger.debug("from " + str(address_port_tuple) + ": " + str(message.event_list))

            time.sleep(0.5)
