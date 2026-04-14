# cheatbind

A Wayland overlay that parses your compositor config and displays a styled keyboard shortcuts cheatsheet.

Instead of maintaining a separate shortcuts list, cheatbind reads your actual config file and renders an overlay with categorized keybindings, 3D keyboard-style key pills, and a multi-column layout.

## Supported compositors

- **niri** — parses `~/.config/niri/config.kdl`
- More compositors planned (Hyprland, Sway)

## Dependencies

- Python 3.11+
- GTK4 + PyGObject
- gtk4-layer-shell

### Arch Linux

```bash
sudo pacman -S python-gobject gtk4 gtk4-layer-shell
```

## Install

```bash
pip install .
# or for development:
pip install -e .
```

## Usage

```bash
# Auto-detect compositor and show overlay
cheatbind

# Force a specific compositor
cheatbind --compositor niri

# Use a custom config path
cheatbind --config ~/my-niri-config.kdl
```

Running `cheatbind` while it's already showing will close the overlay (toggle behavior via PID file).

Press **Escape** or click anywhere to dismiss.

### niri keybinding example

```kdl
Mod+Slash hotkey-overlay-title="Aide raccourcis" { spawn "cheatbind"; }
```

## Config annotations (optional)

You can add markers in your niri config for custom sections and column breaks:

```kdl
binds {
    //##! Applications
    Mod+T hotkey-overlay-title="Terminal" { spawn "alacritty"; }
    Mod+D hotkey-overlay-title="App launcher" { spawn "fuzzel"; }

    //#!
    //##! Navigation
    Mod+Left hotkey-overlay-title="Focus left" { focus-column-left; }

    // [hidden]
    Mod+Secret hotkey-overlay-title="Hidden bind" { do-something; }
}
```

- `//##! Title` — section header
- `//#!` — column break
- `// [hidden]` — exclude a bind from the overlay
- `hotkey-overlay-title=null` — also excludes a bind
- Without markers, cheatbind auto-categorizes binds by action type

## License

MIT
