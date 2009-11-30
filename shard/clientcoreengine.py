""" Shard Client Core Engine
"""

# Extracted from shard.py on 22. Sep 2009

import shard
import shard.coreengine
import time
import datetime

class ClientCoreEngine(shard.coreengine.CoreEngine):
    """An instance of this class is the main engine in every
       Shard client. It connects to the Client Interface and
       to the PresentationEngine, passes events and keeps track
       of Entities. It is normally instantiated in shard.run.
    """

    ####################
    # Init

    def __init__(self, player_id, interface_instance, presentation_engine_instance, logger):
        """The ClientCoreEngine must be instantiated with an
           instance of a subclass of shard.interfaces.Interface
           which handles the connection to the server or supplies
           events in some other way, and an instance of PresentationEngine
           which presents the game action.
        """

        # Save the player id for ServerCoreEngine
        # and PresentationEngine.
        #
        self.player_id = player_id

        # First setup base class
        #
        self.setup_eventprocessor()

        # Then setup CoreEngine internals
        #
        self.setup_core_engine(interface_instance,
                               presentation_engine_instance,
                               logger)

        # Now we have:
        #
        # self.room = shard.Room()
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
        self.message_sent = shard.Message([])

        # Timestamp to detect server dropouts
        #
        self.timestamp = None

        # Remember the latest local MovesToEvent
        #
        self.local_moves_to_event = shard.MovesToEvent(None, None)

        self.logger.info("complete")

    ####################
    # Main Loop

    def run(self):
        """Main loop of the ClientCoreEngine. This is
           a blocking method. It calls all the process
           methods to process events.
        """

        # TODO: The current implementation is too overtrustful.
        # It should check much more thoroughly if the
        # affected Entites exist at all and so on. Since
        # this is a kind of precondition or even invariant, 
        # it should be covered using a "design by contract"
        # approach to the whole thing instead of putting
        # neat "if" clauses here and there.

        self.logger.info("starting")

        self.logger.info("waiting for interface to connect")

        while not self.interface.connections:

            self.logger.info("no connection yet, waiting 1s")

            time.sleep(1.0)

        self.logger.info("connection found, sending InitEvent")

        # There is only one connection in the
        # ClientInterface, so use the first one
        #
        self.message_buffer = self.interface.connections.values()[0] 

        self.message_buffer.send_message(shard.Message([shard.InitEvent(self.player_id)]))

        while not self.plugin.exit_requested:

            # grab_message must and will return a Message, but
            # it possibly has an empty event_list.
            #
            server_message = self.message_buffer.grab_message()

            if server_message.event_list:

                self.logger.info("got server_message: %s"
                                 % server_message.event_list)

                self.got_empty_message = False

            elif not self.got_empty_message:

                # TODO: The PresentationEngine currently locks up when there are no answers from the server. The ClientCoreEngine should time out and exit politely if there is no initial answer from the server or there has been no answer for some time.

                self.logger.info("got an empty server_message.")

                self.got_empty_message = True

            # First handle the events in the ClientCoreEngine, 
            # updating the room and preparing a Message for
            # the PresentationEngine
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
                self.event_dict[current_event.__class__](current_event,
                                                         message = self.message_for_plugin)

            # Now that everything is set and stored, call
            # the PresentationEngine to process the messages.

            # Ideally we want to call process_message()
            # once per frame, but the call may take an
            # almost arbitrary amount of time.
            # At least process_message() must be called
            # regularly even if the server Message and
            # thus message_for_plugin  are empty.
            #
            message_from_plugin = self.plugin.process_message(self.message_for_plugin,
                                                              self.room,
                                                              self.player_id)

            # The PresentationEngine returned, the Server Message has
            # been applied and processed. Clean up.
            #
            self.message_for_plugin = shard.Message([])
            self.message_for_plugin.has_EnterRoomEvent = False
            self.message_for_plugin.has_RoomCompleteEvent = False

            # TODO: possibly unset "AwaitConfirmation" flag
            # If there has been a Confirmation for a LookAt or
            # TriesToManipulate, unset "AwaitConfirmation" flag

            # The PresentationEngine might have collected some
            # player input and converted it to events.
            #
            if message_from_plugin.event_list:

                if self.await_confirmation:

                    # Player input, but we still await confirmation.

                    if self.timestamp == None:

                        self.logger.debug("player attempt but still waiting - starting timer")

                        self.timestamp = datetime.datetime.today()

                    else:

                        timedifference = datetime.datetime.today() - self.timestamp

                        if timedifference.seconds >= 1:

                            self.logger.debug("1s waiting but no confirmation - "
                                              + "resending and resetting timer")

                            self.message_buffer.send_message(self.last_message)

                            self.timestamp = None

                        else:

                            self.logger.debug("still waiting for confirmation")

                else:

                    # If we do not await a Confirmation anymore, 
                    # we evaluate the player input if any.

                    # We queue player triggered events before 
                    # possible events from the ClientCoreEngine.
                    # TODO: Since MessageAppliedEvent is gone, are there any events left to be sent by the ClientCoreEngine?
                    #
                    self.message_for_remote.event_list = (message_from_plugin.event_list
                                                          + self.message_for_remote.event_list)

                    # Local movement tests
                    #
                    for event in message_from_plugin.event_list:

                        if isinstance(event, shard.AttemptEvent):

                            # TODO: similar to ServerCoreEngine.process_TriesToMoveEvent()

                            # Do we need to move / turn at all?
                            #
                            location = self.room.entity_locations[event.identifier]
                            difference = shard.difference_2d(location,
                                                             event.target_identifier)

                            # In case of a TriesToMoveEvent, test and
                            # approve the movement locally to allow
                            # for a smooth user experience. We have
                            # the current map information after all.
                            #
                            # Only allow certain vectors
                            #
                            if (difference in ((0, 1), (0, -1), (1, 0), (-1, 0))
                                and isinstance(event, shard.TriesToMoveEvent)):

                                self.logger.debug("applying TriesToMoveEvent locally")

                                # TODO: event.identifier in self.room.entity_dict? event.target_identifier in shard.DIRECTION_VECTOR?

                                # TODO: code duplicated from ServerCoreEngine.process_TriesToMoveEvent()

                                # Test if a movement from the current
                                # entity location to the new location
                                # on the map is possible
                                #
                                # We queue the event in self.message_for_plugin,
                                # so it will be rendered upon next call. That
                                # way it bypasses the ClientCoreEngine; its status
                                # will be updated upon server confirmation. So
                                # we will have a difference between client state
                                # and presentation. We trust that it will be resolved
                                # by the server in very short time.
                                #
                                try:
                                    # Check tile type
                                    #
                                    tile = self.room.floor_plan[event.target_identifier].tile 

                                    if tile.tile_type == shard.FLOOR:

                                        # Check if this field is occupied
                                        #
                                        occupied = False

                                        for entity in self.room.floor_plan[event.target_identifier].entities:

                                            if entity.entity_type == shard.ITEM_BLOCK:

                                                occupied = True

                                        if occupied:

                                            # Instead of
                                            #self.message_for_plugin.event_list.append(shard.AttemptFailedEvent(event.identifier))
                                            # we wait for the server to respond with
                                            # AttemptFailedEvent
                                            #
                                            pass

                                        else:
                                            # All clear. Go!
                                            #
                                            moves_to_event = shard.MovesToEvent(event.identifier,
                                                                                event.target_identifier)
     
                                            # Update room, needed for PresentationEngine
                                            #
                                            self.process_MovesToEvent(moves_to_event,
                                                                      message = self.message_for_plugin)

                                            # Remember event for crosscheck with
                                            # event from ServerCoreEngine
                                            #
                                            self.local_moves_to_event = moves_to_event

                                    else:
                                        # Instead of
                                        #self.message_for_plugin.event_list.append(shard.AttemptFailedEvent(event.identifier))
                                        # we wait for the server to respond with
                                        # AttemptFailedEvent
                                        #
                                        pass

                                except KeyError:

                                    # Instead of
                                    #self.message_for_plugin.event_list.append(shard.AttemptFailedEvent(event.identifier))
                                    # we wait for the server to respond with
                                    # AttemptFailedEvent
                                    #
                                    pass

                    # Since we had player input, we now await confirmation
                    #
                    self.logger.debug("awaiting confirmation, discarding further user input")

                    self.await_confirmation = True

                    # Reset dropout timer
                    #
                    self.timestamp = None

            # If this iteration yielded any events, send them.
            #
            if self.message_for_remote.event_list:

                self.message_buffer.send_message(self.message_for_remote)

                # Save for possible re-send on dropout
                #
                self.last_message = self.message_for_remote

                # Clean up
                #
                self.message_for_remote = shard.Message([])

            # OK, iteration done. If no exit requested, 
            # grab the next server message!

        # exit has been requested
        
        self.logger.info("exit requested from "
              + "PresentationEngine, shutting down interface...")

        # stop the Client Interface thread
        #
        self.interface.shutdown()

        self.logger.info("shutdown confirmed.")

        # TODO: possibly exit cleanly from the PresentationEngine here

        return

    ####################
    # Auxiliary Methods

    # TODO: unset await_confirmation only if the player (id) is affected!

    def process_AttemptFailedEvent(self, event, **kwargs):
        """Unset await_confirmation flag.
        """

        self.logger.debug("called")

        # Did this fail for the Entity we just moved locally?
        #
        if event.identifier == self.local_moves_to_event.identifier:

            entity = self.room.entity_dict[event.identifier]
            location = self.room.entity_locations[event.identifier]

            self.logger.debug("attempt failed for %s, now at %s"
                              % (event.identifier, location))

            # TODO: This still relies on direction information which has been removed from Shard core. Replace by a custom record of the old position.
            #
            vector = self.plugin.direction_vector_dict[entity.direction]

            restored_x = location[0] - vector[0]
            restored_y = location[1] - vector[1]

            self.room.process_MovesToEvent(shard.MovesToEvent(event.identifier,
                                                              (restored_x, restored_y)))

            self.logger.debug("%s now reverted to %s" % (event.identifier,
                                                         (restored_x, restored_y)))

        self.await_confirmation = False

    #def process_CanSpeakEvent(self, event, **kwargs):
    #    """Currently not implemented."""
    #    #    CoreEngine: if there was a Confirmation and
    #    #    it has been applied or if there was an
    #    #    AttemptFailedEvent: unset "AwaitConfirmation" flag
    #    # Pass on the event.
    #    #
    #    message.event_list.append(event)

    def process_DropsEvent(self, event, **kwargs):
        """Remove affected Entity from rack,
           queue SpawnEvent for room and Plugin,
           and pass on the DropsEvent.
        """

        # TODO: the DropsEvent and PicksUpEvent handling in ClientCoreEngine and Plugin are asymmetrical. This is ugly. Unify.

        # Call default.
        #
        shard.coreengine.CoreEngine.process_DropsEvent(self,
                                                       event,
                                                       message = kwargs["message"])

        # Drop confirmed
        #
        self.await_confirmation = False

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
            self.logger.debug("server issued MovesToEvent already applied: ('%s', '%s')"
                              % (event.identifier, event.location))

            # Reset copy of local event
            #
            self.local_moves_to_event = shard.MovesToEvent(None, None)

            self.await_confirmation = False

        else:

            # Call default implementation
            #
            shard.coreengine.CoreEngine.process_MovesToEvent(self,
                                                             event,
                                                             message = kwargs["message"])

            # Only allow new input if the last
            # MovesToEvent has been confirmed.
            #
            if self.local_moves_to_event.identifier == None:

                # TODO: check location == None as well?
                #
                self.await_confirmation = False

    def process_PicksUpEvent(self, event, **kwargs):
        """The entity is deleted from the
           Room and added to ClientCoreEngine.rack 
        """

        # Call default
        #
        shard.coreengine.CoreEngine.process_PicksUpEvent(self,
                                                         event,
                                                         message = kwargs["message"])

        # picking up confirmed
        #
        self.await_confirmation = False

    def process_PerceptionEvent(self, event, **kwargs):
        """A perception must be displayed by the 
           PresentationEngine, so it is queued in a Message passed
           from the ClientCoreEngine."""

        # That is a confirmation
        #
        self.await_confirmation = False

        # Call default implementation
        #
        shard.coreengine.CoreEngine.process_PerceptionEvent(self,
                                                            event, 
                                                            message = kwargs["message"])

    #def process_SaysEvent(self, event, **kwargs):
    #    """The PresentationEngine usually must display the 
    #       spoken text. Thus the event is put in the
    #       event queue for the PresentationEngine.
    #       The PresentationEngine is going to notify
    #       the Entity once it starts speaking so it
    #       can provide an animation."""
    #
    #    message.event_list.append(event)

    def process_DeleteEvent(self, event, **kwargs):
        """Sanity check, then let self.room process the Event.
        """

        # TODO: This is just a hack, see TODO for run() for details
        #
        if event.identifier in self.room.entity_dict:

            # Now call default implementation which
            # lets self.room process the Event and
            # queues it in the Message given
            #
            shard.coreengine.CoreEngine.process_DeleteEvent(self,
                                                            event,
                                                            message = kwargs["message"])

        else:
            self.logger.warn("Entity to delete does not exist.")

    def process_EnterRoomEvent(self, event, **kwargs):
        """An EnterRoomEvent means the server is
           about to send a new map, respawn the
           player and send items and NPCs. So
           this method empties all data 
           structures and passes the event on to 
           the PresentationEngine.
        """

        # Delete old room and create new
        #
        self.room = shard.Room()

        # There possibly will be no more confirmation
        # for past attempts, so do not wait for them
        #
        self.await_confirmation = False

        # Clear the dict of Entites which have been deleted.
        #
        self.deleted_entities_dict = {}

        # Finally set the flag in the Message
        # for the PresentationEngine.
        #
        kwargs["message"].has_EnterRoomEvent = True

        # Call default implementation
        #
        shard.coreengine.CoreEngine.process_EnterRoomEvent(self,
                                                           event,
                                                           message = kwargs["message"])

    def process_RoomCompleteEvent(self, event, **kwargs):
        """RoomCompleteEvent notifies the client that
           the player, all map elements, items and
           NPCs have been transfered. By the time the
           event arrives the ClientCoreEngine should
           have saved all important data in data
           structures. So the event is queued for
           the PresentationEngine here."""

        # This is a convenience flag so the PresentationEngine
        # does not have to scan the event_list.
        #
        kwargs["message"].has_RoomCompleteEvent = True

        # Call default implementation
        #
        shard.coreengine.CoreEngine.process_RoomCompleteEvent(self,
                                                              event,
                                                              message = kwargs["message"])
