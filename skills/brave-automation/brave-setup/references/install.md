# Install — Get the baa CLI Running

**Goal:** install the `baa` console script from the `tools/` project and verify
the CLI surface resolves.

## Prerequisites

- Linux host
- Python 3.10+ (system Python 3.12 typical)
- `uv` installed
- Brave Browser installed (native, Flatpak, or Snap)

## Steps

### 1. Install the CLI

```bash
cd <repo-root>/skills/brave-automation/tools
uv pip install -e .
```

Both console scripts `baa` and `brave-automation-arwaky` resolve to
`modules.root_baa_entry:main`.

### 2. Verify

```bash
baa --help
# or
brave-automation-arwaky --help
```

Both must print the command tree without `ModuleNotFoundError`.

## Completion

- `baa --help` prints the command tree
- No `ModuleNotFoundError` on either console script
