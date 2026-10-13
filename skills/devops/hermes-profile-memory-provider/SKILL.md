---
name: hermes-profile-memory-provider
description: "Memory provider (hindsight) on all Hermes profiles."
version: 1.0.0
author: hermes-curator
metadata:
  hermes:
    tags: [hermes, profiles, memory, hindsight, provider, env]
    related_skills:
      - hermes-memory-providers
      - profile-scoped-plugins
      - hermes-profiles
---

# Activate a memory provider on every Hermes named profile

## When to Use

Use when the user wants a memory plugin (hindsight today) live on **all**
profiles under `~/.hermes/profiles/`, not just the default home. Symptom of
the gap: default home shows `Provider: hindsight` while every profile shows
`(none — built-in only)` — because profiles inherit nothing (no plugins, no
config sections, no `.env` secrets).

## Procedure (per profile, N profiles)

For each profile `p`, all four steps are required — a partial state
(config + plugin dir present, provider unset) is silent: the profile keeps
running on built-in memory.

```bash
# 0. source of truth: a profile that already has the plugin, else ~/.hermes/plugins/
SRC=~/.hermes/profiles/<have>/plugins   # dir with hindsight/ + .install-metadata.json + .lock

# 1. copy plugin code + provenance (idempotent — skip if dest exists):
[ -d ~/.hermes/profiles/$p/plugins/hindsight ] || {
  cp -r $SRC/hindsight ~/.hermes/profiles/$p/plugins/hindsight
  rm -rf ~/.hermes/profiles/$p/plugins/hindsight/__pycache__
  cp $SRC/.install-metadata.json $SRC/.install-metadata.json.lock ~/.hermes/profiles/$p/plugins/
}

# 2. register + install the plugin's venv deps (one profile per call!):
hermes -p $p plugins enable hindsight

# 3. switch the provider (safe CLI write, no YAML surgery):
hermes -p $p config set memory.provider hindsight

# 4. the LLM key lives in the DEFAULT home's .env; profiles have their own .env:
KEY=$(grep '^HINDSIGHT_LLM_API_KEY=' ~/.hermes/.env | tail -1)
grep -q HINDSIGHT_LLM_API_KEY ~/.hermes/profiles/$p/.env || echo "$KEY" >> ~/.hermes/profiles/$p/.env
```

## Pitfalls

- **`hermes -p <p> plugins enable` re-resolves Python deps every run.** N
  profiles in one execute_code loop blows the 60s kernel timeout mid-batch —
  the kernel dies, partial state is lost, and you don't know which profiles
  finished. Run one profile per terminal/execute_code call; on re-entry, the
  step-1 idempotency check plus `plugins list` tells you where the batch
  stopped. Batch the read-only checks, never the enable calls.
- **Copying files is not activation.** The plugin dir sitting in
  `profiles/<p>/plugins/` does nothing until step 2 registers it; step 3
  is what actually switches memory. Verify step 2 printed
  `✓ Plugin … enabled`, and treat a "venv out of sync" warning as a
  mandatory `hermes pm install` for that profile.
- **Never print the key value.** Extract it with `grep … | tail -1` and
  append with redirection; do not cat `.env` in output or inline the value
  in a heredoc.
- **Per-profile bank isolation is intentional.** Each profile keeps its own
  `profiles/<p>/hindsight/config.json` (bank_id `coding-agent::<p>`).
  Do not merge banks or overwrite per-profile config.json when activating —
  only create one if missing.
- **Verify per profile, not just the default home:**
  `hermes -p $p memory status` must show `Provider: hindsight` and
  `hindsight (API key / local) ← active`. "(none — built-in only)" means a
  step was skipped. Effects apply on the next session; the gateway reloads
  plugins on enable, no restart needed.

## See also

- General profile propagation (plugins/hooks, `__pycache__` red herring,
  shell-wrapper traps): `profile-scoped-plugins` skill.
- Hindsight modes, config schema, daemon lifecycle: `hermes-memory-providers` skill.
