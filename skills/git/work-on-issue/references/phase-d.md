# Phase D — Build isolation

Each worktree MUST use its own build artifact directory — shared dirs cause phantom sibling errors and lock/RAM contention, and a cold-dir retry never falls back to the shared dir. Rationale plus setup recipes for Cargo, Node, and Python: [isolation-recipes.md](isolation-recipes.md).
