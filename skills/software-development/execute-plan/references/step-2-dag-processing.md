# Step 2 Dag Processing

## Step 2: DAG Processing and Linearization

### Level Assignment

Assign execution levels to each PR node:

```
level(node) = 0                                              if dependencies is empty
level(node) = max(level(dep) for dep in dependencies) + 1    otherwise
```

PRs at the same level are independent and can execute in parallel.

### Linearization for Stack Assembly

Stacks (Graphite or plain-git) are strictly linear chains. The DAG is flattened into a single topologically-sorted linear sequence:

```
def linearize(dag):
    """Produce a linear order respecting all dependency edges."""
    nodes_by_level = group_by(dag.nodes, key=lambda n: n.level)
    result = []
    for level in sorted(nodes_by_level.keys()):
        for node in sorted(nodes_by_level[level], key=lambda n: int(n.id.split('-')[1])):
            result.append(node)
    return result
```

Within each level, sort by the numeric PR number (extracted from the id string via `int(n.id.split('-')[1])`) to produce a deterministic, reviewable order. Do NOT use lexicographic string sort on the id -- `"pr-10"` would sort before `"pr-2"` lexicographically.

Store the result in `linearized_order` and update the state file.

### Compute Branch Names

For each PR node, compute the branch name:
```
branch = "execute-plan/<PLAN_ID>-<pr-number>-<slug>"
```

Example: `execute-plan/a1b2c3d4-pr-1-add-retry-config-types`

Update each node's `branch` field.

### Report

Report to the user:
```
"Linearized stack order: PR1 (<title>) -> PR4 (<title>) -> PR2 (<title>) -> ...
Max parallelism: <max PRs at any single level>
Levels: <number of levels>"
```

### Dry-Run Exit

If `--dry-run` was specified, report the full execution plan (linearized order, level assignments, branch names, dependency graph) and stop. Do not proceed to implementation.

