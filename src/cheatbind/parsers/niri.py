"""Parser for niri compositor config.kdl files."""

import re
from pathlib import Path

from .base import Column, Keybind, Parser, Section


# Auto-categorization rules: (category_name, action_pattern_regex)
_CATEGORIES = [
    ("Applications", r"^spawn(?!.*grim)"),
    ("Capture d'écran", r"^spawn.*grim"),
    ("Navigation", r"^focus-(column|window)"),
    ("Déplacement", r"^move-(column|window)"),
    ("Moniteurs", r"(focus|move).*monitor"),
    ("Workspaces", r"(focus|move).*workspace"),
    ("Colonnes", r"(consume|expel|toggle-column)"),
    ("Redimensionnement", r"(set-column-width|set-window-height|switch-preset|reset-window|expand)"),
    ("Disposition", r"(maximize|fullscreen|center|toggle-window-floating|switch-focus-between)"),
    ("Fenêtres", r"^close-window$"),
    ("Système", r"(quit|power-off|toggle-keyboard|toggle-overview|show-hotkey)"),
]


class NiriParser(Parser):
    """Parse niri config.kdl to extract keybindings.

    Supports:
    - hotkey-overlay-title="..." on bind lines for descriptions
    - //##! Title  markers for section headers
    - //#!  markers for column breaks
    - // [hidden] or hotkey-overlay-title=null to exclude binds
    """

    _BIND_RE = re.compile(
        r"^\s+"
        r"(?P<keys>[A-Za-z0-9_+]+)"
        r"(?P<props>[^{]*)"
        r"\{(?P<action>[^}]*)\}"
    )
    _TITLE_RE = re.compile(r'hotkey-overlay-title="(?P<title>[^"]+)"')
    _NULL_TITLE_RE = re.compile(r"hotkey-overlay-title=null")
    _SECTION_RE = re.compile(r"^\s*//##!\s*(?P<title>.+)$")
    _COLBREAK_RE = re.compile(r"^\s*//#!\s*$")
    _HIDDEN_RE = re.compile(r"//\s*\[hidden\]")

    MAX_CONFIG_SIZE = 1_000_000  # 1 MB

    def parse(self, config_path: Path) -> list[Column]:
        if config_path.stat().st_size > self.MAX_CONFIG_SIZE:
            raise ValueError(
                f"Config file too large ({config_path.stat().st_size} bytes, "
                f"max {self.MAX_CONFIG_SIZE})"
            )
        text = config_path.read_text()
        lines = text.splitlines()

        in_binds = False
        brace_depth = 0
        has_markers = False
        skip_next = False
        columns: list[Column] = [Column()]
        current_section = Section(title="Général")
        columns[0].sections.append(current_section)
        flat_binds: list[Keybind] = []

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("binds {") or stripped == "binds{":
                in_binds = True
                brace_depth = 1
                continue

            if in_binds:
                brace_depth += stripped.count("{") - stripped.count("}")
                if brace_depth <= 0:
                    in_binds = False
                    continue

                if self._COLBREAK_RE.match(line):
                    has_markers = True
                    columns.append(Column())
                    current_section = Section(title="Général")
                    columns[-1].sections.append(current_section)
                    continue

                m_section = self._SECTION_RE.match(line)
                if m_section:
                    has_markers = True
                    current_section = Section(title=m_section.group("title").strip())
                    columns[-1].sections.append(current_section)
                    continue

                if self._HIDDEN_RE.search(line):
                    skip_next = True
                    continue

                m_bind = self._BIND_RE.match(line)
                if m_bind:
                    if skip_next:
                        skip_next = False
                        continue
                    props = m_bind.group("props")
                    if self._NULL_TITLE_RE.search(props):
                        continue

                    m_title = self._TITLE_RE.search(props)
                    if not m_title:
                        continue

                    description = m_title.group("title")
                    keys_str = m_bind.group("keys")
                    keys = keys_str.split("+")
                    action_str = m_bind.group("action").strip().rstrip(";").strip()

                    keybind = Keybind(
                        keys=[self.prettify_key(k) for k in keys],
                        description=description,
                        action=action_str,
                    )
                    current_section.binds.append(keybind)
                    flat_binds.append(keybind)

        if has_markers:
            for col in columns:
                col.sections = [s for s in col.sections if s.binds]
                for section in col.sections:
                    section.binds = self._merge_duplicates(section.binds)
            columns = [c for c in columns if c.sections]
            return columns

        # No markers — auto-categorize by action
        if not flat_binds:
            return []
        return self._auto_categorize(flat_binds)

    @staticmethod
    def _merge_duplicates(binds: list[Keybind]) -> list[Keybind]:
        """Merge binds with the same action into a single entry."""
        seen: dict[str, Keybind] = {}
        merged: list[Keybind] = []
        for bind in binds:
            if bind.action in seen:
                seen[bind.action].alt_keys.append(bind.keys)
            else:
                seen[bind.action] = bind
                merged.append(bind)
        return merged

    def _auto_categorize(self, binds: list[Keybind]) -> list[Column]:
        """Group binds into sections by action pattern, then distribute into columns."""
        sections: dict[str, Section] = {}
        uncategorized = Section(title="Divers")

        for bind in binds:
            placed = False
            for cat_name, pattern in _CATEGORIES:
                if re.search(pattern, bind.action):
                    if cat_name not in sections:
                        sections[cat_name] = Section(title=cat_name)
                    sections[cat_name].binds.append(bind)
                    placed = True
                    break
            if not placed:
                uncategorized.binds.append(bind)

        # Ordered list of sections
        ordered = [
            sections[name]
            for name, _ in _CATEGORIES
            if name in sections
        ]
        if uncategorized.binds:
            ordered.append(uncategorized)

        # Merge duplicate actions within each section
        for section in ordered:
            section.binds = self._merge_duplicates(section.binds)

        # Distribute into 3 columns, balanced by bind count
        target_cols = 3
        total = sum(len(s.binds) for s in ordered)
        if total <= 20:
            target_cols = 2
        if total <= 8:
            target_cols = 1

        per_col = total / target_cols

        columns: list[Column] = [Column()]
        current_count = 0

        for section in ordered:
            if (
                current_count >= per_col
                and len(columns) < target_cols
            ):
                columns.append(Column())
                current_count = 0
            columns[-1].sections.append(section)
            current_count += len(section.binds)

        return columns
