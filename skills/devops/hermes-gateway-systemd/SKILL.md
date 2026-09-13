---
name: hermes-gateway-systemd
description: Keep the Hermes gateway running across reboots via systemd.
---

# Hermes Gateway systemd (always-on)

## When To Use
User wants the Hermes gateway (Telegram/Discord/…) running at boot and auto-restarting
after crash or PC restart — "make gateway always on", "persist gateway across reboot".

## Facts (verified)
- Unit: `/home/raka/.config/systemd/user/hermes-gateway.service`
  ExecStart=`.../venv/bin/python -m hermes_cli.main gateway run`, `Restart=always`.
- Hermes CLI: `hermes gateway install|start|stop|restart|status`. No `enable` subcommand —
  use `systemctl --user enable` directly.
- Linger must be ON so the user service runs without an active login session:
  `loginctl show-user raka -p Linger` → should be `Linger=yes`.

## Procedure
```bash
hermes gateway install                       # refresh unit if status says "outdated"
systemctl --user start hermes-gateway.service
systemctl --user enable hermes-gateway.service
# if is-enabled still 'disabled' despite a want-symlink, recreate it:
rm -f ~/.config/systemd/user/default.target.wants/hermes-gateway.service
systemctl --user daemon-reload
systemctl --user enable hermes-gateway.service   # must print 'enabled'
```

## Pitfalls
- `hermes gateway status` may flag "outdated" unit + stale `gateway_state.json`. Run
  `hermes gateway install` (== restart) to refresh before enable.
- `systemctl --user enable` can report "already exists" yet `is-enabled`=disabled when the
  want-symlink is stale. Remove the symlink and re-enable (above) — that is the real fix.
- `Restart=always` covers crash; enabling covers boot. Both needed for "always on".
- After start: `systemctl --user is-active hermes-gateway.service` → `active`.
- Only profiles with a `telegram: { enabled: true, home_channel: {...} }` block receive
  messages. Listing a platform under `platforms:` alone is NOT enough.

## Profile Telegram config (so a profile is reachable)
```yaml
platforms:
  telegram:
    enabled: true
    home_channel:
      platform: telegram
      chat_id: '1060253950'
      name: Raka Arwaky
      thread_id: '41454'
      user_id: '1060253950'
```
Copy this block into each profile's `config.yaml` that should receive DMs.
