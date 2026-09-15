---
name: systemd-headless-service
description: Background a TTY/tray app as a 24/7 user systemd service.
metadata:
  tags: []
---

# systemd Headless Service (user unit)

## When to use
- An app works from a terminal but dies/exits under `systemd --user` with no TTY.
- User wants it "24 jam meski PC restart" without a kept-open terminal.
- App auto-exits because it detects `!process.stdin.isTTY` and drops into tray/background mode that doesn't persist.

## Generic unit template
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
Enable + start:
```bash
systemctl --user daemon-reload
systemctl --user enable <name>.service
systemctl --user start <name>.service
```
Verify survive-crash: `kill -9 $(pgrep -f <pattern>)` then re-check `is-active` + port.

## Steps that actually matter
1. **Find the real process name & port first** — `ss -ltnp | grep <port>` and read the process. Don't assume the app from the port number alone (e.g. port 20128 is used by both "OmniRoute" and a separate "9router" app; deleting the wrong one breaks the user's setup).
2. **Inspect how it launches** — read the CLI entry (`read_file` on the binary, `cli.js`): does it read PORT/HOST from env? Does it spawn a child server (`detached: true`) then `return`? If the parent exits, systemd sees the service stop and the child may be killed too.
3. **Pass the headless/background flag** if the app has one (e.g. `9router --tray --skip-update`). Without it, a TTY-less parent often self-exits.
4. **Set MemoryMax high enough** — first boot frequently compiles native modules (e.g. `better-sqlite3` via node-gyp) and boots a framework (Next.js), spiking ~1.5GB. Use `MemoryMax=3G` to avoid the OOM killer wiping the instance (and sometimes the shell) mid-build.
5. **Wait long enough before checking** — 30–60s, not 5s. A fresh `next-server` + native build can take that long before the port listens.
6. **Linger** — confirm `loginctl show-user <user> | grep Linger=yes` so the user service runs with no active login session. If `no`, `sudo loginctl enable-linger <user>`.

## Pitfalls
- **Don't `rm -rf` the data dir of an app you're only trying to background.** Uninstall and "make it run 24/7" are different requests; confirm scope.
- **Double-launch race**: stop any manually-started instance (`kill` the PID) before `systemd start`, or two processes fight for the port.
- **`cd` into a deleted dir**: if you just removed `~/.omniroute` the shell's cwd may be invalid — always pass `workdir=/home/<user>` to terminal calls after a destructive rm.
- **OOM during build** presents as exit code -9 / SIGKILL on the *shell*, not a clean app error. Raise MemoryMax and retry.
- **`No such column` / SQL errors** from sqlite3 mean the column/table name is wrong or the DB is WAL-locked by a running process — stop the app first, or use `sqlite3` read-only.

## Verify
- `systemctl --user is-active <name>.service` → `active`
- `systemctl --user is-enabled <name>.service` → `enabled`
- `curl -sS -o /dev/null -w "%{http_code}" http://localhost:<port>/` → `307`/`200`
- Kill the PID, wait, confirm it auto-restarts.
