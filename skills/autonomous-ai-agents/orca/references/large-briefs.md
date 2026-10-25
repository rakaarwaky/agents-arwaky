# Delivering large briefs to Orca worktree agents

`ORCA terminal send --text` and `ORCA worktree create --prompt` take the brief
as a shell argument. For briefs beyond a few KB — full design docs, multi-PR
plans, specs with embedded code blocks — inlining the text into the command
fragments on quotes and bloats the process argv. Use the file-in-worktree
pattern instead.

## When to use

- The brief is a full document (design doc, PR plan, acceptance criteria) that
  lives in a file the user pointed at.
- The brief exceeds ~4 KB, or contains shell-sensitive characters that would
  need careful quoting.
- The worktree is a separate checkout and the agent has no prior context.

Inline `--prompt "…"` is fine for short, single-paragraph instructions.

## Steps

1. **Create the worktree with the agent** (no `--prompt`):
   ```bash
   ORCA worktree create --repo id:<repoId> --name <task> --agent grok \
     --no-parent --surface terminal --json
   ```
   Note the `result.launch.outcome.handle` (the terminal handle).

2. **Wait for the TUI to be idle** before sending anything — a prompt typed
   into a still-starting agent is lost:
   ```bash
   ORCA terminal wait --terminal <handle> --for tui-idle --timeout-ms 90000 --json
   ```

3. **Copy the brief into the worktree root:**
   ```bash
   cp /path/to/design-doc.md <worktreePath>/BRIEF.md
   ```
   The worktree path comes from `result.worktree.path` in the create response.
   The agent's cwd is the worktree root, so `BRIEF.md` is discoverable without
   a full path.

4. **Send a short pointer prompt** via `terminal send`:
   ```bash
   ORCA terminal send --terminal <handle> --text \
     'Your full task brief is in BRIEF.md at the root of this worktree (cwd). \
      Read it first, then implement every PR in the PR Plan as one continuous \
      piece of work. Follow the design doc constraints: run the full CI gates \
      after each PR group and commit each PR group atomically. Do not open or \
      merge any PR. Start now.' \
     --enter --json
   ```
   The `accepted: true` in the receipt confirms the input reached the terminal.

5. **Verify the agent picked it up** with `terminal read` — the tail should
   show the agent reading `BRIEF.md` and starting to think or act:
   ```bash
   ORCA terminal read --terminal <handle> --limit 40 --json
   ```
   If the tail shows no activity after a reasonable wait, re-check the handle
   and retry the wait.

## Pitfalls

- **Do not skip the TUI-idle wait.** A prompt sent while the agent TUI is
  still booting is dropped. `satisfied: false` → retry with a larger
  `--timeout-ms`.
- **The brief file is the source of truth, not the terminal echo.** The
  terminal tail shows the pointer prompt, not the full brief. Verify the agent
  reads `BRIEF.md` (the read step appears in the tail), not that the terminal
  contains the full text.
- **Do not embed the full brief in the pointer prompt.** That defeats the
  purpose — the pointer must be short enough to pass as a single `--text`
  argument safely.
- **F-string gotcha when building the brief in Python.** If the design doc
  contains literal `{layer}_{concern}_{role}` or similar brace expressions, an
  f-string will try to interpolate them and raise `NameError`. Build the
  header and design-doc parts separately and concatenate with `+`, or use
  `.replace()` / string concatenation instead of f-strings for the doc body.
