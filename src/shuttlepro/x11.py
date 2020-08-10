"""
"""

from Xlib.display import Display
from Xlib.ext import xinput

__all__ = [
    'X11EventDispatcher',
]


class X11EventDispatcher:
    """
    """
    __slots__ = ('display', 'device_id')

    def __init__(self, device_name):
        self.display = Display()
        self.device_id = None
        for device in self.display.xinput_query_device(xinput.AllDevices).devices:
            if device_name == device.name:
                self.device_id = device.deviceid
                break
        if not self.device_id:
            raise ValueError(f'No X11 device with the name {device_name} could be found!')
