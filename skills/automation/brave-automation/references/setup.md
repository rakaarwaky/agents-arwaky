# Setup: Install, Init, and Configure CSVs

**Goal:** get `baa` running on this host with a configured `profile.csv` and `passwords.csv`.

## Prerequisites

- Linux host
- Python 3.10+ (system Python 3.12 typical)
- `uv` installed
- Brave Browser installed (native, Flatpak, or Snap)

## Steps

### 1. Install the CLI

```bash
cd <repo-root>/skills/automation/brave-automation/app
uv pip install -e .
```

Verify:

```bash
baa --help
# or
brave-automation-arwaky --help
```

Both console scripts resolve to `modules.root_baa_entry:main`.

### 2. Initialize the workspace

```bash
baa init
```

This creates the XDG state and data directories:

- `$XDG_STATE_HOME/baa` — logs and session files
- `$XDG_DATA_HOME/baa` — working data

Never use `/tmp` for any output a reviewer must find.

### 3. Create or edit `profile.csv`

Located in the workspace after `baa init`. Columns:

| Column | Description |
|--------|-------------|
| `name` | Profile name (must be unique; used as directory name under Brave's Profiles dir) |
| `email` | Primary email for the account tied to this profile |
| `label` | Human-readable label for the profile |

Example:

```csv
name,email,label
work,work@example.com,Work account
personal,personal@example.com,Personal
ci,ci@example.com,CI bot
```

### 4. Create or edit `passwords.csv`

Columns:

| Column | Description |
|--------|-------------|
| `profile` | Profile name (must match a `name` in `profile.csv`) |
| `url` | Login URL, e.g. `https://accounts.google.com` |
| `username` | Login username |
| `password` | Login password |
| `extra` | Optional notes |

Example:

```csv
profile,url,username,password,extra
work,https://accounts.google.com,work@example.com,secretpass,work GSuite
```

## Completion

- `baa --help` prints the command tree
- `baa init` succeeded and XDG dirs exist
- `profile.csv` and `passwords.csv` are present and valid
