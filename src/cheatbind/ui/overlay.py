"""Layer-shell overlay window."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gdk, GLib, Gtk, Gtk4LayerShell

from ..parsers.base import Column, Keybind
from .keybinds import KeybindsGrid, SectionWidget


class OverlayWindow(Gtk.Window):
    """Full-screen layer-shell overlay displaying keybindings."""

    def __init__(
        self, app: Gtk.Application, columns: list[Column], compositor: str
    ):
        super().__init__(application=app)
        self._columns = columns
        self._compositor = compositor
        self._all_bind_rows: list[tuple[Gtk.Widget, Keybind]] = []
        self._search_label = None
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

        title_text = f"{self._compositor.capitalize()} — Keyboard Shortcuts"
        title = Gtk.Label(label=title_text)
        title.add_css_class("overlay-title")
        vbox.append(title)

        # Search hint + live filter display
        self._search_label = Gtk.Label(
            label="Press Esc or click to close — Type to search"
        )
        self._search_label.add_css_class("overlay-subtitle")
        vbox.append(self._search_label)

        grid = KeybindsGrid(self._columns)
        vbox.append(grid)

        # Collect all bind rows for search filtering
        self._collect_bind_rows(grid)

        scroll.set_child(vbox)
        self.set_child(scroll)

        self._columns = None
        return GLib.SOURCE_REMOVE

    def _collect_bind_rows(self, grid: KeybindsGrid):
        """Walk the widget tree to collect (row_widget, keybind) pairs."""
        for col_widget in _iter_children(grid):
            for section_widget in _iter_children(col_widget):
                if not isinstance(section_widget, SectionWidget):
                    continue
                for bind, row in zip(
                    section_widget.section.binds,
                    section_widget.bind_rows,
                ):
                    self._all_bind_rows.append((row, bind))

    def _setup_input(self):
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key)
        self.add_controller(key_ctrl)

        click_ctrl = Gtk.GestureClick()
        click_ctrl.connect("pressed", self._on_click)
        self.add_controller(click_ctrl)

        self._search_text = ""

    def _on_key(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            if self._search_text:
                self._search_text = ""
                self._apply_filter()
                return True
            self.get_application().quit()
            return True

        if keyval == Gdk.KEY_BackSpace:
            if self._search_text:
                self._search_text = self._search_text[:-1]
                self._apply_filter()
            return True

        char = Gdk.keyval_to_unicode(keyval)
        if char and chr(char).isprintable():
            self._search_text += chr(char).lower()
            self._apply_filter()
            return True

        return False

    def _apply_filter(self):
        """Show/hide bind rows based on search text."""
        query = self._search_text

        if self._search_label:
            if query:
                self._search_label.set_text(f"Search: {query}")
            else:
                self._search_label.set_text(
                    "Press Esc or click to close — Type to search"
                )

        for row, bind in self._all_bind_rows:
            if not query:
                row.set_visible(True)
                continue
            searchable = (
                bind.description.lower()
                + " "
                + " ".join(bind.keys).lower()
                + " "
                + bind.action.lower()
            )
            row.set_visible(query in searchable)

    def _on_click(self, gesture, n_press, x, y):
        self.get_application().quit()


def _iter_children(widget):
    """Iterate over direct children of a GTK4 widget."""
    child = widget.get_first_child()
    while child:
        yield child
        child = child.get_next_sibling()
