# Isolation Recipes

Phase D/C setup. Shared artifact dirs cause phantom sibling errors and lock/RAM
contention. One Orca worktree = one artifact dir. Never fall back to a shared dir.

The pattern is the same in every ecosystem:

1. After `ORCA worktree create --json`, take `result` path (or full `id:<repoId>::<path>`).
2. Create a per-worktree output directory outside the source tree (or gitignored inside it).
3. Point the build tool at that directory for this worktree only.
4. Persist the setting in the worktree so every child inherits it.
5. Tell every child to source/activate the env before the first build.
6. Gitignore the artifact dirs once per repo.

Defaults below assume Orca worktree path `$WT` and name `issue-NNN`.
Adjust names to match the repo.

## Rust / Cargo

1. Ensure the repo has an init helper (create once if missing). It must write
   `target-issue-*/` as `CARGO_TARGET_DIR` **and** preserve any existing
   `rustc-wrapper = "sccache"` / mold linker flags — never overwrite with a bare
   `[build] target-dir` only:

   ```bash
   # WT = path from ORCA worktree create --json
   bash "$REPO_ROOT/.worktrees/common/init-cargo-isolation.sh" "$WT"
   ```

   Minimum template when no script exists yet:

   ```toml
   # $WT/.cargo/config.toml
   [build]
   target-dir = "/abs/path/to/repo/target-issue-NNN"

   # Preserve if present on main:
   # rustc-wrapper = "sccache"
   # [target.x86_64-unknown-linux-gnu]
   # linker = "clang"
   # rustflags = ["-C", "link-arg=-fuse-ld=mold"]
   ```

   ```bash
   # $WT/.cargo/env.sh
   export CARGO_TARGET_DIR="/abs/path/to/repo/target-issue-NNN"
   ```

2. `.gitignore` must include `target-issue-*/` (add once per repo).
3. Child brief: `source .cargo/env.sh` before any `cargo` command.
4. Targeted only: `cargo check/test/clippy -p <crate>` — never workspace-wide gate scripts.

## Node / pnpm (and npm/yarn)

Per-worktree install or cache isolation:

```bash
# Prefer a per-worktree store so parallel installs do not thrash the shared cache
cd "$WT" && pnpm install --store-dir "$REPO_ROOT/.pnpm-store-issue-NNN"
# or
cd "$WT" && npm ci --cache "$REPO_ROOT/.npm-cache-issue-NNN"
```

Gitignore `.pnpm-store-issue-*/` and `.npm-cache-issue-*/` once per repo.
Child brief: run package scripts only from the worktree root (`pnpm -C <wt> test -- <pkg>`).

## Python / uv

```bash
# venv lives inside the Orca worktree; never share .venv across worktrees
cd "$WT" && uv sync
```

If the project also writes a shared build cache (`.ruff_cache`, `.mypy_cache`,
`__pycache__` of editable installs), point each child at a worktree-local path:

```bash
export RUFF_CACHE_DIR="$PWD/.ruff_cache"
export MYPY_CACHE_DIR="$PWD/.mypy_cache"
```

Targeted only: `uv run pytest modules/<feat>/tests -q` — not the whole workspace gate.

## Child brief fragment (copy into every brief)

```text
Build isolation:
- Work ONLY inside the assigned Orca worktree path <WT>.
- Before the first build/check: source <WT>/.cargo/env.sh  # or the ecosystem equivalent
- Never set the shared repo artifact dir (target/, dist/, .venv at repo root) from this worktree.
- Targeted checks only. If a cold isolated build fails, retry once; do not switch to a shared dir.
```
