---
name: agent-harness-connectors
description: Fix aa connect harness auth, MCP wiring, and skill provisioning.
---
# Harness Connector Debugging (agents-arwaky `aa connect`)

Use when a harness (Qwen Code, Hermes, OpenCode, Antigravity) is still broken
after `aa connect` — 401 Invalid API key, wrong model endpoint, or MCP servers
failing to start.

`aa connect <harness>` provisions three separate things, and a failure in one is
invisible in the others. A green "Connection complete" does NOT mean the harness
can authenticate.

| Layer | What connect writes | Where | What it does NOT touch |
|---|---|---|---|
| MCP servers | merged server map | harness settings/config file | whether those commands start |
| Skills | the whole skills dir becomes ONE symlink to `agents-arwaky/skills/` (verified harnesses: hermes, qwencode, opencode; per-skill copies elsewhere) | `<harness>/skills` | named-profile skill dirs |
| Env | `NINEROUTER_URL`, `NINEROUTER_KEY`, `MNEMOSYNE_DATA_DIR` | `<harness>/.env` + `~/.config/environment.d/9router.conf` | the harness's own provider/model config |

Code: `tools/connect/connect.py` (dispatch + adapter registry),
`tools/connect/<harness>_adapter.py` (per-harness), `tools/connect/connect_shared.py`
(`inject_9router_env`, `get_9router_credentials`, `engine_merge_mcp`,
`link_skills_root`, `provision_skill_to_dir`, `resolve_skill_link`,
`merge_dir_into`, `remove_provisioned_skills`),
`tools/lib/engine.py` (the JSON/JSONC/YAML mutator the adapters shell out to).

## Golden rule: env != provider binding

`inject_9router_env` only writes `<harness>/.env`. Most harnesses resolve a
provider credential as `process.env[envKey]` where `envKey` comes from the
provider entry in their settings file. If that entry points at a different
variable — typically a key captured earlier by the harness's interactive
auth/setup wizard — the harness keeps sending a stale key and the router
returns 401 forever, no matter how often you re-run `aa connect`.

So: after any 401-from-a-harness report, read BOTH the `.env` and the provider
config and compare them. Do not conclude from `aa connect` output that auth works.

A correct `.env` can still lose: dotenv loading does not override a variable
already present in the process environment, and the systemd user session injects
`~/.config/environment.d/*.conf` exports into EVERY new terminal at login. After
a router-key rotation, every terminal in that session carries the dead export
while all on-disk files look right and the agent's own headless tests pass (they
spawn from a different environment). `inject_9router_env` syncs environment.d
too; if that file exists and connect has not re-run since the rotation, that is
the 401 — not a stale harness session.

## Debug sequence for a 401 / auth failure

1. Enumerate every key the harness could be sending — grep the harness home for
   `NINEROUTER_KEY`, `API_KEY`, `envKey`, and any inline key the wizard stored:
   `grep -rn 'sk-' ~/.<harness>/settings.json ~/.<harness>/.env`. Also capture
   what a fresh login shell actually exports — `bash -lc 'echo $NINEROUTER_KEY'`
   and `systemctl --user show-environment | grep NINEROUTER` — and compare the
   prefix against the live key; an inherited export beats the `.env` file.
2. Find the authoritative live key: `~/.config/agents-arwaky/ninerouter.env`
   (`get_9router_credentials()` reads that, then `~/.config/9router/.env`, then
   `tools/config/ninerouter.env`). Treat `sk-your-9router-consumer-key-here` and
   `<YOUR_API_KEY>` as placeholders (`PLACEHOLDER_KEYS` in connect_shared.py).
3. Probe each candidate key against the router directly. Only the live one
   returns 200; the stale one returns 401 `invalid_api_key`. This identifies
   which key the client holds without reading harness logs:
   ```bash
   curl -s -o /tmp/r.json -w '%{http_code}\n' -X POST \
     http://127.0.0.1:20128/v1/chat/completions \
     -H 'Content-Type: application/json' -H "Authorization: Bearer $KEY" \
     -d '{"model":"my9router","messages":[{"role":"user","content":"ping"}],"max_tokens":5}'
   ```
4. Fix the BINDING, not just the key value: point the provider entry's `envKey`
   at the variable the connector actually maintains (`NINEROUTER_KEY`), and
   delete the wizard's inline copy so it can never shadow `.env` again after a
   key rotation. Rewriting only the stale value re-breaks on the next rotation.
5. Verify end to end by running the harness headless, not by re-reading config:
   `qwen -p "sapa singkat" --yolo` (see `references/qwen-code.md` for the
   equivalent on other harnesses and for the exact settings.json shape).

## Pitfalls

- **Inline keys shadow env.** Interactive provider-setup wizards store the key in
  the settings file itself (Qwen Code: `settings.env["QWEN_CUSTOM_API_KEY_<…>"]`,
  keyed by a hash of the baseUrl). Deleting or rebinding it is part of the fix;
  leaving it means `.env` changes have no effect.
- **baseUrl must match exactly**, including `127.0.0.1` vs `localhost`. Qwen
  matches provider entries by `id` + `baseUrl`; a persisted `model.baseUrl` that
  no longer matches emits "Persisted model.baseUrl … no longer matches any
  provider" and silently picks the first id match. Normalize both sides
  (`_router_v1`: strip trailing slash, append `/v1`) and write `model.baseUrl`.
- **`/v1/models` answers without auth.** 200 on the models endpoint proves the
  router is up, NOT that a key is valid — always probe `chat/completions` with
  the bearer header when testing keys.
- **A passing `aa check` is not proof the change works.** The repo gate only
  validates JSON syntax, compiles Python under `tools/`, and shellchecks scripts.
  Prove a connector change by re-writing the harness settings back into the
  broken state, running `aa connect <harness>`, and confirming the repair plus a
  live router check in the connect output.
- **Generic config mutation belongs in `engine.py`, not the adapter.** Adapters
  are thin per-harness dispatch; anything reusable across harnesses (env writing,
  MCP merging, credential lookup) goes in `connect_shared.py`, and JSON/JSONC/YAML
  edits go through `engine.py` subcommands so comment preservation is not lost.
  A provider-binding sync that is specific to one harness's schema may live in
  that harness's adapter (as qwencode's does) provided it only read-modify-writes
  a plain-JSON file the connector owns — never hand-edit YAML or JSONC there,
  and add an `engine.py` subcommand instead once a second harness needs it.
- **Mirror the guarded path shape in test fixtures.** A guard that compares a
  destination against `<REPO_ROOT>/skills` never fires for a fixture built at
  `<tmp>/pack/<name>/` — the test passes vacuously while the dangerous path
  (rmtree through a linked root) is untested. Build the fake repo as
  `<tmp>/skills/<name>/` and monkeypatch `REPO_ROOT` to `<tmp>`.
- **Drain then delete when union-moving a directory.** After merging a source
  dir's children into a twin, the emptied source dir still exists and the
  caller's `rmdir` of the old skills root fails with ENOTEMPTY mid-migration,
  leaving the harness dir half-moved. Remove the drained dir in the merge step.
- **Probe symlink support end-to-end before flipping a gate, and prefer a
  deterministic probe over an LLM one.** A `debug`-style skill dump (e.g.
  `opencode debug skill` prints every loaded skill as JSON) or an isolated-home
  listing (`HERMES_HOME=/tmp/x hermes skills list` where `/tmp/x/skills` is one
  symlink to the pack) proves discovery without spending model quota and without
  ambiguity; an LLM-turn probe (`agy --print`, `qwen -p`) can be blocked by a
  429 quota reset days away, and a probe at an arbitrary path proves nothing if
  it is not the dir the harness actually scans. Exact commands: `references/harness-skill-probes.md`.
- **`pkill -f <pattern>` matches the invoking command line itself** — killing a
  stuck harness probe with a pattern copied from that command SIGTERMs your own
  shell call. Enumerate first (`pgrep -af <name>`), kill by PID, exclude the
  current shell.
- **Verify a change with the state the user actually had.** Re-simulating the
  exact broken config (stale `envKey` + inline key + mismatched baseUrl) and
  re-running connect is what proves the fix; a clean config proves nothing.
- **"I always open a fresh terminal" from the user is data, not noise.** When
  your headless verification passes but the user still fails in new shells, the
  two processes inherit different environment layers (environment.d exports,
  shell rc files, service-level env). Reproduce via `bash -lc` and diff the key
  prefix before theorizing about stale sessions or telling them to restart.

## MCP servers fail to start in the harness

Separate failure from auth. Compare the `command` values in
`mcp_servers.generated.json` against what is installed in `~/.local/bin` — an
entry may name the plain CLI (`lint-arwaky`) when the stdio MCP server is a
different binary (`lint-arwaky-mcp`). A CLI invoked over stdio prints usage and
exits, which surfaces as "MCP server(s) failed to start: …". The generator reads
the tool registry in `tools/config/manifest.json`, so fix the command mapping
there or in `tools/mcp/generate_config.py`, then `aa mcp generate`. Placeholder
harness env values (e.g. an Anytype `Bearer <YOUR_API_KEY>`) also fail, and are a
credential gap, not a connector bug.

## Skill provisioning: the whole skills root IS the pack (default profile only)

`aa connect <harness>` replaces the harness's skills DIRECTORY with one symlink
to the pack: `~/.hermes/skills -> agents-arwaky/skills`, `~/.qwen/skills ->` the
same. There is no per-skill provisioning step, so adding, removing, or editing a
skill in the pack is instantly visible to every linked harness with zero re-run,
and a self-improving agent's edit writes through the link straight into the repo
(a pack `git diff` is the proof). Implemented by `link_skills_root()` in
`connect_shared.py`, gated per adapter by `SKILL_LINK_VERIFIED` (hermes,
qwencode, opencode True; antigravity False until its probe passes — probe
commands per harness live in `references/harness-skill-probes.md`);
`--copy-skills` falls back to per-skill copies for any harness.

Contrast: `aa skill install` into a PROJECT `.agents/skills/` always COPIES —
projects get pushed and git stores absolute-path symlinks as dead mode-120000
blobs in other clones (plain text on Windows with `core.symlinks=false`);
`--link` exists only for uncommitted local workspaces.

Migration and safety invariants, all under test in `tools/tests/test_skill_provision.py`:
- Non-empty existing skills dir ABORTS and lists what it would move; `--force`
  MIGRATES with per-entry collision semantics — never clobbers the pack:
  dot-prefixed STATE dirs (`.hub`) are union-merged file-by-file with the
  harness copy winning (it is the live one); a normal child byte-identical to
  its pack twin is DISCARDED (it is a stale copy-era snapshot; the pack is the
  source); a divergent child is kept but renamed `name.harness-N` for review,
  never moved over the pack source. Harness-native skills therefore end up in
  the pack as real dirs (expect them untracked there).
- Old per-skill symlinks pointing into the pack are simply unlinked.
- Runtime STATE the harness writes beside its skills (`.hub`, `.usage.json`,
  `.curator_*`, `.bundled_manifest`, `skills-lock.json`) lands in the pack root,
  so it MUST be in `.gitignore` or harness state pollutes skill history. When a
  state dir already has a pack twin, union-merge it file-by-file with the
  harness copy winning (`merge_dir_into`) — renaming to `X.harness-1` silently
  strands live state.
- Generated alias twins land there too: a loader that indexes hyphen names from
  underscore pack dirs (`anytype_mcp` -> `anytype-mcp`) writes real hyphen dirs
  INTO the pack through the root link. gitignore them (underscore dir is the
  tracked canonical, never commit the twin) — worse, while both exist a bare
  `skill_view`/skill-name lookup is refused as ambiguous by name collision, so
  resolve such skills by their full categorized path until the twins are gone.
- Any per-skill provision/remove targeting a linked root must be REFUSED
  (`_skills_root_link_guard`): its `rmtree` would delete real pack sources.
- `aa disconnect` unlinks the root and restores an empty real dir; pack sources
  survive. `rmtree`/`unlink` on a symlink never follows it, so removal is safe.

`hermes_targets()` returns the main profile (`~/.hermes`) plus every named
profile, and MCP/env merge into all of them. Skills must NOT. Raka's rule:
named profiles (currie/fangyuan/linus, ...) are task-specific specialists, so
linking/copying the generalist arwaky skill pack into them adds irrelevant
skills. `hermes_adapter.connect()` therefore acts on `~/.hermes/skills` once —
`link_skills_root` in link mode, one `provision_skill_to_dir` per pack skill in
copy mode — instead of looping `hermes_targets`, and `disconnect` still purges
profiles (leftover pack copies from the old behaviour are removable via
`remove_provisioned_skills`).
Side effect to remember: `~/.hermes` is itself a git repo pushed to
`rakaarwaky/hermes-backup`; once its skills dir is a single symlink, every
tracked file under `skills/` shows as deleted plus one untracked link — commit
that state so the backup repo reflects reality (pack content itself is preserved
by the agents-arwaky repo).
Related: how a named profile's `skills/` dir ends up pointing at the pack (and what
that shared root implies for per-profile state) is documented once, in the
`hermes-profiles` skill (`references/skills-layout.md`). Do not confuse connector
output with it: `connect` links `~/.hermes/skills` and never touches
`profiles/<p>/skills`, yet on this host the named profiles are root-linked to the hub
anyway (`ls -ld ~/.hermes/profiles/*/skills`) — that was a manual migration, so
profiles do see the generalist pack despite the rule above.

Consequence of the shared root link: every harness session edits the SAME pack
checkout, so other agent sessions (or the user) can commit — even push — work in
progress. Before acting on a "commit" request, `git status` + `git log --oneline`
+ `git ls-tree HEAD <paths>` to see what is already in history, and commit only
the genuine residue; never re-commit a diff you merely see staged. Check
`git reflog` when commits appear that you did not make, and flag concurrent
committers to the user instead of silently layering on top.

Rule for pruning irrelevant skills in a named profile: add their names to that
profile's `skills.disabled` list — do NOT delete the dirs or move them to a
`~/.hermes/.skill-trash/<profile>/` (that path does not exist on this host, and
nothing reads it). The root link makes the pack shared by every profile and
harness, so a deletion in one profile deletes it everywhere. The mechanism, the write form the
CLI actually accepts for a list key, and the KEEP-vs-DISABLE audit are documented once,
in the `hermes-profiles` skill (`references/skill-filtering.md`) — load that, do not
improvise here. Match each SKILL.md description against the profile's SOUL.md role before
deciding; never restore bundled upstream into profiles that opted out.

## Migration checklist for a provisioning-model change

Changing how skills reach a harness is a real-host migration, not just a code
edit — the linked live host is the test subject:
1. Add the guard first, then the mechanism, then wire adapters one at a time,
   flipping a per-adapter gate only after an end-to-end probe on the real CLI.
2. Run `aa connect <harness> --skills-only --dry-run` to enumerate every item the
   migration would move, and inventory non-pack children (harness-native skills
   and dot-file state) before committing to `--force`.
3. After each `--force` run verify all three: the link (`ls -ld`), discovery
   through it (`hermes skills list`, headless `qwen` probe), and that the pack's
   `git status` shows no runtime state leaking in (gitignore the state files in
   the same change).
4. Expect a crash mid-migration to leave the tree half-moved (children already
   relocated, old root still present). Inspect both sides before re-running
   `--force` rather than assuming the first run was a clean no-op.

## References

- `references/qwen-code.md` — Qwen Code (`qwa`/`qwen`) settings.json provider
  schema, where its bundled docs live, key-resolution chain, headless verify
  command, and the connector's provider-sync step.
- `references/harness-skill-probes.md` — per-harness commands to verify skill
  discovery through a symlinked skills root (the evidence required before
  flipping `SKILL_LINK_VERIFIED`), with each CLI's invocation quirks.
- `references/mcp-server-registration.md` — Hermes `hermes mcp add` traps the
  upstream docs do not cover: `--env` must precede `--command`/`--args`, a
  saved-but-disabled entry is not success, and the raw JSON-RPC-over-stdin way
  to tell a broken server from a broken registration.
