# keepalive-mover

A lightweight Ubuntu Linux CLI tool that prevents Discord (and any other app monitoring input) from marking your status as idle/away by subtly moving the mouse after a configurable period of inactivity.

## Features

- **Smart idle detection** - Only jiggles mouse when you've been truly idle (no mouse/keyboard activity)
- **Non-disruptive** - Moves mouse 1-2 pixels and back to current position, never to a fixed point
- **X11/Wayland compatible** - Uses `pyautogui` with `xdotool` fallback for sessions that block synthetic input
- **Configurable** - Adjustable interval, idle threshold, and pixel movement via CLI flags
- **Graceful shutdown** - Clean exit on Ctrl+C with log message
- **Systemd support** - Optional user service for persistent background operation

## Requirements

- Ubuntu Linux (X11 or Wayland)
- Python 3.8+
- `xdotool` (for fallback on Wayland/some X11 sessions)

## Installation

### 1. Install system dependencies

Install `xdotool` for synthetic mouse fallback and `python3-dev` to compile Python modules (like `evdev` used by `pynput`):

```bash
sudo apt update && sudo apt install -y python3-dev xdotool
```

*(Optional)* You can also install `python3-tk` if you want PyAutoGUI to work natively. If `python3-tk` (tkinter) is missing, `keepalive-mover` will automatically detect the import failure and gracefully fall back to X11-level mouse movement using `xdotool`.

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Make the script executable

```bash
chmod +x main.py
```

## Usage

```bash
# Run with defaults (check every 45s, jiggle after 120s idle, move 1 pixel)
./main.py

# Custom configuration
./main.py --interval 30 --idle-threshold 60 --pixels 2 --verbose

# Help
./main.py --help
```

### CLI Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--interval` | `-i` | 45 | Check interval in seconds |
| `--idle-threshold` | `-t` | 120 | Seconds of inactivity before jiggling |
| `--pixels` | `-p` | 1 | Pixels to move mouse (1-2 recommended) |
| `--verbose` | `-v` | false | Log each jiggle event with timestamp |

## Systemd User Service (Optional)

For persistent background operation with auto-restart:

```bash
# Install service file
mkdir -p ~/.config/systemd/user
cp keepalive-mover.service ~/.config/systemd/user/

# Reload and enable
systemctl --user daemon-reload
systemctl --user enable --now keepalive-mover

# Check status
systemctl --user status keepalive-mover

# View logs
journalctl --user -u keepalive-mover -f
```

The service file uses your user's Python environment. If using a virtual environment, update the `ExecStart` path accordingly.

### Persist across reboots and logouts (Lingering)

By default, systemd user services run only while the user has an active login session. To allow the service to start automatically on system boot and continue running in the background after you log out:

```bash
loginctl enable-linger $USER
```

## Permissions Notes

### X11
- Ensure your user has access to the X server (typically automatic for logged-in users)
- May need `xhost +local:` or proper Xauthority setup for headless/server environments

### Wayland
- Native Wayland support for synthetic input is limited
- Tool falls back to `xdotool` which requires XWayland
- For pure Wayland, you may need `ydotool` (not yet supported) or a daemon like `wlr-randr`

## How It Works

1. **Activity listeners** (`pynput`) track real mouse/keyboard input
2. **Idle timer** resets on any genuine user activity
3. **Periodic check** every `--interval` seconds
4. **Jiggle** only if idle time exceeds `--idle-threshold`
5. **Relative movement** - moves N pixels right, then N pixels left, returning to exact position

## License

MIT License - see LICENSE file for details.

## Contributing

Issues and PRs welcome. Please ensure:
- Code follows existing style
- New dependencies are well-maintained and necessary
- Changes are tested on both X11 and Wayland if possible