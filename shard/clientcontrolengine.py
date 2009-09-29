""" Shard Client Control Engine

    Extracted from shard.py on 22. Sep 2009
"""

import shard

class ClientControlEngine:
    '''An instance of this class is the main engine in every
       Shard client. It connects to the Client Interface and
       to the PresentationEngine, passes events and keeps track
       of Entities. It is normally instantiated in a small
       setup script "run_shardclient.py".'''

    ####################
    # Init

    def __init__(self, interface_instance, presentation_engine_instance, logger):
        '''The ClientControlEngine must be instantiated with an
           instance of a subclass of shard.interfaces.Interface
           which handles the connection to the server or supplies
           events in some other way, and an instance of PresentationEngine
           which presents the game action.'''

        # Attach logger
        #
        self.logger = logger

        self.interface = interface_instance
        self.presentation_engine = presentation_engine_instance

        # Set up flags used by self.run()
        #
        self.await_confirmation = False

        # A dictionary that maps event classes to functions 
        # to be called for the respective event.
        # I just love to use dicts to avoid endless
        # if... elif... clauses. :-)
        #
        self.event_dict = {shard.AttemptFailedEvent : self.process_AttemptFailedEvent, 
                           shard.CanSpeakEvent : self.process_CanSpeakEvent, 
                           shard.DropsEvent : self.process_DropsEvent, 
                           shard.MovesToEvent : self.process_MovesToEvent, 
                           shard.PicksUpEvent : self.process_PicksUpEvent, 
                           shard.CustomEntityEvent : self.process_CustomEntityEvent, 
                           shard.PerceptionEvent : self.process_PerceptionEvent, 
                           shard.SaysEvent : self.process_SaysEvent, 
                           shard.ChangeMapElementEvent : self.process_ChangeMapElementEvent, 
                           shard.DeleteEvent : self.process_DeleteEvent, 
                           shard.EnterRoomEvent : self.process_EnterRoomEvent, 
                           shard.RoomCompleteEvent : self.process_RoomCompleteEvent, 
                           shard.SpawnEvent : self.process_SpawnEvent}

        # self.entity_dict keeps track of all active Entites.
        # It uses the identifier as a key, assuming that it
        # is unique.
        #
        self.entity_dict = {}

        # A dict for Entites which have been deleted, for
        # the convenience of the PresentationEngine. Usually it
        # should be cleared after each rendering.
        #
        self.deleted_entities_dict = {}

        # A list of tiles for the current room, for
        # the convenience of the PresentationEngine.
        #
        self.tile_list = []

        # self.map is an attempt of an efficient storage of
        # an arbitrary two-dimensional map. To save space, 
        # only explicitly defined elements are stored. This
        # is done in a dict of dicts, hopefully speeding up
        # the retrieval of elements by avoiding tests 
        # element-by-element. Keys are numbers. Access the
        # elemty using self.map[x][y]. The lower left element
        # is self.map[0][0].
        #
        self.map = {}

        # The ClientControlEngine examines the events of a Server
        # Message and applies them. events for special
        # consideration for the PresentationEngine are collected
        # in a Message for the PresentationEngine.
        # The ClientControlEngine has to empty the Message once 
        # the PresentationEngine has rendered all Events.
        #
        self.presentation_engine_message = shard.Message([])

        # We attach custom flags to the Message to notify
        # the PresentationEngine whether an EnterRoomEvent or
        # RoomCompleteEvent occured, so it does not have
        # to scan the events.
        #
        self.presentation_engine_message.has_EnterRoomEvent = False
        self.presentation_engine_message.has_RoomCompleteEvent = False

        # In self.client_message we collect Client events to be
        # sent to the server in each loop.
        #
        self.client_message = shard.Message([])
        
        self.got_empty_message = False

        self.logger.info("complete")

        # TODO: set up the inventory

    ####################
    # Main Loop

    def run(self):
        '''Main loop of the ClientControlEngine. This is
           a blocking method. It calls all the process methods
           to process events.'''

        # TODO: The current implementation is too overtrustful.
        # It should check much more thoroughly if the
        # affected Entites exist at all and so on. Since
        # this is a kind of precondition or even invariant, 
        # it should be covered using a "design by contract"
        # approach to the whole thing instead of putting
        # neat "if" clauses here and there.

        self.logger.info("starting")

        # Send InitEvent to trigger a complete update
        # from the server
        #
        self.interface.send_message(shard.Message([shard.InitEvent()]))

        while not self.presentation_engine.exit_requested:

            # grab_message must and will return a Message, but
            # it possibly has an empty event_list.
            #
            server_message = self.interface.grab_message()

            if server_message.event_list:

                self.logger.info("got server_message: \n"
                      + str(server_message.event_list))

                self.got_empty_message = False

            elif not self.got_empty_message:

                self.logger.info("got an empty server_message.")

                self.got_empty_message = True

            # First handle the events in the ClientControlEngine, 
            # gathering Entities and Map Elements and preparing
            # a Message for the PresentationEngine
            #
            for current_event in server_message.event_list:

                # This is a bit of Python magic. 
                # self.event_dict is a dict which maps classes to handling
                # functions. We use the class of the event supplied as
                # a key to call the appropriate handler, and hand over
                # the event.
                #
                self.event_dict[current_event.__class__](current_event)

            # Now that everything is set and stored, call
            # the PresentationEngine to render the messages.

            # First hand over / update the necessary data.
            #
            self.presentation_engine.entity_dict = self.entity_dict
            self.presentation_engine.deleted_entities_dict = self.deleted_entities_dict
            self.presentation_engine.tile_list = self.tile_list
            self.presentation_engine.Map = self.map

            # This call may take an almost arbitrary amount
            # of time, since there may be long actions to
            # be shown by the PresentationEngine.
            # Notice: render_message() must be called regularly
            # even if the server Message and thus the
            # PresentationEngine_message are empty!
            #
            self.presentation_engine.render_message(self.presentation_engine_message)

            # The PresentationEngine returned, the Server Message has
            # been applied and rendered. Clean up.
            #
            self.presentation_engine_message = shard.Message([])
            self.deleted_entities_dict = {}
            self.presentation_engine_message.has_EnterRoomEvent = False
            self.presentation_engine_message.has_RoomCompleteEvent = False

            # Up to now, we did not care whether the server Message
            # had any events at all. But we only send a 
            # MessageAppliedEvent if it had.
            #
            if server_message.event_list:
                self.client_message.event_list.append(shard.MessageAppliedEvent())

            # TODO: possibly unset "AwaitConfirmation" flag
            # If there has been a Confirmation for a LookAt or
            # TriesToManipulate, unset "AwaitConfirmation" flag

            # If we do not await a Confirmation anymore, 
            # we evaluate the player input if any.
            # The PresentationEngine might have collected some
            # player input and converted it to events.
            #
            if (self.presentation_engine.player_event_list
                and not self.await_confirmation):

                # We queue player triggered events before 
                # MessageAppliedEvent so the server processes
                # all events before sending anything new.
                #
                self.client_message.event_list = (self.presentation_engine.player_event_list
                                                  + self.client_message.event_list)

                # Since we had player input, we now await confirmation
                #
                self.await_confirmation = True

            # If this iteration yielded any events, send them.
            #
            if self.client_message.event_list:
                self.interface.send_message(self.client_message)

                # Clean up
                #
                self.client_message = shard.Message([])

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

    def process_AttemptFailedEvent(self, event):
        '''Currently not implemented.'''

        #    ControlEngine: if there was a Confirmation and
        #    it has been applied or if there was an
        #    AttemptFailedEvent: unset "AwaitConfirmation" flag
        #
        pass

    def process_CanSpeakEvent(self, event):
        '''Currently not implemented.'''

        #    ControlEngine: if there was a Confirmation and
        #    it has been applied or if there was an
        #    AttemptFailedEvent: unset "AwaitConfirmation" flag

        # Pass on the event.
        #
        self.presentation_engine_message.event_list.append(event)

    def process_DropsEvent(self, event):
        '''Currently not implemented.'''

        # Remove the Entity from the Inventory
        #
        # Add it to the entity_dict, setting the
        # coordinates from direction
        #
        # Queue the DropsEvent (for Animation) and
        # a SpawnEvent for the PresentationEngine
        #
        #    ControlEngine: if there was a Confirmation and
        #    it has been applied or if there was an
        #    AttemptFailedEvent: unset "AwaitConfirmation" flag
        #
        pass

    def process_MovesToEvent(self, event):
        '''Currently not implemented.'''

        # ControlEngine: if there was a Confirmation and it has been applied
        # or if there was an AttemptFailedEvent: unset "AwaitConfirmation" flag
        #
        # ControlEngine: pass events to Entities
        #     Entity: change location, set graphics, custom actions
        # ControlEngine: pass Message/Events to PresentationEngine
        #
        pass

    def process_PicksUpEvent(self, event):
        '''Currently not implemented.'''

        # Remove from the entity_dict
        #
        # Save in deleted_entities_dict
        #
        # Move the Entity to the Inventory
        #
        # Queue the PicksUpEvent (for Animation) and
        # a DeleteEvent for the PresentationEngine
        #
        #    ControlEngine: if there was a Confirmation and
        #    it has been applied or if there was an
        #    AttemptFailedEvent: unset "AwaitConfirmation" flag
        #
        pass

    def process_CustomEntityEvent(self, event):
        '''The key-value dict of a CustomEntiyEvent 
           is just passed on to the Entity.'''

        self.entity_dict[event.identifier].process_CustomEntityEvent(event.key_value_dict)

    def process_PerceptionEvent(self, event):
        '''A perception must be displayed by the 
           PresentationEngine, so it is queued in a Message passed
           from the ClientControlEngine.'''

        #    ControlEngine: if there was a Confirmation
        #    (here: for LookAt, Manipulate)
        #    and it has been applied
        #    or if there was an AttemptFailedEvent: unset
        #    "AwaitConfirmation" flag
        #
        self.presentation_engine_message.event_list.append(event)

    def process_SaysEvent(self, event):
        '''The PresentationEngine usually must display the 
           spoken text. Thus the event is put in the
           event queue for the PresentationEngine.
           The PresentationEngine is going to notify
           the Entity once it starts speaking so it
           can provide an animation.'''

        self.presentation_engine_message.event_list.append(event)

    def process_ChangeMapElementEvent(self, event):
        '''Store the tile given in self.map, 
           a dict of dicts with x- and
           y-coordinates as keys. Also save
           it for the PresentationEngine.'''

        try:
            # see if a dict for the column (x coordinate)
            # already exists
            #
            self.map[event.location[0]]

        except KeyError:

            self.map[event.location[0]] = {}

        # possibly overwrite existing tile
        #
        self.map[event.location[0]][event.location[1]] = event.tile

        # Append the tile to a list for easy
        # fetching of the tile's asset
        #
        self.tile_list.append(event.tile)

        # Append the event to the queue for the PresentationEngine.
        #
        self.presentation_engine_message.event_list.append(event)

    def process_DeleteEvent(self, event):
        '''Save the Entity to be deleted in the
           deleted_entities_dict for the 
           PresentationEngine, then remove it from the
           entity_dict.'''

        # TODO: This is just a hack, see TODO for run() for details
        #
        if event.identifier in self.entity_dict.keys():

            # Save the Entity in the deleted_entities_dict
            # to notify the PresentationEngine
            #
            self.deleted_entities_dict[event.identifier] = self.entity_dict[event.identifier]

            # Now remove the Entity
            #
            del self.entity_dict[event.identifier]

            # Append the event to the queue for the PresentationEngine.
            # The PresentationEngine needs the event for knowing
            # when exactly to remove the Entity.
            #
            self.presentation_engine_message.event_list.append(event)

        else:
            self.logger.warn("Entity to delete does not exist.")

    def process_EnterRoomEvent(self, event):
        '''An EnterRoomEvent means the server is
           about to send a new map, respawn the
           player and send items and NPCs. So
           this method empties all data 
           structures and passes the event on to 
           the PresentationEngine.'''

        # There possibly will be no more confirmation
        # for past attempts, so do not wait for them
        #
        self.await_confirmation = False

        # All Entities in this room have to be sent.
        # No use keeping old ones around, expecially with old
        # locations.
        #
        self.entity_dict = {}

        # Clear the dict of Entites which have been deleted.
        #
        self.deleted_entities_dict = {}

        # Clear the list of tiles for the room.
        #
        self.tile_list = []

        # Awaiting a new map!
        #
        self.map = {}

        # Finally set the flag in the Message
        # for the PresentationEngine and queue the event
        # so the PresentationEngine knows what happend after
        # that.
        #
        self.presentation_engine_message.has_EnterRoomEvent = True

        self.presentation_engine_message.event_list.append(event)

    def process_RoomCompleteEvent(self, event):
        '''RoomCompleteEvent notifies the client that
           the player, all map elements, items and
           NPCs have been transfered. By the time the
           event arrives the ClientControlEngine should
           have saved all important data in data
           structures. So the event is queued for
           the PresentationEngine here.'''

        # This is a convenience flag so the PresentationEngine
        # does not have to scan the event_list.
        #
        self.presentation_engine_message.has_RoomCompleteEvent = True

        # Queue the event. All events after this are
        # rendered.
        #
        self.presentation_engine_message.event_list.append(event)

    def process_SpawnEvent(self, event):
        '''Add the Entity given to the entity_dict
           and pass the SpawnEvent on to the PresentationEngine.'''

        self.entity_dict[event.entity.identifier] = event.entity

        self.presentation_engine_message.event_list.append(event)
