"""Tests for the niri config parser."""

from pathlib import Path
from textwrap import dedent

import pytest

from cheatbind.parsers.niri import NiriParser


@pytest.fixture
def parser():
    return NiriParser()


def _write_config(tmp_path: Path, content: str) -> Path:
    config = tmp_path / "config.kdl"
    config.write_text(dedent(content))
    return config


class TestBasicParsing:
    def test_extracts_binds_with_title(self, parser, tmp_path):
        config = _write_config(tmp_path, """
            binds {
                Mod+T hotkey-overlay-title="Terminal" { spawn "alacritty"; }
            }
        """)
        columns = parser.parse(config)
        binds = [b for c in columns for s in c.sections for b in s.binds]
        assert len(binds) == 1
        assert binds[0].description == "Terminal"
        assert binds[0].keys == ["Super", "T"]

    def test_skips_binds_without_title(self, parser, tmp_path):
        config = _write_config(tmp_path, """
            binds {
                Mod+H { focus-column-left; }
                Mod+T hotkey-overlay-title="Terminal" { spawn "alacritty"; }
            }
        """)
        columns = parser.parse(config)
        binds = [b for c in columns for s in c.sections for b in s.binds]
        assert len(binds) == 1

    def test_skips_null_title(self, parser, tmp_path):
        config = _write_config(tmp_path, """
            binds {
                Mod+X hotkey-overlay-title=null { do-something; }
                Mod+T hotkey-overlay-title="Terminal" { spawn "alacritty"; }
            }
        """)
        columns = parser.parse(config)
        binds = [b for c in columns for s in c.sections for b in s.binds]
        assert len(binds) == 1

    def test_skips_hidden_marker(self, parser, tmp_path):
        config = _write_config(tmp_path, """
            binds {
                // [hidden]
                Mod+Secret hotkey-overlay-title="Secret" { secret; }
                Mod+T hotkey-overlay-title="Terminal" { spawn "alacritty"; }
            }
        """)
        columns = parser.parse(config)
        binds = [b for c in columns for s in c.sections for b in s.binds]
        assert len(binds) == 1


class TestMarkers:
    def test_section_markers(self, parser, tmp_path):
        config = _write_config(tmp_path, """
            binds {
                //##! Apps
                Mod+T hotkey-overlay-title="Terminal" { spawn "alacritty"; }
                //##! Navigation
                Mod+Left hotkey-overlay-title="Left" { focus-column-left; }
            }
        """)
        columns = parser.parse(config)
        sections = [s for c in columns for s in c.sections]
        assert len(sections) == 2
        assert sections[0].title == "Apps"
        assert sections[1].title == "Navigation"

    def test_column_break_marker(self, parser, tmp_path):
        config = _write_config(tmp_path, """
            binds {
                //##! Col1
                Mod+T hotkey-overlay-title="Terminal" { spawn "alacritty"; }
                //#!
                //##! Col2
                Mod+D hotkey-overlay-title="Launcher" { spawn "fuzzel"; }
            }
        """)
        columns = parser.parse(config)
        assert len(columns) == 2
        assert columns[0].sections[0].title == "Col1"
        assert columns[1].sections[0].title == "Col2"


class TestAutoCategories:
    def test_categorizes_spawn_as_applications(self, parser, tmp_path):
        config = _write_config(tmp_path, """
            binds {
                Mod+T hotkey-overlay-title="Terminal" { spawn "alacritty"; }
            }
        """)
        columns = parser.parse(config)
        sections = [s for c in columns for s in c.sections]
        assert any(s.title == "Applications" for s in sections)

    def test_categorizes_focus_as_navigation(self, parser, tmp_path):
        config = _write_config(tmp_path, """
            binds {
                Mod+Left hotkey-overlay-title="Left" { focus-column-left; }
            }
        """)
        columns = parser.parse(config)
        sections = [s for c in columns for s in c.sections]
        assert any(s.title == "Navigation" for s in sections)


class TestMergeDuplicates:
    def test_merges_same_action(self, parser, tmp_path):
        config = _write_config(tmp_path, """
            binds {
                Mod+Left hotkey-overlay-title="Left" { focus-column-left; }
                Mod+H hotkey-overlay-title="Left" { focus-column-left; }
            }
        """)
        columns = parser.parse(config)
        binds = [b for c in columns for s in c.sections for b in s.binds]
        assert len(binds) == 1
        assert binds[0].keys == ["Super", "Left"]
        assert len(binds[0].alt_keys) == 1
        assert binds[0].alt_keys[0] == ["Super", "H"]


class TestKeyPrettify:
    def test_mod_to_super(self, parser):
        assert parser.prettify_key("Mod") == "Super"

    def test_page_down(self, parser):
        assert parser.prettify_key("Page_Down") == "PgDn"

    def test_xf86_key(self, parser):
        assert parser.prettify_key("XF86AudioRaiseVolume") == "Audio Raise Volume"

    def test_unknown_key_unchanged(self, parser):
        assert parser.prettify_key("F5") == "F5"


class TestEdgeCases:
    def test_empty_config(self, parser, tmp_path):
        config = _write_config(tmp_path, "")
        columns = parser.parse(config)
        assert columns == []

    def test_no_binds_block(self, parser, tmp_path):
        config = _write_config(tmp_path, """
            input { keyboard { } }
        """)
        columns = parser.parse(config)
        assert columns == []

    def test_empty_binds_block(self, parser, tmp_path):
        config = _write_config(tmp_path, """
            binds { }
        """)
        columns = parser.parse(config)
        assert columns == []

    def test_rejects_oversized_config(self, parser, tmp_path):
        config = tmp_path / "big.kdl"
        config.write_text("x" * 1_100_000)
        with pytest.raises(ValueError, match="too large"):
            parser.parse(config)
