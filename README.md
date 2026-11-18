# port-hud

A lightweight, zero-dependency CLI & Cyberpunk Floating HUD for inspecting and killing listening local TCP ports.

## Features

- **CLI Table Mode**: Lists listening TCP ports (`Port`, `PID`, `Process`, `Address`) via `lsof`.
- **Interactive Kill**: Quickly terminate a process bound to a specific port (`--kill <port>`).
- **Cyberpunk Floating HUD**: Frameless, semi-transparent, always-on-top `tkinter` overlay (`--overlay`) with neon cyan/pink styling, click-to-kill buttons, drag-to-move, and 3-second auto-refresh.

## Installation

```bash
uv tool install .
```

Or run directly with `uv`:

```bash
uv run port-hud
```

## Usage

```bash
# Show listening TCP ports in a table
port-hud

# Interactively kill the process on port 3000
port-hud --kill 3000

# Force kill without confirmation
port-hud --kill 3000 --force -y

# Launch the Cyberpunk Floating HUD
port-hud --overlay
```

## Requirements

- Python >= 3.11
- `lsof` (pre-installed on macOS and most Linux distributions)
- `tkinter` (for `--overlay` mode)

## License

MIT
