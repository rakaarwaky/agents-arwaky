# Shared skills layout (local mirror)

Canonical: `skills/devops/hermes-profiles/references/skills-layout.md`.
One symlinked root serves every profile and harness:
`profiles/<p>/skills` -> `~/.hermes/skills` -> the pack repo.
Every profile sees the identical skill set; new pack skills need
no re-sync. Load the canonical file for migration and verify steps.
