"""
"""
from collections import namedtuple
import evdev

from .base import ButtonState, get_mapping_id_for_button

__all__ = [
    'EventListener',
    'BaseEvent',
    'JogEvent',
    'ShuttleEvent',
    'ButtonEvent',
    'DeviceEvent',
]


class DeviceEvent(namedtuple('_DeviceEventBase', ('base_event', 'device', 'device_state'))):
    """
    """

    def __new__(cls, device, event):
        return super().__new__(cls, event, device, tuple(device.active_keys(verbose=True)))

    def __getattr__(self, name):
        return getattr(self.base_event, name)


class EventListener:
    """
    """
    __slots__ = ('_device',)

    def __init__(self, device):
        self._device = device

    def __iter__(self):
        event_batch = []
        for event in self._device.read_loop():
            event = evdev.util.categorize(event)
            if isinstance(event, evdev.SynEvent):
                yield tuple(event_batch)
                event_batch = []
            else:
                event_batch.append(DeviceEvent(self._device, event))


class BaseEvent:
    """
    """
    __slots__ = ('dev_events', 'device', 'device_state', 'mapping_id')

    def __init__(self, device, events):
        self.device = device
        self.device_state = None
        self.mapping_id = None
        self.dev_events = tuple(events)

    @classmethod
    # pylint: disable=self-cls-assignment
    def from_dev_events(cls, device, events):
        """
        """
        if len(events) == 3:
            return NormalButtonEvent(device, events)
        if len(events) == 2:
            return ShuttleEvent(device, events)
        if len(events) == 1:
            event = events[0]
            if isinstance(event, evdev.RelEvent):
                pass
        raise TypeError('Could not determine event type!')


class JogEvent(BaseEvent):
    """
    """
    __slots__ = ('direction', 'value')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #TODO
        #pylint: disable=unused-variable
        for event in self.dev_events:
            pass


class ShuttleEvent(BaseEvent):
    """
    """
    __slots__ = ('direction', 'value')


class ButtonEvent(BaseEvent):
    """
    """
    __slots__ = ('button_state',)


class MiddleButtonEvent(ButtonEvent):
    """Middle buttons don't work and I don't think they ever will. But just in case, this is a place
    holder.
    """
    __slots__ = ()


class NormalButtonEvent(ButtonEvent):
    """
    """
    __slots__ = ('key_dev_event',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for event in self.dev_events:
            if isinstance(event.base_event, evdev.KeyEvent):
                self.key_dev_event = event
                break
        self.button_state = ButtonState(self.key_dev_event.keystate)
        self.mapping_id = get_mapping_id_for_button(self.key_dev_event.keycode)
