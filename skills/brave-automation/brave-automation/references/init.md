# Init — Create the XDG Workspace and Configure CSVs

**Goal:** get a configured `profile.csv` and `passwords.csv` under the XDG
state/data directories, ready for the sibling skills to consume.

## Commands

```bash
# Initialize the workspace in the current directory
baa init

# Initialize in a specific target directory
baa init --dir /path/to/workspace
```

This creates the XDG state and data directories:

- `$XDG_STATE_HOME/baa` — logs and session files
- `$XDG_DATA_HOME/baa` — working data

Never use `/tmp` for any output a reviewer must find.

## Configure `profile.csv`

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

## Configure `passwords.csv`

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

- `baa init` succeeded and XDG dirs exist
- `profile.csv` and `passwords.csv` are present and valid
