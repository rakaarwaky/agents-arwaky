---
name: hermes-profiles
description: "Manage Hermes profiles: config, keys, and which skills load."
metadata:
  tags: []
---

# Managing Hermes Profiles

Use for anything scoped to one Hermes profile rather than the whole install: replicating
settings/keys across profiles, deciding which skills a profile sees, where a profile's
skills actually come from, and editing a persona (`SOUL.md`).

## Key facts

- Profiles live at `~/.hermes/profiles/<name>/` each with their own `config.yaml` and `.env`.
  They do NOT inherit settings or API keys from the default `~/.hermes/` — everything must be
  replicated explicitly.
- Any `hermes` CLI command can target another profile by prefixing `HERMES_HOME=~/.hermes/profiles/<name>`.
- List existing profiles first: `ls ~/.hermes/profiles/`.
- **Editing config: always `hermes config set`, never a hand edit.** A stray indent corrupts the
  file and breaks the live gateway. List-valued keys work through the CLI too, but only via a
  **JSON array literal** (`skills.disabled '["a","b"]'`); the comma form stores a scalar that
  silently disables nothing, and there is no append flag — appending means read-modify-write with
  `config get --json`. One real cost: the CLI rewrites the file and drops hand-written comments,
  so when those must survive, the ruamel round-trip in `references/skill-filtering.md`
  § "Safe write procedure" is the only sanctioned non-CLI writer.

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

```text

## Workflow: delete a profile (clean, no resurrection)

Never `rm -rf` the profile dir as the primary delete. The gateway keeps routing/session rows
keyed by `agent:<name>:...`, and on the next start it re-materialises an EMPTY
`~/.hermes/profiles/<name>/` dir from those rows, so the profile looks deleted but comes back.

```bash
# 1. Optional safety copy (profile dir can be hundreds of MB of cache/installs)
cp -r ~/.hermes/profiles/<name> ~/.hermes/profiles-pre-deletion/<name>

# 2. Delete WITH THE CLI (removes dir + purges session/routing identity)
hermes profile delete <name> -y

# 3. If the dir was already removed by hand, re-run the purge
hermes profile purge-identity <name>   # idempotent; profile dir may already be gone

# 4. Restart the gateway so it reloads the routing index from the DB
systemctl --user restart hermes-gateway.service
```

Verify: `hermes profile list` shows only the wanted profiles, `~/.hermes/profiles/` has no stray
empty dirs, and the gateway log has zero references to the deleted names:

```bash
journalctl --user -u hermes-gateway.service --since "2 min ago" --no-pager | grep -c '<name>'
```

Leftover state rows, before/after:
`sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM gateway_routing WHERE session_key LIKE '%<name>%';"`

## Pitfalls

- **Deleting a profile orphans its platform bot.** The token lives only in that profile's `.env`
  (`TELEGRAM_BOT_TOKEN`). Once the profile is gone the bot keeps polling with no home and must be
  revoked with @BotFather by hand. Tell the user which bots are about to be orphaned first.
- **One gateway unit, many bots.** With `gateway.multiplex_profiles: true` the single
  `hermes-gateway.service` serves every profile's bot; there is no per-profile systemd unit to
  disable. Profile dir removal + `purge-identity` is the whole cleanup — but a profile delete does
  NOT stop the gateway, so restart it explicitly to drop the stale routing index.
- **Skill packs shared via symlink.** If `~/.hermes/skills` is a symlink into a skill repo, a
  profile's `skills/` may be a root symlink to the same place. Deleting the profile removes only
  the symlink; the shared pack is untouched. Check before assuming skills were lost.

- **Custom provider = two entries.** An `auxiliary.<role>` section pointing at a custom provider
  also needs a matching `providers.<name>` entry (`base_url` + `key_env`) in the same config, or
  resolution fails. Check for BOTH blocks when copying.
- **`.env` is per-profile.** If the provider needs a key (`key_env`), the var must exist in each
  profile's own `.env` — copying config alone is not enough. Append with `printf >>`, verify with
  `grep -c`.
- Read back after writing (`grep` the configs) before telling the user it's done.
- Profiles do NOT get their own skill copies: `profiles/<p>/skills` is a symlink to the shared
  hub root. Assume "install a skill into profile X" means pack-level unless the layout reference
  says otherwise.

## References

- `references/skill-filtering.md` — **load for any "which skills should this profile see /
  hide / install" question.** Holds the pack's single statement of the pruning rule (disable
  via `skills.disabled`, never delete or trash), the install-vs-apply-vs-embed disambiguation,
  the ruamel safe-write procedure, and the skill-suite audit pass.
- `references/skills-layout.md` — load to find out where profile skills physically come from
  (the `profiles/<p>/skills` -> `~/.hermes/skills` -> pack symlink chain), the category-dir
  layout rule, the one-time migration for a new profile, and how to recount without trusting
  a remembered skill total.
- `references/soul-md-injection-scan.md` — load after writing or editing any `SOUL.md` /
  persona / context file: one regex hit blocks the whole file silently. Includes the gate
  command, the pattern-id table, and safe rewordings.
- `references/auto-detected-provider-shadowing.md` — load on a cross-profile model 401
  ("Model free is not supported"): an auto-detected CLI provider shadows the profile's own
  model setting.
- `scripts/skill_suite_audit.py <skills-root>` — read-only per-SKILL.md flags (description past
  the 57-char index window, missing trigger section, oversized body, slop words, 0-use skills).
  Accepts any path in the symlink chain.
