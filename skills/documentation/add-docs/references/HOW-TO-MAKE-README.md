# HOW TO MAKE README.md

> **Purpose**: Answer *how do I get this running, and where do I look
> next*.
>
> **Audience**: A developer who just cloned the repo, possibly you in six
> months.
>
> **Scope**: Onboarding: prerequisites, quick start, structure, commands.
> Exactly one per project root.
>
> **Location**: Project root.
>
> **Length**: 50–500 lines (flat budget shared by every document type).

---

## Rules

Eight rules. Each one prevents a specific failure mode.

1. **The test is time, not completeness.** Clone → install → build → run
 in under 10 minutes. If the Quick Start cannot clear that, the
 missing step is the bug in this file.
2. **Every command was actually run, and says how to confirm it
 worked.** A reader who cannot tell success from silence will assume
 failure and go ask a human.
3. **Prerequisites are the ones the build fails without**, with versions
 pinned. Optional tooling listed as required teaches readers to
 distrust the list.
4. **Link, do not restate** (`dead-link` catches the broken half).
 Requirements, API detail and status live in
 `PRD.md`/`FRD.md`/`BACKLOG.md`; a copied requirement drifts with no
 precedence rule to settle the disagreement.
5. **Testing and Commands show what CI runs**, verbatim — the same rule
 that gates `AGENTS.md` (`ci-command-drift`). A local variant teaches
 readers to pass a gate they fail in review.
6. **Configuration names variables and files, never values**
 (`secret-in-docs`). Use `<placeholders>` and repo-relative paths
 (`absolute-path`).
7. **Project Structure teaches the doc layout.** Showing `FRD.md`
 beside `BACKLOG.md` in each feature directory is where most readers
 learn the spec/status split.
8. **50–500 lines** (`doc-length`). Beyond that, split by audience —
 that is what the other four documents are for.

---

## Template

Copy, fill, delete nothing.

```markdown
# <project-name>

> One-liner: what this project does and who it's for.

## Prerequisites

- <see per-language table below>
- <other dependencies>

## Quick Start

<see per-language table below — then make it self-confirming>

## Architecture

<High-level diagram or link to full docs>

## Project Structure

<see per-language block below>

## Available Scripts / Available Commands

<see per-language table below — Rust: "Available Commands"; Python and
TypeScript: "Available Scripts">

## Configuration

<Environment variables, config files — names only, never values>

## Testing

<per-language test command, as CI runs it>

## Contributing

<Branching strategy, PR conventions>

## License

<License type>

<!-- Per-language Variables -->
<!-- Python: Python 3.10+ | git clone → cd <project> → pip install -e . →
     python -m <package> | Available Scripts
     python -m <package> = Run; pytest = Tests; ruff check . = Lint -->
<!-- Rust: Rust 1.70+ | git clone → cd crates/<name> → cargo build →
     cargo run | Available Commands
     cargo build = Build; cargo test = Tests; cargo run = Run -->
<!-- TypeScript: Node 20+ | git clone → cd <project> → npm install →
     npm run dev | Available Scripts
     npm run dev = Dev; npm run build = Build; npm test = Tests -->

<!-- Per-language Project Structure  
Python:
modules/
├── feature-a/
│   ├── FRD.md        # feature specs
│   └── BACKLOG.md    # feature real condition
├── feature-b/
│   ├── FRD.md
│   └── BACKLOG.md
└── ...

Rust:
crates/
├── feature-a/
│   ├── FRD.md        # feature specs
│   └── BACKLOG.md    # feature real condition
├── feature-b/
│   ├── FRD.md
│   └── BACKLOG.md
└── ...
TypeScript:
packages/
├── feature-a/
│   ├── FRD.md        # feature specs
│   └── BACKLOG.md    # feature real condition
├── feature-b/
│   ├── FRD.md
│   └── BACKLOG.md
└── ...
-->
```

---

## Section Contract

Every section is required unless marked optional. Each exists for one
reason.

| Section                               | Why it belongs here                                                                      |
| ------------------------------------- | ---------------------------------------------------------------------------------------- |
| One-liner (rec)                       | Decides in five seconds whether to keep reading. Watch for restating the project name.   |
| Prerequisites (required)              | Prevents a build failure with no cause. Watch for optional tooling listed as required.   |
| Quick Start (required)                | The 10-minute promise. Watch for steps that assume state the reader lacks.               |
| Architecture (required)               | Orientation before the file tree. Watch for a copy of the FRD system overview.           |
| Project Structure (required)          | Teaches where specs and backlogs live. Watch for every generated file listed.            |
| Available Scripts/Commands (required) | The daily loop, as CI runs it. Watch for flags that differ from the CI job.              |
| Configuration (required)              | What to set before the first run. Watch for values, secrets, or real hostnames.          |
| Testing (required)                    | How a contributor proves their change. Watch for a local variant of the gated command.   |
| Contributing (required)               | Branching and PR conventions, once. Watch for conflicts with `AGENTS.md`'s Git Workflow. |
| License (required)                    | Legally load-bearing for a reused repo. Watch when missing in a vendored or OSS tree.    |

---

## Verify

```bash
aa docs check . --strict
# Checks: readme-section-missing, dead-link, absolute-path, secret-in-docs, doc-length.
```
