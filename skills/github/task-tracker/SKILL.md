---
name: task-tracker
description: >
  Map incomplete tasks from AES-architecture spec documents (PRD, ROADMAP, BACKLOG, FRD,
  DESIGN, plus module and package feature docs) into modular, deduplicated GitHub tracking
  issues. Scans every State Definitions table, classifies each row as incomplete,
  done-verified, or done-but-stale, verifies against git and GitHub, and opens one issue
  per task — tracking only, with no implementation. Use when the user runs /task-tracker,
  asks to map backlog tasks to GitHub issues, or asks for doc-sync tracking.
when-to-use: >
  /task-tracker, map incomplete tasks to GitHub issues, create tracking issues from
  ROADMAP or BACKLOG, audit document states against reality, doc-sync issues for stale
  spec documents
argument-hint: <repo-root> [--dry-run] [--state-label task-tracker]
---

# Task Tracker — AES spec states → modular GitHub tracking issues

One run covers one repo. It reads the spec-document states, proves which rows are real
work, which are already open issues, and which are stale doc text, and opens a modular
issue per finding. The run outputs GitHub issues only. It never edits source code,
never creates a branch, never opens a PR.

## Scope

The skill is repo-agnostic: any AES-architecture repo that keeps spec documents inside
the repo tree works. Discover scope at run time with the two rules below; do not
assume a layout.

**In scope** — any `.md` that either:
1. Contains a `## State Definitions` or `### State definitions` heading (the authoritative vocabulary table), or
2. Is a feature `BACKLOG.md`, `FRD.md`, or `DESIGN.md` listed by the root spec docs, or sits under a feature directory (`modules/`, `packages/`, `crates/`) and has a row table whose headers include `ID` (or `Feature` / `Branch`) and `State`.

**Out of scope** — any path whose first segment after the repo root starts with a dot
(`.git/`, `.agents/`, `.grok/`, `.venv/`, `.tox/`, `.pytest_cache/`, `.mypy_cache/`,
`.ruff_cache/`, `.idea/`, `.vscode/`, and any other dot-prefixed directory) —
dot-prefixed directories are always scratch, session, or tooling, never spec docs.
Also exclude build and template paths matching `node_modules|target|dist|__pycache__|htmlcov|coverage|junit|vendor|skills|references|workspaces-bad|workspaces-good`.

Prompt scratch files and skill reference templates quote the words "State Definitions"
without being specs — never include them.

## State sources

Two common layouts, both in scope:

| Shape | Where the state lives |
| --- | --- |
| Roadmap-owned | `ROADMAP.md` (or `ROADMAP.md`/`DESIGN.md` at root) holds the definitions, a backlog table, a phase plan, and a feature roll-up; feature `BACKLOG.md` files carry only their own row table |
| Backlog-owned | Root `BACKLOG.md` holds the definitions (`### State definitions`), the feature index, the roll-up, and the root row table; each feature `BACKLOG.md` declares its own doc-level `State: <value>` line plus its row table |

In the backlog-owned shape the doc-level `State:` line at the top of a feature backlog
is a real classification target in its own right — a feature still `In Progress` or
`Idea` while its row table is empty produces a tracking issue for the feature roll-up
row, not for the vanished rows.

If the repo uses neither shape exactly, follow the discovery rule and extract every
table that has both an ID (or Feature) column and a State column.

## State vocabulary

The five base states every AES repo carries:

| State | Meaning |
| --- | --- |
| Idea | Not examined; no spec. |
| Refinement | Being specced. |
| Ready | Specified; not started. |
| In Progress | Active now. |
| Blocked | Name the blocker in Actual Condition. |

Extended states seen in some repos: `In Review`, `QA`, `Done`, `Released`, `Deferred`.
The authoritative table for the current repo is its own State Definitions table —
parse it, do not assume the full vocabulary.

## Classification

| Row state | Classification | Action |
| --- | --- | --- |
| Idea, Refinement, Ready, In Progress, Blocked | `incomplete` | tracking issue |
| In Review, QA | `incomplete` | tracking issue, body notes the current gate |
| Deferred | `incomplete` | tracking issue, label `deferred`, body carries the reason |
| Done / Released with cited evidence (commit hash, merged PR number, published release) in the row | `skip` | no issue, ledger records the evidence |
| Done / Released with no cited evidence | `doc_sync` | doc-update issue |
| Any incomplete state where the work is provably finished (merged PR or release found via `gh` / `git log`) | `doc_sync` | doc-update issue |

A `Done` row whose evidence does not reproduce is `doc_sync`, never `skip`.

## Workflow

### Step 1 — discover

Run the discovery grep from the Scope section above, then walk feature directories
(`modules/`, `packages/`, `crates/` — whichever exist) and add every feature
`BACKLOG.md`, `FRD.md`, and `DESIGN.md` even when that file holds no definitions
table itself — its backlog table may still carry a `State` column.

### Step 2 — spawn scanner subagents

Spawn one subagent per doc group (group by directory so a repo with 15 features gets
15 parallel scanners plus 1 for the root docs). Scanner prompt, self-contained:

```text
You are a read-only scanner. Read the file <abs path to doc> in full.
1. Extract its State Definitions table; list the state names it defines. If the file
   has none, note that and continue — rows still count.
2. Extract every table row whose headers include ID (or Feature / Branch) and State.
   Also capture the doc-level "State: <value>" line at the top of a feature backlog.
3. For each row output one JSON object:
   {"id":"<row id>","title":"<item text>","state":"<verbatim state>","priority":"<P0/P1/P2 or —>","health":"<health or —>","source_doc":"<repo-relative doc path>","row_text":"<verbatim row text>"}
   State must appear in the source row verbatim. Do not infer, fill in, or normalize
   state values. A row without a state column value is {"id":...,"state":"unknown"}.
4. Return the JSON array. An empty array is valid only after reading the whole file.
```

Wait on all handles. Collect rows; dedupe on `(id, source_doc)`.

### Step 3 — classify

Apply the classification table above locally. For `stale_candidate` flags: any row whose
`Updated` date predates the newest commit touching its source doc.

```bash
git -C <repo-root> log -1 --format=%cd --date=short -- <source_doc>
```

### Step 4 — verify (read-only)

For every `incomplete` and every `stale_candidate` row:

```bash
gh issue list --state open --search "<row id> in:title" --json number,title
gh pr list --state merged --search "<row id>" --json number,title,mergedAt
```

Verdicts:

| Verdict | Meaning | Action |
| --- | --- | --- |
| `open` | no open issue for this row | create a tracking issue |
| `exists` | open issue already tracks it | comment freshness, no new issue |
| `doc_sync` | work is done (merged PR / release) but the doc still says otherwise | create a `[DOC-SYNC]` issue |
| `skip` | Done/Released with reproducing evidence | ledger only |

For `done` rows claiming a commit: `git merge-base --is-ancestor <sha> HEAD` (or `git
cat-file -e <sha>`) to confirm the commit exists in the repo.

### Step 5 — open modular issues

One row, one issue. A row whose `Next Action` or `Item` text lists two or more
independent deliverables (separable by a semicolon / comma with distinct objects)
splits into one issue per deliverable; each split issue carries the parent row id in
its title and lists the siblings in its body.

**Title format**

```text
[BACKLOG] <ROW-ID> — <one-line task summary>        # root rows
[<feature>] <ROW-ID> — <one-line task summary>       # feature-scoped rows
[DOC-SYNC] <ROW-ID> — <doc path> still reports <stale state>
```

The feature tag is the lowercase directory name of the owning feature (e.g. `browser`,
`cli`, `api`, `compositor`); for Rust workspaces use the crate name.

**Body**

````markdown
Source: `<source_doc>` · row `<ROW-ID>` · scanned by `/task-tracker` on `<date>`

| Field | Value |
| --- | --- |
| State (doc) | <verbatim state> |
| Priority | <P0/P1/P2 or —> |
| Health | <health or —> |
| Owner | <owner or —> |
| Target | <target date or —> |
| Classification | incomplete / doc_sync |

## Task
<verbatim Next Action / Item text>

## Evidence in doc
> <verbatim Actual Condition / row text>

## Verification
<for doc_sync: the gh/git evidence that the work is done>
<for incomplete: the open-issue check result (none found / issue #N already open)>

## Tracking only
This issue tracks the task. Implementation lands in its own PR and closes this
issue with verification evidence (commit + command output). For a `[DOC-SYNC]`
issue, the fix is the document edit aligning the state with reality.
````

**Labels** (create on first use, then reuse): `task-tracker`, one `state:<doc-state>`,
one of `p0` / `p1` / `p2`, plus `doc-sync` for the doc_sync class and `deferred` for
Deferred rows. Pass the tracker label through as a single arg so a team can keep
different repos distinct.

**Dry run**: `--dry-run` executes steps 1–4 and prints every would-be title, body, and
label without calling `gh issue create`.

### Step 6 — ledger + report

Append one JSON object per row to `<repo-root>/docs/task-tracker-ledger.jsonl`:

```json
{"run":"YYYY-MM-DD","row":"<ROW-ID>","doc":"<source_doc>","state":"<state>","priority":"<P0/P1/P2>","class":"<incomplete|doc_sync|skip>","issue":<issue-number>,"action":"<created|commented|skipped-exists|skipped-evidence>"}
```

`action` values: `created`, `commented`, `skipped-exists`, `skipped-evidence`.

Close with a count table: `rows scanned N | incomplete A | doc_sync B | skipped C |
created X | commented Y`.

## Personas

The workflow ships as `workflows/task-tracker.rhai` in this repo, runnable as
`/task-tracker <repo-root>` once `~/.grok` symlinks resolve to this tree. It drives
the four personas, defined in `personas/task-tracker-*.toml`:

| Persona | Capability | Role |
| --- | --- | --- |
| `task-tracker-scanner` | read-only | extracts state table + rows as JSON |
| `task-tracker-classifier` | read-only | buckets rows, flags stale candidates |
| `task-tracker-verifier` | read-only + GitHub API | dedupe + stale checks, verdicts |
| `task-tracker-issuer` | write (GitHub issues only) | creates / comments issues |

## Completion criteria

- [ ] Every row from every in-scope doc appears in the ledger with a class.
- [ ] Every `incomplete` row maps to exactly one open issue (created, commented, or pre-existing).
- [ ] Every `doc_sync` row maps to an open `[DOC-SYNC]` issue.
- [ ] No `skip` row dropped silently — each has its evidence cited in the ledger.
- [ ] No file changed outside `docs/task-tracker-ledger.jsonl`.
- [ ] No branch, PR, or code change created.
