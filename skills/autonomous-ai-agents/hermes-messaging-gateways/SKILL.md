---
name: hermes-messaging-gateways
description: "Set up Hermes Telegram bots and multiplex profile gateways."
tags: [hermes, gateway, telegram, multiplex, profiles]
---

# Hermes Messaging Gateways (multi-bot / multiplex)

Companion to the `hermes-agent` hub skill (bundled — see it for general gateway commands). This skill holds **source-verified internals** for wiring several Telegram bots to several Hermes profiles on one machine, gathered by reading `gateway/config.py`, `gateway/run.py`, and plugin adapters in the installed repo (`~/.hermes/hermes-agent/`).

## Standard flow

1. Per-profile token goes in `<profile>/.env`: `TELEGRAM_BOT_TOKEN=...` (+ `TELEGRAM_ALLOWED_USERS=<id>`). Secrets live ONLY in `.env`; enablement lives in config.
2. Give each secondary profile its own provider auth: `hermes -p <name> auth add nous --type oauth` — it auto-detects `~/.hermes/shared/nous_auth.json` and offers one-tap import instead of a fresh device-code login.
3. One process for all bots: `hermes config set gateway.multiplex_profiles true` on the DEFAULT profile, then `hermes gateway restart`. Do NOT run `hermes gateway start` for secondary profiles — hard error while the multiplexer runs.
4. Verify: `hermes gateway status`, then DM each bot; unknown senders get a pairing code (`hermes pairing approve telegram <CODE>`).

## Pitfalls

- Merely putting `TELEGRAM_BOT_TOKEN` in `.env` auto-enables the platform (`_apply_env_overrides`) — but a platform enabled with NO resolvable token can queue an infinite reconnect loop (multiplex skips empty-token primaries instead, #64674).
- Secondary profiles must NOT enable port-binding platforms under multiplex → whole profile skipped (`SecondaryPortBindingConfigError`).
- Open DM/group policy requires explicit allow-all opt-in (`GATEWAY_ALLOW_ALL_USERS=true` etc.) or startup aborts.
- Two profiles polling the same bot token = credential-collision refusal at startup.
- `gateway.multiplex_profiles` is read from top-level OR nested `gateway:` key; env `GATEWAY_MULTIPLEX_PROFILES` overrides both. Optional `gateway.multiplex_profile_allowlist` restricts served profiles (default serves all).
- Cron under multiplex: default gateway ticks every served profile's cron store (only when multiplex on).

## References

- `references/multiplex-internals.md` — code-path walkthrough (secret scoping, token resolution, handler stamping) with file:line pointers from v0.20.5.
