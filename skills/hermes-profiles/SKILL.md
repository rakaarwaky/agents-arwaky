---
name: hermes-profiles
description: "Use when copying Hermes config or keys across profiles."
version: 1.0.0
---

# Managing Hermes Profiles (multi-profile config replication)

Use when the user wants settings (models, providers, auxiliary vision, toolsets) copied from one
Hermes profile to others, or when inspecting what a profile is configured to do.

## Key facts

- Profiles live at `~/.hermes/profiles/<name>/` each with their own `config.yaml` and `.env`.
  They do NOT inherit settings or API keys from the default `~/.hermes/` — everything must be
  replicated explicitly.
- Any `hermes` CLI command can target another profile by prefixing `HERMES_HOME=~/.hermes/profiles/<name>`.
  This is the safe way to edit another profile's config (never hand-edit config.yaml).
- List existing profiles first: `ls ~/.hermes/profiles/`.

## Workflow: replicate a setting across all profiles

```bash
# 1. Inspect source profile's current values
grep -n -A4 "^auxiliary:" ~/.hermes/config.yaml

# 2. Apply the same keys to every other profile via the CLI (not sed)
for p in $(ls ~/.hermes/profiles/); do
  HERMES_HOME=~/.hermes/profiles/$p hermes config set auxiliary.vision.provider vision
  # ... repeat per key
done

# 3. Verify each profile actually got the block
grep -n -A4 "^auxiliary:" ~/.hermes/profiles/*/config.yaml
```

## Pitfalls

- **Custom provider = two entries.** An `auxiliary.<role>` section pointing at a custom provider
  also needs a matching `providers.<name>` entry (`base_url` + `key_env`) in the same config, or
  resolution fails. Check for BOTH blocks when copying.
- **`.env` is per-profile.** If the provider needs a key (`key_env`), the var must exist in each
  profile's own `.env` — copying config alone is not enough. Append with `printf >>`, verify with
  `grep -c`.
- Read back after writing (`grep` the configs) before telling the user it's done.
