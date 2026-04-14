"""Abstract base class for compositor config parsers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Keybind:
    """A keybinding with one or more key combos and a description."""

    keys: list[str]  # e.g. ["Mod", "Shift", "Left"]
    description: str
    action: str = ""
    alt_keys: list[list[str]] = field(default_factory=list)  # alternative combos


@dataclass
class Section:
    """A group of keybindings under a category title."""

    title: str
    binds: list[Keybind] = field(default_factory=list)


@dataclass
class Column:
    """A column of sections in the overlay layout."""

    sections: list[Section] = field(default_factory=list)


class Parser(ABC):
    """Abstract parser for compositor keybinding configs."""

    @abstractmethod
    def parse(self, config_path: Path) -> list[Column]:
        """Parse a config file and return columns of sections with keybindings."""

    @staticmethod
    def prettify_key(key: str) -> str:
        """Convert an XKB key name to a human-friendly label."""
        mapping = {
            "Mod": "Super",
            "Super": "Super",
            "Ctrl": "Ctrl",
            "Alt": "Alt",
            "Shift": "Shift",
            "Return": "Enter",
            "Escape": "Esc",
            "Page_Up": "PgUp",
            "Page_Down": "PgDn",
            "Home": "Home",
            "End": "End",
            "Delete": "Del",
            "BackSpace": "Bksp",
            "Tab": "Tab",
            "Print": "PrtSc",
            "Space": "Space",
            "Equal": "=",
            "Parenright": ")",
            "dead_circumflex": "^",
            "dollar": "$",
            "Comma": ",",
            "semicolon": ";",
            "Semicolon": ";",
            "Slash": "/",
        }
        if key.startswith("XF86"):
            short = key.removeprefix("XF86")
            # Split CamelCase
            result = []
            for char in short:
                if char.isupper() and result:
                    result.append(" ")
                result.append(char)
            return "".join(result)
        return mapping.get(key, key)
