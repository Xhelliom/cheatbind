# cheatbind

A Wayland overlay that parses your compositor config and displays a styled keyboard shortcuts cheatsheet.

Instead of maintaining a separate shortcuts list, cheatbind reads your actual config file and renders an overlay with categorized keybindings, 3D keyboard-style key pills, and a multi-column layout.

## Supported compositors

- **niri** — parses `~/.config/niri/config.kdl`
- More compositors planned (Hyprland, Sway)

## Install

### Arch Linux (AUR)

```bash
yay -S cheatbind
```

This installs cheatbind and all dependencies (GTK4, gtk4-layer-shell, PyGObject).

### PyPI

```bash
pipx install cheatbind
```

System dependencies must be installed separately:

```bash
# Arch Linux
sudo pacman -S python-gobject gtk4 gtk4-layer-shell

# Fedora
sudo dnf install python3-gobject gtk4 gtk4-layer-shell

# Ubuntu/Debian (24.04+)
sudo apt install python3-gi gir1.2-gtk-4.0 libgtk4-layer-shell-dev
```

### From source

```bash
git clone https://github.com/Xhelliom/cheatbind.git
cd cheatbind
python3 -m venv .venv && .venv/bin/pip install -e .
.venv/bin/cheatbind
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
