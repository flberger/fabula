"""Fabula JSON RPC Interface

   Copyright 2012 Florian Berger <fberger@florian-berger.de>
"""

# This file is part of Fabula.
#
# Fabula is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Fabula is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fabula.  If not, see <http://www.gnu.org/licenses/>.

# Work started on 26. Mar 2012
#
# First attempt implemented using the bjsonrpc module, but it has not yet been
# ported to Python 3, and did not allow for convenient management of clients
# by IP number.
#
# Now this is a copy of fabula.interfaces.python_tcp, but handling the byte
# streams as JSON-RPC objects.

import fabula.interfaces.python_tcp
import json

class JSONRPCServerInterface(fabula.interfaces.python_tcp.TCPServerInterface):
    """Fabula Server interface using JSON-RPC.
    """

    def __init__(self):
        """Initialisation.

           Additional attributes:

           JSONRPCServerInterface.decoder
               An instance of json.JSONDecoder.

           JSONRPCServerInterface.json_rpc_id_list
               A list containing the incoming JSON-RPC ids, to be used as a
               FIFO.
        """

        # Call base class
        #
        fabula.interfaces.python_tcp.TCPServerInterface.__init__(self)

        self.decoder = json.JSONDecoder()

        self.json_rpc_id_list = []

        # The main difference to TCPServerInterface is a RequestHandler that
        # handles JSON-RPC.

        parent = self

        # We define the class here to be able to access local variables through
        # parent.
        #
        # TODO: FabulaRequestHandler copied from TCPServerInterface, but the actual difference is only a few lines. Abstract protocol.
        #
        class FabulaRequestHandler(fabula.interfaces.python_tcp.socketserver.BaseRequestHandler):

            def handle(self):

                # TODO: this will run in a thread spawned by the custom ThreadingTCPServer class. How thread safe are these operations?

                # Fabula uses persistent TCP connections, so every call to this
                # method should be from a new client. Blindly add this one.
                #
                message_buffer = parent.connections[self.client_address] = fabula.interfaces.MessageBuffer()

                fabula.LOGGER.info("adding and handling new client: {}".format(self.client_address))

                # Register in thread list, which is used for Interface shutdown
                #
                parent.thread_list.append(fabula.interfaces.python_tcp.threading.current_thread())

                # Now, handle messages in a persistent fashion.

                self.request.settimeout(0.3)

                received_data = bytearray()

                while not parent.shutdown_flag:

                    # TODO: partly copied from TCPClientInterface.handle_messages() with a few renamings

                    # Only the Interface may add connections to
                    # Interface.connections, but the server may remove them if
                    # a client exits on the application level.
                    # So, first check whether the client handled by this
                    # FabulaRequestHandler has been removed, and if so,
                    # terminate.
                    #
                    if not self.client_address in parent.connections.keys():

                        fabula.LOGGER.info("client '{}' has been removed by the server".format(self.client_address))

                        # We are *not* setting parent.shutdown_flag, since only
                        # this connection should terminate.

                        try:

                            self.request.shutdown(fabula.interfaces.python_tcp.socket.SHUT_RDWR)

                        except:

                            # Socket may be unavailable already
                            #
                            fabula.LOGGER.warning("could not shut down socket")

                        self.request.close()

                        fabula.LOGGER.info("handler connection closed, stopping thread")

                        raise SystemExit

                    # First deliver waiting local messages.
                    #
                    if message_buffer.messages_for_remote:

                        fabula.LOGGER.debug("sending 1 message of {} to {}".format(len(message_buffer.messages_for_remote),
                                                                                   self.client_address))

                        # Send a JSON representation, wrapped as a JSON-RPC
                        # response.
                        #
                        json_rpc_response = '{{"result" : {}, "error" : null, "id" : {}}}'

                        json_event_list = '[{}]'.format(", ".join([event.json() for event in message_buffer.messages_for_remote.popleft().event_list]))

                        try:
                            id = parent.json_rpc_id_list.pop(0)

                        except IndexError:

                            fabula.LOGGER.debug("List of queued JSON_RPC ids exhausted, sending JSON-RPC notification instead")

                            id = 'null'

                        representation = json_rpc_response.format(json_event_list,
                                                                  id)

                        fabula.LOGGER.debug("attempting to send {}".format(representation))

                        try:
                            # Add a double newline as separator for convenience.
                            # Use ASCII.
                            # TODO: implement UTF-16
                            #
                            self.request.sendall(bytes(representation + "\n\n", "ascii"))

                        except fabula.interfaces.python_tcp.socket.error:

                            fabula.LOGGER.error("socket error while sending to {}".format(self.client_address))

                            try:
                                fabula.LOGGER.debug("closing socket")

                                self.request.shutdown(fabula.interfaces.python_tcp.socket.SHUT_RDWR)

                            except:

                                # Socket may be unavailable already
                                #
                                fabula.LOGGER.warning("could not shut down socket")

                            self.request.close()

                            fabula.LOGGER.info("handler connection closed")

                            # This is the only way to notify the Server
                            #
                            fabula.LOGGER.debug("removing connection from connections dict")

                            del parent.connections[self.client_address]

                            fabula.LOGGER.debug("removing thread from thread list")

                            parent.thread_list.remove(threading.current_thread())

                            fabula.LOGGER.info("stopping thread")

                            raise SystemExit

                    # Now listen for incoming client messages for some time (set
                    # above). This should catch any messages received in the
                    # meantime by the OS.
                    #
                    chunk = None

                    try:

                        # TODO: evaluate recv size
                        #
                        chunk = self.request.recv(4096)

                    except fabula.interfaces.python_tcp.socket.timeout:

                        # Nobody likes us, evereyone left us, there all out
                        # without us, having fun...
                        #
                        pass

                    except fabula.interfaces.python_tcp.socket.error:

                        fabula.LOGGER.error("socket error while receiving")

                    if chunk:

                        fabula.LOGGER.debug("received {} bytes from {}".format(len(chunk),
                                                                               self.client_address))

                        # Assuming we are dealing with bytes here
                        #
                        received_data.extend(chunk)

                        # Strip leading whitespace. Works on bytearrays.
                        # TODO: check for either ASCII or UTF-16 before stripping leading whitespace. UTF-16 strings should start with FFFE.
                        #
                        received_data = received_data.lstrip()

                        json_decoded = end_index = None

                        try:
                            # Currently we only accept ASCII.
                            # TODO: Accept UTF-16 for convenient length calculation
                            #
                            json_decoded, end_index = parent.decoder.raw_decode(str(received_data, "ascii"))

                        except ValueError:

                            fabula.LOGGER.debug("JSON object not yet complete, keeping buffer")

                        # There actually may be more than one JSON-RCP request
                        # in received_data. Catch them all!
                        #
                        while (json_decoded is not None and end_index is not None):

                            # Found!

                            received_data = received_data[end_index:]

                            msg = "message from {} complete at {} bytes, {} left in buffer"

                            fabula.LOGGER.debug(msg.format(self.client_address,
                                                           end_index,
                                                           len(received_data)))

                            fabula.LOGGER.debug("decoded JSON: {}".format(json_decoded))

                            message = parent.json_to_message(json_decoded["params"])

                            # Queue id
                            #
                            fabula.LOGGER.debug("queueing request id '{}'".format(json_decoded["id"]))

                            parent.json_rpc_id_list.append(json_decoded["id"])

                            message_buffer.messages_for_local.append(message)

                            # Next
                            #
                            json_decoded = end_index = None

                            if len(received_data):

                                try:
                                    json_decoded, end_index = parent.decoder.raw_decode(str(received_data, "ascii"))

                                except ValueError:

                                    fabula.LOGGER.debug("JSON object not yet complete, keeping buffer")

                        # No more complete JSON-RPC objects, end of evaluation.

                    # No need to run as fast as possible.
                    #
                    fabula.interfaces.python_tcp.sleep(1/60)

                fabula.LOGGER.debug("shutdown flag set in parent")

                # Deliver waiting local messages.
                #
                while len(message_buffer.messages_for_remote):

                    # Copied from above
                    #
                    fabula.LOGGER.debug("sending 1 message of {} to {}".format(len(message_buffer.messages_for_remote),
                                                                               self.client_address))

                    # Send a JSON representation, wrapped as a JSON-RPC
                    # response.
                    #
                    json_rpc_response = '{{"result" : {}, "error" : null, "id" : {}}}'

                    json_event_list = '[{}]'.format(", ".join([event.json() for event in message_buffer.messages_for_remote.popleft().event_list]))

                    try:
                        id = parent.json_rpc_id_list.pop(0)

                    except IndexError:

                        fabula.LOGGER.debug("List of queued JSON_RPC ids exhausted, sending JSON-RPC notification instead")

                        id = 'null'

                    representation = json_rpc_response.format(json_event_list,
                                                              id)

                    # Add a double newline as separator for convenience.
                    # Use ASCII.
                    # TODO: implement UTF-16
                    #
                    self.request.sendall(bytes(representation + "\n\n", "ascii"))

                try:

                    self.request.shutdown(fabula.interfaces.python_tcp.socket.SHUT_RDWR)

                except:

                    # Socket may be unavailable already
                    #
                    fabula.LOGGER.warning("could not shut down socket")

                self.request.close()

                fabula.LOGGER.info("handler connection closed, stopping thread")

                raise SystemExit

        # End of class.

        self.FabulaRequestHandler = FabulaRequestHandler

        return

    def json_to_message(self, json_event_list):
        """Read a list of JSON Event representations converted to dicts, and return an according Fabula Message.
        """

        message = fabula.Message([])

        for event_dict in json_event_list:

            fabula.LOGGER.debug("attempting to recreate Event from {}".format(event_dict))

            event_class = fabula.__dict__[event_dict["class"]]

            del event_dict["class"]

            # Convert target identifiers from JSON lists to tuples
            #
            if ("target_identifier" in event_dict.keys()
                and type(event_dict["target_identifier"]) is list):

                event_dict["target_identifier"] = tuple(event_dict["target_identifier"])

            # Using the infamous argument unpacking from dict
            # TODO: this will of course fail with Tiles and Entities
            #
            event = event_class(**event_dict)

            fabula.LOGGER.debug("recreated {}".format(event))

            message.event_list.append(event)

        return message
