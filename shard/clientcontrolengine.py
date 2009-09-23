""" Shard Client Control Engine

    Extracted from shard.py on 22. Sep 2009
"""

import shard

class ClientControlEngine:
    '''An instance of this class is the main engine in every
       Shard client. It connects to the Client Interface and
       to the VisualEngine, passes events and keeps track
       of Entities. It is normally instantiated in a small
       setup script "run_shardclient.py".'''

    ####################
    # Init

    def __init__(self, client_interface_instance, visual_engine_instance):
        '''The ClientControlEngine must be instantiated with an
           instance of shard.ClientInterface which handles
           the connection to the server or supplies events
           in some other way, and an instance of 
           shard.VisualEngine which graphically renders the
           game action.'''

        self.client_interface = client_interface_instance
        self.visual_engine = visual_engine_instance

        # Set up flags used by self.run()
        self.await_confirmation = False

        # A dictionary that maps event classes to functions 
        # to be called for the respective event.
        # I just love to use dicts to avoid endless
        # if... elif... clauses. :-)
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
        # It uses the identifier as a key, assuming that is
        # is unique.
        self.entity_dict = {}

        # A dict for Entites which have been deleted, for
        # the convenience of the VisualEngine. Usually it
        # should be cleared after each rendering.
        self.deleted_entities_dict = {}

        # A list of tiles for the current room, for
        # the convenience of the VisualEngine.
        self.tile_list = []

        # self.map is an attempt of an efficient storage of
        # an arbitrary two-dimensional map. To save space, 
        # only explicitly defined elements are stored. This
        # is done in a dict of dicts, hopefully speeding up
        # the retrieval of elements by avoiding tests 
        # element-by-element. Keys are numbers. Access the
        # elemty using self.map[x][y]. The lower left element
        # is self.map[0][0].
        self.map = {}

        # The ClientControlEngine examines the events of a Server
        # Message and applies them. events for special
        # consideration for the VisualEngine are collected
        # in a Message for the VisualEngine.
        # The ClientControlEngine has to empty the Message once 
        # the VisualEngine has rendered all Events.
        self.visual_engine_message = shard.Message([])

        # We attach custom flags to the Message to notify
        # the VisualEngine whether an EnterRoomEvent or
        # RoomCompleteEvent occured, so it does not have
        # to scan the events.
        self.visual_engine_message.has_EnterRoomEvent = False
        self.visual_engine_message.has_RoomCompleteEvent = False

        # In self.client_message we collect Client events to be
        # sent to the server in each loop.
        self.client_message = shard.Message([])
        
        # DELETE
        self.got_empty_message = False
        print("ClientControlEngine: __init__ complete.")
        # DELETE

        # TODO: set up the inventory

    ####################
    # Main Loop

    def run(self):
        '''Main loop of the ClientControlEngine. This is
           a blocking method. It calls all the process methods
           to process events.'''

        # TODO:
        # The current implementation is too overtrustful.
        # It should check much more thoroughly if the
        # affected Entites exist at all and so on. Since
        # this is a kind of precondition or even invariant, 
        # it should be covered using a "design by contract"
        # approach to the whole thing instead of putting
        # neat "if" clauses here and there.

        # DELETE
        print("ClientControlEngine: starting main loop in run().")

        # Send InitEvent to trigger a complete update
        # from the server
        self.client_interface.send_message(shard.Message([shard.InitEvent()]))

        while not self.visual_engine.exit_requested:
            # grab_message must and will return a Message, but
            # it possibly has an empty event_list.
            server_message = self.client_interface.grab_message()

            # DELETE
            if len(server_message.event_list):
                print("ClientControlEngine: got server_message: \n"
                      + str(server_message.event_list))
                self.got_empty_message = False
            elif not self.got_empty_message:
                print("ClientControlEngine: got an empty server_message.")
                self.got_empty_message = True
            # DELETE

            # First handle the events in the ClientControlEngine, 
            # gathering Entities and Map Elements and preparing
            # a Message for the VisualEngine
            for current_event in server_message.event_list:
                # This is a bit of Python magic. 
                # self.event_dict is a dict which maps classes to handling
                # functions. We use the class of the event supplied as
                # a key to call the appropriate handler, and hand over
                # the event.
                self.event_dict[current_event.__class__](current_event)

            # Now that everything is set and stored, call
            # the VisualEngine to render the messages.

            # First hand over / update the necessary data.
            self.visual_engine.entity_dict = self.entity_dict
            self.visual_engine.deleted_entities_dict = self.deleted_entities_dict
            self.visual_engine.tile_list = self.tile_list
            self.visual_engine.Map = self.map

            # This call may take an almost arbitrary amount
            # of time, since there may be long actions to
            # be shown by the VisualEngine.
            # Notice: render_message() must be called regularly
            # even if the server Message and thus the
            # Visualengine_message are empty!
            self.visual_engine.render_message(self.visual_engine_message)

            # The VisualEngine returned, the Server Message has
            # been applied and rendered. Clean up.
            self.visual_engine_message = shard.Message([])
            self.deleted_entities_dict = {}
            self.visual_engine_message.has_EnterRoomEvent = False
            self.visual_engine_message.has_RoomCompleteEvent = False

            # Up to now, we did not care whether the server Message
            # had any events at all. But we only send a 
            # MessageAppliedEvent if it had.
            if len(server_message.event_list)>0:
                self.client_message.event_list.append(shard.MessageAppliedEvent())

            # TODO:
            # If there has been a Confirmation for a LookAt or
            # TriesToManipulate, unset "AwaitConfirmation" flag

            # If we do not await a Confirmation anymore, 
            # we evaluate the player input if any.
            # The VisualEngine might have collected some
            # player input and converted it to events.
            if (len(self.visual_engine.player_event_list)>0
                and not self.await_confirmation):
                # We queue player triggered events before 
                # MessageAppliedEvent so the server processes
                # all events before sending anything new.
                self.client_message.event_list = (self.visual_engine.player_event_list
                                                  + self.client_message.event_list)

                # Since we had player input, we now await confirmation
                self.await_confirmation = True

            # If this iteration yielded any events, send them.
            if len(self.client_message.event_list)>0:
                self.client_interface.send_message(self.client_message)

                # Clean up
                self.client_message = shard.Message([])

            # OK, iteration done. If no exit requested, 
            # grab the next server event!

        # exit has been requested
        
        # DELETE
        print("ClientControlEngine.run: exit requested from "
              + "VisualEngine, shutting down interface...")

        # stop the Client Interface thread
        self.client_interface.shutdown()

        # DELETE
        print("ClientControlEngine.run: shutdown confirmed.")

        # TODO:
        # possibly exit cleanly from the VisualEngine here

        return

    ####################
    # Auxiliary Methods

    def process_AttemptFailedEvent(self, event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        #    ControlEngine: if there was a Confirmation and
        #    it has been applied or if there was an
        #    AttemptFailedEvent: unset "AwaitConfirmation" flag
        pass

    def process_CanSpeakEvent(self, event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        #    ControlEngine: if there was a Confirmation and
        #    it has been applied or if there was an
        #    AttemptFailedEvent: unset "AwaitConfirmation" flag

        # Pass on the event.
        self.visual_engine_message.event_list.append(event)

    def process_DropsEvent(self, event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        #
        # Remove the Entity from the Inventory
        #
        # Add it to the entity_dict, setting the
        # coordinates from direction
        #
        # Queue the DropsEvent (for Animation) and
        # a SpawnEvent for the VisualEngine
        #
        #    ControlEngine: if there was a Confirmation and
        #    it has been applied or if there was an
        #    AttemptFailedEvent: unset "AwaitConfirmation" flag
        pass

    def process_MovesToEvent(self, event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        # 
        # ControlEngine: if there was a Confirmation and it has been applied
        # or if there was an AttemptFailedEvent: unset "AwaitConfirmation" flag
        #
        # ControlEngine: pass events to Entities
        #     Entity: change location, set graphics, custom actions
        # ControlEngine: pass Message/Events to VisualEngine
        pass

    def process_PicksUpEvent(self, event):
        '''Currently not implemented.'''
        # Not required for Charanis!
        #
        # Remove from the entity_dict
        #
        # Save in deleted_entities_dict
        #
        # Move the Entity to the Inventory
        #
        # Queue the PicksUpEvent (for Animation) and
        # a DeleteEvent for the VisualEngine
        #
        #    ControlEngine: if there was a Confirmation and
        #    it has been applied or if there was an
        #    AttemptFailedEvent: unset "AwaitConfirmation" flag
        pass

    def process_CustomEntityEvent(self, event):
        '''The key-vlaue dict of a CustomEntiyEvent 
           is just passed on to the Entity.'''
        self.entity_dict[event.identifier].process_CustomEntityEvent(event.key_value_dict)

    def process_PerceptionEvent(self, event):
        '''A perception must be displayed by the 
           VisualEngine, so it is queued in a Message passed
           from the ClientControlEngine.'''
        #    ControlEngine: if there was a Confirmation
        #    (here: for LookAt, Manipulate)
        #    and it has been applied
        #    or if there was an AttemptFailedEvent: unset
        #    "AwaitConfirmation" flag
        self.visual_engine_message.event_list.append(event)

    def process_SaysEvent(self, event):
        '''The VisualEngine usually must display the 
           spoken text. Thus the event is put in the
           event queue for the VisualEngine.
           The VisualEngine is going to notify
           the Entity once it starts speaking so it
           can provide an animation.'''
        self.visual_engine_message.event_list.append(event)

    def process_ChangeMapElementEvent(self, event):
        '''Store the tile given in self.map, 
           a dict of dicts with x- and
           y-coordinates as keys. Also save
           it for the VisualEngine.'''
        try:
            # see if a dict for the column (x coordinate)
            # already exists
            self.map[event.location[0]]
        except KeyError:
            self.map[event.location[0]] = {}

        # possibly overwrite existing tile
        self.map[event.location[0]][event.location[1]] = event.tile

        # Append the tile to a list for easy
        # fetching of the tile's asset
        self.tile_list.append(event.tile)

        # Append the event to the queue for the VisualEngine.
        self.visual_engine_message.event_list.append(event)

    def process_DeleteEvent(self, event):
        '''Save the Entity to be deleted in the
           deleted_entities_dict for the 
           VisualEngine, then remove it from the
           entity_dict.'''

        # DELETE
        # This is just a hack, see TODO for run() for details
        if event.identifier in self.entity_dict.keys():
        # DELETE

            # Save the Entity in the deleted_entities_dict
            # to notify the VisualEngine
            self.deleted_entities_dict[event.identifier] = self.entity_dict[event.identifier]

            # Now remove the Entity
            del self.entity_dict[event.identifier]

            # Append the event to the queue for the VisualEngine.
            # The VisualEngine needs the event for knowing
            # when exactly to remove the Entity.
            self.visual_engine_message.event_list.append(event)

        # DELETE
        else:
            print("process_DeleteEvent: Entity to delete does not exist.")
        # DELETE

    def process_EnterRoomEvent(self, event):
        '''An EnterRoomEvent means the server is
           about to send a new map, respawn the
           player and send items and NPCs. So
           this method  empties all data 
           structures and passes the event on to 
           the VisualEngine.'''
        # There possibly will be no more confirmation
        # for past attempts, so do not wait for them
        self.await_confirmation = False

        # All Entities in this room have to be sent.
        # No use keeping old ones around, expecially with old
        # locations.
        self.entity_dict = {}

        # Clear the dict of Entites which have been deleted.
        self.deleted_entities_dict = {}

        # Clear the list of tiles for the room.
        self.tile_list = []

        # Awaiting a new map!
        self.map = {}

        # Finally set the flag in the Message
        # for the VisualEngine and queue the event
        # so the VisualEngine knows what happend after
        # that.
        self.visual_engine_message.has_EnterRoomEvent = True
        self.visual_engine_message.event_list.append(event)

    def process_RoomCompleteEvent(self, event):
        '''RoomCompleteEvent notifies the client that
           the player, all map elements, items and
           NPCs have been transfered. By the time the
           event arrives the ClientControlEngine should
           have saved all important data in data
           structures. So the event is queued for
           the VisualEngine here.'''
        # This is a convenience flag so the VisualEngine
        # does not have to scan the event_list.
        self.visual_engine_message.has_RoomCompleteEvent = True

        # Queue the event. All events after this are
        # rendered.
        self.visual_engine_message.event_list.append(event)

    def process_SpawnEvent(self, event):
        '''Add the Entity given to the entity_dict
           and pass the SpawnEvent on to the VisualEngine.'''
        self.entity_dict[event.entity.identifier] = event.entity
        self.visual_engine_message.event_list.append(event)

