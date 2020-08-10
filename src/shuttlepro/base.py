"""
"""
import enum
import errno
import os
from collections import namedtuple

import evdev

__all__ = [
    'DEV_BUTTON_IDS',
    'MAPPING_IDS',
    'ButtonState',
    'Direction',
    'find_shuttle_device',
    'InputKeymapEntry',
    'get_mapping_id_for_button',
]


def __get_ids():
    _Buttons = namedtuple('_Buttons', ('top', 'bottom'))
    _ButtonRows = namedtuple('_ButtonRows', ('upper', 'lower'))
    _Dial = namedtuple('_Dial', ('left', 'right'))
    _MappingIds = namedtuple('_MappingIds', ('buttons', 'jog', 'shuttle'))
    button_ids = _Buttons(
        top=_ButtonRows(
            upper=('BTN_0', 'BTN_2', 'BTN_3', 'BTN_4'),
            lower=('BTN_5', 'BTN_6', 'BTN_7', 'BTN_8', 'BTN_9'),
        ),
        bottom=_ButtonRows(
            upper=('BTN_10', 'BTN_11'),
            lower=('BTN_12', 'BTN_13'),
        ),
    )
    mapping_ids = _MappingIds(
        buttons=_Buttons(
            top=_ButtonRows(
                upper=tuple(f'top-upper-{i}' for i in range(4)),
                lower=tuple(f'top-lower-{i}' for i in range(5)),
            ),
            bottom=_ButtonRows(
                upper=tuple(f'bottom-upper-{i}' for i in range(2)),
                lower=tuple(f'bottom-lower-{i}' for i in range(2)),
            ),
        ),
        jog=_Dial(left='jog-left', right='jog-right'),
        shuttle=_Dial(
            left=tuple(f'shuttle-left-{i}' for i in range(10)),
            right=tuple(f'shuttle-right-{i}' for i in range(10)),
        ),
    )
    return button_ids, mapping_ids


DEV_BUTTON_IDS, MAPPING_IDS = __get_ids()


class ButtonState(enum.Enum):
    """
    """
    UP = evdev.KeyEvent.key_up
    """ """
    DOWN = evdev.KeyEvent.key_down
    """ """
    HOLD = evdev.KeyEvent.key_hold
    """ """


class Direction(enum.Enum):
    """
    """
    LEFT = enum.auto()
    """ """
    CENTER = enum.auto()
    """ """
    RIGHT = enum.auto()
    """ """


def find_shuttle_device():
    """
    """
    for device_path in (f'/dev/input/{p}' for p in os.listdir('/dev/input')):
        if not os.access(device_path, os.R_OK) or os.path.isdir(device_path):
            continue
        try:
            device = evdev.InputDevice(device_path)
        except OSError as e:
            if e.errno == errno.ENOTTY:
                continue
            raise
        if not device.name:
            continue
        name = device.name.lower()
        if 'contour' in name and 'shuttle' in name and 'pro' in name:
            return device
    return None


def flatten_mappings(mappings):
    """
    """
    new_mappings = {}

    def _process_side(side):
        if side not in mappings['buttons']:
            return
        side_ids = getattr(MAPPING_IDS.buttons, side)
        side_mappings = mappings['buttons'][side]
        for row, row_mappings in side_mappings.items():
            row_ids = getattr(side_ids, row)
            new_mappings.update(dict(zip(row_ids, row_mappings)))

    if 'buttons' in mappings:
        _process_side('top')
        _process_side('bottom')
    if 'jog' in mappings:
        new_mappings[MAPPING_IDS.jog.left] = mappings['jog'].get('left')
        new_mappings[MAPPING_IDS.jog.right] = mappings['jog'].get('right')
    if 'shuttle' in mappings:
        if 'left' in mappings['shuttle']:
            new_mappings.update(dict(zip(MAPPING_IDS.shuttle.left, mappings['shuttle']['left'])))
        if 'right' in mappings['shuttle']:
            new_mappings.update(dict(zip(MAPPING_IDS.shuttle.right, mappings['shuttle']['right'])))
    return new_mappings


def get_mapping_id_for_button(button_id):
    """
    """

    def _process_side(side):
        if button_id in side.upper:
            return 'upper', side.upper.index(button_id)
        if button_id in side.lower:
            return 'lower', side.lower.index(button_id)
        return None, None

    row, idx = _process_side(DEV_BUTTON_IDS.top)
    if row:
        side = 'top'
    else:
        row, idx = _process_side(DEV_BUTTON_IDS.bottom)
        if row:
            side = 'bottom'
        else:
            raise ValueError(f'Unknown button: {button_id}')
    return getattr(getattr(MAPPING_IDS.buttons, side), row)[idx]


InputKeymapEntry = namedtuple('InputKeymapEntry', ('flags', 'len', 'index', 'keycode', 'scancode'))
