"""Shard Core Engine Base Class

   Work started on 30. Sep 2009
   Based on a former implementations of
   the ClientControlEngine
"""

import shard

class CoreEngine:
    """This is the common base class for Shard
       server and client core engines. They define
       a main method run() and some auxiliary
       methods. Most likely you want to override
       all of them when subclassing CoreEngine,
       so the use of this class is providing
       a structure for CoreEngines.
    """

    def __init__(self, interface_instance, plugin_engine_instance, logger):
        """When subclassing CoreEngine you will very
           likely want to write your own __init__()
           method. That's fine, but be sure to call
           the setup() method of this class with the
           appropriate arguments as done by the
           default implementation.
        """

        self.setup(interface_instance,
                   plugin_engine_instance,
                   logger)

    def setup(self, interface_instance, plugin_engine_instance, logger):
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

        self.plugin_engine = plugin_engine_instance

        # A dictionary that maps event classes to functions 
        # to be called for the respective event.
        # I just love to use dicts to avoid endless
        # if... elif... clauses. :-)
        #
        self.event_dict = {shard.TriesToMoveEvent :
                               self.process_TriesToMoveEvent,
                           shard.TriesToLookAtEvent :
                               self.process_TriesToLookAtEvent,
                           shard.TriesToPickUpEvent :
                               self.process_TriesToPickUpEvent,
                           shard.TriesToDropEvent :
                               self.process_TriesToDropEvent,
                           shard.TriesToManipulateEvent :
                               self.process_TriesToManipulateEvent,
                           shard.TriesToTalkToEvent :
                               self.process_TriesToTalkToEvent,
                           shard.MovesToEvent :
                               self.process_MovesToEvent,
                           shard.PicksUpEvent :
                               self.process_PicksUpEvent,
                           shard.DropsEvent :
                               self.process_DropsEvent,
                           shard.CanSpeakEvent :
                               self.process_CanSpeakEvent,
                           shard.AttemptFailedEvent :
                               self.process_AttemptFailedEvent,
                           shard.PerceptionEvent :
                               self.process_PerceptionEvent,
                           shard.SaysEvent :
                               self.process_SaysEvent,
                           shard.CustomEntityEvent :
                               self.process_CustomEntityEvent,
                           shard.PassedEvent :
                               self.process_PassedEvent,
                           shard.LookedAtEvent :
                               self.process_LookedAtEvent,
                           shard.PickedUpEvent :
                               self.process_PickedUpEvent,
                           shard.DroppedEvent :
                               self.process_DroppedEvent,
                           shard.SpawnEvent :
                               self.process_SpawnEvent,
                           shard.DeleteEvent :
                               self.process_DeleteEvent,
                           shard.EnterRoomEvent :
                               self.process_EnterRoomEvent,
                           shard.RoomCompleteEvent :
                               self.process_RoomCompleteEvent,
                           shard.ChangeMapElementEvent :
                               self.process_ChangeMapElementEvent,
                           shard.InitEvent :
                               self.process_InitEvent,
                           shard.MessageAppliedEvent :
                               self.process_MessageAppliedEvent
                          }

        # The CoreEngine examines the events of a received
        # Message and applies them. Events for special
        # consideration for the PluginEngine are collected
        # in a Message for the PluginEngine.
        # The CoreEngine has to empty the Message once 
        # the PluginEngine has processed all Events.
        #
        self.plugin_engine_message = shard.Message([])

        # In self.message_for_remote we collect events to be
        # sent to the remote host in each loop.
        #
        self.message_for_remote = shard.Message([])
        
        self.logger.info("complete")

    def run(self):
        """This is the main loop of a CoreEngine. Put all
           the business logic here. This is a blocking method
           which calls all the process methods to process events.
        """

        self.logger.info("starting")

        # You will probably want to run until the
        # plugin engine decides that the game is
        # over.
        #
        while not self.plugin_engine.exit_requested:
            pass

        # exit has been requested
        
        self.logger.info("exit requested from "
              + "PluginiEngine, shutting down interface...")

        # stop the Interface thread
        #
        self.interface.shutdown()

        self.logger.info("shutdown confirmed.")

        # TODO: possibly exit cleanly from the PluginEngine here

        return

    def process_TriesToMoveEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_TriesToLookAtEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_TriesToPickUpEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_TriesToDropEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_TriesToManipulateEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_TriesToTalkToEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_MovesToEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_PicksUpEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_DropsEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_CanSpeakEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_AttemptFailedEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_PerceptionEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_SaysEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_CustomEntityEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_PassedEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_LookedAtEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_PickedUpEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_DroppedEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_SpawnEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_DeleteEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_EnterRoomEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_RoomCompleteEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_ChangeMapElementEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_InitEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)

    def process_MessageAppliedEvent(self, event):
        """Process the Event.
           The default implementation adds
           the event to the message for
           the plugin engine.
        """

        self.plugin_engine_message.event_list.append(event)
