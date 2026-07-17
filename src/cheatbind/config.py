"""Configuration and compositor detection."""

import os
from pathlib import Path

from .parsers.base import Column, Parser
from .parsers.niri import NiriParser
from .parsers.zsh import ZshParser

COMPOSITORS = {
    "niri": {
        "parser": NiriParser,
        "config_paths": [
            Path("~/.config/niri/config.kdl").expanduser(),
        ],
        "env_hint": "NIRI_SOCKET",
    },
}

_ZSHRC = Path("~/.zshrc").expanduser()


def detect_compositor() -> str | None:
    """Detect the running Wayland compositor from environment."""
    for name, info in COMPOSITORS.items():
        if os.environ.get(info["env_hint"]):
            return name
    # Fallback: check XDG_CURRENT_DESKTOP
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    for name in COMPOSITORS:
        if name in desktop:
            return name
    return None


def get_parser(compositor: str | None = None) -> tuple[Parser, Path]:
    """Return the parser and config path for the given or detected compositor."""
    if compositor is None:
        compositor = detect_compositor()
    if compositor is None:
        raise RuntimeError(
            "Could not detect compositor. Use --compositor to specify one.\n"
            f"Supported: {', '.join(COMPOSITORS)}"
        )
    if compositor not in COMPOSITORS:
        raise RuntimeError(
            f"Unsupported compositor: {compositor}\n"
            f"Supported: {', '.join(COMPOSITORS)}"
        )

    info = COMPOSITORS[compositor]
    parser = info["parser"]()

    for path in info["config_paths"]:
        if path.exists():
            return parser, path

    raise RuntimeError(
        f"Config file not found for {compositor}. "
        f"Looked in: {', '.join(str(p) for p in info['config_paths'])}"
    )


def get_extra_columns() -> list[Column]:
    """Parse additional shortcut sources beyond the compositor (shell config)."""
    if not _ZSHRC.is_file():
        return []
    return ZshParser().parse(_ZSHRC)
