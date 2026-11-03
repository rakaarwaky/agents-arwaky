# Step 0: Argument parsing (path, persona flags, --all)

## Persona roster

The 10 lens personas, in canonical order. Each maps to a flag of the same name and to `personas/<name>.toml`:

| Flag | Persona |
|---|---|
| `--backend-engineer` | backend-engineer |
| `--business-analyst` | business-analyst |
| `--devops-engineer` | devops-engineer |
| `--frontend-engineer` | frontend-engineer |
| `--product-engineer` | product-engineer |
| `--qa-engineer` | qa-engineer |
| `--security-engineer` | security-engineer |
| `--software-architect` | software-architect |
| `--system-analyst` | system-analyst |
| `--ui-ux-designer` | ui-ux-designer |

## Parsing rules

Parse the raw argument tokens in two phases: extract the persona flags, then resolve the module path.

**Phase 1 — persona flag extraction.** Scan the raw tokens for any of the 10 persona flags and for `--all`. For each persona flag found, add its name to the `personas` list and remove all occurrences. `--all` is a boolean `ALL=true` that is also removed. If `--all` appears together with one or more individual persona flags, treat the individual flags as a no-op (the set is all 10 either way) and note it once: "--all already selects every persona; ignoring --qa-engineer etc."

**Phase 2 — path resolution.** The first remaining token that is not a flag is the module path. Rules, applied in order:

1. **No path token**: reject with `Module path required. Usage: /review <path> [persona flags].` and stop.
2. **Multiple path tokens**: reject with `Only one module path may be given.` and stop.
3. **Path resolves to a file** (`[ -f <path> ]` is true after resolving against cwd): reject with `Path <path> is a file. Give a module, crate, or package directory.` and stop.
4. **Path does not exist** (`[ -d <path> ]` is false and `[ -f <path> ]` is false): reject with `Path <path> not found under the current directory.` and stop.
5. **Path exists but has no tracked files**: Step 1 detects this and short-circuits with "No tracked files under `<path>`. Nothing to review."

If `ALL` is true (or no persona flags were given at all), `personas` is the full 10-name roster above in canonical order. Otherwise `personas` is exactly the set of flagged names, in the order the flags were passed.

**Rejected flags.** Any `--`-prefixed token that is not one of the 10 persona flags or `--all` is rejected with `Unknown flag: <flag>. Valid persona flags: --backend-engineer, --business-analyst, --devops-engineer, --frontend-engineer, --product-engineer, --qa-engineer, --security-engineer, --software-architect, --system-analyst, --ui-ux-designer, --all.` and stop. Do NOT fall through to a default.

This skill has no `--approve`, `--submit`, `--pr`, `--stack`, or `--main`/`--local`/`--branch` flags. Those forms are retired.
