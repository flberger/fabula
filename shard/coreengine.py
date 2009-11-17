"""Shard Core Engine Base Class

   Based on former implementations of
   the ClientControlEngine
"""

# Work started on 30. Sep 2009

import shard
import shard.eventprocessor

class CoreEngine(shard.eventprocessor.EventProcessor):
    """Common base class for Shard server and client core engines.
       Most likely you will want to override all of the methods
       when subclassing CoreEngine, so the use of this class is
       providing a structure for CoreEngines.

       Attributes:

       CoreEngine.logger
       CoreEngine.interface
       CoreEngine.plugin
       CoreEngine.message_for_plugin
       CoreEngine.message_for_remote
       CoreEngine.room
       CoreEngine.rack
    """

    def __init__(self, interface_instance, plugin_instance, logger):
        """When subclassing CoreEngine you will very
           likely want to write your own __init__()
           method. That's fine, but be sure to call
           the setup_core_engine() method of this class with the
           appropriate arguments as done by the
           default implementation.
        """

        # First setup base class
        #
        self.setup_eventprocessor()

        self.setup_core_engine(interface_instance,
                               plugin_instance,
                               logger)

        return

    def setup_core_engine(self, interface_instance, plugin_instance, logger):
        """Set up CoreEngine attributes.

           Arguments:

           interface_instance
               An instance of a subclass of
               shard.interfaces.Interface to communicate
               with the remote host.

           plugin_instance
               Most CoreEngines will deploy a plugin
               engine to control or present the game.

           logger
               An instance of logging.Logger.
        """

        # Attach logger
        #
        self.logger = logger

        self.interface = interface_instance

        self.plugin = plugin_instance

        # Attach reference to this CoreEngine
        # to the Plugin.
        #
        self.plugin.host = self

        # The CoreEngine examines the events of a received
        # Message and applies them. Events for special
        # consideration for the PluginEngine are collected
        # in a Message for the PluginEngine.
        # The CoreEngine has to empty the Message once 
        # the PluginEngine has processed all Events.
        #
        self.message_for_plugin = shard.Message([])

        # In self.message_for_remote we collect events to be
        # sent to the remote host in each loop.
        #
        self.message_for_remote = shard.Message([])
        
        # self.room keeps track of the map and active Entites.
        #
        self.room = shard.Room()

        # self.rack serves as a storage for deleted Entities
        # because there may be the need to respawn them.
        #
        self.rack = shard.Rack()

        self.logger.info("complete")

        return

    def run(self):
        """This is the main loop of a CoreEngine.
           Put all the business logic here. This
           is a blocking method which should call
           all the process methods to process events.
        """

        self.logger.info("starting")

        # You will probably want to run until the
        # plugin engine decides that the game is
        # over.
        #
        while not self.plugin.exit_requested:
            pass

        # exit has been requested
        
        self.logger.info("exit requested from "
              + "PluginEngine, shutting down interface...")

        # stop the Interface thread
        #
        self.interface.shutdown()

        self.logger.info("shutdown confirmed.")

        # TODO: possibly exit cleanly from the PluginEngine here

        return

    def process_TriesToMoveEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_TriesToLookAtEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_TriesToPickUpEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_TriesToDropEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_TriesToManipulateEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_TriesToTalkToEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_MovesToEvent(self, event, message):
        """Let self.room process the event and
           pass it on.
        """

        self.logger.debug("%s location before: %s "
                          % (event.identifier,
                             self.room.entity_locations[event.identifier]))

        self.room.process_MovesToEvent(event)

        self.logger.debug("%s location after: %s "
                          % (event.identifier,
                             self.room.entity_locations[event.identifier]))

        message.event_list.append(event)

        return

    def process_PicksUpEvent(self, event, message):
        """Save the Entity to be picked up in CoreEngine.rack,
           delete the it from CoreEngine.room and pass the
           PicksUpEvent on.
        """

        self.logger.debug("called")

        # Save the Entity to be picked up in CoreEngine.rack
        #
        picked_entity = self.room.entity_dict[event.item_identifier]

        self.rack.store(picked_entity, event.identifier)

        # Delete it from CoreEngine.room
        #
        # TODO: Why not pass the PicksUpEvent to the room and let it handle an according removal?
        #
        delete_event = shard.DeleteEvent(event.item_identifier)

        self.room.process_DeleteEvent(delete_event)

        # and pass the PicksUpEvent on
        #
        message.event_list.append(event)

        return

    def process_DropsEvent(self, event, message):
        """Respawn the Entity to be dropped in CoreEngine.room,
           delete it from CoreEngine.rack
           and pass the PicksUpEvent on.
        """

        self.logger.debug("called")

        # Respawn the Entity to be dropped in CoreEngine.room
        # Delete it from CoreEngine.rack
        #
        # TODO: Fails when Entity not in rack. Contracts.
        #
        dropped_entity = self.rack.retrieve(event.item_identifier)

        spawn_event = shard.SpawnEvent(dropped_entity, event.location)

        self.room.process_SpawnEvent(spawn_event)

        # and pass the PicksUpEvent on
        #
        message.event_list.append(event)

        return

    def process_CanSpeakEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_AttemptFailedEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_PerceptionEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_SaysEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_ChangeStateEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        # A CoreEngine should not talk to the Entiy
        # directly - rather, the Plugin should do.
        #
        message.event_list.append(event)

        return

    def process_PassedEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_LookedAtEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_PickedUpEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_DroppedEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_SpawnEvent(self, event, message):
        """Let self.room process the event and
           pass it on.
        """

        self.logger.debug("spawning entity '%s', type %s, location %s"
                          % (event.entity.identifier,
                             event.entity.entity_type,
                             event.location))

        self.room.process_SpawnEvent(event)

        message.event_list.append(event)

        return

    def process_DeleteEvent(self, event, message):
        """Let self.room process the event and
           pass it on.
        """

        self.logger.debug("called")

        self.room.process_DeleteEvent(event)

        message.event_list.append(event)

        return

    def process_EnterRoomEvent(self, event, message):
        """On the client side, an EnterRoomEvent
           means that the server is about to send
           a new map, respawn the player and send
           items and NPCs.
           On the server side, things may be a little
           more complicated. In a single player
           scenario the server might replace the
           current room or save it to be able to
           return to it later. In a multiplayer
           environment however the server has
           to set up another room to manage in
           parallel to the established rooms.
           The default implementation simply
           forwards the Event.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_RoomCompleteEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return

    def process_ChangeMapElementEvent(self, event, message):
        """Let the shard.Room instance in
           self.room process the Event and
           add it to message.
        """

        self.logger.debug("called")

        self.room.process_ChangeMapElementEvent(event)

        message.event_list.append(event)

        return

    def process_InitEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

        return
