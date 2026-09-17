# README.md — developer onboarding

Audience: a developer who just cloned the repo, possibly you in six months. Exactly **one per
project root**, 50–500 lines. Answers *how do I get this running, and where do I look next*.

Checked by `aa docs check`: `readme-section-missing`, `dead-link`, `absolute-path`,
`secret-in-docs`, `doc-length`. Invariants:
[SKILL.md → Invariants](../SKILL.md#invariants).

## Rules

1. **The test is time, not completeness.** Clone → install → build → run in under 10 minutes. If the
   Quick Start cannot clear that, the missing step is the bug in this file.
2. **Every command was actually run, and says how to confirm it worked.** A reader who cannot tell
   success from silence will assume failure and go ask a human.
3. **Prerequisites are the ones the build fails without**, with versions pinned. Optional tooling
   listed as required teaches readers to distrust the list.
4. **Link, do not restate** (`dead-link` catches the broken half). Requirements, API detail and
   status live in `PRD.md`/`FRD.md`/`BACKLOG.md`; a copied requirement drifts with no precedence rule
   to settle the disagreement.
5. **Testing and Commands show what CI runs**, verbatim — the same rule that gates
   `AGENTS.md` (`ci-command-drift`). A local variant teaches readers to pass a gate they fail in review.
6. **Configuration names variables and files, never values** (`secret-in-docs`). Use `<placeholders>`
   and repo-relative paths (`absolute-path`).
7. **Project Structure teaches the doc layout.** Showing `FRD.md` beside `BACKLOG.md` in each feature
   directory is where most readers learn the spec/status split.
8. **50–500 lines** (`doc-length`). Beyond that, split by audience — that is what the other four
   documents are for.

## Exemplar

Weak — three commands, none of which a clean machine can finish:

```markdown
## Quick Start
1. Install the dependencies
2. Run the app
3. Open http://localhost:8000
```

Strong — copy-pasteable, pinned, self-confirming, and it names the failure the reader will hit:

````markdown
## Quick Start

```bash
uv sync --python 3.12                      # creates the venv at .venv/, ~20 s
uv run demo ingest fixtures/sample.json    # exits 0 and prints "12 rows in 0.4s"
```

Nothing prints `12 rows`? `uv --version` must be ≥ 0.4 — older releases skip `--python` and build the
venv against your system 3.13, where `demo` has no wheel.

Next: [PRD.md](PRD.md) for why, [modules/alpha/FRD.md](modules/alpha/FRD.md) for how,
[BACKLOG.md](BACKLOG.md) for what is actually finished.
````

The last line is the part most READMEs skip: it tells the reader which question each other document
answers, so they stop asking this one to answer all five.

## Template

```markdown
# <project-name>

> One-liner: what this project does and who it's for.

## Prerequisites

- <see per-language table below>
- <other dependencies>

## Quick Start

<see per-language table below — then make it self-confirming, like the exemplar above>

## Architecture

<High-level diagram or link to full docs>

## Project Structure

<see per-language block below>

## Available Scripts / Available Commands

<see per-language table below — Rust titles this section "Available Commands", Python and
TypeScript title it "Available Scripts">

## Configuration

<Environment variables, config files — names only, never values>

## Testing

<per-language test command, as CI runs it>

## Contributing

<Branching strategy, PR conventions>

## License

<License type>
```

## Per-language variables

| Language   | Prerequisites | Quick Start                                                             | Section title         | Command table rows                                                                        |
| ---------- | ------------- | ----------------------------------------------------------------------- | --------------------- | ----------------------------------------------------------------------------------------- |
| Python     | Python 3.10+  | `git clone ...` → `cd <project>` → `pip install -e .` → `python -m <package>` | Available Scripts     | `python -m <package>` = Run the package; `pytest` = Run tests; `ruff check .` = Lint code  |
| Rust       | Rust 1.70+    | `git clone ...` → `cd crates/<name>` → `cargo build` → `cargo run`            | Available Commands    | `cargo build` = Build the crate; `cargo test` = Run tests; `cargo run` = Run the binary    |
| TypeScript | Node 20+      | `git clone ...` → `cd <project>` → `npm install` → `npm run dev`              | Available Scripts     | `npm run dev` = Start development; `npm run build` = Build for production; `npm test` = Run tests |

Rust templates say `<crate-name>` / "this crate" where the shared template says `<project-name>` /
"this project", and `Build the crate` for the `cargo build` row.

## Per-language `## Project Structure`

Python:

```
modules/
├── feature-a/
│   ├── FRD.md        # feature specs
│   └── BACKLOG.md    # feature real condition
├── feature-b/
│   ├── FRD.md
│   └── BACKLOG.md
└── ...
```

Rust:

```
src/
├── lib.rs
├── modules/
└── ...
```

TypeScript:

```
packages/
├── feature-a/
│   ├── FRD.md        # feature specs
│   └── BACKLOG.md    # feature real condition
├── feature-b/
│   ├── FRD.md
│   └── BACKLOG.md
└── ...
```

## Section contract

Every **yes** row below is enforced: `aa docs check` reports `readme-section-missing` for a missing
one (warning-level, because heading names vary most here — see
[SKILL.md → Invariants](../SKILL.md#invariants)). Synonyms count: `Quickstart in 60 Seconds`
satisfies `Quick Start`. **rec** rows are judgement calls the gate leaves you.

| Section                     | Required | Belongs here because                            | Watch for                                  |
| --------------------------- | -------- | ----------------------------------------------- | ------------------------------------------ |
| One-liner                   | rec      | Decides in five seconds whether to keep reading. | Restates the project name.                 |
| Prerequisites               | yes      | Prevents a build failure with no cause.          | Optional tooling listed as required.       |
| Quick Start                 | yes      | The 10-minute promise.                           | Steps that assume state the reader lacks.  |
| Architecture                | yes      | Orientation before the file tree.                | A copy of the FRD system overview.         |
| Project Structure           | yes      | Teaches where specs and backlogs live.           | Every generated file listed.               |
| Available Scripts/Commands  | yes      | The daily loop, as CI runs it.                   | Flags that differ from the CI job.         |
| Configuration               | yes      | What to set before the first run.                | Values, secrets, or real hostnames.        |
| Testing                     | yes      | How a contributor proves their change.           | A local variant of the gated command.      |
| Contributing                | yes      | Branching and PR conventions, once.              | Conflicts with `AGENTS.md`'s Git Workflow.  |
| License                     | yes      | Legally load-bearing for a reused repo.          | Missing in a vendored or OSS tree.         |

## Verify

```bash
aa docs check . --strict          # sections, links, paths, secrets, length
grep -nE 'pytest|npm test|cargo test' README.md .github/workflows/*.yml
```

Then the check that is not a grep: on a machine that has never had the project, run the Quick Start
top to bottom and time it. Every place you had to think is a line the README is missing.

Done when a reader with a clean machine and no conversation history reaches a running program from
this file alone, and knows which of `PRD.md` / `FRD.md` / `BACKLOG.md` to open next.
