"""Layer-shell overlay window."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gdk, GLib, Gtk, Gtk4LayerShell

from ..parsers.base import Column
from .keybinds import KeybindsGrid


class OverlayWindow(Gtk.Window):
    """Full-screen layer-shell overlay displaying keybindings."""

    def __init__(self, app: Gtk.Application, columns: list[Column]):
        super().__init__(application=app)
        self._columns = columns
        self._setup_layer_shell()
        self._setup_placeholder()
        self._setup_input()

    def _setup_layer_shell(self):
        Gtk4LayerShell.init_for_window(self)
        Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.OVERLAY)
        Gtk4LayerShell.set_keyboard_mode(
            self, Gtk4LayerShell.KeyboardMode.EXCLUSIVE
        )
        for edge in (
            Gtk4LayerShell.Edge.TOP,
            Gtk4LayerShell.Edge.BOTTOM,
            Gtk4LayerShell.Edge.LEFT,
            Gtk4LayerShell.Edge.RIGHT,
        ):
            Gtk4LayerShell.set_anchor(self, edge, True)
        Gtk4LayerShell.set_namespace(self, "cheatbind")

    def _setup_placeholder(self):
        """Show an empty overlay immediately, populate content on next frame."""
        self.add_css_class("overlay")
        self._container = Gtk.Box()
        self._container.set_hexpand(True)
        self._container.set_vexpand(True)
        self.set_child(self._container)

        # Defer heavy widget creation to after the window is mapped
        self.connect("map", self._on_mapped)

    def _on_mapped(self, _widget):
        GLib.idle_add(self._build_ui)

    def _build_ui(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        vbox.set_margin_top(40)
        vbox.set_margin_bottom(40)
        vbox.set_margin_start(48)
        vbox.set_margin_end(48)
        vbox.set_halign(Gtk.Align.FILL)
        vbox.set_valign(Gtk.Align.START)

        title = Gtk.Label(label="Keyboard Shortcuts")
        title.add_css_class("overlay-title")
        vbox.append(title)

        subtitle = Gtk.Label(label="Press Esc or click anywhere to close")
        subtitle.add_css_class("overlay-subtitle")
        vbox.append(subtitle)

        grid = KeybindsGrid(self._columns)
        vbox.append(grid)

        scroll.set_child(vbox)
        self.set_child(scroll)

        self._columns = None
        return GLib.SOURCE_REMOVE

    def _setup_input(self):
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key)
        self.add_controller(key_ctrl)

        click_ctrl = Gtk.GestureClick()
        click_ctrl.connect("pressed", self._on_click)
        self.add_controller(click_ctrl)

    def _on_key(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.get_application().quit()
            return True
        return False

    def _on_click(self, gesture, n_press, x, y):
        self.get_application().quit()
