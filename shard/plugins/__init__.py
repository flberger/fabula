"""Shard Engine Plugin Base Class
"""

# Work started on 30. Sep 2009

import shard           
import shard.eventprocessor

class Plugin(shard.eventprocessor.EventProcessor):
    """Base class for plugins to be used by a shard.core.Engine.

       Attributes:

       Plugin.logger
           The host's logger

       Plugin.message_for_host
           Shard Message to be returned by Plugin.process_message()

       Plugin.host
           The host of this plugin, an instance of shard.core.Engine
    """

    def __init__(self, logger):
        """Initialise the plugin.
           logger is an instance of logging.Logger.
        """

        shard.eventprocessor.EventProcessor.__init__(self)

        self.logger = logger

        self.message_for_host = shard.Message([])

    def process_message(self, message):
        """This is the main method of a plugin.

           It is called with an instance of shard.Message. This method does not
           run in a thread. It should process the message quickly and return
           another instance of shard.Message to be processed by the host and
           possibly to be sent to the remote host.

           The default implementation calls the respective functions for the
           Events in message and returns Plugin.message_for_host.
        """

        # Clear message for host
        #
        self.message_for_host = shard.Message([])

        if message.event_list:

            self.logger.debug("processing message {}".format(message.event_list))

            for event in message.event_list:

                # event_dict from EventProcessor base class
                #
                self.event_dict[event.__class__](event)

        return self.message_for_host

    def process_TriesToMoveEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_TriesToLookAtEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_TriesToPickUpEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_TriesToDropEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_TriesToManipulateEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_TriesToTalkToEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_MovesToEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_PicksUpEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_DropsEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_ManipulatesEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_CanSpeakEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_AttemptFailedEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_PerceptionEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_SaysEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_ChangeStateEvent(self, event, **kwargs):
        """Return the Event to the host.
        """
        # ChangeState is based on a concept by Alexander Marbach.

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_PassedEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_LookedAtEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_PickedUpEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_DroppedEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_SpawnEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_DeleteEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_EnterRoomEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_RoomCompleteEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_ChangeMapElementEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return

    def process_InitEvent(self, event, **kwargs):
        """Return the Event to the host.
        """

        self.logger.debug("returning Event to host")
        self.message_for_host.event_list.append(event)
        return
