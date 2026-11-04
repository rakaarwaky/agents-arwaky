# Where to write

Resolve the config file as `$GROK_HOME/config.toml` when `GROK_HOME` is
set, otherwise `~/.grok/config.toml`. If that path is a symlink, edit the
target. Create the file if it is missing; keep every other key.

Write `[ui.status_line]` only in that user file. A repository
`.grok/config.toml` cannot set this row, and campaign or version-override
patches strip it.

**Goal:** the edit lands in the one file Grok actually reads, with the
rest of the config untouched.

## Decision rule

Read the current `[ui.status_line]` table first. If the user already
named the row they want — built-in items, a custom script, or off — write
that and do not ask again. If they did not, do not write. In one short
reply, say what the row is, show the current table when one exists, and
ask what they want shown: which built-in items, a custom script, or off.

The row is optional and off by default. It shows live session context.
There is no settings screen for it.

## Completion

- The table was written only to the resolved user config file.
- If the user had not named a row, no write happened and a one-line
  question was asked instead.
