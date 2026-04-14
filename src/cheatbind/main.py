"""Cheatbind — Wayland keyboard shortcuts overlay."""

import argparse
import ctypes
import fcntl
import os
import signal
import sys
from pathlib import Path

# Preload gtk4-layer-shell before any GTK import to fix linker order
_LAYER_SHELL_LIB = "/usr/lib/libgtk4-layer-shell.so"
if os.path.exists(_LAYER_SHELL_LIB):
    ctypes.cdll.LoadLibrary(_LAYER_SHELL_LIB)

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gdk, Gio, Gtk

from .config import get_parser
from .ui.overlay import OverlayWindow

_APP_NAME = "cheatbind"
CSS_PATH = Path(__file__).parent / "style" / "cheatsheet.css"


def _get_pidfile() -> Path:
    """Return PID file path in XDG_RUNTIME_DIR. Refuse /tmp fallback."""
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime_dir:
        print(
            "XDG_RUNTIME_DIR is not set. Cannot safely create PID file.",
            file=sys.stderr,
        )
        sys.exit(1)
    return Path(runtime_dir) / f"{_APP_NAME}.pid"


def _is_cheatbind_process(pid: int) -> bool:
    """Verify that a PID actually belongs to a cheatbind process."""
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes()
        return _APP_NAME.encode() in cmdline
    except OSError:
        return False


def _read_pid(pidfile: Path) -> int | None:
    try:
        pid = int(pidfile.read_text().strip())
        os.kill(pid, 0)
        if not _is_cheatbind_process(pid):
            return None
        return pid
    except (FileNotFoundError, ValueError, ProcessLookupError, OSError):
        return None


def _acquire_lock(pidfile: Path):
    """Acquire an exclusive file lock and write our PID. Returns the fd."""
    fd = open(pidfile, "w")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fd.close()
        print("Another cheatbind instance is running.", file=sys.stderr)
        sys.exit(0)
    fd.write(str(os.getpid()))
    fd.flush()
    return fd


def _resolve_config_path(args: argparse.Namespace) -> Path:
    """Resolve and validate the config file path."""
    parser, config_path = get_parser(args.compositor)
    if args.config:
        config_path = Path(args.config).resolve()

    if not config_path.is_file():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    return parser, config_path


def _toggle_or_run(args: argparse.Namespace):
    """If already running, kill the existing instance. Otherwise, start."""
    pidfile = _get_pidfile()

    existing = _read_pid(pidfile)
    if existing is not None:
        os.kill(existing, signal.SIGTERM)
        sys.exit(0)

    lock_fd = _acquire_lock(pidfile)

    try:
        parser, config_path = _resolve_config_path(args)
        columns = parser.parse(config_path)

        if not columns:
            print("No keybindings found.", file=sys.stderr)
            sys.exit(1)

        app = CheatbindApp(columns)
        app.run([])
    finally:
        lock_fd.close()
        pidfile.unlink(missing_ok=True)


class CheatbindApp(Gtk.Application):
    def __init__(self, columns):
        super().__init__(
            application_id="io.github.xhelliom.cheatbind",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self._columns = columns

    def do_activate(self):
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
        prog=_APP_NAME,
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
