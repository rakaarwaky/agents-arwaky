# Agent Integration

## Investigation Tools

Use these tools during Phase 1:

- **`grep` / `codegraph_explore`** — find error strings, trace function calls, locate patterns
- **`read_file`** — read source with line numbers for precise analysis
- **`run_terminal_command`** — run tests, check git history, reproduce bugs
- **`web_search` / `web_fetch`** — research error messages, library docs

## With Subagents

For complex multi-component debugging, dispatch investigation subagents in parallel
(Orca worktrees when isolation is needed):

- Goal: "Investigate why [specific test/behavior] fails"
- Context: error, file, test command; instruct: read error, reproduce, trace data flow, report findings — do NOT fix yet.

## With test-driven-development (now Phase 4)

Bug found? Write a failing test reproducing it, then follow the Phase 4 cycle.
The test proves the fix and prevents regression. Never fix bugs without a test.