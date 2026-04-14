"""Keybindings grid layout with sections and columns."""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from ..parsers.base import Column, Section
from .keyboard_key import KeyCombo


class SectionWidget(Gtk.Box):
    """A section: title + list of keybindings."""

    def __init__(self, section: Section):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add_css_class("section")
        self.section = section
        self.bind_rows: list[Gtk.Widget] = []

        title = Gtk.Label(label=section.title)
        title.add_css_class("section-title")
        title.set_halign(Gtk.Align.START)
        self.append(title)

        for bind in section.binds:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.add_css_class("bind-row")

            combos_box = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, spacing=6
            )
            combos_box.add_css_class("key-combos")
            combos_box.set_halign(Gtk.Align.START)

            combos_box.append(KeyCombo(bind.keys))
            for alt in bind.alt_keys:
                sep = Gtk.Label(label="/")
                sep.add_css_class("key-alt-separator")
                combos_box.append(sep)
                combos_box.append(KeyCombo(alt))

            row.append(combos_box)

            desc = Gtk.Label(label=bind.description)
            desc.add_css_class("bind-description")
            desc.set_halign(Gtk.Align.START)
            desc.set_hexpand(True)
            row.append(desc)

            self.append(row)
            self.bind_rows.append(row)


class ColumnWidget(Gtk.Box):
    """A column of sections."""

    def __init__(self, column: Column):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.add_css_class("column")
        self.set_hexpand(True)
        self.set_valign(Gtk.Align.START)

        for section in column.sections:
            self.append(SectionWidget(section))


class KeybindsGrid(Gtk.Box):
    """The full multi-column keybindings layout."""

    def __init__(self, columns: list[Column]):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=32)
        self.add_css_class("keybinds-grid")
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_hexpand(True)
        self.set_vexpand(True)

        for col in columns:
            self.append(ColumnWidget(col))
