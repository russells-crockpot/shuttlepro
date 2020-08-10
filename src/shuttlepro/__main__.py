#!/bin/python3
"""
"""
import sys

import click
import evdev

from .base import find_shuttle_device
from .config import load_mappings_file
from .dev_events import EventListener

# Some of the buttons have values outside of what evdev defines, so we need to add them
for i, code in enumerate(range(266, 269)):
    evdev.ecodes.keys.setdefault(code, f'BTN_1{i}')


def find_mappings_file():
    """
    """
    return 'configs'


@click.command()
@click.option(
    '-m',
    '--mappings',
    'mappings_file',
    default=None,
    help='The file or folder with the key map(s).'
)
@click.argument('device', default=None, required=False)
def _cli(*, device, mappings_file):
    if not mappings_file:
        mappings_file = find_mappings_file()
    mappings = load_mappings_file(mappings_file)  # pylint: disable=unused-variable
    if not device:
        device = find_shuttle_device()
        if not device:
            print('ShuttlePro device could not be determined.', file=sys.stderr)
            sys.exit(1)
    if isinstance(device, str):
        device = evdev.InputDevice(device)
    for event in EventListener(device):
        if isinstance(event, evdev.SynEvent):
            print()
            continue
        print(repr(event))
        # lw.dumpobj(event, protected=True, dunder=True)
        # exit()


def _raw():
    with open(sys.argv[1], 'rb') as dev:
        while True:
            event = dev.read(24)
            print(event.hex())


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter, missing-kwoa
    _cli()
    # _raw()
    # code_names = (sorted(n for n in dir(evdev.ecodes) if n.startswith('EV_')))
    # print('\n'.join(f'{n}: {getattr(evdev.ecodes, n)}' for n in code_names))
    # pp(evdev.ecodes.REL)
