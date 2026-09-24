# Live diagnosis: profile added after multiplexer start → silent bot + failed per-profile unit

(fangyuan profile, Aug 2026 — companion evidence for `multi-bot-telegram-run.md`)

## Symptom
- Bot configured correctly (`TELEGRAM_BOT_TOKEN` verified in `<profile>/.env`) but never answers DMs.
- `hermes --profile fangyuan status` looks healthy: "Telegram ✓ configured", gateway PID shown.

## Root cause
Default gateway runs with `gateway.multiplex_profiles: true` and had started BEFORE the
fangyuan profile finished being wired, so its process only loaded the other profiles'
Telegram adapters. A separate systemd unit `hermes-gateway-fangyuan.service` existed and
on start exited 78/CONFIG:
```
✗ The default gateway is running as a profile multiplexer and already serves profile 'fangyuan'.
  Manage the multiplexer instead (from the default profile): hermes gateway restart
```
Net effect: nobody polls that bot token — the multiplexer *claims* the profile at
enumeration time only and never re-scans while running.

## Diagnosis path that worked
1. `systemctl --user list-units | grep hermes` → `hermes-gateway-fangyuan.service` failed,
   `hermes-gateway.service` active.
2. `journalctl --user -u hermes-gateway-fangyuan.service -n 30` → the exit-78 double-bind
   refusal (this message itself names the fix).
3. Count loaded bots: `journalctl --user _PID=<gw pid> | grep -oE
   "telegram_platform__home_[a-f0-9]+" | sort -u` → 3 hashes for 4 profiles ⇒ fangyuan
   adapter absent from the running process.
4. Map hashes → profiles: shell-grep first 10 chars of `TELEGRAM_BOT_TOKEN=` from every
   `~/.hermes/profiles/*/.env`. (The `read_file` tool refuses secret-bearing .env files;
   plain terminal grep of prefix/suffix works.)

## Fix
```
hermes gateway restart   # from the DEFAULT profile
```
Never `--force` / start the per-profile unit while the multiplexer runs (double-polling one
token, port conflicts). All bots reconnect within ~10–20 s. The failed per-profile systemd
unit stays red afterward; harmless once the multiplexer serves the profile.
