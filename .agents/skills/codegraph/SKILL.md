---
name: codegraph
description: Fast local code graph engine, symbol search, cross-file references, call hierarchies, and codebase intelligence for AI agents.
version: 1.0.0
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

Before querying via MCP, the project workspace must be initialized:

```bash
# Initialize CodeGraph and build the full repository graph
cd /path/to/project
aa run codegraph init

# Or manually re-index after substantial file changes
aa run codegraph index
```

CodeGraph watches project files automatically and updates the index incrementally on file modifications.

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
