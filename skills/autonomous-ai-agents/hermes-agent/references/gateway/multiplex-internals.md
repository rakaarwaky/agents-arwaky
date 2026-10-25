# Multiplex gateway internals — source walkthrough (Hermes v0.20.5)

Verified by reading the installed repo at `~/.hermes/hermes-agent/`. Line numbers drift; use them as search anchors.

## How a Telegram token becomes a connected adapter

1. **Token → platform enablement.** `gateway/config.py::_apply_env_overrides` (~L1968): if `TELEGRAM_BOT_TOKEN` resolves, `_enable_from_env(Platform.TELEGRAM)` flips `enabled=True` even without any config entry. So a bare token in `.env` is enough to enable the platform.
2. **Token resolution order.** `_getenv` (gateway/config.py ~L287) prefers the active *secret scope* over `os.environ`. Outside multiplex, plain `os.getenv` semantics apply.
3. **Empty-token guard (multiplex only).** `gateway/run.py` ~L12910: under `multiplex_profiles`, platforms enabled on the default profile but lacking a bot credential are skipped with log "Skipping <platform> on default profile: no bot credential…" (#64674). Secondary profiles still connect using their own `.env`.
4. **Profile secret scoping.** `gateway/run.py::_profile_runtime_scope` (~L2218) + `agent/secret_scope.py::build_profile_secret_scope` (~L289): per-turn, the profile's `<home>/.env` is parsed into an isolated dict (`load_env_file`, no os.environ mutation) and installed via `set_secret_scope`. Subprocesses (MCP, kanban) never inherit cross-profile secrets.
5. **Secondary adapter startup.** `gateway/run.py::_start_secondary_profile_adapters` (~L15365): enumerates profiles via `profiles_to_serve(multiplex=True)` (`hermes_cli/profiles.py` ~L1056 — default profile + every valid dir under `profiles/`, optional allowlist), claims credential/listener fingerprints to refuse double-polling the same token.
6. **Message routing.** `_make_profile_message_handler` (~L15828) stamps `event.source.profile` then runs `_handle_message` inside `_profile_runtime_scope`, so auth allowlists AND agent config/skills/memory all resolve from that profile.

## Multiplex flag resolution chain

`GATEWAY_MULTIPLEX_PROFILES` env (recognized tokens 1/true/yes/on etc.; blank = unset, not false) > top-level `multiplex_profiles:` in config.yaml > nested `gateway.multiplex_profiles` (what `hermes config set` writes) > default False. See `gateway/config.py` ~L1216–1290 and ~L90–122.

## Auth sharing across profiles (Nous Portal)

- Shared store: `~/.hermes/shared/nous_auth.json`; path helper `_nous_shared_store_path()` (`hermes_cli/auth.py` ~L5508).
- `hermes auth add nous --type oauth` in a secondary profile detects the shared store and offers import (`auth_commands.py` ~L339+, `_try_import_shared_nous_state` ~L5875) — refreshes the shared refresh_token once under a file lock, so sibling profiles don't race single-use tokens.
- Runtime resolution: `resolve_nous_runtime_credentials` (~L6431) reads `providers.nous` singleton state from that profile's own `auth.json`; empty `providers: {}` + `active_provider: null` means the profile has NO usable Nous credentials even though model/provider keys point at nous.

## Diagnostic shortcuts

- "No messaging platforms enabled" in gateway log ⇒ nothing set `enabled=true`: no token resolved anywhere, or explicit disable.
- MCP 'parked' warnings at startup are unrelated to messaging; check separately.
- `hermes status` / `hermes profile list` show per-profile gateway running/stopped state.
