"""Keyboard key pill widget with 3D effect."""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class KeyboardKey(Gtk.Label):
    """A single keyboard key rendered as a 3D pill."""

    def __init__(self, label: str):
        super().__init__()
        self.set_label(label)
        self.add_css_class("key")
        # Wider keys for modifiers
        if label in ("Super", "Ctrl", "Alt", "Shift", "Enter", "Space", "Bksp", "Tab"):
            self.add_css_class("key-wide")


class KeyCombo(Gtk.Box):
    """A horizontal row of KeyboardKey pills with + separators."""

    def __init__(self, keys: list[str]):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.add_css_class("key-combo")
        for i, key in enumerate(keys):
            if i > 0:
                sep = Gtk.Label(label="+")
                sep.add_css_class("key-separator")
                self.append(sep)
            self.append(KeyboardKey(key))
