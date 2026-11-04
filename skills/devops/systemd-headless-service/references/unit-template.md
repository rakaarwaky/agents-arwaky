# Generic unit template

The user-unit shape for backgrounding a TTY/tray app, plus enable and
survive-crash verification.

**Goal:** a `~/.config/systemd/user/<name>.service` that starts the app,
restarts it, and survives reboot via linger.

## Template

```ini
[Unit]
Description=<App> Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=<absolute path to binary> <flags>
Restart=always
RestartSec=5
Environment=HOME=/home/<user>
Environment=PATH=/home/<user>/.local/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=default.target
```

Substitute `<name>`, the absolute binary path, and flags; drop in
`MemoryMax=` when the first boot compiles native modules (see
`steps.md` step 4).

## Enable + start

```bash
systemctl --user daemon-reload
systemctl --user enable <name>.service
systemctl --user start <name>.service
```

## Verify survive-crash

`kill -9 $(pgrep -f <pattern>)` then re-check `is-active` and the
port after `RestartSec`.

## Completion

- The unit file exists under `~/.config/systemd/user/` with the
  substituted values.
- `systemctl --user is-active <name>.service` reports `active` after a
  manual `kill -9` of the app PID.
