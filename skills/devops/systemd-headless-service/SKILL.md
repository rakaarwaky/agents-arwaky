---
name: systemd-headless-service
description: "Background a TTY/tray app as a 24/7 user systemd service that survives reboot. Use when an app exits under `systemd --user` with no TTY, auto-exits because `!process.stdin.isTTY`, or must run headless with linger after PC restart."
when-to-use: "Use when an app works in a terminal but dies under systemd --user (no TTY), drops to tray/background mode, or must survive reboot via `systemctl --user enable` with `loginctl linger`."
argument-hint: "<binary> <flags>"
metadata:
  tags: []
---

# systemd Headless Service

Background a TTY/tray app as a 24/7 user systemd service that survives reboot: write the user unit, walk the six steps that actually matter, and verify active + enabled + auto-restart.

## Global Rules

- **Confirm scope before destructive steps.** "Run 24/7" is not an uninstall; any `rm -rf` of an app's data dir needs explicit confirmation (see `pitfalls.md`).
- **Find the real process and port before killing or enabling anything.** A port number does not name an app; the wrong `kill` breaks the user's setup.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Unit template | [`references/unit-template.md`](references/unit-template.md) | The user-unit INI, enable + start commands, and survive-crash check. |
| Steps that matter | [`references/steps.md`](references/steps.md) | The six in-order steps: process/port, launch inspection, headless flag, MemoryMax, wait time, linger. |
| Pitfalls | [`references/pitfalls.md`](references/pitfalls.md) | Double-launch race, deleted cwd, OOM during build, sqlite WAL lock. |
| Verify | [`references/verify.md`](references/verify.md) | `is-active`, `is-enabled`, port check, and auto-restart proof. |
