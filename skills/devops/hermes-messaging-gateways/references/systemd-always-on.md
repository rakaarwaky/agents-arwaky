# Keeping the Hermes gateway always on (systemd user service)

Load when the user wants the gateway (Telegram/Discord/…) running at boot and
auto-restarting after a crash or a PC restart — "make gateway always on",
"persist gateway across reboot".

## Facts (verified)

- Unit: `~/.config/systemd/user/hermes-gateway.service`
  `ExecStart=<hermes venv>/bin/python -m hermes_cli.main gateway run`, `Restart=always`.
- Hermes CLI: `hermes gateway install|start|stop|restart|status`. There is **no**
  `enable` subcommand — use `systemctl --user enable` directly.
- Linger must be ON so the user service runs without an active login session:
  `loginctl show-user <user> -p Linger` → should be `Linger=yes`
  (set with `sudo loginctl enable-linger $USER`).
- `Restart=always` covers a crash; enabling the unit covers boot. **Both** are needed
  for "always on".

## Procedure

```bash
hermes gateway install                       # refresh unit if status says "outdated"
systemctl --user start hermes-gateway.service
systemctl --user enable hermes-gateway.service
# if is-enabled still reports 'disabled' despite a want-symlink, recreate it:
rm -f ~/.config/systemd/user/default.target.wants/hermes-gateway.service
systemctl --user daemon-reload
systemctl --user enable hermes-gateway.service   # must print 'enabled'
```

## Verify

```bash
systemctl --user is-enabled hermes-gateway.service   # enabled
systemctl --user is-active  hermes-gateway.service   # active
hermes gateway status
```

## Pitfalls

- `hermes gateway status` may flag an "outdated" unit plus a stale
  `gateway_state.json`. Run `hermes gateway install` (== restart) to refresh **before**
  enable.
- `systemctl --user enable` can report "already exists" while `is-enabled` is still
  `disabled`, because the want-symlink is stale. Remove the symlink and re-enable
  (procedure above) — that is the real fix.
- Gateway dies on SSH logout → linger is off (see Facts).
- Gateway dies when WSL2 closes → WSL2 needs `systemd=true` in `/etc/wsl.conf`; without
  it the gateway falls back to `nohup` and dies with the session.
- Crash-loop state stuck failed → `systemctl --user reset-failed hermes-gateway`.
- A per-profile unit (`hermes-gateway-<profile>.service`) must NOT be started while the
  default profile runs the multiplexer — it exits 78/CONFIG on a double bind. Restart the
  multiplexer instead (`SKILL.md` standard flow, step 3; diagnosis walkthrough in
  `multiplex-late-profile-adoption.md`).

Which profile actually receives messages (the `platforms.telegram.enabled` +
`home_channel` block) is a messaging-config question, not a systemd one — that block is
documented once, in `SKILL.md` § "A profile is only reachable if it declares its channel".
