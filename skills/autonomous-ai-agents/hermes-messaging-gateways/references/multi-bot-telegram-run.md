# Verified end-to-end run: 4 Telegram bots → 4 profiles via multiplex (Aug 2026, Fedora)

Session evidence for the standard flow in SKILL.md. Setup: default profile + secondary
profiles `currie`, `linus`, `tesla`, each with its own BotFather token.

## Exact steps that worked

1. **Tokens into per-profile `.env`** (append, replacing any commented placeholder):
   ```
   TELEGRAM_BOT_TOKEN=<token>
   TELEGRAM_ALLOWED_USERS=1060253950   # owner's Telegram user id — always set this
   ```
   Files touched: `~/.hermes/.env` and `~/.hermes/profiles/<name>/.env` ×3.

2. **Nous auth into secondary profiles** (they had empty `auth.json`:
   `active_provider: None, providers: {}` — model/provider config pointed at nous but no creds):
   ```
   printf 'y\n' | hermes -p currie auth add nous --type oauth --no-browser --timeout 30
   ```
   Output: "Found existing Nous OAuth credentials at ~/.hermes/shared/nous_auth.json →
   Imported nous OAuth credentials". Repeated for tesla and linus. No device-code login needed.

3. **Multiplex on**:
   ```
   hermes config set gateway.multiplex_profiles true --force
   hermes gateway restart
   ```
   The `--force` is needed: without it Hermes prints "not a recognized config key" and asks.
   The key IS honored at runtime via the nested `gateway:` bridge (see multiplex-internals.md).

4. **Verification** (~1–2 min after restart):
   - `~/.hermes/logs/gateway.log`:
     - `✓ telegram connected (profile: currie)` / `(profile: linus)` / `(profile: tesla)`
     - `Gateway running with 4 platform(s)`
     - `Cron scheduler will tick 4 profile(s) under multiplex: ['default','currie','linus','tesla']`
   - DM `/start` to each bot from the owner account; gateway.log shows routing proof:
     `Ignoring /start platform ping for session agent:<profile>:telegram:dm:<owner_id>`
     (session keys `agent:main`, `agent:tesla`, `agent:currie`, `agent:linus` — one per profile).
   - Independent token check (bypasses gateway):
     `curl -s https://api.telegram.org/bot<TOKEN>/getMe`

## Observations / gotchas hit

- journalctl showed only the first "Connecting to Telegram (attempt 1/8)" lines and looked
  stalled; the real success lines were in `gateway.log`. Check the log file, not just journald.
- One transient `Sticky Telegram path 149.154.x.x failed; re-walking IPv4 literals…` warning
  ~8 min after start — adapter self-healed, polling stayed healthy. Not actionable.
- Pre-existing unrelated warning at every startup: MCP server 'anytype' parked/revived —
  don't confuse it with messaging failures.
- Before tokens were added, the running gateway logged
  `No env user allowlists configured…` and `No messaging platforms enabled.` — those two
  lines are the signature of "gateway alive but zero platforms wired".

## What did NOT need doing

- No platform blocks in any config.yaml — token-in-`.env` alone enabled Telegram per profile.
- No `hermes gateway install/start` for secondary profiles (multiplexer serves them;
  starting them would hard-error with double-bind).
