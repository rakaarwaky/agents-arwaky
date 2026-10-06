---
name: harness-source-audit
description: Compare coding harnesses by auditing their source trees.
metadata:
  hermes:
    tags:
      - codebase-inspection
      - agent-harness
      - source-audit
---

# Coding Agent Harness Source Audit

Audit and compare coding-agent harnesses (e.g. Hermes vs Grok Build) by reading their actual source trees. Use when the user asks which harness is "better" at coding, wants a capability comparison, or suspects a feature exists in source but is undocumented in the shipped binary.

## When to Use

- User asks to compare two AI coding agents/harnesses by capability
- User suspects a feature is implemented but not documented
- Need to verify a capability by reading source, not by trial
- Auditing whether an open-source agent has the architecture claimed

## Core Principle

A capability documented in CLI flags is cheap evidence — anyone can add a flag without implementing the feature. A capability visible in the source tree is stronger evidence because it requires code to exist. **Source is the source of truth for closed tools too** — if the repo is public, read the code; if it is private, fall back to binary introspection (strings/otool/objdump) and document that limitation.

## Measurement Rules

### LOC measurement

Count all files of interest, then `cat | wc -l`. Never `find | xargs wc -l | tail -1` — that undercounts dramatically when find splits the file list into multiple wc invocations (each prints its own `total`, so `tail -1` returns only the last batch).

```bash
# Correct for a single-language grand total
find . -name "*.rs" -not -path "./target/*" -print0 | xargs -0 cat | wc -l

# Per-directory breakdown (bounded, one batch per dir)
find <dir> -name "*.py" | while read f; do loc=$(wc -l < "$f"); echo "$loc $f"; done | sort -rn | head -20
```

For a multi-language repo use pygount with `--folders-to-skip`. Decide one method before measuring both sides of a comparison and state it.

### Avoid false negatives from closed-source binaries

A stripped release binary (like Grok Build's 159MB ELF) does NOT prove absence of a feature. Clone the public repo first, then check the source tree. Only if the repo is private or unavailable fall back to binary strings/analysis.

## Comparative Dimensions

When comparing harnesses, audit these classes. For each, note the crate/module and LOC as evidence, not as the final judgment.

1. **Agent loop / conversation management** — how turns are composed, continuation, recovery
2. **Tool suite** — registered tool names, implementations, whether they are wrappers or native
3. **Codebase intelligence** — LSP integration, code graph, symbol search, cross-file reasoning
4. **Context management & compaction** — how conversations grow and are compressed; this is the single biggest factor in long-session coding quality
5. **Subagent delegation** — parallel agents, worktree isolation, result merging
6. **Workspace / isolation** — git worktrees, btrfs/overlay copy-on-write, Docker/sandbox
7. **Edit mechanics** — exact patch algorithm (fuzzy vs line-based vs search-replace), diff tracking, undo/rollback
8. **Permissions & safety** — permission gate models (ask/auto/always-approve), sandbox profiles, hook deny
9. **Mid-turn steering** — can the user intervene without aborting the turn
10. **Cross-session memory** — persistent facts, episodic recall

## Workflow

1. **Locate source trees** — clone public repos with `--depth 1 --filter=blob:none` to avoid downloading the full history. For private repos, ask the user to provide access.
2. **Measure surface area** — run LOC counts on both repos using the same method.
3. **Map architecture** — list directories/crates for each, focusing on the 10 dimensions above.
4. **Read key modules** — for each dimension where both have candidates, read the top-level file(s) to confirm the implementation exists and understand its approach.
5. **Synthesize** — report findings per dimension, not just totals. A larger LOC count does not mean better capability; an implementation may be thin.

## Pitfalls

1. **`find | xargs wc -l | tail -1` undercounts by an order of magnitude** — xargs splits a large file list into several `wc` invocations, each printing its own `total`, so `tail -1` returns only the LAST batch's subtotal. A 1.9M-line Rust tree measured this way reported 267k. Count the whole tree in one stream: `find ... -print0 | xargs -0 cat | wc -l`.
2. **Comparing two codebases requires the same measurement on both sides** — `wc -l` on one repo and pygount on the other mixes gross lines with code-only lines and manufactures a difference that is an artifact of the method. Decide one method, run it on both, and state it in the result.
3. **A stripped binary is not evidence of absence** — always check the public repo before concluding a feature is missing.
4. **Surface area ≠ capability** — many LOC can mean thin, repetitive wrappers. Read the actual implementation files for the dimension you care about before drawing conclusions.
5. **Both harnesses may share the same design pattern** — e.g., both Grok Build and Hermes now have LSP, codebase graphs, and subagent worktrees. A claim like "Hermes has X but Grok doesn't" is fragile; verify both sides explicitly in this session's source tree, not from memory.
