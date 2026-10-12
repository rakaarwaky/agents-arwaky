---
name: profile-scoped-plugins
description: "Sync plugins & hooks across isolated Hermes profile homes."
metadata:
  tags: [hermes, profiles, plugins, hooks, shell-wrapper, orca]
---

# Profile-scoped plugins & hooks: propagation and shell-wrapper pitfalls

Hermes named profiles (`~/.hermes/profiles/<p>/`) are **isolated homes**. They
inherit nothing from the default `~/.hermes/` — not settings, not API keys, not
**plugins**, not **hooks**, not `config.yaml` sections. `hermes -p <p>` (or any
wrapper that sets `HERMES_HOME=~/.hermes/profiles/<p>`) switches the whole
home to the profile, so anything installed *only* at the default home stops
firing for that session.

## When to Use

Load this skill when:
- A host-side feature (Orca sidebar agent tag, a status reporter, a gateway
  hook) **works on bare `hermes` but vanishes once the user's shell routes to a
  profile** — the classic "appears for a few seconds, then disappears" symptom.
- You just created/adopted a new profile and its host-side hooks don't fire.
- You need to make a plugin/hook available on **every** profile at once.

## The diagnostic signature (default-home has it, profile homes don't)

1. A host-side cache (e.g. `~/.config/orca/agent-hooks/last-status.json`) shows
   **N entries** for the default-profile agent and **0** for profile-routed
   agents, while *both* agent processes are alive and posting.
   That asymmetry is the bug, not a timing flake.
2. `ls ~/.hermes/profiles/<p>/plugins/` shows only `__pycache__/` (or nothing).
   A `__pycache__`-only plugin dir is a red herring: the real `.py` files were
   never copied, so the plugin won't register even if config enables it.
3. `grep -A4 '^plugins:' ~/.hermes/profiles/<p>/config.yaml` shows no `enabled:`
   block, or the needed plugin is absent from it.

## Propagate a plugin/hook to every profile (reproducible)

This is a **file task**, not a CLI task. The `hermes` CLI manages
config keys; it has no "copy this plugin into all profiles" verb.

```bash
src=~/.hermes/plugins/<name>
for p in $(ls ~/.hermes/profiles/); do
  dest=~/.hermes/profiles/$p/plugins/<name>
  [ -d "$src" ] || continue
  rm -rf "$dest"; mkdir -p "$dest"
  cp -r "$src/." "$dest/" && rm -rf "$dest/__pycache__"   # strip stale cache
done
```

Then **enable it in each profile's `config.yaml`**. If the plugin registers via
a `plugins.enabled` list, add the name there; if it registers via a dedicated
`<name>.yaml` / a `hermes profile add-plugin`-style key, use *that* mechanism
instead. Learn the shape first: `hermes -p <p> plugin list` or
`hermes -p <p> config get plugins --json` against one profile.

Write the enablement through the **safe-write procedure** documented in the
`hermes-profiles` skill (its `skill-filtering` reference § Safe write
procedure): JSON-array literals for list keys, ruamel round-trip only when
comments must survive. A hand `patch`-based YAML edit is the last resort and
loses the comment-preservation guarantee.

Finally **verify a real session posts**: restart the routed hermes, then check
the host cache gained an entry for that profile (read the cache file or run
the host's status command). Config parsing + a fresh log line is the proof;
"the files are in place" is not.

## Re-propagate on two triggers

- **After any host update that rewrites the source plugin** (files marked
  "Managed by Orca / do not edit" are the authoritative copies; your
  per-profile copies are derivative and go stale on the next host update).
- **After creating a new profile** (it is born with the same gap). Fold
  "create profile → copy plugins → enable in config → verify host cache
  posts" into your new-profile checklist.

## Shell-wrapper pitfall that triggers this whole class

When wiring an auto-routing wrapper that picks the profile from cwd, the user's
**actual login shell** is what runs it — not the shell you tested in.

1. Check the user's real shell *before* writing the wrapper:
   `grep "^$USER:" /etc/passwd | grep -oE '/bin/[a-z]+'`.
2. If their shell is fish but you wired `~/.bashrc`, the wrapper **never
   loads in their real session**. Mirror it into every rc the user sources:
   `~/.config/fish/config.fish` (fish), `~/.bashrc` (bash).
3. Fastest tell when the user says "I'm still on the default profile": read
   their prompt format (`user@host >` vs fish's style) to learn which shell
   they're actually in, then check that shell's rc — not the one you edited.
4. **Keep the detection logic in ONE POSIX-sh script** that both the bash and
   the fish wrappers source; each wrapper only calls the real CLI with the
   detected argument. Duplicating detection across two shells drifts the
   moment a new profile is added — the single-script design is what keeps
   bash and fish permanently in sync.

## Pitfalls

- **`__pycache__`-only dirs = the plugin was never actually copied.** Always
  `cp -r "$src/."` then `rm -rf "$dest/__pycache__"`.
- **A green config parse is not proof.** Run a real routed session and confirm
  the host cache got a fresh entry before declaring fixed.
- **Don't patch the user's hand-owned `hermes-profiles` skill to carry this.
  The propagation rule is general and belongs here**; the per-profile config
  write mechanics stay in `hermes-profiles`.
