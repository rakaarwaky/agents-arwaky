---
name: codegraph
description: Code graph: symbols, callers, impact. Prefer over grep. Use when exploring or refactoring a repo.
---
# CodeGraph MCP & CLI

CodeGraph is a high-performance, Rust-powered codebase intelligence engine. It builds and maintains a live graph of symbols, types, call hierarchies, and cross-file dependencies with zero cloud dependencies.

## When to Use This Skill

Reach for this **before** grep/Read, not after they fail:

- Exploring an unfamiliar codebase or a large multi-file architecture.
- Finding callers, callees, or references of a specific function or class.
- Resolving a symbol's declaration and signature across files.
- Checking cross-file blast radius before refactoring a shared interface.
- Picking which tests to run for a set of changed files.

Grep matches text; CodeGraph resolves symbols and the edges between them. The difference
shows up in the questions only it can answer — "what breaks if I change this", "which tests
cover this file", "what calls this and how".

## An Index Must Exist First

A project is queryable only after `codegraph init` has built `<project>/.codegraph/`. The MCP
server registers and starts fine with no index anywhere, so a dead-looking tool is usually a
missing index, not a broken wiring:

```bash
codegraph status <project-path>     # "⚠ Not initialized" ⇒ nothing to query from

```text

- `init` is a write to the repository (creates untracked `.codegraph/`) — ask before running
  it in someone else's tree, and check whether `.gitignore` covers it.
- `sync` applies the delta since last index; the background daemon keeps indexes fresh, so
  don't re-index by hand mid-session.
- Indexing belongs to the orchestrator: `aa tool run codegraph <cmd>`.

## MCP Tools

The installed build (v1.6.0) exposes exactly these eight. Any other `codegraph_*` name is a
hallucinated tool and will fail.

| Tool | Purpose |
|---|---|
| `codegraph_explore` | **Primary.** One call returns the relevant symbols' line-numbered source, the call paths between them, and a blast-radius summary — replaces a grep+Read loop. |
| `codegraph_node` | A single symbol's source plus its caller/callee trail, or a file read with line numbers and its dependents. |
| `codegraph_search` | Symbol lookup by name/kind. |
| `codegraph_callers` | Who calls a symbol. |
| `codegraph_callees` | What a symbol calls. |
| `codegraph_impact` | What code is affected by changing a symbol. |
| `codegraph_files` | Project file structure from the index. |
| `codegraph_status` | Index presence and statistics — call this when a query comes back empty. |

**No default project:** this server may start somewhere without a `.codegraph/`. For any
project that isn't the session's working directory, pass its path as `projectPath`; the tool
resolves the nearest `.codegraph/` at or above it. A project with no index needs `codegraph
init` run in it first (the user's decision, not yours).

## CLI Direct Queries

Same outputs as MCP, useful for a quick check or when piping:

```bash
codegraph status                       # is there an index, and how big?
codegraph explore "how does the dispatcher route commands"
codegraph node <symbol>                # source + caller/callee trail
codegraph impact <symbol>              # blast radius of changing it
codegraph affected src/foo.py src/bar.py   # test files touched by these changes
codegraph files                        # indexed tree
codegraph ui                           # browse the graph in a browser

```text

Each subcommand takes `--path` / `-p` for another project and `--help` for its own flags.

## References

Maintainer-only workflows for the vendored `vendor/codegraph` submodule. Load the
matching file — do not guess at these procedures:

| Reference | Read it when |
|---|---|
| [`references/add-language.md`](references/add-language.md) | Adding/supporting a new tree-sitter language end-to-end: grammar health-check, AST node discovery, the 4-file wiring, extraction verify loop, tests, then benchmarking on 3 real repos. |
| [`references/evaluating.md`](references/evaluating.md) | Benchmarking/auditing retrieval quality: a with-vs-without-codegraph A/B on a real repo for a chosen codegraph version (local dev build or published npm). |
