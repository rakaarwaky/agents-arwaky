---
name: codegraph
description: "Inspect codebases: LOC, languages, ratios via pygount, plus symbol/call graphs and blast radius via CodeGraph."
when-to-use: "Repository LOC counts, language breakdowns, file counts, and code-vs-comment ratios (pygount — general 'how big is this repo' questions); or symbol lookup, callers/callees, cross-file impact, and test selection for a set of changed files (CodeGraph — use before grep/Read when asking 'what breaks if I change this')."
argument-hint: "[pygount] [--format=summary|json] [--suffix=<langs>] [--folders-to-skip=<globs>] [<path>]  |  [codegraph] <project-path>"
metadata:
  tags:
    - LOC
    - Code Analysis
    - pygount
    - Codebase
    - Metrics
    - Repository
    - symbols
    - call graph
    - impact
    - CodeGraph
  related_skills:
    - repo-manager
---

# Codebase Inspection

Two complementary lenses on a codebase, routed by the question.

## Global rules

- **Routing.** Pick the lens from the question, then read the matching reference end to end; the two tools answer different jobs — pygount counts lines by language, CodeGraph resolves symbols and the edges between them.
- **Order of operations.** Reach for CodeGraph **before** grep/Read, not after they fail: grep matches text, CodeGraph answers "what breaks if I change this", "which tests cover this file", "what calls this and how".
- **Completion.** The chosen reference was read in full and its commands executed against the target repo; results are interpreted with that reference's pitfalls and pseudo-language notes applied.

## Routing

| Question | Tool | Reference |
| --- | --- | --- |
| How big is this repo? Language mix? Code-vs-comment ratios? | `pygount` | [`references/pygount.md`](references/pygount.md) — prerequisites, summary commands, folder exclusions, language filters, output formats, result interpretation, pitfalls. |
| What calls this symbol? What breaks if I change it? Which tests cover it? | `CodeGraph` | [`references/codegraph.md`](references/codegraph.md) — MCP tool table, CLI direct-query syntax, "an index must exist first" notes. |
