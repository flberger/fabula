"""Shard Event Processor Base Class
"""

# Work started on 01. Oct 2009

import shard

class EventProcessor:
    """This is the base class for all
       Shard objects that process events.
    """

    def __init__(self):
        """You can override this, but make sure
           to call self.setup_eventprocessor()
           like the default implementation does.
        """
        self.setup_eventprocessor()

    def setup_eventprocessor(self):
        """Set up EventProcessor.event_dict which maps
           event classes to functions to be called for
           the respective event.
        """
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
                           shard.ChangeStateEvent :
                               self.process_ChangeStateEvent,
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
                          }

    def process_TriesToMoveEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_TriesToLookAtEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_TriesToPickUpEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_TriesToDropEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_TriesToManipulateEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_TriesToTalkToEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_MovesToEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_PicksUpEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_DropsEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_CanSpeakEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_AttemptFailedEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_PerceptionEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_SaysEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_ChangeStateEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """

        # ChangeState is based on a concept by Alexander Marbach.

        pass

    def process_PassedEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_LookedAtEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_PickedUpEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_DroppedEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_SpawnEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_DeleteEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_EnterRoomEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_RoomCompleteEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_ChangeMapElementEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_InitEvent(self, event):
        """Process the Event.
           The default implementation does nothing.
        """
        pass
