# Step 0: Confirm the audit root

Resolve the directory the prune runs on before any read or merge.

**Goal:** confirm a valid audit root: the `/home/raka/agents-arwaky/skills` root, a specific category, or the user's path.

## Resolution

Default to `/home/raka/agents-arwaky/skills`, a specific category, or the user's path. Reject a path that resolves to a file; stop if the directory holds no `SKILL.md` subfolders.

## Completion

- The audit root resolves to a directory (a file path is rejected).
- The root contains at least one `SKILL.md` subfolder, otherwise the run stops.
- The root is recorded for the inventory step.
