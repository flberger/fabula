"""Fabula Event Processor Base Class

   Copyright 2010 Florian Berger <mail@florian-berger.de>
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

# Work started on 01. Oct 2009

import fabula

class EventProcessor:
    """This is the base class for all Fabula objects that process events.
    """

    # TODO: implement process_Event fallback

    def __init__(self):
        """Set up EventProcessor.event_dict
           which maps event classes to functions to be called for
           the respective event.
        """
        # I just love to use dicts to avoid endless
        # if... elif... clauses. :-)
        #
        self.event_dict = {fabula.TriesToMoveEvent :
                               self.process_TriesToMoveEvent,
                           fabula.TriesToLookAtEvent :
                               self.process_TriesToLookAtEvent,
                           fabula.TriesToPickUpEvent :
                               self.process_TriesToPickUpEvent,
                           fabula.TriesToDropEvent :
                               self.process_TriesToDropEvent,
                           fabula.TriesToManipulateEvent :
                               self.process_TriesToManipulateEvent,
                           fabula.TriesToTalkToEvent :
                               self.process_TriesToTalkToEvent,
                           fabula.MovesToEvent :
                               self.process_MovesToEvent,
                           fabula.PicksUpEvent :
                               self.process_PicksUpEvent,
                           fabula.DropsEvent :
                               self.process_DropsEvent,
                           fabula.ManipulatesEvent :
                               self.process_ManipulatesEvent,
                           fabula.CanSpeakEvent :
                               self.process_CanSpeakEvent,
                           fabula.AttemptFailedEvent :
                               self.process_AttemptFailedEvent,
                           fabula.PerceptionEvent :
                               self.process_PerceptionEvent,
                           fabula.SaysEvent :
                               self.process_SaysEvent,
                           fabula.ChangePropertyEvent :
                               self.process_ChangePropertyEvent,
                           fabula.PassedEvent :
                               self.process_PassedEvent,
                           fabula.LookedAtEvent :
                               self.process_LookedAtEvent,
                           fabula.PickedUpEvent :
                               self.process_PickedUpEvent,
                           fabula.DroppedEvent :
                               self.process_DroppedEvent,
                           fabula.SpawnEvent :
                               self.process_SpawnEvent,
                           fabula.DeleteEvent :
                               self.process_DeleteEvent,
                           fabula.EnterRoomEvent :
                               self.process_EnterRoomEvent,
                           fabula.RoomCompleteEvent :
                               self.process_RoomCompleteEvent,
                           fabula.ChangeMapElementEvent :
                               self.process_ChangeMapElementEvent,
                           fabula.InitEvent :
                               self.process_InitEvent,
                           fabula.ExitEvent :
                               self.process_ExitEvent,
                           fabula.ServerParametersEvent :
                               self.process_ServerParametersEvent,
                          }

    def __getstate__(self):
        """Return a copy of self.__dict__ with un-pickleable items removed to the pickle module.
        """
        dict = self.__dict__.copy()

        del dict["event_dict"]

        return dict

    def __setstate__(self, state_dict):
        """Update self.__dict__ with state_dict provided by the pickle module, then call __init__().
        """
        self.__dict__.update(state_dict)

        # Setup the un-pickleable event_dict
        #
        self.__init__()

    def process_TriesToMoveEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_TriesToLookAtEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_TriesToPickUpEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_TriesToDropEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_TriesToManipulateEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_TriesToTalkToEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_MovesToEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_PicksUpEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_DropsEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_ManipulatesEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_CanSpeakEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_AttemptFailedEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_PerceptionEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_SaysEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_ChangePropertyEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """

        # ChangeProperty is based on a concept by Alexander Marbach.

        pass

    def process_PassedEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_LookedAtEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_PickedUpEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_DroppedEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_SpawnEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_DeleteEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_EnterRoomEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_RoomCompleteEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_ChangeMapElementEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_InitEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_ExitEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass

    def process_ServerParametersEvent(self, event, **kwargs):
        """Process the Event.
           The default implementation does nothing.
        """
        pass
