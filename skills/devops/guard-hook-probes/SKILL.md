---
name: guard-hook-probes
description: "Use when verifying guard hooks are live in a session."
metadata:
  version: 1.0.0
  author: hermes-curator
  license: MIT
  tags:
    - guard-hooks
    - hook-liveness
    - audit-log
    - probe-protocol
  related_skills:
    - agent-worktree-hooks
    - hermes-shell-hooks
    - git-hook-probing
---

# Guard-Hook Liveness Probes

## When to Use

Run Raka's two-tier guard-hook probe suite inside a running Hermes session —
when the user says "verify the guard hooks are live", attaches a
hook-test-prompt file, asks to classify probe failures by layer, or wants
the audit log as proof of liveness. Skipped if the goal is just to wire or
repair the hooks themselves (use `agent-worktree-hooks` / `hermes-shell-hooks` for that).

Verification protocol for Raka's two-tier guard hooks in a running Hermes
session: hard pre-block on git verbs in the main clone; soft post-revert on
file writes; Orca-worktree exemption as the control.

Applies to profiles whose `config.yaml` wires:
- `pre_tool_call` → `~/.hermes/scripts/guard-main-pre.sh` (HARD block)
- `post_tool_call` → `~/.hermes/scripts/guard-main-revert.sh` (SOFT revert + nudge)

The class-level architecture lives in `agent-worktree-hooks`; this skill
covers only the in-session verification protocol and its interpretation.

## What probes prove, and what they cannot

A probe suite run by the model under test proves only that the hook
PIPELINE is live: scripts run, exit codes are honored, revert logic
executes. It cannot prove by itself that (a) the deny reason text reached
the model, or (b) the post context injection arrived on the next turn —
both are model-visible channels, and a deviation there is a
harness-delivery gap, not a guard failure. Distinguish the two before
writing a FAIL verdict, and name the failing layer explicitly.

## Audit log: the ground truth

Every guarded event appends one JSON line to:
- `~/.hermes/logs/hook-audit.log` — default profile
- `~/.hermes/profiles/<name>/logs/hook-audit.log` — sub-profiles

Shape: `{"ts": "...", "event": "pre_tool_call|post_tool_call|grok", "tool": "...", "action": "deny|allow|allow-worktree", "repo": "..."}`.

- `event` is the payload's `hook_event_name`; `lib.sh` defaults it to
  `grok` when the payload omits it, so `"event":"grok"` lines in a Hermes
  log are normal, not a foreign harness leaking in.
- `action: "deny"` lines are written inside `emit_deny_json` — only when a
  pre-hook actually emitted a deny. `allow` lines are written by the
  post-hook after the tool ran. `allow-worktree` = a worktree command was
  cleared by the worktree policy.
- **Liveness test**: after the probe window, tail the log and require fresh
  lines (within a few minutes) for the probed repo. No recent lines for a
  repo the manifest allowlists = hooks NOT running in this session —
  report that as a distinct FAIL class ("hooks not live") and stop; the
  probes are all fail-open now, so keep chasing them yields no new
  signal.

## Probe order (run in sequence; report each result before the next)

1. **Baseline**: `git status --short` + `git log --oneline -1` on the main
   clone. Record HEAD; if the tree is dirty, STOP and report — do not
   touch it.
2. **HARD: git commit** — `git -C <main clone> commit --allow-empty -m "hook-test: commit blocked"`.
   Expect: tool result is an error. If the error is the bare string
   `Blocked by shell hook.` with no "immutable default-branch clone" /
   "Orca worktree" text, the pipeline fired but the deny reason did not
   reach the model. Confirm the pipeline actually fired from the audit log
   (fresh deny line) before concluding either way.
   **Pass-shape**: the deny text must contain both (a) the reason the
   directory is off-limits ("immutable default-branch clone" or
   "read-only source of truth") and (b) the remedy ("Orca worktree" /
   `~/orca/workspaces/`). A bare generic block with neither is a
   harness-delivery gap; one with reason but no remedy is a guard-template
   gap — both are reportable, and naming which one you saw tells Raka
   where to fix it.
3. **HARD: git push** — `git -C <main clone> push origin main`.
   Expect the same block shape; nothing actually pushed. Pass-shape same
   as P1: reason + remedy both present in the deny text.
4. **HARD: git checkout to a non-default branch** —
   `git -C <main clone> checkout -b hook-test-branch`.
   Expect: blocked with the branch name in the reason. Pass-shape:
   the deny text must name `hook-test-branch` specifically (a generic
   "branch work is blocked" message that does not echo the branch name
   means the guard's deny template is missing the `BRANCH_NAME` variable
   — quote the actual text in the report so Raka can see the gap).
   In older guard versions this probe SUCCEEDED (the branch got created)
   and the post hook silently pinned back to the default branch — check
   `git -C <main clone> rev-parse --abbrev-ref HEAD` after; the clone
   must still be on the default branch. If the clone is left on a probe
   branch, that is a real guard gap: pin back (`git -C <main clone>
   checkout <default> && git -C <main clone> branch -D <probe-branch>`)
   and report it. `git checkout <default-branch>` IS
   allowed on the main clone; the `git checkout -b <new>` /
   `git checkout <non-default>` forms are the deny targets.
5. **SOFT: write_file (tracked)** — expect the write_file call SUCCEEDS (the
   pre-stage's write matcher allows it), the next `git status --short`
   is CLEAN (post-stage reverted it), and the next model turn begins
   with injected context containing `Your write was reverted...`.
   **The nudge is delivered via `pre_verify`, NOT `post_tool_call`** — Hermes
   drops `post_tool_call` context (observer-only event, `_parse_context` is
   parsed but never injected into the next turn). The post hook reverts the
   file on disk AND drops a marker at `/tmp/hermes-revert-nudge/<sid>.revert`;
   `turn_stop_gates._pre_verify_nudge` globs that marker and surfaces it
   through `verify-workflow.sh → verify-revert-nudge.sh` as
   `{"decision":"block","reason":...}`, which Hermes injects at the next
   turn start. Missing nudge + clean tree = revert fired but the marker or
   the `pre_verify` path is broken — report that layer.
   **Same-turn nudge requires a Python plugin, not a shell hook.** The
   `transform_tool_result` event fires after `post_tool_call` and before the
   result enters the model's context — the only hook that can deliver a
   nudge inline in the same turn. But the shell-hook response parser returns
   a `dict` (`{"context": "..."}` via the default `_parse_context`), and
   `_apply_transform_tool_result_hook` (model_tools.py) only accepts a bare
   `str` return from hooks. A shell hook's dict output is silently discarded
   and the original tool result passes through unchanged. A true
   same-turn, no-marker nudge requires registering a **Python plugin**
   callback for `transform_tool_result` that returns the modified result
   string. Shell hooks for `transform_tool_result` are registered but
   inert — do not expect them to work; if you add one and the nudge never
   appears, the hook is not broken, it is structurally incapable. The
   `pre_verify` marker path remains the only shell-hook-supported channel.
   If `write_file` refuses to overwrite because the session only had a
   partial read, read the file in full (single call, no pagination) and
   retry once — the refusal is a write-hygiene guard, not the hook.
   5b. **SOFT: write_file creating a NEW (untracked) file** — same shape as P4b
   but the file never existed in git, so the post tier DELETES it (no
   `git checkout`), tree goes clean, marker dropped, nudge at next turn
   contains `New file created reverted (deleted)`. Before the untracked-file
   branch in `revert-dirty-clone.sh`, a new file created on the main clone by
   `write_file` survived untouched (the tracked-file path only matched
   `git ls-files` hits, and the terminal branch only handled `run_terminal_command`) —
   if P4c's probe file still exists on disk, the untracked branch is missing
   or unregistered; that is a guard-logic gap, report it as such.
5. **Control: worktree exemption** — P6 (`which orca && orca --version`) FIRST so the tool choice is known: `orca worktree create --repo path:<main clone> --name hook-test-soft --agent claude --prompt "hook test" --no-parent --json` (use a built-in Orca TUI agent id — `claude`, `codex`, `opencode`, `devin` — not a Hermes profile name; `--agent hermes` / `--agent qwen-web-arwaky` / `--agent test` / `--agent system` all fail with `Unknown TUI agent`), then `write_file` a probe file into that worktree path. Expect: write succeeds AND is NOT reverted (worktree is exempt). A reverted worktree write means the exemption path is broken. Clean up: `orca worktree rm --worktree path:<worktree-path> --force` (the verb is `rm`, not `remove`; `remove` does not exist in the current CLI). If `--agent` is omitted, also omit `--prompt` (`--prompt` requires `--agent`).

## Baseline restore before finishing

- Clean tree, clone on the default branch, no probe branches left behind.
- Only the `git checkout -- <file>` restore form is allowed on the
  default branch; `git reset --hard` is exactly what the guards deny,
  so never use it for cleanup.

## Report format (return verbatim to the user)

```
HEAD baseline:        <short sha> / clean|dirty
P1 commit:            blocked|allowed  | reason: "<first 80 chars of the reason>" or "no reason, generic block"
P2 push:              blocked|allowed  | reason: "..."
P3 checkout:          blocked|allowed  | main still on: <branch>
P4a terminal-dirty:   blocked|ran
P4b write_file tracked: succeeded|blocked
P4b-cleanness:        clean|dirty
P4c write_file new:   succeeded+deleted|succeeded+survived|blocked
P4d nudge received:   yes|no | text: "<exact injected context>"
P5 worktree write:    allowed+not-reverted|reverted|blocked
VERDICT:              PASS (all expectations met) | FAIL (<which probes, which layer, why>)
```

FAIL reasons must name the layer: guard logic (script), harness
reason-delivery, context injection, or exemption path — each is a
different bug with a different fix location. A bare "FAIL (P3)" with no
layer is not an acceptable report.

- **`orca worktree create --agent` accepts only built-in Orca TUI agent ids** (`claude`, `codex`, `opencode`, `devin`). Hermes profile names, `hermes`, `test`, `system`, and arbitrary strings all fail with `Unknown TUI agent`. Use `claude` as the default TUI agent for probe worktrees. If the operator wants NO agent, omit both `--agent` and `--prompt` (`--prompt` requires `--agent`).
- **`orca worktree rm` is the correct removal verb** (with `--worktree path:<path> --force`). `orca worktree remove` does not exist in the current CLI — it rejects with "Unknown command". The `--worktree` selector accepts `path:<path>`, `name:<displayName>`, `id:<repo-id>::<path>`, or `branch:<branch>`.
- **P4's "nudge received" is turn-observed.** The `File write reverted:` context lands as ephemeral turn-start injection via `pre_verify` — check the start of the model turn AFTER the write. The `revert` audit line (when present) proves the post revert FIRED and emitted a marker at `/tmp/hermes-revert-nudge/<sid>.revert`, but it cannot prove the marker reached the model — the nudge-proof is always the turn-start check, not the log. If a `revert` line is logged yet no nudge appeared at turn start, that is a `pre_verify` delivery gap (marker not globbed by `turn_stop_gates._pre_verify_nudge`, or `verify-revert-nudge.sh` not registered), not a guard failure. The `post_tool_call` context JSON is also emitted by the post hook but Hermes drops it (observer-only event) — the marker + `pre_verify` path is the only channel that actually reaches the model.
- **Pre-stage audit lines from the TUI can carry `event: "grok"` even under the Hermes bridge**, when `lib.sh`'s payload normalization sees a Grok-shaped input (Hermes TUI payloads are normalized by `read_hook_input`'s tool-name mapping but the event field may still default). Liveness judgment stays on `ts` timestamps, never on event names.
- **The nudge marker survives across sessions if not consumed.** `/tmp/hermes-revert-nudge/<sid>.revert` files are per-session but `/tmp` persists across Hermes restarts on this host. A stale marker from an earlier probe session (e.g. a test that fired the post hook but the `pre_verify` nudge never ran because the session ended before the stop-gate fired) will make the *next* session's P4 probe show `yes` for "nudge received" with a message describing a write from the *previous* session — a false-positive PASS. Always `ls /tmp/hermes-revert-nudge/` before starting a probe run and delete any stale `.revert` files that don't belong to the current session; treat an nudge that names a file/operation you did not just perform as "stale marker, not this session's write".

## Pitfalls

- **Post hook reverts the tree even when the probe "succeeded"** — a
  probe that left the clone dirty is not a probe that passed; run
  `git status --short` and `git rev-parse --abbrev-ref HEAD` immediately
  after every probe before interpreting it.
- **The `write_file` stale-refusal is orthogonal to the hook system.**
  Partial reads (offset/limit pagination) leave the write guard armed;
  a full single-call read disarms it. Do not conflate the refusal with
  a hook block — it happens with the hooks healthy.
- **`event: "grok"` in the audit log is not a foreign harness.**
  `lib.sh` defaults the event name; the guard scripts predate the Hermes
  dialect and keep the Grok default. Treat `grok` lines as Hermes lines
  when the script path is `~/.hermes/scripts/`. Newer bridge versions
  populate `event` with the actual Hermes event name (`pre_tool_call` /
  `post_tool_call`) instead of the `grok` default — both shapes are
  normal; use the `ts` timestamp for liveness, not the event name.
- **Do not use `git reset --hard` for probe cleanup** — the guard
  denies it on the default branch; use `git checkout -- <file>` and
  `git branch -D <probe-branch>` instead.
- **A worktree write that got reverted is an exemption bug, not a
  revert bug.** The two directions of failure point at different
  scripts: a reverted worktree write = `in_orca_exemption()` mis-resolved
  the path; a non-reverted main-clone write = the post revert pipeline
  itself is dead. Name which one you saw.
- **Write-typo in a deny reason is a real bug to report** — when a
  probe block message names the wrong remedy script (e.g. a write
  denial that points at the branch-pin guard instead of the worktree
  create flow), quote the mangled text in the report; it means the
  guard's deny template is stale.
- **A hard-blocked write kills the soft-tier probe.** If the pre hook
  denies a main-clone `write_file` (a guard regression where the hard
  tier claims the write path the soft tier owns), no post revert or
  nudge can fire: report P4 as hard-blocked and the nudge as
  untestable, NOT as "context injection broken". The fix is on the
  guard side (restore the two-tier contract: pre-allow writes, post
  revert + nudge), not in the probe — after such a regression, the
  probe suite can pass P1–P3 and P5 while P4 remains structurally
  untestable. To still exercise the soft path in the same session,
  dirty a tracked file through a terminal append (`printf '\nprobe-line\n'
  >> <file>`, single git segment with `git -C`) and confirm that gets
  reverted + nudged.
- **Hermes handoff dialects.** The pre hook's deny JSON must use the
  verb `block` (`{"action":"block","reason":...}` or
  `{"decision":"block","reason":...}`) — Hermes's parser does not
  recognize `deny` as a verb, so a bare `{"decision":"deny"}` silently
  drops the reason text and the model sees a generic block. The post
  hook's context nudge must be top-level `{"context":"..."}` — the
  Claude-Code `hookSpecificOutput.additionalContext` shape is ignored
  by Hermes and never injected. Test both directions by parsing the
  guard script's stdout before trusting the in-session behavior.
- **Multi-segment commands can slip past command-parsing guards.** A
  guard that extracts the command string may only inspect the first
  segment of a `cd <repo> && git ...` chain — a probe or fallback
  command written as `cd <repo> && git commit ...` can be classified
  "no git command" and silently allowed. Write probes and fallbacks
  as single git segments: `git -C <repo> commit ...`. The v2 probe
  suite (attached as `hook-test-prompt-v2.md`) already uses
  `cd <repo> && git ...` for P1–P3 and those blocks still fire — the
  guard's `effective_git_dir()` now resolves through `cd` chains — but
  keep single-segment `git -C` form for any *new* probes you add,
  since it is the one form the guard's own regression tests pin.
- **Write probes use `write_file`, not terminal append.** The P4 probe
  uses the `write_file` tool directly (not `printf >> <file>` in
  terminal) because the soft tier's matcher is on the write tool, not
  on shell redirection. If `write_file` is refused (stale-read guard),
  read the file in full first — the refusal is a write-hygiene guard,
  not the hook. The skill's older probe-5 fallback (`printf '\nprobe-line\n'
  >> <file>`) is for the hard-tier regression case where `write_file`
  is denied by the pre hook; in normal operation `write_file` succeeds
  and the post hook reverts it silently.
- **Audit `allow`/`revert` lines are conditional.** `hook_audit` writes a
  line per guarded event only when the payload's `event` is `post_tool_call`;
  pre events return without logging. Fresh `allow`/`revert` lines are positive
  liveness proof; their absence alone is not — corroborate with
  `hermes hooks doctor` or the tool results before calling the pipeline dead.
  The post tier logs `action:"revert"` when it actually reverted a mutation
  (v3 and earlier logged `allow` uniformly, so old guidance saying "no revert
  line is written" is stale for current `guard-main-revert.sh`).
- **Post tier reverts tracked files modified via terminal — via `guard-branch-pin.sh post`, not `revert-dirty-clone.sh`.** `revert-dirty-clone.sh`'s tracked-file branch is keyed on `TOOL_NAME` being `write`/`search_replace`/`create_file` only. A terminal append (`printf >> <tracked-file>`) does NOT go through that path; instead `guard-main-revert.sh` also calls `guard-branch-pin.sh post`, which reverts modified tracked files and removes untracked non-skill files for `run_terminal_command`. So a terminal write to a tracked file on the main clone **is** reverted (by the branch-pin post path), and the audit log shows `action:"revert"`. The old note (pre-`guard-branch-pin.sh` wiring) saying terminal writes leave the tree dirty is stale for the current pipeline. `revert-dirty-clone.sh` additionally handles NEW untracked files created by the write tool: an untracked `FILE_PATH` on the main clone is `rm -f`'d (not `git checkout`'d) and a marker dropped so the `pre_verify` nudge fires.
