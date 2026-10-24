# Per-Workspace Environments — recipe scaffolding and validation

Set up, review, debug, or validate an Orca per-workspace environment recipe:
the on-demand, disposable runtime (cloud sandbox, VM, SSH host, or local
container) Orca creates fresh for each workspace. Use to stand up a new recipe
end to end, fix an `environmentRecipes` entry in `orca.yaml`, scaffold provider
lifecycle scripts, or resolve an `orca vm recipe doctor` failure.

Use [cli.md](cli.md) for ordinary worktree and workspace creation with no
recipe involved.

## Load the version-matched guide

```text
ORCA skills get orca-per-workspace-env
```
