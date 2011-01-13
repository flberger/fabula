"""Fabula Engine Base Class

   Based on former implementations of the ClientControlEngine
"""

# Work started on 30. Sep 2009

import fabula
import fabula.eventprocessor

class Engine(fabula.eventprocessor.EventProcessor):
    """Common base class for Fabula server and client engines.
       Most likely you will want to override all of the methods when subclassing
       Engine, so the use of this class is providing a structure for Engines.

       Attributes:

       Engine.logger

       Engine.interface

       Engine.plugin
           This is None upon initialisation and must be set to an instance of
           fabula.plugins.Plugin using Engine.set_plugin().

       Engine.message_for_plugin

       Engine.message_for_remote

       Engine.room
           An instance of fabula.Room, initialy None.

       Engine.rack
    """

    def __init__(self, interface_instance, logger):
        """Set up Engine attributes.

           Arguments:

           interface_instance
               An instance of a subclass of
               fabula.interfaces.Interface to communicate
               with the remote host.

           logger
               An instance of logging.Logger.
        """

        # First setup base class
        #
        fabula.eventprocessor.EventProcessor.__init__(self)

        # Attach logger
        #
        self.logger = logger

        self.interface = interface_instance

        self.plugin = None

        # The Engine examines the events of a received
        # Message and applies them. Events for special
        # consideration for the PluginEngine are collected
        # in a Message for the PluginEngine.
        # The Engine has to empty the Message once
        # the PluginEngine has processed all Events.
        #
        self.message_for_plugin = fabula.Message([])

        # In self.message_for_remote we collect events to be
        # sent to the remote host in each loop.
        #
        self.message_for_remote = fabula.Message([])

        # self.room keeps track of the map and active Entites.
        # An actual room is created when the first EnterRoomEvent is
        # encountered.
        #
        self.room = None

        # self.rack serves as a storage for deleted Entities
        # because there may be the need to respawn them.
        #
        self.rack = fabula.Rack()

        self.logger.info("complete")

        return

    def set_plugin(self, plugin_instance):
        """Set the pluginto control or present the game.
           plugin_instance must be an instance of fabula.plugins.Plugin.
        """

        self.plugin = plugin_instance

        return

    def run(self):
        """This is the main loop of an Engine.
           Put all the business logic here.
           This is a blocking method which should call all the process methods
           to process events.
        """

        self.logger.info("starting")

        # You will probably want to run until the
        # plugin engine decides that the game is
        # over.
        #
        while not self.plugin.exit_requested:
            pass

        # exit has been requested

        self.logger.info("exit requested from PluginEngine, shutting down interface...")

        # stop the Interface thread
        #
        self.interface.shutdown()

        self.logger.info("shutdown confirmed.")

        # TODO: possibly exit cleanly from the Plugin here

        return

    def process_TriesToMoveEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_TriesToLookAtEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_TriesToPickUpEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_TriesToDropEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_TriesToManipulateEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_TriesToTalkToEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_MovesToEvent(self, event, **kwargs):
        """Let self.room process the event and pass it on.
        """

        self.logger.debug("%s location before: %s "
                          % (event.identifier,
                             self.room.entity_locations[event.identifier]))

        self.room.process_MovesToEvent(event)

        self.logger.debug("%s location after: %s "
                          % (event.identifier,
                             self.room.entity_locations[event.identifier]))

        kwargs["message"].event_list.append(event)

        return

    def process_PicksUpEvent(self, event, **kwargs):
        """Save the Entity to be picked up in Engine.rack,
           delete the it from Engine.room and pass the
           PicksUpEvent on.
        """

        self.logger.debug("called")

        # Save the Entity to be picked up in Engine.rack
        #
        picked_entity = self.room.entity_dict[event.item_identifier]

        self.rack.store(picked_entity, event.identifier)

        # Delete it from Engine.room
        #
        # TODO: Why not pass the PicksUpEvent to the room and let it handle an according removal?
        #
        delete_event = fabula.DeleteEvent(event.item_identifier)

        self.room.process_DeleteEvent(delete_event)

        # and pass the PicksUpEvent on
        #
        kwargs["message"].event_list.append(event)

        return

    def process_DropsEvent(self, event, **kwargs):
        """Respawn the Entity to be dropped in Engine.room, delete it from Engine.rack and pass the PicksUpEvent on.
        """

        self.logger.debug("called")

        # Respawn the Entity to be dropped in Engine.room
        # Delete it from Engine.rack
        #
        # TODO: Fails when Entity not in rack. Contracts.
        #
        self.logger.debug("removing '{}' from Rack and respawning in Room".format(event.item_identifier))

        dropped_entity = self.rack.retrieve(event.item_identifier)

        spawn_event = fabula.SpawnEvent(dropped_entity, event.location)

        self.room.process_SpawnEvent(spawn_event)

        # and pass the DropsEvent on
        #
        kwargs["message"].event_list.append(event)

        return

    def process_ManipulatesEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_CanSpeakEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_AttemptFailedEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_PerceptionEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_SaysEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_ChangeStateEvent(self, event, **kwargs):
        """Let the Entity handle the Event. Then add the event to the message.
        """

        self.logger.debug("called")

        self.room.entity_dict[event.identifier].process_ChangeStateEvent(event)

        kwargs["message"].event_list.append(event)

        return

    def process_PassedEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_LookedAtEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_PickedUpEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_DroppedEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_SpawnEvent(self, event, **kwargs):
        """Let self.room process the event and pass it on.
        """

        self.logger.debug("spawning entity '%s', type %s, location %s"
                          % (event.entity.identifier,
                             event.entity.entity_type,
                             event.location))

        self.room.process_SpawnEvent(event)

        kwargs["message"].event_list.append(event)

        return

    def process_DeleteEvent(self, event, **kwargs):
        """Save the Entity to be deleted in Engine.rack,
           delete the it from Engine.room and pass the DeleteEvent on.
        """

        # TODO: very similar to PicksUpEvent

        self.logger.debug("called")

        # Save the Entity to be deleted in Engine.rack
        #
        deleted_entity = self.room.entity_dict[event.identifier]

        # Entities stored by Engine are owned by None
        #
        self.rack.store(deleted_entity, None)

        # Delete it from Engine.room
        #
        self.room.process_DeleteEvent(event)

        # and pass the PicksUpEvent on
        #
        kwargs["message"].event_list.append(event)

        return

    def process_EnterRoomEvent(self, event, **kwargs):
        """The default implementation simply forwards the Event.
           On the client side, an EnterRoomEvent means that the server is about
           to send a new map, respawn the player and send items and NPCs.
           On the server side, things may be a little more complicated. In a
           single player scenario the server might replace the current room or
           save it to be able to return to it later. In a multiplayer
           environment however the server has to set up another room to manage
           in parallel to the established rooms.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_RoomCompleteEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def process_ChangeMapElementEvent(self, event, **kwargs):
        """Let the fabula.Room instance in self.room process the Event
           and add it to message.
        """

        self.logger.debug("called")

        self.room.process_ChangeMapElementEvent(event)

        kwargs["message"].event_list.append(event)

        return

    def process_InitEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation adds the event to the message.
        """

        self.logger.debug("called")

        kwargs["message"].event_list.append(event)

        return

    def tile_is_walkable(self, target_identifier):
        """Auxiliary method which returns True if the tile exists in self.room and can be accessed by Entities.
        """

        if self.room is None:

            self.logger.debug("not walkable: room is None")

            return False

        elif target_identifier not in self.room.floor_plan.keys():

            self.logger.debug("{} not walkable: not in floor_plan".format(target_identifier))

            return False

        else:
            floor_plan_element = self.room.floor_plan[target_identifier]

            if floor_plan_element.tile.tile_type != fabula.FLOOR:

                self.logger.debug("{} not walkable: target tile_type != fabula.FLOOR".format(target_identifier))

                return False

            else:
                occupied = False

                for entity in floor_plan_element.entities:

                    if entity.entity_type == fabula.ITEM_BLOCK:

                        occupied = True

                if occupied:

                    self.logger.debug("{} not walkable: target occupied by fabula.ITEM_BLOCK".format(target_identifier))

                    return False

                else:

                    return True
