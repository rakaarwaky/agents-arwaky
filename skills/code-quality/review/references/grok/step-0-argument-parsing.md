# Step 0: Argument parsing (commit / uncommit / pr N / path <p>)

## Argument form

```
/review commit
/review uncommit
/review pr <pr-number>
/review path <path>
```

One target, exactly one. No persona flags, no `--all`. Persona selection is automatic (see below).

## Parsing rules

Parse the raw argument tokens:

1. **First token determines the mode.** Map as follows:

   | First token | Mode | Required second token |
   |---|---|---|
   | `commit` | last-commit | none |
   | `uncommit` | uncommitted | none |
   | `pr` | pr | `<pr-number>` (integer, 1–4096, e.g. `48`) |
   | `path` | path | `<path>` (one path, directory **or** file, relative to cwd or absolute) |

2. **`commit` / `uncommit` with extra tokens:** reject with `Extra tokens not allowed: <extras>. Usage: /review commit` (or `uncommit` respectively) and stop.

3. **`pr` missing or invalid number:** reject with `PR number required. Usage: /review pr <pr-number>` and stop.

4. **`path` missing second token:** reject with `Path required. Usage: /review path <path>` and stop.

5. **`path` resolves to a file:** allowed. `mode = path`, `target = <resolved absolute file path>`.

6. **`path` does not exist:** reject with `Path <path> not found.` and stop.

7. **First token not one of `commit`, `uncommit`, `pr`, `path`:** reject with `Unknown target. Usage: /review commit | uncommit | pr <pr-number> | path <path>` and stop.

## Persona selection (automatic, 1–3 per run)

No persona flags. After the target is resolved and the run state is set up (Step 1), the orchestrator (this agent) selects 1–3 personas from the roster below, based on what the target's content tells it:

- `commit` / `uncommit` / `pr` modes: read the diff summary (added/changed file extensions, directory names, file sizes, and the commit/PR title + description if available) before launching subagents. The diff itself gives the orchestrator the signal.
- `path` mode: read the directory tree or single file content (at least the first ~50 lines or imports) before launching subagents.

Pick 1–3 personas from the roster. Use the most relevant ones for the observed content. Common heuristics:

| Signal observed | Personas to prefer |
|---|---|
| Python / Rust / Go backend logic, DB queries, API handlers | backend-engineer, software-architect, qa-engineer |
| UI / JSX / TSX / CSS / design tokens / component files | frontend-engineer, ui-ux-designer, qa-engineer |
| Security-sensitive: auth, tokens, crypto, secrets, network endpoints | security-engineer, backend-engineer |
| Tests / fixtures / mocks / test scaffolding | qa-engineer, system-analyst |
| CI / Docker / deploy / infra / Terraform / cloud config | devops-engineer, system-analyst |
| Docs / markdown / product copy / PRD / spec files | product-engineer, business-analyst |
| Data / schemas / migrations / ETL / analytics | business-analyst, system-analyst |
| Small or ambiguous diff (< 3 files, single language) | qa-engineer, software-architect |

If the signal is unclear or the diff is large and mixed, fall back to the full 3 most common: backend-engineer, qa-engineer, software-architect.

Store the selected list (ordered, deduplicated, 1–3 entries) as `personas` for Steps 2 and 3.

## Persona roster

The 10 available lens personas:

backend-engineer, business-analyst, devops-engineer, frontend-engineer, product-engineer, qa-engineer, security-engineer, software-architect, system-analyst, ui-ux-designer
