"""
"""
import enum
import fnmatch
import pathlib
import re
from collections import namedtuple

from Xlib import Xatom
try:
    from ruamel import yaml
except ImportError:
    import yaml

from .base import flatten_mappings

__all__ = [
    'PredicateProperty',
    'PredicateMatch',
    'KeyModifier',
    'Predicate',
    'KeyCombo',
    'KeyMappings',
    'load_mappings_file',
]


class PredicateProperty(enum.Enum):
    """
    """
    ANY = 'any'
    """ """
    NAME = 'name'
    """ """
    COMMAND = 'command'
    """ """
    CLASS = 'class'
    """ """


class PredicateMatch(enum.Enum):
    """
    """
    EXACT = 'exact'
    """ """
    STARTSWITH = 'starts with'
    """ """
    ENDSWITH = 'ends with'
    """ """
    REGEX = 'regex'
    """ """
    GLOB = 'glob'
    """ """


class KeyModifier(enum.Enum):
    """
    """
    CTRL = 'ctrl'
    """ """
    SHIFT = 'shift'
    """ """
    ALT = 'alt'
    """ """
    MOD = 'mod'
    """ """


class Predicate(namedtuple('_PredicateBase', ('value', 'properties', 'match', 'case_sensitive'))):
    """
    """

    # pylint: disable=redefined-builtin
    def __new__(
        cls,
        *,
        value,
        properties=PredicateProperty.ANY,
        match=PredicateMatch.GLOB,
        case_sensitive=False
    ):
        if isinstance(match, str):
            match = PredicateMatch(match)
        if match == PredicateMatch.GLOB:
            value = fnmatch.translate(value)
            match = PredicateMatch.REGEX
        if match == PredicateMatch.REGEX:
            if case_sensitive:
                value = re.compile(value)
            else:
                value = re.compile(value, re.I)
        elif not case_sensitive:
            value = value.casefold()
        if not isinstance(properties, (tuple, list, set)):
            properties = (properties,)
        else:
            properties = list(properties)
        properties = tuple(PredicateProperty(p) for p in properties)
        if PredicateProperty.ANY in properties:
            properties = tuple(p for p in PredicateProperty if p != PredicateProperty.ANY)
        return super().__new__(
            cls,
            value=value,
            properties=properties,
            match=match,
            case_sensitive=case_sensitive,
        )

    def check_value(self, value):
        """
        """
        if not value:
            return False
        if self.match == PredicateMatch.REGEX:
            return self.value.fullmatch(value)
        value = value.casefold()
        if self.match == PredicateMatch.EXACT:
            return value == self.value
        if self.match == PredicateMatch.STARTSWITH:
            return value.startswith(self.value)
        if self.match == PredicateMatch.ENDSWITH:
            return value.endswith(self.value)
        raise ValueError()

    # pylint: disable=redefined-builtin
    def get_property_value(self, property, window):
        """
        """
        if property == PredicateProperty.NAME:
            return window.get_wm_name()
        if property == PredicateProperty.CLASS:
            cls = window.get_wm_class()
            if cls:
                return cls[1]
            return None
        if property == PredicateProperty.COMMAND:
            return window.get_full_text_property(Xatom.WM_COMMAND, Xatom.STRING)
        raise ValueError(f'Unknown predicate property match: {property}')

    def matches(self, window):
        """
        """
        for prop in self.properties:
            if self.check_value(self.get_property_value(prop, window)):
                return True
        return False


class KeyCombo(namedtuple('_KeyComboBase', ('key', 'modifiers'))):
    """
    """

    def __new__(cls, key_combo_def):
        key = None
        parts = ()
        if isinstance(key_combo_def, int):
            key_combo_def = str(key_combo_def)
        elif isinstance(key_combo_def, str):
            parts = key_combo_def.split('+')
            key = parts.pop(-1)
            if key and key.strip():
                key = key.strip()
        elif key_combo_def:
            raise ValueError(f'Invalid Key Combo: {key_combo_def}')
        return super().__new__(cls, key, tuple(KeyModifier(p.strip()) for p in parts))

    def __str__(self):
        if not self.key:
            return ''
        return ' + '.join((*(m._value_ for m in self.modifiers), self.key))

    def __repr__(self):
        return f'{type(self).__qualname__}({repr(str(self))})'


class KeyMappings(namedtuple('_KeyMappingsBase', ('predicate', 'mappings'))):
    """
    """

    def __new__(cls, predicate, mappings):
        if isinstance(predicate, dict):
            predicate = Predicate(**predicate)
        mappings = flatten_mappings(mappings)
        for k, v in mappings.items():
            if v is None:
                continue
            if isinstance(v, (str, int)):
                v = (v,)
            mappings[k] = tuple(KeyCombo(c) for c in v)
        return super().__new__(cls, predicate, mappings)

    def matches(self, window):
        """
        """
        return self.predicate.matches(window)

    def get_key_combos(self, mapping_id):
        """
        """
        return self.mappings.get(mapping_id, ())

    def __getitem__(self, key):
        return self.get_key_combos(key)


def load_mappings_file(file_or_folder_name):
    """
    """
    mappings = []
    if not isinstance(file_or_folder_name, pathlib.Path):
        file_or_folder_name = pathlib.Path(file_or_folder_name)
    if file_or_folder_name.exists():
        if file_or_folder_name.is_dir():
            for child in file_or_folder_name.iterdir():
                mappings += load_mappings_file(child)
        else:
            with open(file_or_folder_name) as f:
                mappings += [KeyMappings(**d) for d in yaml.safe_load_all(f)]
    return mappings
