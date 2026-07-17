"""Parser for zsh rc file annotations.

Reads `# cheatbind: <keys> <description>` comment lines, the same
opt-in annotation convention as niri's `hotkey-overlay-title` — the
shortcut description lives right next to the code it documents.
"""

import re
from pathlib import Path

from .base import Column, Keybind, Parser, Section

_SECTION_TITLE = "Terminal (zsh)"
_ANNOTATION_RE = re.compile(r"^\s*#\s*cheatbind:\s*(?P<keys>\S+)\s+(?P<description>.+?)\s*$")


class ZshParser(Parser):
    """Parse `# cheatbind: <keys> <description>` annotations from a zsh rc file."""

    MAX_CONFIG_SIZE = 1_000_000  # 1 MB

    def parse(self, config_path: Path) -> list[Column]:
        if config_path.stat().st_size > self.MAX_CONFIG_SIZE:
            raise ValueError(
                f"Config file too large ({config_path.stat().st_size} bytes, "
                f"max {self.MAX_CONFIG_SIZE})"
            )
        section = Section(title=_SECTION_TITLE)
        for line in config_path.read_text().splitlines():
            match = _ANNOTATION_RE.match(line)
            if not match:
                continue
            keys = match.group("keys").split("+")
            section.binds.append(
                Keybind(keys=keys, description=match.group("description"))
            )

        if not section.binds:
            return []
        return [Column(sections=[section])]
