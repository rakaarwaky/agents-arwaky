# agents-arwaky — Restructure & Hardening Plan (v2: Hardened)

Status: **READY FOR EXECUTION — Improved with DevOps Best Practices**

This plan merges DevOps audit findings, repo consolidation, and production-grade software engineering best practices. It restructures wrapper repositories into top-level submodules (`vendor/`) and clean orchestration glue (`tools/`), eliminates brittle hardcoded paths, introduces automated validation/CI, and centralizes licensing and configuration.

---

## Architecture & Layout Overview

```
agents-arwaky/
├── .github/
│   └── workflows/
│       └── ci.yml                     # Secret scan, shellcheck, JSON validation, submodule smoke test
├── vendor/                            # Direct 1-level-deep submodules -> upstream source
│   ├── context7/                      # → upstash/context7 @ 769c6cd2
│   ├── fetch-mcp/                     # → zcaceres/fetch-mcp @ 1ddb1a59
│   ├── lean-ctx/                      # → yvgude/lean-ctx @ 106f9044
│   ├── ponytail/                      # → DietrichGebert/ponytail @ 2ed6c52c
│   ├── graphify/                      # → Graphify-Labs/graphify @ b14b52e9
│   └── anytype-mcp/                   # → anyproto/anytype-mcp @ pinned commit
├── tools/                             # Portable build scripts & tool glue (no hardcoded paths)
│   ├── build-all.sh                   # Master build orchestrator
│   ├── generate-mcp-config.sh         # Generates unified mcpServers JSON for clients
│   ├── context7/                      # install.sh + template configs
│   ├── fetch-mcp/                     # install.sh + template configs
│   ├── lean-ctx/                      # install.sh + template configs
│   ├── ponytail/                      # install.sh + template configs
│   ├── graphify/                      # build.sh + template configs
│   └── anytype-mcp/                   # install.sh + template configs
├── Makefile                           # Developer ergonomic entrypoint (make build, make check, etc.)
├── THIRD_PARTY_LICENSES.md            # Centralized attribution, upstream URLs & licenses
├── LICENSE                            # MIT License for agents-arwaky
├── .gitattributes                     # Cross-platform line endings (* text=auto)
├── .gitmodules                        # Cleaned top-level submodules
└── README.md                          # Comprehensive documentation & quickstart
```

*Note: Original standalone repos remain untouched in their existing submodule locations (`blender-arwaky`, `cloudmail-arwaky`, `lint-arwaky`, `testing-arwaky`, `vision-arwaky`, `qwen-web-arwaky`, `codegraph-arwaky`).*

---

## Phase 0 — Safety Net & Baseline Check

**Goal:** Ensure absolute reversibility and confirm that current submodules resolve cleanly before any modifications.

1. **Tag baseline state:**
   ```bash
   git tag pre-restructure-2026-09-04
   git push origin pre-restructure-2026-09-04
   ```
2. **Scratch clone smoke test:**
   Perform a clean test checkout in a temporary directory to verify baseline submodule resolution:
   ```bash
   TMP_DIR=$(mktemp -d)
   git clone --recurse-submodules . "$TMP_DIR/verify-baseline"
   rm -rf "$TMP_DIR"
   ```

**Risk:** Zero. Read-only verification plus a safety tag.

---

## Phase 1 — Foundation Hardening & CI

**Goal:** Establish repository standards, fix known inconsistencies, and set up continuous automated verification.

1. **Add Root `LICENSE`:**
   - Add standard MIT License for `rakaarwaky/agents-arwaky`.
2. **Fix `.gitmodules` URL Inconsistency:**
   - Update `qwen-web-arwaky` entry from `https://github.com/rakaarwaky/qwen-web.git` to `https://github.com/rakaarwaky/qwen-web-arwaky.git`.
3. **Add `.gitattributes`:**
   - Set `* text=auto` and ensure shell scripts maintain `eol=lf`.
4. **Implement Robust CI (`.github/workflows/ci.yml`):**
   - **Secret Scanning:** `gitleaks/gitleaks-action` on pull request and push to `main`.
   - **Syntax & Lint Checks:**
     - `shellcheck` across all shell scripts in `tools/` and `scripts/`.
     - `jq` schema/syntax validation across all `.json` configuration templates.
   - **Submodule Smoke Test:** `git submodule update --init --recursive` check.
5. **Enable Branch Protection on `main` (via GitHub CLI):**
   - Require linear history.
   - Block force-pushes (`allow_force_pushes = false`).
   - Block branch deletion (`allow_deletions = false`).

**Risk:** Low. Reversible, no structural file moves yet.

---

## Phase 2 — Restructure Wrappers into `vendor/` + `tools/`

**Goal:** Eliminate redundant wrapper repository hops, flatten submodules directly to upstream, make all scripts 100% portable, and provide a unified build interface.

### Key Engineering Standards for Phase 2:
- **No Hardcoded Absolute Paths:** Every build script must resolve its repository paths dynamically:
  ```bash
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
  VENDOR_DIR="$REPO_ROOT/vendor/<tool>"
  DIST_DIR="$SCRIPT_DIR/dist"
  ```
- **Cross-Submodule Safe Migration:**
  Submodules cannot be moved with `git mv` directly. We use a safe 4-step migration per tool:
  1. Extract wrapper glue files (`scripts/*`, `*.json`) and stage into `tools/<name>/`.
  2. De-register and remove the old wrapper submodule:
     ```bash
     git submodule deinit -f <wrapper-arwaky>
     git rm -rf <wrapper-arwaky>
     ```
  3. Register the direct upstream submodule under `vendor/<name>`:
     ```bash
     git submodule add https://github.com/<upstream>/<repo>.git vendor/<name>
     git -C vendor/<name> checkout <pinned-commit>
     ```
  4. Refactor `tools/<name>/install.sh` and JSON templates to dynamic paths.

### Migration Matrix:

| Tool | Upstream Repository | Pinned Commit | Destination Vendor | Destination Tools |
|---|---|---|---|---|
| Context7 | `upstash/context7` | `769c6cd2` | `vendor/context7` | `tools/context7` |
| Fetch-MCP | `zcaceres/fetch-mcp` | `1ddb1a59` | `vendor/fetch-mcp` | `tools/fetch-mcp` |
| Lean-Ctx | `yvgude/lean-ctx` | `106f9044` | `vendor/lean-ctx` | `tools/lean-ctx` |
| Ponytail | `DietrichGebert/ponytail` | `2ed6c52c` | `vendor/ponytail` | `tools/ponytail` |
| Graphify | `Graphify-Labs/graphify` | `b14b52e9` | `vendor/graphify` | `tools/graphify` |
| Anytype-MCP | `anyproto/anytype-mcp` | Latest stable release | `vendor/anytype-mcp` | `tools/anytype-mcp` |

### Orchestrator & Configuration Generator:
1. **Master Build Orchestrator (`tools/build-all.sh` & `Makefile`):**
   - Provide targets: `make build-all`, `make build-<name>`, `make check`, `make clean`.
2. **Universal MCP Config Generator (`tools/generate-mcp-config.sh`):**
   - Reads installed tools and outputs a ready-to-use JSON block for:
     - Claude Desktop (`claude_desktop_config.json`)
     - Gemini CLI / Antigravity
     - Qwen Code
   - Automatically populates the current machine's absolute paths into output configurations without committing local machine paths to git.

**Risk:** Medium. Mitigated by Phase 0 snapshot tag, deterministic submodule checkout, and verification steps.

---

## Phase 3 — Documentation, Attribution & Licensing

**Goal:** Ensure clear documentation, maintain legal license compliance, and eliminate stale references.

1. **Centralized `THIRD_PARTY_LICENSES.md`:**
   - Explicit table documenting:
     - Submodule name and upstream repository URL
     - Pinned commit / release version
     - Upstream license type (MIT, Apache 2.0, MPL 2.0, etc.)
     - Full copy of required upstream notices/licenses.
2. **README.md Overhaul:**
   - Updated architecture diagram and repository layout.
   - Step-by-step Quickstart guide (`git clone --recurse-submodules`, `make build-all`).
   - Instruction on generating MCP client configurations via `make config`.
   - Remove stale references (`caveman-arwaky`, `graphyarwaky`).
3. **Template Environment & Ignore Files:**
   - Ensure root `.gitignore` ignores build outputs (`dist/`, `target/`, `node_modules/`, `*.local.json`).

**Risk:** None. Documentation and hygiene.

---

## Phase 4 — Decommission Old Wrapper Repositories

**Goal:** Safely retire deprecated individual wrapper repos without breaking external links.

1. **Deprecation Notice Commit:**
   - Push a final commit to each of the 6 wrapper repos (`contex7-arwaky`, `fetch-arwaky`, `lean-arwaky`, `ponytail-arwaky`, `graphify-arwaky`, `anytype-arwaky`):
     - Replace `README.md` with:
       ```markdown
       # Deprecated & Relocated
       This repository has been consolidated directly into [rakaarwaky/agents-arwaky](https://github.com/rakaarwaky/agents-arwaky).
       Active maintenance and build tools live under `vendor/` and `tools/` in the main monorepo.
       ```
2. **Archive Repositories:**
   - Mark each wrapper repository as **Archived (Read-Only)** on GitHub via `gh repo archive rakaarwaky/<repo> --yes`.

**Risk:** None to `agents-arwaky`. Preserves git history and stars while signaling clear deprecation.

---

## Phase 5 — Verification & End-to-End Testing

**Goal:** Formally prove everything works cleanly from a completely fresh environment.

1. **Automated Verification Script (`tools/verify.sh`):**
   - Check all submodules are initialized and at expected commits.
   - Run `shellcheck` across all shell scripts.
   - Validate all JSON configuration templates with `jq`.
2. **Clean-Room Clone Test:**
   - Clone repository to a temporary directory:
     ```bash
     git clone --recurse-submodules https://github.com/rakaarwaky/agents-arwaky.git /tmp/agents-arwaky-clean
     ```
3. **Build Smoke Tests:**
   - Execute builds for tools in the clean clone to verify no dependencies or relative paths are broken.
4. **CI Verification:**
   - Verify GitHub Actions workflow runs cleanly on push/PR.

---

## Execution Checklist

- [ ] **Phase 0:** Tag `pre-restructure-2026-09-04` & push to remote.
- [ ] **Phase 1:** Add root `LICENSE`, `.gitattributes`, fix `qwen-web-arwaky` URL, add `.github/workflows/ci.yml`.
- [ ] **Phase 2:** Execute submodule migration to `vendor/` + `tools/`, remove hardcoded paths, add `Makefile` and `tools/build-all.sh`.
- [ ] **Phase 3:** Create `THIRD_PARTY_LICENSES.md` and rewrite `README.md`.
- [ ] **Phase 4:** Push deprecation notices and archive the 6 wrapper repositories.
- [ ] **Phase 5:** Run `tools/verify.sh` and confirm CI passes.
