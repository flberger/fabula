"""Fabula Client Engine

   Copyright 2010 Florian Berger <fberger@florian-berger.de>
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

# Extracted from shard.py on 22. Sep 2009

import fabula
import fabula.core
import time
import datetime
import traceback

class Client(fabula.core.Engine):
    """An instance of this class is the main engine in every Fabula client.
       It connects to the Client Interface and to the UserInterface,
       passes events and keeps track of Entities.
       It is normally instantiated in fabula.run.

       Additional attributes:

       Client.client_id
           The unique id for this Client. Initially an empty string.

       Client.await_confirmation
       Client.got_empty_message
           Flags used by Client.run()

       Client.message_sent
           Buffer for sent message

       Client.timestamp
           Timestamp to detect server dropouts

       Client.local_moves_to_event
           Cache for the latest local MovesToEvent
    """

    ####################
    # Init

    def __init__(self, interface_instance):
        """Initalisation.
           The Client must be instantiated with an instance of a subclass of
           fabula.interfaces.Interface which handles the connection to the
           server or supplies events in some other way.
        """

        # Save the player id for Server and UserInterface.
        #
        self.client_id = ""

        # First setup base class
        #
        fabula.core.fabula.eventprocessor.EventProcessor.__init__(self)

        # Then setup Engine internals
        #
        fabula.core.Engine.__init__(self, interface_instance)

        # Now we have:
        #
        # self.room = fabula.Room()
        #
        #     self.room.entity_dict
        #         A dict of all Entities in this room,
        #         mapping Entity identifiers to Entity
        #         instances.
        #
        #     self.room.floor_plan
        #         A dict mapping 2D coordinate tuples
        #         to a FloorPlanElement instance.
        #
        #     self.room.entity_locations
        #         A dict mapping Entity identifiers to a
        #         2D coordinate tuple.
        #
        # self.rack
        #
        #     self.rack serves as a storage for deleted Entities
        #     because there may be the need to respawn them.

        # Set up flags used by self.run()
        #
        self.await_confirmation = False

        self.got_empty_message = False

        # Buffer for sent message
        #
        self.message_sent = fabula.Message([])

        # Timestamp to detect server dropouts
        #
        self.timestamp = None

        # Remember the latest local MovesToEvent
        #
        self.local_moves_to_event = fabula.MovesToEvent(None, None)

        fabula.LOGGER.debug("complete")

    ####################
    # Main Loop

    def run(self):
        """Main loop of the Client.
           This is a blocking method. It calls all the process methods to
           process events, and then the plugin.
           The loop will terminate when Client.plugin.exit_requested is True.
        """

        # TODO: The current implementation is too overtrustful.
        # It should check much more thoroughly if the
        # affected Entites exist at all and so on. Since
        # this is a kind of precondition or even invariant,
        # it should be covered using a "design by contract"
        # approach to the whole thing instead of putting
        # neat "if" clauses here and there.

        fabula.LOGGER.info("starting")

        # By now we should have self.plugin. This is the reason why we do not
        # do this in __init__().

        fabula.LOGGER.info("prompting the user for connection details")

        while self.client_id == "":

            self.client_id, connector = self.plugin.get_connection_details()

        if len(self.interface.connections.keys()):

            fabula.LOGGER.info("interface is already connected to '{}', using connection".format(list(self.interface.connections.keys())[0]))

        else:

            if self.client_id == "exit requested":

                # partly copied from below

                fabula.LOGGER.info("exit requested from UserInterface, shutting down interface")

                # stop the Client Interface thread
                #
                self.interface.shutdown()

                fabula.LOGGER.info("shutdown confirmed.")

                # TODO: possibly exit cleanly from the UserInterface here

                return

            elif connector is None:

                msg = "can not connect to Server: client_id == '{}', connector == {}"

                fabula.LOGGER.critical(msg.format(self.client_id, connector))

                # TODO: exit properly
                #
                raise Exception(msg.format(self.client_id, connector))

            else:

                fabula.LOGGER.info("connecting client interface to '{}'".format(connector))

                try:
                    self.interface.connect(connector)

                except:
                    fabula.LOGGER.critical("error connecting to server")

                    fabula.LOGGER.info("shutting down interface")

                    self.interface.shutdown()

                    fabula.LOGGER.info("exiting")

                    raise SystemExit

        # Use only the first connection in the ClientInterface
        #
        self.message_buffer = list(self.interface.connections.values())[0]

        init_event = fabula.InitEvent(self.client_id)

        fabula.LOGGER.info("sending {}".format(init_event))

        self.message_buffer.send_message(fabula.Message([init_event]))

        # Now loop
        #
        while not self.plugin.exit_requested:

            # grab_message must and will return a Message, but
            # it possibly has an empty event_list.
            #
            server_message = self.message_buffer.grab_message()

            if server_message.event_list:

                fabula.LOGGER.debug("server incoming: {}".format(server_message))

                # Message was not empty
                #
                self.got_empty_message = False

            elif not self.got_empty_message:

                # TODO: The UserInterface currently locks up when there are no answers from the server. The Client should time out and exit politely if there is no initial answer from the server or there has been no answer for some time.

                fabula.LOGGER.debug("got an empty server_message.")

                # Set to True to log empty messages only once
                #
                self.got_empty_message = True

            # First handle the events in the Client, updating the room and
            # preparing self.message_for_plugin for the UserInterface
            #
            for current_event in server_message.event_list:

                # This is a bit of Python magic.
                # self.event_dict is a dict which maps classes to handling
                # functions. We use the class of the event supplied as
                # a key to call the appropriate handler, and hand over
                # the event.
                # These methods may add events for the plugin engine
                # to self.message_for_plugin
                #
                # TODO: This really should return a message, instead of giving one to write to
                #
                self.event_dict[current_event.__class__](current_event,
                                                         message = self.message_for_plugin)

            # Now that everything is set and stored, call the UserInterface to
            # process the messages.

            # Ideally we want to call process_message() once per frame, but the
            # call may take an almost arbitrary amount of time.
            # At least process_message() must be called regularly even if the
            # server Message and thus message_for_plugin  are empty.
            #
            try:

                message_from_plugin = self.plugin.process_message(self.message_for_plugin)

            except:
                fabula.LOGGER.critical("the UserInterface raised an exception:\n{}".format(traceback.format_exc()))

                fabula.LOGGER.info("shutting down interface")

                self.interface.shutdown()

                fabula.LOGGER.info("exiting")

                return

            # The UserInterface returned, the Server Message has been applied
            # and processed. Clean up.
            #
            self.message_for_plugin = fabula.Message([])

            # TODO: possibly unset "AwaitConfirmation" flag
            # If there has been a Confirmation for a LookAt or TriesToManipulate,
            # unset "AwaitConfirmation" flag

            # The UserInterface might have collected some player input and
            # converted it to events.
            #
            if message_from_plugin.event_list:

                if self.await_confirmation:

                    # Player input, but we still await confirmation.

                    if self.timestamp == None:

                        fabula.LOGGER.warning("player attempt but still waiting - starting timer")

                        self.timestamp = datetime.datetime.today()

                    else:

                        timedifference = datetime.datetime.today() - self.timestamp

                        if timedifference.seconds >= 3:

                            fabula.LOGGER.warning("waited 3s, still no confirmation, notifying user and resetting timer")

                            self.timestamp = None

                            msg = "The server does not reply.\nConsider to restart."

                            perception_event = fabula.PerceptionEvent(self.client_id,
                                                                      msg)

                            # Not catching reaction
                            #
                            self.plugin.process_message(fabula.Message([perception_event]))

                        else:

                            fabula.LOGGER.info("still waiting for confirmation")

                else:

                    # If we do not await a Confirmation anymore, we evaluate the
                    # player input if any.

                    # We queue player triggered events before possible events
                    # from the Client.
                    # TODO: Since MessageAppliedEvent is gone, are there any events left to be sent by the Client?
                    #
                    self.message_for_remote.event_list = (message_from_plugin.event_list
                                                          + self.message_for_remote.event_list)

                    # Local movement tests
                    #
                    # TODO: Can't this be handled much easier by simply processing a MovesToEvent in UserInterface.collect_player_input? But then again, an UserInterface isn't supposed to check maps etc.
                    #
                    for event in message_from_plugin.event_list:

                        if isinstance(event, fabula.TriesToMoveEvent):

                            # TODO: similar to Server.process_TriesToMoveEvent()

                            # Do we need to move / turn at all?
                            #
                            location = self.room.entity_locations[event.identifier]
                            difference = fabula.difference_2d(location,
                                                             event.target_identifier)

                            # In case of a TriesToMoveEvent, test and approve
                            # the movement locally to allow for a smooth user
                            # experience. We have the current map information
                            # after all.
                            #
                            # Only allow certain vectors
                            #
                            if difference in ((0, 1), (0, -1), (1, 0), (-1, 0)):

                                fabula.LOGGER.info("applying TriesToMoveEvent locally")

                                # TODO: event.identifier in self.room.entity_dict? event.target_identifier in fabula.DIRECTION_VECTOR?

                                # TODO: code duplicated from Server.process_TriesToMoveEvent()

                                # Test if a movement from the current entity
                                # location to the new location on the map is
                                # possible
                                #
                                # We queue the event in self.message_for_plugin,
                                # so it will be rendered upon next call. That
                                # way it bypasses the Client; its status will be
                                # updated upon server confirmation. So we will
                                # have a difference between client state and
                                # presentation. We trust that it will be
                                # resolved by the server in very short time.
                                #
                                try:
                                    if self.tile_is_walkable(event.target_identifier):

                                        moves_to_event = fabula.MovesToEvent(event.identifier,
                                                                            event.target_identifier)

                                        # Update room, needed for UserInterface
                                        #
                                        self.process_MovesToEvent(moves_to_event,
                                                                  message = self.message_for_plugin)

                                        # Remember event for crosscheck with
                                        # event from Server
                                        #
                                        self.local_moves_to_event = moves_to_event

                                    else:
                                        # Instead of
                                        #self.message_for_plugin.event_list.append(fabula.AttemptFailedEvent(event.identifier))
                                        # we wait for the server to respond with
                                        # AttemptFailedEvent
                                        #
                                        pass

                                except KeyError:

                                    # Instead of
                                    #self.message_for_plugin.event_list.append(fabula.AttemptFailedEvent(event.identifier))
                                    # we wait for the server to respond with
                                    # AttemptFailedEvent
                                    #
                                    pass

                    # If any of the Events to be sent is an AttemptEvent, we now
                    # await confirmation
                    #
                    # TODO: has_attempt_event is used nowhere else. Remove?
                    #
                    has_attempt_event = False

                    for event in message_from_plugin.event_list:

                        if isinstance(event, fabula.AttemptEvent):

                            fabula.LOGGER.info("got attempt '{}' from Plugin: awaiting confirmation and discarding further user input".format(event.__class__.__name__))

                            self.await_confirmation = True

                    # Reset dropout timer
                    #
                    self.timestamp = None

            # If this iteration yielded any events, send them.
            #
            if self.message_for_remote.event_list:

                fabula.LOGGER.debug("server outgoing: %s" % self.message_for_remote)

                self.message_buffer.send_message(self.message_for_remote)

                # Save for possible re-send on dropout
                #
                self.last_message = self.message_for_remote

                # Clean up
                #
                self.message_for_remote = fabula.Message([])

            # OK, done with the whole server message.
            # If no exit requested, grab the next one!

        # exit has been requested

        fabula.LOGGER.info("exit requested from UserInterface")

        fabula.LOGGER.info("sending ExitEvent to Server")

        self.message_buffer.send_message(fabula.Message([fabula.ExitEvent(self.client_id)]))

        fabula.LOGGER.info("shutting down interface")

        # stop the Client Interface thread
        #
        self.interface.shutdown()

        fabula.LOGGER.info("shutdown confirmed.")

        # TODO: possibly exit cleanly from the UserInterface here

        return

    ####################
    # Auxiliary Methods

    def process_AttemptFailedEvent(self, event, **kwargs):
        """Possibly revert movement or call default, then unblock the client.
        """

        fabula.LOGGER.info("attempt failed for '{}'".format(event.identifier))

        # Did this fail for the Entity we just moved locally?
        #
        if event.identifier == self.local_moves_to_event.identifier:

            entity = self.room.entity_dict[event.identifier]
            location = self.room.entity_locations[event.identifier]

            fabula.LOGGER.warning("attempt failed for '{}', now at {}".format(event.identifier,
                                                                              location))

            # !!! TODO: This still relies on direction information which has been removed from Fabula core. Replace by a custom record of the old position.
            #
            vector = self.plugin.direction_vector_dict[entity.direction]

            restored_x = location[0] - vector[0]
            restored_y = location[1] - vector[1]

            self.room.process_MovesToEvent(fabula.MovesToEvent(event.identifier,
                                                              (restored_x, restored_y)))

            fabula.LOGGER.info("'{}' now reverted to {}".format(event.identifier,
                                                                (restored_x, restored_y)))

        # Call default to forward to the Plugin.
        #
        fabula.core.Engine.process_AttemptFailedEvent(self,
                                                     event,
                                                     message = kwargs["message"])

        if event.identifier == self.client_id:

            self.await_confirmation = False

    def process_CanSpeakEvent(self, event, **kwargs):
        """Check if this affects the player. If yes, call default and unblock client.
        """
        # Contrary to other Events, CanSpeakEvent has no meaning for any local
        # Entity except for the current player. So only proceed if this is
        # actually for us.
        #
        if event.identifier == self.client_id:

            # Call default.
            #
            fabula.core.Engine.process_CanSpeakEvent(self,
                                                    event,
                                                    message = kwargs["message"])

            # TriesToTalkTo confirmed
            #
            self.await_confirmation = False

        else:
            fabula.LOGGER.debug("ignoring {}".format(event))

    def process_DropsEvent(self, event, **kwargs):
        """Remove affected Entity from rack,
           queue SpawnEvent for room and Plugin,
           and pass on the DropsEvent.
        """

        # TODO: the DropsEvent and PicksUpEvent handling in Client and Plugin are asymmetrical. This is ugly. Unify.

        # Call default.
        #
        fabula.core.Engine.process_DropsEvent(self,
                                             event,
                                             message = kwargs["message"])

        # Drop confirmed
        #
        if event.identifier == self.client_id:

            self.await_confirmation = False

    def process_ChangePropertyEvent(self, event, **kwargs):
        """Call default and unblock client.
        """

        # Call default.
        #
        fabula.core.Engine.process_ChangePropertyEvent(self,
                                                   event,
                                                   message = kwargs["message"])

        # ChangeProperty confirmed
        #
        if event.identifier == self.client_id:

            self.await_confirmation = False

    def process_ManipulatesEvent(self, event, **kwargs):
        """Unset await confirmation flag.
        """

        # TODO: ManipulatesEvent is currently not passed to the UserInterface

        if event.identifier == self.client_id:

            self.await_confirmation = False

        fabula.LOGGER.debug("await_confirmation unset")

    def process_MovesToEvent(self, event, **kwargs):
        """Notify the Room and add the event to the message.
        """

        # Is this the very same as the latest
        # local MovesToEvent?
        #
        if (event.identifier == self.local_moves_to_event.identifier
            and event.location == self.local_moves_to_event.location):

            # Fine, we already had that.
            #
            fabula.LOGGER.info("server issued MovesToEvent already applied: ('%s', '%s')"
                              % (event.identifier, event.location))

            # Reset copy of local event
            #
            self.local_moves_to_event = fabula.MovesToEvent(None, None)

            if event.identifier == self.client_id:

                self.await_confirmation = False

        else:

            # Call default implementation
            #
            fabula.core.Engine.process_MovesToEvent(self,
                                                   event,
                                                   message = kwargs["message"])

            # Only allow new input if the last
            # MovesToEvent has been confirmed.
            #
            if self.local_moves_to_event.identifier == None:

                # TODO: check location == None as well?
                #
                if event.identifier == self.client_id:

                    self.await_confirmation = False

    def process_PicksUpEvent(self, event, **kwargs):
        """The entity is deleted from the Room and added to Client.rack
        """

        # Call default
        #
        fabula.core.Engine.process_PicksUpEvent(self,
                                                event,
                                                message = kwargs["message"])

        # picking up confirmed
        #
        if event.identifier == self.client_id:

            self.await_confirmation = False

    def process_PerceptionEvent(self, event, **kwargs):
        """Unblock the client and call the base class implementation.
        """

        # That is a confirmation
        #
        if event.identifier == self.client_id:

            self.await_confirmation = False

        # Call default implementation
        #
        fabula.core.Engine.process_PerceptionEvent(self,
                                                   event,
                                                   message = kwargs["message"])

    def process_SaysEvent(self, event, **kwargs):
        """Unblock the client and call the base class implementation.
        """

        # TODO: This is a temporary fix. A SaysEvent is a valid confirmation of an attempt, but only if the player is the target. Introduce targets in SaysEvent?
        #
        self.await_confirmation = False

        # Call default implementation
        #
        fabula.core.Engine.process_PerceptionEvent(self,
                                                   event,
                                                   message = kwargs["message"])

    def process_DeleteEvent(self, event, **kwargs):
        """Sanity check, then let self.room process the Event.
        """

        # TODO: This is just a hack, see TODO for run() for details
        #
        if event.identifier in self.room.entity_dict:

            # Now call default implementation which lets self.room process the
            # Event and queues it in the Message given
            #
            fabula.core.Engine.process_DeleteEvent(self,
                                                   event,
                                                   message = kwargs["message"])

        else:
            fabula.LOGGER.warning("Entity to delete does not exist.")

    def process_EnterRoomEvent(self, event, **kwargs):
        """This method empties all data structures and passes the event on
           to the UserInterface since an EnterRoomEvent means the server
           is about to send a new map, respawn the player and send items and
           NPCs.
        """

        # Delete old room and create new
        #
        self.room = fabula.Room(event.room_identifier)

        # There possibly will be no more confirmation
        # for past attempts, so do not wait for them
        #
        self.await_confirmation = False

        # Clear the dict of Entites which have been deleted.
        #
        self.deleted_entities_dict = {}

        # Call default implementation
        #
        fabula.core.Engine.process_EnterRoomEvent(self,
                                                 event,
                                                 message = kwargs["message"])

    def process_RoomCompleteEvent(self, event, **kwargs):
        """The event is queued for the UserInterface here.
           RoomCompleteEvent notifies the client that the player,
           all map elements, items and NPCs have been transfered.
           By the time the event arrives the Client
           should have saved all important data in data structures.
        """

        # Call default implementation
        #
        fabula.core.Engine.process_RoomCompleteEvent(self,
                                                    event,
                                                    message = kwargs["message"])

    def process_ExitEvent(self, event, **kwargs):
        """Trigger Client shutdown by setting self.plugin.exit_requested to True.
        """

        fabula.LOGGER.critical("server has closed the session")

        self.plugin.exit_requested = True

        return
