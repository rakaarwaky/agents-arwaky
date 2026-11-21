# Step 3: Spawn Grok Sessions with `/implement`

Create isolated Orca worktrees for each planned issue group, configure build isolation, and spawn a new Grok Build session running `/implement`.

The orchestrator workflow is completely unified: whether the orchestrator running `issue-worker` is Hermes or Grok, it coordinates the worktrees and delegates implementation to new Grok Build sessions.

## 3a: Resolve Orca CLI & Repository ID

Always resolve the Orca binary by its dynamically mounted or path-resolved location:

```bash
ORCA="$(command -v orca-ide)"
```

Do not rely on `$ORCA` being exported or bare `orca`. Retrieve the current repository ID:

```bash
REPO_ID="$("$ORCA" repo list --json | jq -r '.[0].id // empty')"
REPO_PATH="$(pwd)"
```

## 3b: Create Worktree per Group

For each group planned in Step 2 (within the active wave):

```bash
"$ORCA" worktree create \
  --repo "id:$REPO_ID" \
  --name "$GROUP_SLUG" \
  --agent grok \
  --no-parent \
  --surface terminal \
  --json
```

Capture output variables:
- `WT_PATH`: `result.worktree.path`
- `WT_ID`: `result.worktree.id`
- `WT_BRANCH`: `result.worktree.branch` (strip `refs/heads/`)
- `TERMINAL_HANDLE`: terminal handle for the spawned Grok session.

If Orca worktree creation fails, report the error verbatim and halt. Do not work directly in the root workspace or main branch.

## 3c: Establish Build Isolation

Prevent sibling build lock contention and cache corruption by ensuring each worktree uses dedicated, isolated output paths:

- **Rust / Cargo**:
  Write `$WT_PATH/.cargo/config.toml` or `$WT_PATH/.cargo/env.sh`:
  ```bash
  mkdir -p "$WT_PATH/.cargo"
  cat << 'EOF' > "$WT_PATH/.cargo/env.sh"
  export CARGO_TARGET_DIR="$PWD/target-isolated"
  EOF
  ```
- **Python / uv / virtualenv**:
  Ensure local environment and caches remain local to the worktree:
  ```bash
  export RUFF_CACHE_DIR="$WT_PATH/.ruff_cache"
  export MYPY_CACHE_DIR="$WT_PATH/.mypy_cache"
  ```
- **Node / pnpm / npm**:
  Use isolated store or cache directories (e.g. `--store-dir "$WT_PATH/.pnpm-store"`).

## 3d: Wait for TUI Idle & Dispatch `/implement`

A prompt sent while the Grok TUI is initializing is dropped. Always wait for TUI idle:

```bash
"$ORCA" terminal wait --terminal "$TERMINAL_HANDLE" --for tui-idle --timeout-ms 60000 --json
```

When `satisfied: true`, dispatch the `/implement` brief composed in Step 2:

```bash
"$ORCA" terminal send \
  --terminal "$TERMINAL_HANDLE" \
  --text "$BRIEF" \
  --enter \
  --json
```

Confirm `"accepted": true` in the output JSON.

**Strict Protocol**:
After sending the brief, do not send follow-up questions, status inquiries, or intermediate messages to the running Grok session.

## 3e: Verify Process Turn

Read the terminal once to confirm Grok has received and started processing the `/implement` turn:

```bash
"$ORCA" terminal read --terminal "$TERMINAL_HANDLE" --cursor 0 --limit 100 --json
```

If the input was not accepted into a running turn, re-send once. Once confirmed, proceed to Step 4 (`step-4-wait-and-verify.md`).
