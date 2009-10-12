"""Shard Core Engine Base Class

   Based on former implementations of
   the ClientControlEngine
"""

# Work started on 30. Sep 2009

import shard
import shard.eventprocessor

class CoreEngine(shard.eventprocessor.EventProcessor):
    """This is the common base class for Shard
       server and client core engines. They define
       a main method run() and some auxiliary
       methods. Most likely you want to override
       all of them when subclassing CoreEngine,
       so the use of this class is providing
       a structure for CoreEngines.
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

    def setup_core_engine(self, interface_instance, plugin_instance, logger):
        """CoreEngines need an instance of a subclass
           of shard.interfaces.Interface to communicate
           with the remote host. Most CoreEngines will
           deploy a plugin engine to control or present
           the game. Finally, logger is an instance of
           logging.Logger for, eh, logging purposes. ;-)
        """

        # Attach logger
        #
        self.logger = logger

        self.interface = interface_instance

        self.plugin = plugin_instance

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
        
        # self.entity_dict keeps track of all active Entites.
        # It uses the identifier as a key, assuming that it
        # is unique.
        #
        self.entity_dict = {}

        # self.map is an attempt of an efficient storage of
        # an arbitrary two-dimensional map. To save space, 
        # only explicitly defined elements are stored. This
        # is done in a dict whose keys are tuples. Access the
        # elemty using self.map[(x, y)]. The upper left element
        # is self.map[(0, 0)].
        #
        self.map = {}

        self.logger.info("complete")

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

    def process_TriesToLookAtEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_TriesToPickUpEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_TriesToDropEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_TriesToManipulateEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_TriesToTalkToEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_MovesToEvent(self, event, message):
        """Notify the Entity and add
           the event to the message.
        """

        self.logger.debug("entity location before call: "
                          + str(self.entity_dict[event.identifier].location))

        self.entity_dict[event.identifier].process_MovesToEvent(event)

        self.logger.debug("entity location after call: "
                          + str(self.entity_dict[event.identifier].location))

        message.event_list.append(event)

    def process_PicksUpEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_DropsEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_CanSpeakEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_AttemptFailedEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_PerceptionEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_SaysEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_ChangeStateEvent(self, event, message):
        """The new state
           is just passed on to the Entity."""

        self.entity_dict[event.identifier].change_state(event.state)

    def process_ChangeStateEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_PassedEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_LookedAtEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_PickedUpEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_DroppedEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_SpawnEvent(self, event, message):
        """If not already present, add the Entity given to
           the entity_dict and pass the SpawnEvent on.
        """

        if event.entity.identifier in self.entity_dict:
            self.logger.debug("entity already in entity_dict: %s" % event.entity.identifier)

        else:
            self.logger.debug("spawning entity: %s" % event.entity.identifier)

            self.entity_dict[event.entity.identifier] = event.entity

            message.event_list.append(event)

    def process_DeleteEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_EnterRoomEvent(self, event, message):
        """An EnterRoomEvent means the server is
           about to send a new map, respawn the
           player and send items and NPCs. So
           this method empties all data 
           structures and passes the event on.
        """

        self.logger.debug("called")

        # All Entities in this room have to be sent.
        # No use keeping old ones around, expecially with old
        # locations.
        #
        self.entity_dict = {}

        # Awaiting a new map!
        #
        self.map = {}

        message.event_list.append(event)

    def process_RoomCompleteEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)

    def process_ChangeMapElementEvent(self, event, message):
        """Store the tile given in self.map, 
           a dict of dicts with x- and
           y-coordinates as keys. Also save
           it in the message.
        """

        self.logger.debug("called")

        # possibly overwrite existing tile
        #
        self.map[event.location] = event.tile

        message.event_list.append(event)

    def process_InitEvent(self, event, message):
        """Process the Event.
           The default implementation adds
           the event to the message.
        """

        self.logger.debug("called")

        message.event_list.append(event)
