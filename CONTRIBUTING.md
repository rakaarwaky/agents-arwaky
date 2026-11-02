# CONTRIBUTING — <project-name>

## Contribution Overview

<One paragraph: how to contribute, what mindset contributors should have, and what "ready to merge" looks like.>

## Contribution Guidelines

## Workflow

| Step | Action | Detail |
|------|--------|--------|
| 1 | Fork / Branch | `<branch-naming-convention>` |
| 2 | Implement | Follow FRD spec, write tests |
| 3 | Self-review | Check against acceptance criteria in PRD |
| 4 | Submit PR | Link to BACKLOG ID, describe what changed |
| 5 | Review | <reviewer / approval criteria> |
| 6 | Merge | <merge strategy: squash / rebase / merge> |

## Commit Convention

| Type | Usage | Example |
|------|-------|---------|
| `feat` | New feature | `feat(feature-name): <new-description>` |
| `fix` | Bug fix | `fix(feature-name): <fix-description>` |
| `docs` | Documentation only | `docs(doc-name): <update-description>` |
| `test` | Adding/updating tests | `test(feature-name): <test-description>` |
| `refactor` | Code refactor, no behaviour change | `refactor(feature-name): <refactor-description>` |
| `chore` | Maintenance, deps, config | `chore: <bump-description>` |

## Worktree-local catalog checks

When validating or regenerating `skills/CATALOG.md` from an Orca worktree (a tree that is not the main clone), use the `--skills-root` flag to point at the worktree's `skills/` directory. The bare `aa` wrapper pins `AGENTS_ARWAKY_ROOT` to the main clone at `/home/raka/agents-arwaky` and does not reflect the worktree's tree:

```bash
# regenerate (worktree root as CWD)
python3 -m modules.root_cli_entry skills catalog --skills-root "$PWD/skills"
# verify (exit 0 = in sync)
python3 -m modules.root_cli_entry skills catalog --check --skills-root "$PWD/skills"
```

In GitHub Actions CI, CWD is already the checkout root (`$GITHUB_WORKSPACE`), so the module's default skills root resolves to the branch's `skills/` tree and no `--skills-root` is needed.

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| PRD | <Business goals, user stories, and scope> | [PRD.md](PRD.md) |
| Architecture | <System boundaries, tech stack, and infra> | [ARCHITECTURE.md](ARCHITECTURE.md) |
