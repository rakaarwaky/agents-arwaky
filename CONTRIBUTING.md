# Contributing to agents-arwaky

Thank you for your interest in contributing to **agents-arwaky**! This document provides comprehensive, step-by-step guides for contributing code, maintaining the orchestration tooling, and specifically:
- [Adding a New Vendor Tool](#-adding-a-new-vendor-tool-step-by-step)
- [Removing a Vendor Tool](#-removing-a-vendor-tool-step-by-step)
- [Updating an Existing Vendor Tool](#-updating-an-existing-vendor-tool)
- [Contributing to Internal Agents](#-contributing-to-internal-agents-internal)
- [Quality Verification & Pull Request Process](#-quality-verification--pr-process)

---

## 🏛️ Architecture & Principles to Keep in Mind

Before making changes, please review our core architectural rules:

1. **Distrobox First-Class & Zero Host Contamination:**
   - All toolchains (Node, Rust, Python, Bun, C-compilers) run inside the rootless `agents-env` container.
   - Do **NOT** install global packages on the host machine.
   - All tools are compiled inside containerized XDG prefixes and exported to `~/.local/bin/` via `distrobox-export`.

2. **Strict XDG Base Directory Compliance:**
   - Never write persistent data or cache to the repository directory.
   - Use [`tools/lib/xdg.sh`](tools/lib/xdg.sh) helper functions (`xdg_data_dir`, `xdg_config_dir`, `xdg_cache_dir`).
   - Binary launchers are placed into `${XDG_BIN_HOME:-$HOME/.local/bin}` (host) or `${XDG_DATA_HOME}/agents-arwaky/internal-bin` (container).

3. **Single Source of Truth (SSOT):**
   - [`tools/arwaky/manifest.json`](tools/arwaky/manifest.json) is the definitive registry of all tools. Any addition or deletion must update this file.

---

## 🛠️ Development Setup

1. **Clone the repository with submodules:**
   ```bash
   git clone --recurse-submodules https://github.com/rakaarwaky/agents-arwaky.git
   cd agents-arwaky
   ```

2. **Verify host prerequisites:**
   ```bash
   make setup
   ```
   *(Checks for Podman/Docker and Distrobox, offering automated installation via system package managers).*

3. **Provision the environment:**
   ```bash
   make install
   ```

4. **Verify installation:**
   ```bash
   arwaky doctor
   arwaky status
   ```

---

## ➕ Adding a New Vendor Tool (Step-by-Step)

Adding an upstream community tool or MCP server involves a structured, repeatable 9-step pipeline.

### Step 1: Register Upstream as a Git Submodule

Add the upstream git repository under the `vendor/` directory:

```bash
# Syntax: git submodule add <repository-url> vendor/<tool-name>
git submodule add https://github.com/example-org/my-cool-tool.git vendor/my-cool-tool
```

Pin or checkout the desired release tag or stable commit:
```bash
cd vendor/my-cool-tool
git checkout v1.2.0  # or specific stable commit hash
cd ../..
```

Ensure `.gitmodules` marks the submodule with `ignore = dirty` so local build artifacts inside the submodule don't clutter git status:
```ini
[submodule "vendor/my-cool-tool"]
	path = vendor/my-cool-tool
	url = https://github.com/example-org/my-cool-tool.git
	ignore = dirty
```

---

### Step 2: Create Tool Installer Script (`tools/<tool-name>/install.sh`)

Create a dedicated directory under `tools/` and add an `install.sh` script:

```bash
mkdir -p tools/my-cool-tool
touch tools/my-cool-tool/install.sh
chmod +x tools/my-cool-tool/install.sh
```

The script must:
- Start with `#!/usr/bin/env bash` and `set -euo pipefail`.
- Source `tools/lib/xdg.sh`.
- Install or compile the tool into `$XDG_DATA_HOME/<tool-name>/`.
- Create an executable wrapper/launcher in `$XDG_BIN_HOME/<binary-name>`.

#### Template A: For Python Tools (via `uv`)
```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

VENDOR_DIR="$REPO_ROOT/vendor/my-cool-tool"
TARGET_DIR="$XDG_DATA_HOME/my-cool-tool"
LAUNCHER="$XDG_BIN_HOME/my-cool-tool-mcp"

if [ ! -d "$VENDOR_DIR" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  echo "Run 'git submodule update --init vendor/my-cool-tool' first."
  exit 1
fi

echo ">>> Setting up my-cool-tool in XDG Data Directory ($TARGET_DIR)..."
mkdir -p "$TARGET_DIR"

if command -v uv >/dev/null 2>&1; then
  if [ ! -d "$TARGET_DIR/venv" ]; then
    uv venv "$TARGET_DIR/venv"
  fi
  echo ">>> Installing dependencies with uv..."
  uv pip install --quiet -e "$VENDOR_DIR" --python "$TARGET_DIR/venv"
else
  echo "Error: uv is required for Python installations." >&2
  exit 1
fi

echo ">>> Generating executable launcher at $LAUNCHER..."
cat <<'EOF' > "$LAUNCHER"
#!/usr/bin/env bash
set -euo pipefail
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/my-cool-tool"
exec "$DATA_DIR/venv/bin/my-cool-tool" "$@"
EOF
chmod +x "$LAUNCHER"

echo ">>> Successfully installed my-cool-tool -> $LAUNCHER"
```

#### Template B: For Node / TypeScript Tools (via `pnpm` or `npm`)
```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

VENDOR_DIR="$REPO_ROOT/vendor/my-cool-tool"
TARGET_DIR="$XDG_DATA_HOME/my-cool-tool"
LAUNCHER="$XDG_BIN_HOME/my-cool-tool-mcp"

if [ ! -d "$VENDOR_DIR" ] || [ ! -f "$VENDOR_DIR/package.json" ]; then
  echo "Error: Upstream source not found at $VENDOR_DIR."
  exit 1
fi

echo ">>> Building my-cool-tool..."
cd "$VENDOR_DIR"
pnpm install --ignore-scripts
pnpm run build

mkdir -p "$TARGET_DIR"

echo ">>> Creating launcher at $LAUNCHER..."
cat <<EOF > "$LAUNCHER"
#!/usr/bin/env bash
set -euo pipefail
exec node "$VENDOR_DIR/dist/index.js" "\$@"
EOF
chmod +x "$LAUNCHER"

echo ">>> Successfully installed my-cool-tool -> $LAUNCHER"
```

#### Template C: For Rust Tools (via `cargo`)
```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=/dev/null
source "$REPO_ROOT/tools/lib/xdg.sh"

VENDOR_DIR="$REPO_ROOT/vendor/my-cool-tool"
TARGET_DIR="$XDG_DATA_HOME/my-cool-tool"
LAUNCHER="$XDG_BIN_HOME/my-cool-tool"

mkdir -p "$TARGET_DIR/bin"

if command -v cargo >/dev/null 2>&1; then
  echo ">>> Building my-cool-tool from source with cargo..."
  cargo install --path "$VENDOR_DIR" --root "$TARGET_DIR"
  cp "$TARGET_DIR/bin/my-cool-tool" "$LAUNCHER"
  chmod +x "$LAUNCHER"
else
  echo "Error: cargo not found." >&2
  exit 1
fi

echo ">>> Successfully installed my-cool-tool -> $LAUNCHER"
```

---

### Step 3: Register in Manifest (`tools/arwaky/manifest.json`)

Add the tool entry to the `"tools"` array in [`tools/arwaky/manifest.json`](tools/arwaky/manifest.json):

```json
{
  "id": "my-cool-tool",
  "category": "vendor",
  "binary": "my-cool-tool-mcp",
  "isMcp": true,
  "description": "Short explanation of tool capabilities",
  "path": "vendor/my-cool-tool"
}
```

- `id`: Unique identifier used for `arwaky run <id>` and `arwaky install <id>`.
- `category`: Must be `"vendor"` for upstream tools (`"internal"` is reserved for in-house agents).
- `binary`: Name of the executable script generated in `$XDG_BIN_HOME`.
- `isMcp`: `true` if the binary exposes a Model Context Protocol server over stdio/SSE; `false` otherwise.
- `description`: Single-line summary of functionality.
- `path`: Submodule directory path relative to repository root (`vendor/<tool-name>`).

---

### Step 4: Register in Master Build Script (`tools/build/build-all.sh`)

Open [`tools/build/build-all.sh`](tools/build/build-all.sh) and append your tool to the build sequence:

```bash
build_tool "my-cool-tool" "$TOOLS_DIR/my-cool-tool/install.sh"
```

---

### Step 5: Register in Binary Exporter (`tools/distrobox/export-bins.sh`)

To make the binary executable directly from the host terminal, register its binary name in the `TOOLS` array in [`tools/distrobox/export-bins.sh`](tools/distrobox/export-bins.sh):

```bash
TOOLS=(
  "context7-mcp"
  "fetch-mcp"
  "lean-ctx"
  "ponytail-mcp"
  "anytype-mcp"
  "codegraph-mcp"
  "my-cool-tool-mcp"   # <-- Add your binary here
)
```

---

### Step 6: Configure MCP Server Generation (If Applicable)

If your tool provides an MCP server (`isMcp: true`):

1. Edit [`tools/mcp/generate-config.sh`](tools/mcp/generate-config.sh) to include the server definition inside the JSON template:
   ```json
   "my-cool-tool": {
     "command": "my-cool-tool-mcp"
   }
   ```
2. If your tool needs arguments or environment variables:
   ```json
   "my-cool-tool": {
     "command": "my-cool-tool-mcp",
     "args": ["serve"],
     "env": {
       "SOME_KEY": "some_value"
     }
   }
   ```
3. Add the vendor name to the distribution loop in `generate-config.sh`:
   ```bash
   for vendor in context7 fetch-mcp lean-ctx ponytail anytype-mcp codegraph my-cool-tool; do
   ```
4. Regenerate the client configuration:
   ```bash
   arwaky mcp generate
   ```

---

### Step 7: Add Host-Build Fallback in `Makefile` (Optional)

Add a direct fallback target in [`Makefile`](Makefile) for host-only environments:

```makefile
host-build-my-cool-tool:
	git submodule update --init vendor/my-cool-tool
	./tools/my-cool-tool/install.sh
```

---

### Step 8: Update Licenses & Documentation

1. **Attribution:** Add the upstream project name, source repository, pinned commit hash, and license in [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md):
   ```markdown
   | `vendor/my-cool-tool` | [example-org/my-cool-tool](https://github.com/example-org/my-cool-tool) | `a1b2c3d4` | MIT License |
   ```
2. **Catalog Update:** Add a row to the **Curated Upstream Vendor Tools** table in [`README.md`](README.md) and [`AGENTS.md`](AGENTS.md).

---

### Step 9: Verify & Test

Run the quality gate:
```bash
make check
```
Test the integration end-to-end:
```bash
# Check presence in status and catalog
arwaky status
arwaky list

# Test execution
arwaky run my-cool-tool --help

# Verify MCP manifest
arwaky mcp show
```

---

## ➖ Removing a Vendor Tool (Step-by-Step)

When deprecating or removing an upstream tool, follow this procedure to ensure clean de-registration with zero dangling references or broken CI checks.

### Step 1: De-register from Manifest
Open [`tools/arwaky/manifest.json`](tools/arwaky/manifest.json) and remove the object matching the tool's ID from `.tools[]`. Ensure the remaining JSON is valid.

### Step 2: Remove from Master Build Pipeline
Open [`tools/build/build-all.sh`](tools/build/build-all.sh) and delete the corresponding `build_tool` line:
```bash
# Delete this line:
build_tool "my-cool-tool" "$TOOLS_DIR/my-cool-tool/install.sh"
```

### Step 3: Remove from Binary Exporter
Open [`tools/distrobox/export-bins.sh`](tools/distrobox/export-bins.sh) and remove the tool binary from the `TOOLS` array.

### Step 4: Remove from MCP Configuration Generator (If Applicable)
In [`tools/mcp/generate-config.sh`](tools/mcp/generate-config.sh):
- Remove the server block from the JSON template.
- Remove the vendor name from the distribution loop.
- Re-run `arwaky mcp generate` to refresh `mcp_servers.generated.json`.

### Step 5: Remove Tool Setup Directory
Delete the tool's recipe directory under `tools/`:
```bash
rm -rf tools/my-cool-tool
```

### Step 6: Remove Host-Build Target in `Makefile`
If a `host-build-<tool-name>` target was added to [`Makefile`](Makefile), remove it and update `.PHONY`. Also remove binary references in `clean-host`.

### Step 7: De-initialize and Remove Git Submodule
Use Git to cleanly purge the submodule:

```bash
# 1. De-initialize the submodule
git submodule deinit -f vendor/my-cool-tool

# 2. Remove the submodule directory and stage .gitmodules change
git rm -f vendor/my-cool-tool

# 3. Remove internal git cached metadata
rm -rf .git/modules/vendor/my-cool-tool
```

### Step 8: Update Documentation & Licenses
- Remove the tool entry from [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md).
- Remove the tool row from the catalog tables in [`README.md`](README.md) and [`AGENTS.md`](AGENTS.md).

### Step 9: Verify Cleanliness
Execute the verification suite to ensure no broken references remain:
```bash
make check
arwaky status
```

---

## 🔄 Updating an Existing Vendor Tool

To upgrade a vendor tool to a newer upstream release or commit:

1. Navigate to the submodule:
   ```bash
   cd vendor/<tool-name>
   git fetch origin
   git checkout <new-tag-or-commit>
   cd ../..
   ```

2. Test the build inside the container:
   ```bash
   arwaky install <tool-name>
   # or: ./tools/<tool-name>/install.sh
   ```

3. Test execution:
   ```bash
   arwaky run <tool-name> --help
   ```

4. Update the pinned commit SHA in [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md).

5. Stage the submodule pointer update:
   ```bash
   git add vendor/<tool-name> THIRD_PARTY_LICENSES.md
   git commit -m "chore(vendor): bump <tool-name> to <new-tag-or-commit>"
   ```

---

## 🤖 Contributing to Internal Agents (`internal/`)

The repository hosts several core in-house agents under `internal/`:
- [`vision-arwaky`](internal/vision-arwaky/) (Python / `uv`)
- [`qwen-web-arwaky`](internal/qwen-web-arwaky/) (Python / Playwright)
- [`blender-arwaky`](internal/blender-arwaky/) (Python / Blender)
- [`lint-arwaky`](internal/lint-arwaky/) (Rust)

### In-House Agent Principles:
1. **AES Architecture Standards:**  
   In-house code adheres to the 7-layer Agentic Engineering System (AES). Every file follows `layer_concern_role.<ext>`. Run `arwaky run lint --help` to audit rules.
2. **Submodule Workflows:**  
   Internal agents are tracked as submodules. When making code changes inside `internal/<agent>/`, commit inside the submodule repository before staging the pointer change in the root repository.
3. **Parity between CLI and MCP:**  
   Internal tools exposing an MCP interface must preserve 1:1 parity with their CLI commands.

---

## 🧪 Quality Verification & PR Process

Before committing code or submitting a Pull Request, verify that all automated checks pass.

### 1. Run the CI Verification Script
```bash
make check
# Equivalent to: ./tools/ci/verify.sh
```

The script verifies:
- **Executable permissions:** All shell scripts under `tools/` have executable bits (`+x`).
- **JSON validity:** All JSON configurations (manifests, schemas) pass `jq empty`.
- **ShellCheck:** Bash code adheres to best practices without unquoted variables or syntax hazards.
- **Submodules status:** All submodules match registered commits.

### 2. Conventional Commit Guidelines
We follow standard Conventional Commits:

| Prefix | Usage | Example |
|---|---|---|
| `feat:` | New feature, agent, or capability | `feat(vendor): add repomix MCP tool` |
| `fix:` | Bug fix in orchestrator or installer | `fix(arwaky): resolve symlink path resolution` |
| `chore:` | Maintenance, submodule bump, cleanup | `chore(vendor): bump codegraph to v1.6.0` |
| `docs:` | Documentation changes | `docs: add vendor lifecycle guide to CONTRIBUTING.md` |
| `refactor:`| Code refactoring without behavioral change | `refactor(mcp): simplify template rendering` |

### 3. Pull Request Checklist
When submitting a PR, ensure:
- [ ] Submodule pointers are updated cleanly without detached state conflicts.
- [ ] New shell scripts include `set -euo pipefail` and executable bits (`chmod +x`).
- [ ] `tools/arwaky/manifest.json` is updated and validated with `jq`.
- [ ] `THIRD_PARTY_LICENSES.md` lists the upstream license and commit.
- [ ] `make check` passes with zero errors.
