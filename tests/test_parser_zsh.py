"""Tests for the zsh rc file annotation parser."""

from pathlib import Path
from textwrap import dedent

import pytest

from cheatbind.parsers.zsh import ZshParser


@pytest.fixture
def parser():
    return ZshParser()


def _write_rc(tmp_path: Path, content: str) -> Path:
    rc = tmp_path / ".zshrc"
    rc.write_text(dedent(content))
    return rc


class TestBasicParsing:
    def test_extracts_annotated_bind(self, parser, tmp_path):
        rc = _write_rc(tmp_path, """
            # cheatbind: Ctrl+R Historique de commandes (fzf)
            source /usr/share/fzf/key-bindings.zsh
        """)
        columns = parser.parse(rc)
        binds = [b for c in columns for s in c.sections for b in s.binds]
        assert len(binds) == 1
        assert binds[0].keys == ["Ctrl", "R"]
        assert binds[0].description == "Historique de commandes (fzf)"

    def test_ignores_unannotated_lines(self, parser, tmp_path):
        rc = _write_rc(tmp_path, """
            # A regular comment
            bindkey '^[[1;5C' forward-word
            # cheatbind: Ctrl+T Recherche de fichiers (fzf)
        """)
        columns = parser.parse(rc)
        binds = [b for c in columns for s in c.sections for b in s.binds]
        assert len(binds) == 1

    def test_single_key(self, parser, tmp_path):
        rc = _write_rc(tmp_path, """
            # cheatbind: Tab Complétion (menu de sélection)
        """)
        columns = parser.parse(rc)
        binds = [b for c in columns for s in c.sections for b in s.binds]
        assert binds[0].keys == ["Tab"]

    def test_groups_into_one_section(self, parser, tmp_path):
        rc = _write_rc(tmp_path, """
            # cheatbind: Ctrl+R Historique
            # cheatbind: Ctrl+T Fichiers
        """)
        columns = parser.parse(rc)
        sections = [s for c in columns for s in c.sections]
        assert len(sections) == 1
        assert sections[0].title == "Terminal (zsh)"
        assert len(sections[0].binds) == 2


class TestEdgeCases:
    def test_empty_file(self, parser, tmp_path):
        rc = _write_rc(tmp_path, "")
        assert parser.parse(rc) == []

    def test_no_annotations(self, parser, tmp_path):
        rc = _write_rc(tmp_path, """
            bindkey '^[[1;5C' forward-word
            # just a comment
        """)
        assert parser.parse(rc) == []

    def test_rejects_oversized_config(self, parser, tmp_path):
        rc = tmp_path / ".zshrc"
        rc.write_text("x" * 1_100_000)
        with pytest.raises(ValueError, match="too large"):
            parser.parse(rc)
