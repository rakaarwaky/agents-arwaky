# TDD: Agent integration, anti-patterns, and final rule

## Agent Integration

### Running Tests

Use the `run_terminal_command` tool to run tests at each step:

```python
# RED — verify failure
run_terminal_command("pytest tests/test_feature.py::test_name -v")

# GREEN — verify pass
run_terminal_command("pytest tests/test_feature.py::test_name -v")

# Full suite — verify no regressions
run_terminal_command("pytest tests/ -q")
```

### With spawn_subagent

When dispatching subagents for implementation, enforce TDD in the goal:

```python
spawn_subagent(
    prompt="""
    Implement [feature] using strict TDD.

    Follow test-driven-development skill:
    1. Write failing test FIRST
    2. Run test to verify it fails
    3. Write minimal code to pass
    4. Run test to verify it passes
    5. Refactor if needed
    6. Commit

    Project test command: pytest tests/ -q
    Project structure: [describe relevant files]
    """
)
```

### With systematic-debugging

Bug found? Write failing test reproducing it. Follow TDD cycle. The test proves the fix and prevents regression.

Never fix bugs without a test.

## Testing Anti-Patterns

- **Testing mock behavior instead of real behavior** — mocks should verify interactions, not replace the system under test
- **Testing implementation details** — test behavior/results, not internal method calls
- **Happy path only** — always test edge cases, errors, and boundaries
- **Brittle tests** — tests should verify behavior, not structure; refactoring shouldn't break them

## Final Rule

```
Production code → test exists and failed first
Otherwise → not TDD
```

No exceptions without the user's explicit permission.