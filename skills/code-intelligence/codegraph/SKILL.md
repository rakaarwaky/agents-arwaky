---
name: codegraph
description: Local code graph search with symbols and refs. Use when adding languages, benchmarking retrieval.
---
# CodeGraph MCP & CLI

CodeGraph is a high-performance, Rust-powered codebase intelligence engine. It builds and maintains a live graph of symbols, types, call hierarchies, and cross-file dependencies with zero cloud dependencies.

## When to Use This Skill

Activate this skill when:
- Exploring unfamiliar codebases or large multi-file architectures.
- Finding all references, callers, or callees of a specific function or class.
- Looking up symbol definitions and signatures across files without blind grep searching.
- Verifying cross-file impacts before refactoring critical shared interfaces.

## Project Setup & Indexing

Querying requires an initialized project index — a per-project `codegraph init`
(builds the graph in the same step). Indexing and re-indexing commands are the
orchestrator's (`aa tool run codegraph ...`, see the repo README); the watcher
keeps the index current afterwards, so do not re-sync by hand mid-session.

## MCP Tools & Capabilities

When running with MCP clients, CodeGraph exposes specialized tools:

| Tool | Purpose | Primary Parameters |
|---|---|---|
| `codegraph_search_symbols` | Search for functions, methods, classes, types, or interfaces by name | `query` (string) |
| `codegraph_get_definition` | Resolve the exact declaration file and line range for a symbol | `symbol` (string), `path` (optional) |
| `codegraph_find_references` | Locate all usages and imports of a symbol across the repository | `symbol` (string), `path` (optional) |
| `codegraph_call_hierarchy` | Inspect caller and callee chains for a function or method | `symbol` (string), `direction` ("incoming" \| "outgoing") |
| `codegraph_file_outline` | Retrieve structured outline of symbols declared in a file | `path` (string) |

## CLI Direct Queries

You can also run quick queries via the command-line:

```bash
# Check index status and coverage
aa run codegraph status

# Inspect symbol definitions
aa run codegraph query definition "MyService"
```

## References

Maintainer-only workflows for the vendored `vendor/codegraph` submodule. Load the
matching file — do not guess at these procedures:

| Reference | Read it when |
|---|---|
| [`references/add-language.md`](references/add-language.md) | Adding/supporting a new tree-sitter language end-to-end: grammar health-check, AST node discovery, the 4-file wiring, extraction verify loop, tests, then benchmarking on 3 real repos. |
| [`references/evaluating.md`](references/evaluating.md) | Benchmarking/auditing retrieval quality: a with-vs-without-codegraph A/B on a real repo for a chosen codegraph version (local dev build or published npm). |

