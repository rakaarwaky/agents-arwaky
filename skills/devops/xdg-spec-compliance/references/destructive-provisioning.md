# Destructive provisioning

The rules for provisioners that replace state dirs with symlinks, and
for symlinking config/cache into a workspace.

**Goal:** a provisioner that loses nothing and a workspace that cannot
leak credentials.

## Stale-dir replacement

Workspace provisioners replacing a stale regular directory with a
symlink should rename it to `<name>.stale-<timestamp>` beside the
link, not `rmtree` it. Keep the rename idempotent: if a timestamped
copy already exists, delete the stale source instead of stacking
backups.

## Symlink exfiltration

Symlinking config/cache into the workspace (`.bwc/config ->
$XDG_CONFIG_HOME/app`) is convenient but means `tar -h` / `rsync -L`
of the repo exfiltrates real credentials — document it at the
symlink-creating function.

## Completion

- No provisioner path calls `rmtree` on a user-owned dir; the
  timestamped rename is idempotent.
- Every symlink-creating function carries the exfiltration
  documentation.
