---
name: graphify-wrapper
description: Create or fix wrapper repos in the mcp-arwaky collection (upstream source as a git submodule plus build/install scripts), and integrate with the Graphify-MCP knowledge graph system.
source: auto-skill
extracted_at: '2026-08-20T13:52:10.827Z'
---

# Wrapper repo pattern for mcp-arwaky + Graphify integration

Use this when the user asks to create or restructure a repo under `rakaarwaky` that wraps upstream source, or when they reference a sibling wrapper like `graphify-arwaky`, `lean-arwaky/lean-ctx`, or `ponytail-arwaky/ponytail`.

## When to use

- User says a repo is a "wrapper", "repo dalam repo", or references a sibling wrapper (`lean-arwaky/lean-ctx`, `ponytail-arwaky/ponytail`).
- A repo should aggregate upstream source under a local directory and build it locally.
- User asks to explore codebases via the Graphify knowledge graph (see Graphify integration below).
- Do NOT use this for forks. If the goal is just a GitHub fork, use `gh repo fork`.

## Structure (the actual pattern used by this collection)

Every wrapper in `mcp-arwaky` follows this shape — the upstream source is a **git submodule**, not regular tracked files:

```
<wrapper-repo>/
  <source-dir>/        # upstream source as a git submodule (e.g. graphify/, lean-ctx/, ponytail/)
  .gitmodules          # points <source-dir> at the upstream repo URL
  scripts/build.sh     # or scripts/install.sh — builds upstream into dist/ or equivalent
  dist/                # build artifact directory (gitignored)
  .gitignore           # ignores dist/, node_modules/, etc.
  *_local.json         # optional MCP client config snippets
  *_remote.json
```

Wrapper-specific files live at the repo root; upstream source lives in a nested submodule directory. Do NOT copy upstream source in as plain files and do NOT remove its `.git` — that contradicts how every wrapper in this collection is built.

## Procedure

1. Create the wrapper directory locally:
   - `mkdir -p <wrapper>/<source-dir> scripts`
   - Copy a wrapper template if available, e.g. `scripts/install.sh` and `.gitignore` from `lean-arwaky/` or `ponytail-arwaky/`.

2. Add the upstream source as a submodule:
   - `git submodule add <upstream-url> <source-dir>` inside the wrapper repo.
   - This creates `<source-dir>/` plus a `.gitmodules` entry; both are committed to the wrapper repo.
   - Reference `.gitmodules` of `contex7-arwaky`, `fetch-arwaky`, `lean-arwaky`, `ponytail-arwaky`, or `graphify-arwaky` for the exact entry shape.

3. Adjust `scripts/build.sh` or `scripts/install.sh`:
   - Point `REPO_DIR`/equivalent at the local `<source-dir>` path.
   - Ensure it creates `dist/` and produces the expected binary/output.
   - `lean-arwaky/scripts/install.sh` (Rust → `dist/lean-ctx` + `~/.local/bin`) and `contex7-arwaky/scripts/install.sh` (TypeScript → `dist/index.js`) are the canonical examples.

4. Initialize the wrapper repo:
   - `git init`
   - `git checkout -b main`
   - `git add -A` (includes `.gitmodules` and the submodule pointer)
   - `git commit -m "Add <source> source checkout"`
   - `git remote add origin https://github.com/rakaarwaky/<wrapper>.git`
   - `git push -u origin main`

5. Avoid committing large build artifacts unless the wrapper model explicitly requires them. `.gitignore` should cover `dist/`, `node_modules/`, and build output. If a large file was committed by mistake, remove it from the working tree and history, then commit and push.

6. Parent meta-repo `mcp-arwaky`:
   - Register the wrapper as a normal HTTPS submodule under `rakaarwaky` in the meta-repo `.gitmodules` (see `graphify-arwaky` entry).
   - Keep it public.

## Graphify integration

This skill also enables seamless integration with the Graphify knowledge graph system through the Graphify-MCP interface.

- The wrapper repo at https://github.com/rakaarwaky/graphify-arwaky contains the Graphify source as a submodule (`graphify/` → https://github.com/Graphify-Labs/graphify.git) plus `scripts/build.sh`.
- `scripts/build.sh` checks for `graphify/.git` and re-clones the upstream if missing.

### How to use

1. **Setup**: Ensure the Graphify-MCP server is running and configured in your Qwen Code settings.

2. **Usage**:
   - Use `/graphify` in your AI assistant to explore codebases
   - Use `/graphify query "<question>"` for specific queries
   - Use `/graphify path <A> <B>` to trace relationships between symbols
   - Use `/graphify explain <concept>` for focused concept exploration

3. **Maintenance**:
   - The wrapper repo is updated via `git submodule update --remote` inside `graphify-arwaky/`.
   - Build scripts handle dependency management and configuration.
   - Documentation is maintained in the wrapper repo's README.

## Anti-patterns (rejected shapes for this collection)

- Do not create a fork unless the user explicitly asks for a fork.
- Do not treat the upstream source as regular tracked files or delete its `.git` — this collection uses submodules.
- Do not commit upstream git metadata of *other* repos, binary artifacts, or build output into the wrapper.

## Sibling references

- `lean-arwaky/lean-ctx` — canonical Rust wrapper example (submodule + `scripts/install.sh` → `dist/`).
- `ponytail-arwaky/ponytail` — canonical Node/TypeScript wrapper example (submodule + `scripts/install.sh` + `*_local.json`/`*_remote.json`).
- `graphify-arwaky/graphify` — canonical Graphify wrapper (submodule + `scripts/build.sh`).
