---
ingested: 2026-11-07
type: session-note
session: agents-arwaky git submodule repair (Grok Build + Raka)
---

# Session: Repair of broken internal/ git submodules

Repo: /home/raka/agents-arwaky
Date: 2026-11-07

## Symptom

Running `git switch main` inside any of `internal/blender-arwaky`,
`internal/lint-arwaky`, `internal/qwen-web-arwaky`, `internal/vision-arwaky`
failed with:

    fatal: not a git repository:
    /home/raka/agents-arwaky/internal/lint-arwaky/../../.git/modules/lint-arwaky

`git submodule status` in the parent repo gave the same fatal.

## Diagnosis

- All four paths are real submodules of the parent repo. `.gitmodules` maps:
  - internal/blender-arwaky  -> https://github.com/rakaarwaky/blender-arwaky.git
  - internal/lint-arwaky     -> https://github.com/rakaarwaky/lint-arwaky.git
  - internal/qwen-web-arwaky -> https://github.com/rakaarwaky/qwen-web-arwaky.git
  - internal/vision-arwaky   -> https://github.com/rakaarwaky/vision-arwaky.git
- Each internal/<name> directory holds a normal `.git` *file* containing
  `gitdir: ../../.git/modules/<name>` (standard submodule pointer layout).
- The directories `.git/modules/<name>` were missing or contained only a
  nested `.git` subdirectory (from a failed `git init` repair attempt),
  so the pointer resolved to nothing.
- Parent repo `git ls-tree HEAD` shows each path as mode 160000 (gitlink):
  - internal/blender-arwaky   commit bf7691ce6027ae242109b5595efda2cdd1074152
  - internal/lint-arwaky      commit 6eac44375e7e4037dc7803aa8ebbf87756528003
  - internal/qwen-web-arwaky  commit f04388cd85a36772ca95d02075deadcd66ffd889
  - internal/vision-arwaky    commit 66c0b3f506ee736fc66aea46ffc0e7a0fe36c2fd

## Attempted fixes and why they failed

1. `git submodule update --init internal/<name>` - failed; the parent's
   gitdir layout was already broken so init had nothing valid to work from.
2. `git init .git/modules/<name>` - WRONG. `git init` called on a path that
   is inside the parent's `.git` directory creates a *nested* gitdir:
   `.git/modules/<name>/.git` (confirmed by `ls` - the directory only
   contains a `.git` subdirectory). The pointer
   `gitdir: ../../.git/modules/<name>` then points at a directory that is
   not itself a gitdir. Every subsequent attempt re-nested again.
3. `git -C internal/<name> ...` immediately after - still failed because
   the nested `.git` remained.

## Working fix (applied)

For each of blender-arwaky, qwen-web-arwaky, vision-arwaky
(lint-arwaky was already repaired mid-session using the same technique):

1. `rm -rf .git/modules/<name>`
2. `git clone --bare --quiet https://github.com/rakaarwaky/<name>.git .git/modules/<name>`
   - produces a *flat* gitdir (no nested .git): config, HEAD, objects/,
     refs/, packed-refs, description, hooks/
3. `git -C .git/modules/<name> config core.bare false`
   - bare clone sets core.bare=true; submodule gitdir must be non-bare so
     it can hold an index and track a worktree.
4. `git -C .git/modules/<name> symbolic-ref HEAD refs/heads/main`
5. `echo "gitdir: ../../.git/modules/<name>" > internal/<name>/.git`
   - rewrites the pointer file with the standard relative path.

Verification:
- `git -C internal/<name> rev-parse --show-toplevel` -> /home/raka/agents-arwaky/internal/<name>
- `git -C internal/<name> branch --show-current` -> main
- `git -C internal/lint-arwaky switch main` -> "Switched to branch 'main'"

## Post-repair state and one open item

- blender-arwaky, lint-arwaky, vision-arwaky: on branch main, matching
  parent's pinned commit. `git submodule status` clean.
- qwen-web-arwaky: now on main, but its HEAD is 19cbe39c9a702a54d9977c80a9512b988865f726
  (v6.5.2-201-g19cbe39) while the parent pins f04388cd. Parent `git status`
  therefore shows ` M internal/qwen-web-arwaky`.
  Two options (not yet decided by user):
  - Keep local 19cbe39 and commit the new gitlink in the parent repo.
  - Snap back: `git -C internal/qwen-web-arwaky switch f04388cd`
    or from parent root `git submodule update -- internal/qwen-web-arwaky`.
- Each submodule's `git status --short` shows D lines for tracked files
  (e.g. .codacy.yaml, .agents/rules/...) - this is index-vs-worktree drift
  from the restored gitdir, files still exist on disk, not real deletions.

## Related observations

- `.gitmodules` sets `ignore = dirty` on all four submodules, so the parent
  repo reports clean status even when a submodule worktree has local edits.
- vendor/* submodules (context7, fetch-mcp, codegraph, omniroute, 9router)
  and skills/automation/brave-automation/app also live in .git/modules;
  9router's gitdir was also missing (same fatal pattern). Not repaired in
  this session.
