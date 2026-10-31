# Step 2: Pattern Analysis (Phase 2)

**Find the pattern before fixing.**

## 0. Minimize the Reproduction

Once the loop is red, shrink the repro to the smallest scenario that still goes red. Cut inputs, callers, config, data, and steps **one at a time**, re-running the loop after each cut. Keep only what is load-bearing for the failure.

Done when removing any remaining element makes the loop go green. A minimal repro narrows the hypothesis space and often becomes the cleanest regression test.

## 1. Find Working Examples

- Locate similar working code in the same codebase.
- What works that's similar to what's broken?

**Action:** Use `grep` / `codegraph_explore` to find comparable patterns:

```bash
grep -rn "similar_pattern" src/
```

## 2. Compare Against References

- If implementing a pattern, read the reference implementation COMPLETELY.
- Don't skim — read every line.
- Understand the pattern fully before applying.

## 3. Identify Differences

- What's different between working and broken?
- List every difference, however small.
- Don't assume "that can't matter".

## 4. Understand Dependencies

- What other components does this need?
- What settings, config, environment?
- What assumptions does it make?

## Next

Feed the identified differences into Step 3 to build the ranked hypothesis list.
