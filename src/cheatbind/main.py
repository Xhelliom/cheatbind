"""Cheatbind — Wayland keyboard shortcuts overlay."""

import argparse
import os
import signal
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gdk, Gio, Gtk

from .config import get_parser
from .ui.overlay import OverlayWindow

PIDFILE = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "cheatbind.pid"
CSS_PATH = Path(__file__).parent / "style" / "cheatsheet.css"


def _read_pid() -> int | None:
    try:
        pid = int(PIDFILE.read_text().strip())
        # Check if process is alive
        os.kill(pid, 0)
        return pid
    except (FileNotFoundError, ValueError, ProcessLookupError, OSError):
        return None


def _write_pid():
    PIDFILE.write_text(str(os.getpid()))


def _remove_pid():
    PIDFILE.unlink(missing_ok=True)


def _toggle_or_run(args: argparse.Namespace):
    """If already running, kill the existing instance. Otherwise, start."""
    existing = _read_pid()
    if existing is not None:
        os.kill(existing, signal.SIGTERM)
        _remove_pid()
        sys.exit(0)

    _write_pid()

    try:
        parser, config_path = get_parser(args.compositor)
        if args.config:
            config_path = Path(args.config)
        columns = parser.parse(config_path)

        if not columns:
            print("No keybindings found.", file=sys.stderr)
            sys.exit(1)

        app = CheatbindApp(columns)
        app.run([])
    finally:
        _remove_pid()


class CheatbindApp(Gtk.Application):
    def __init__(self, columns):
        super().__init__(
            application_id="io.github.xhelliom.cheatbind",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self._columns = columns

    def do_activate(self):
        # Load CSS
        if CSS_PATH.exists():
            provider = Gtk.CssProvider()
            provider.load_from_path(str(CSS_PATH))
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

        win = OverlayWindow(self, self._columns)
        win.present()


def main():
    arg_parser = argparse.ArgumentParser(
        prog="cheatbind",
        description="Wayland keyboard shortcuts overlay",
    )
    arg_parser.add_argument(
        "--compositor",
        choices=["niri"],
        help="Force compositor (auto-detected by default)",
    )
    arg_parser.add_argument(
        "--config",
        help="Path to compositor config file",
    )
    args = arg_parser.parse_args()

    _toggle_or_run(args)


if __name__ == "__main__":
    main()
