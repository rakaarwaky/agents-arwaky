---
name: issue-batch-fanout
description: Use when fixing many GitHub issues in parallel worktrees.
version: 1.0.0
author: Hermes
license: MIT
metadata:
  tags:
    - GitHub
    - Issues
    - Delegation
    - Worktrees
    - Triage
  related_skills:
    - github-issues
    - coding-agent-delegation
---

# Issue Batch Fan-out

## When to Use

- The user asks to audit many open issues at once ("which open issues can be closed").
- The user asks to fix a batch of issues with isolation ("1 issue 1 worktree", parallel subagents).
- A repo carries 10+ filed-audit issues (ARCH/UX/Data style) needing per-issue verification against current HEAD.

End-to-end pipeline for a repo with many open issues: verify which can close, ask the
remaining decisions as one quiz, then fan out 1 issue → 1 worktree → 1 subagent.
Default until the user says otherwise: subagents commit locally only — NO push, NO PR.

After a wave of PRs merges, rebase every still-open PR branch onto the main tip
before letting CI re-run: a stale base fails self-lint and format against
already-merged code, and the fix is a one-command rebase, not a debug session.
Rebase one branch at a time and confirm `git status` is clean before
force-pushing — a blind rebase-and-force-push loop across worktrees leaves
dirty rebase states that block the next wave.

## Sibling-PR conflict shape (the expensive one)

When PR A (long-lived refactor, e.g. an API-seam change) is rebased onto main
and main has since merged PR B (built against the OLD API), the rebase is
usually textually clean but fails to compile: B's new file still calls the
helper A deleted. Git has no conflict markers to point at it — you get
`E0432: unresolved import` / `E0609: no field` for symbols that no longer exist.

Diagnose with: `grep -rn 'fn <deleted_symbol>' crates/` returning nothing while
`<new_file>.rs` still references it. Fix by porting B's call sites onto A's
replacement, matching the pattern already used elsewhere in the same PR
(`git show origin/main:<file> | grep '<replacement>'`). Do not restore the
deleted symbol — A's removal is the intent. Expect N call sites, not one, and
expect a trailing-comma/`}));` mismatch when hand-editing a conflict block:
compare against a sibling `all.extend(run_isolated(...))` call for the exact
closer shape.

Verify a CI failure is real before debugging it: `gh api .../jobs/<id>/logs`
shows the SHA GitHub built, which is often older than the branch head if a fix
was pushed after the run started. Confirm with
`gh api repos/O/R/actions/runs/<run> -q .head_sha` and
`git show origin/<branch>:<file>` before treating a "still failing" report as live.
Also: scan a worktree by `cd`ing INTO it. Running the checker against
`.worktrees/issue-N` from the repo root reports phantom violations (broken
relative paths → phantom E0425 unresolved-name), which reads exactly like a
broken branch.

## Phase A — Triage: "which open issues can actually be closed?"

Never close on a `status: done` label, the audit date, or a merged PR's `Closes #N`
line — GitHub can silently close only a fraction of the issues one PR body declares,
while the fix itself did land. Verify against the current tree:

1. Dump all open issues with bodies once, read the file in windows:
   `gh issue list --state open --limit 300 --json number,title,body,labels,updatedAt --jq '.[] | "### #\(.number)\n\(.title)\n\(.body)\n"' > /tmp/issues.md`
2. Check per-issue real state: `gh issue view N --json state,closed` — OPEN despite a
   merged "Closes #N" means the closer didn't fire; still verify the fix by code
   inspection before closing manually with an evidence comment.
3. Verify every claim in the code at HEAD: grep the exact file:line the issue cites.
   Issue text still matching the code = still valid, keep open. A fix may have landed
   in an unrelated PR: `git log --oneline --since <issue-date> -- <path>`.
4. Cross-references when gh is old (rejects `stateReason` / `closingIssuesReferences`;
   the error prints the valid fields): use
   `gh api repos/{o}/{r}/issues/N/timeline --paginate --jq '[.[]|select(.event=="cross-referenced")|.source.issue.number]|unique'`
   and grep `gh pr list --state merged --json number,body` for `Closes #N`.
5. Close only verified ones, each with a comment stating the evidence (file:line or
   command output).

## Phase B — Ask decisions as ONE quiz before spawning work

Issues the code cannot answer (versioning policy, whether to enforce a process gate, a
bug whose fix may already be in main) need the user's decision, not a guess. Collect
all open questions and ask them in ONE `clarify` call as an interactive quiz: one
question per decision, recommended option first, choices concrete enough to execute
directly from the answer. Do not start implementation before the quiz is answered.

## Phase C — Fan-out: 1 issue → 1 worktree → 1 subagent

1. Create all worktrees from current main HEAD in one loop:
   `git worktree add -b <type>/issue-N .worktrees/issue-N HEAD` — verify `.worktrees`
   is gitignored first (`git check-ignore -v .worktrees/`).
2. Write decisions + per-issue evidence to the repo's session state file
   (e.g. `.agents/session-notes.md`). It is the source for every child's `context:` —
   children see nothing else of this conversation.
3. Spawn in waves capped at the delegation concurrency limit (typically 10), one
   `delegate_task` entry per issue. State these rules in EVERY child brief:
   - work ONLY inside the assigned worktree; never touch other worktrees or shared state dirs;
   - **per-worktree build isolation** — each worktree has its own `CARGO_TARGET_DIR`
     (see Phase F); source `.cargo/env.sh` in the worktree before any cargo command;
     never set `CARGO_TARGET_DIR` to the shared `<repo>/target` from inside a worktree;
   - targeted checks only (`cargo check/test/clippy -p <crate>`); never workspace-wide gate scripts — they serialize and slow every sibling;
   - local commits allowed (conventional messages), NO push, NO PR, no `gh` writes;
   - close the report with: files changed, mechanism, verification command + real output, commit sha.
4. For "verify first, fix if still broken" issues, the child brief asks for a verdict
   (fixed-on-main / still-broken) plus the regression test pinning the behavior —
   never for issue closure (the parent decides closure).

## Phase D — Running the waves: build isolation

Each worktree MUST use its own `CARGO_TARGET_DIR` (set up via Phase G below).
This eliminates two failure modes:
1. **Phantom compile errors** — a sibling worktree's half-built new symbols leak
   into a shared artifact cache, causing `E0063: missing field` in unrelated worktrees.
   This cost 3 child re-dispatches in one session.
2. **Contention** — parallel builds on one target dir exhaust file locks / RAM
   (mold exit 254, 60s lock waits).

First build in an isolated dir is slower (no shared sccache cache across
worktrees), but that cost is always less than debugging phantom failures.
If a child's build genuinely fails on a cold isolated dir, retry once; do NOT
fall back to the shared target dir.

## Phase E — Verify children before reporting

A child's summary is a self-report, not evidence. For each finished child: `git log
--oneline main..HEAD` and `git status` inside its worktree, read the changed code at
the cited file:line, re-run the key test yourself when the claim is load-bearing (e.g.
"already fixed on main"). Only then tell the user what landed. Wave N+1 spawns after
wave N's results arrive — stacking all waves at once worsens Phase D contention.

## Phase G — Per-worktree build isolation setup

Before spawning any child on a new worktree, set up isolated build dirs:

1. Create `.cargo/config.toml` + `.cargo/env.sh` in each worktree:
   ```bash
   bash .worktrees/common/init-cargo-isolation.sh .worktrees/issue-NNN
   ```
   (script creates `target-<worktree-name>/` as `CARGO_TARGET_DIR` and writes
   both files; re-run on existing worktrees to fix any stale shared-target config)

2. Each child brief must say: `source .cargo/env.sh` before any cargo command.

3. `.gitignore` must include `target-issue-*/` (add once per repo).

4. **Preserve sccache+mold** — the `.cargo/config.toml` in this repo carries
   `rustc-wrapper = "sccache"` + mold linker flags. The init script includes these
   in its output template; never overwrite with a bare `[build] target-dir` only.

## Overlap note

Single-issue triage commands live in `github-issues` (user-owned); this skill owns the
verify→quiz→fan-out pipeline end to end.
