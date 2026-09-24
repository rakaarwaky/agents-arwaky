# Mnemosyne — repo & devops context

Load this when working on the mnemosyne **codebase** itself — its repo, sync
server, memory databases, or CI — or when a sync/import/recall behaviour looks
wrong. For ordinary "remember / recall this" questions you do not need it.

This host vendors it as a git submodule at `vendor/mnemosyne` (URL
`github.com/mnemosyne-oss/mnemosyne`, `ignore = dirty` in `.gitmodules`). Do not
assume push access: authority over that repo is the operator's call, so check
remote and permissions before promising a push or a merge.

**Any point-in-time fact below (open issues/PRs, versions, CI shape) can be
stale.** Confirm with `gh`, the installed `mnemosyne`, or a fresh recall before
acting on it. The durable model and the conventions change slowly; the numbers do
not.

## Architecture (mental model)

- **BEAM** is the core store. Tables: `working_memory` (live), `episodic_memory`
  (consolidated summaries), `triples` + `graph_edges` (knowledge graph),
  `annotations` (entity mentions / facts), `memory_events` (sync log), plus
  `memoria_*` tables for structured recall.
- **Recall** is hybrid: vector + FTS5 + importance (+ optional temporal boost);
  weights are tunable per query or via env.
- **Scope** matters everywhere: `scope='global'` is durable, cross-session and
  the only thing sync replicates; `scope='session'` is conversation-local and
  never synced. Most memories are session-scoped.
- **Consolidation** ("sleep") compresses old working memories into episodic
  summaries and runs on a daemon thread.

## Sync / surface model — the thing people get wrong

`mnemosyne sync` does **NOT** replicate the private DB. It replicates a **shared
surface**: a *separate, dedicated* DB containing only `scope='global'` rows
tagged with a `sync_surface_id`.

- Pointing sync at a private `mnemosyne.db` **fails** with
  `surface-only sync requires a dedicated DB with no unowned working rows`. Use a
  dedicated relay DB (`sync-init` / `sync-serve --initialize-surface`).
- An empty surface → every sync reports 0 objects. That is correct, not a bug.
- Push is **reconciliation**: `_discover_local_mutations()` diffs the surface's
  `working_memory` against `sync_memory_state` and emits create/update/delete
  events. It does not send a hand-written event log.
- **Dedup is by event identity** (`event_id`) plus a content-hash integrity
  guard; `INSERT OR IGNORE` on the event PK and the `known_states` check make
  pull/push **idempotent** (retrying after a failure re-processes the same events
  safely, no duplicate memories). It does NOT dedup two *different* events that
  happen to carry identical text.
- **Conflicts**: last-writer-wins by (timestamp → importance → device_id), with
  v2 causal-chain resolution via `parent_event_ids`.
- To share existing memories you must put them on the surface
  (`sync-init --claim-existing` on an all-global DB, or write global memories
  directly to the surface). To mirror an entire DB **including session
  memories**, use export/import, not sync.
- The relay server is normally `mnemosyne sync-serve` bound to loopback and
  reverse-proxied; it serves `/sync/pull|push|status` and `/healthz`. A
  read-only **dashboard** UI runs on a separate port and is *not* a sync server —
  pointing `sync_remote` at it 404s every `/sync/*` call. Hosts, addresses,
  service definitions and credential paths are operator-specific and deliberately
  not documented in this repo.

## What actually runs on this host

Verified, and it contradicts the usual "pipx install" story:

- `~/.local/bin/mnemosyne` and `~/.local/bin/mnemosyne-mcp` are ~285-byte **uv
  wrapper scripts**, not pipx venvs and not copies. Each execs
  `uv run --extra mcp --directory "$AGENTS_ARWAKY_ROOT/vendor/mnemosyne" mnemosyne …`,
  with `AGENTS_ARWAKY_ROOT` defaulting to this repo. `~/.local/share/pipx/` does
  not exist here.
- **So the CLI and MCP server run the submodule checkout.** An edit to
  `vendor/mnemosyne` is live on the next invocation — there is no
  "merged but not released yet" gap locally, and no reinstall step. (The flip
  side: don't claim upstream is fixed on a user's machine from local behaviour;
  releases move at their own pace.)
- Every call prints a benign `warning: VIRTUAL_ENV=… does not match the project
  environment path .venv and will be ignored` from uv. Ignore it; `--active`
  targets the outer env instead if you really want to silence it.
- Data lives in `~/.local/share/mnemosyne/` (`config.yaml`, `mnemosyne.db`,
  `banks/`), **not** `~/.config/mnemosyne/`. Config precedence is
  `config.yaml` > env > default, so exported env vars can be silently shadowed
  by a pinned key in that file — and many keys need a process restart
  (`mnemosyne config reload` for a live provider). See issue **#482**.

## Dev workflow

- **Tests**: run them from the checkout's own venv —
  `.venv/bin/python -m pytest tests/<file> -q` at
  `~/agents-arwaky/vendor/mnemosyne`. `pytest` is a `dev` extra dependency, not
  part of the runtime install.
- Set **`MNEMOSYNE_NO_EMBEDDINGS=1`** for fast runs (equivalently `no_embeddings:
  true` in config.yaml — remember which one wins). Embedding-dependent tests
  are flaky without it because the model download gets rate-limited (`429`). CI
  defaults to this and caches the fastembed model dir.
- A wall-clock perf gate in the temporal-recall tests (sub-10ms budget) is a
  known flake under load: a single red there is usually noise, so re-run the job
  instead of "fixing" the code.
- **Ruff** is pinned exactly in the `dev` extra (read the pin; it was
  `ruff==0.15.22`) and CI's merge gate is `ruff check --select E9,F63,F7,F82`
  over the tree plus `ruff check --select F,RUF022 -- <changed files>` — a
  *changed-files* gate, so pre-existing violations are grandfathered and only new
  ones fail. `integrations/hermes/` has its **own nested `pyproject.toml`** with
  a broader selection (E,W,F,I,B,C4,UP), so lint it from that directory. On this
  host `ruff` is on PATH (`~/.local/bin/ruff`); otherwise `uvx ruff@<pin> check …`.
- **pytest config**: `--import-mode=importlib`, per-test `timeout = 300` so a
  deadlock reports as one named failing test rather than hanging the job to the
  workflow timeout.
- **CI matrix / required checks**: read `.github/workflows/ci.yml` (plus the
  other workflow files in that dir) rather than trusting a remembered job list.
  Watch a PR with `gh pr checks <n>` and re-run flakes with
  `gh run rerun <run-id> --failed`. Merging is gated on **green CI**; never merge
  with failing or pending required checks.
- **CLA**: the bot validates **commit** authors, not the PR author. Agent-identity
  commits break it; fix with `git commit --amend --author="Name <github-email>"`
  and force-push. If it won't re-trigger after a branch update, close and reopen
  the PR — `recheck`-style comments do not work.

## Release policy

- **Strict SemVer** from v3.1.2 onward (MAJOR = breaking, MINOR = feature,
  PATCH = bugfix); `RELEASING.md` documents it and `.githooks/pre-push` enforces
  tag format + version bump. Confirm the current floor before citing it.
- **Cadence**: substantial fixes and features are bundled into the next MAJOR
  rather than drip-fed as incremental MINORs. Meaningful new-surface PRs get
  reviewed now with the merge deferred to the MAJOR cycle; MINORs ship once enough
  additive opt-in features accumulate.

## Known gotchas / decided designs

- **No schema-level foreign keys (#503, closed as intentional)**:
  `PRAGMA foreign_keys=ON` broke ~22 tests that deliberately create orphan rows.
  Orphan cleanup is done at application level during sleep/consolidation.
- **Beam access is lock-serialized (#498 / #520)**: `_beam_access_lock` guards
  Beam/SQLite between the main thread and the `auto_sleep` daemon — a WAL
  checkpoint mid-statement once caused a SEGV. Do not introduce unguarded
  cross-thread Beam access.
- **Import idempotency (#538, merged)**: the annotation store's bulk import skips
  `(memory_id, kind, value)` UNIQUE collisions instead of aborting, so
  `mnemosyne import` is safely re-runnable.
- **Provider context gating**: `skip_contexts` in `config.yaml` (default
  `cron,flush,subagent,background,skill_loop`) disables the Hermes provider's
  prefetch and turn-sync in those contexts, overriding `sync_roles`. A memory
  that "should have been written" during a subagent or cron run was skipped by
  design, not lost to a bug.
- **Sync security**: auth is a bearer API key or JWT. A past JWT signature bypass
  was fixed — signatures are compared with `hmac.compare_digest` and the
  algorithm is pinned to HS256. The sync HTTP server is **off by default** in the
  Hermes plugin.
- **Diagnostics before theory**: `mnemosyne diagnose` reports deps, DB state and
  vector-search readiness (`--dry-run`, `--repair-vec-working` to backfill missing
  `vec_working` rows from `memory_embeddings`); `mnemosyne doctor` checks the
  install. `mnemosyne hygiene audit` (dry-run) ranks noise — terminal spam,
  stack traces, heartbeats, secrets — for a later `hygiene clean`.

## CLI cheat-sheet

`mnemosyne --help` is the only reliable help: per-subcommand `--help` is
swallowed as a positional argument (verified on `store`).

```
mnemosyne store <content> [source] [importance]     # NOT `remember`; no --tags
mnemosyne recall <query> [top_k]
mnemosyne update <id> <content> [importance] ;  mnemosyne delete <id>
mnemosyne stats | sleep | doctor | diagnose | repair | reindex | version
mnemosyne bank list|create|delete                    # banks are rows/subdirs of the DATA dir
mnemosyne export [file.json] [--include-sync-events] # read-only dump
mnemosyne import <file.json> [--force]               # merge into local DB
mnemosyne sync --db-path <surface.db> --remote <url> --api-key-file <f> --mode bidirectional
mnemosyne sync-init --db-path <surface.db> [--claim-existing --yes]
mnemosyne sync-serve --db-path <relay.db> --host 127.0.0.1 --port <p> --api-key-file <f> [--initialize-surface]
mnemosyne sync-status --db-path <surface.db> [--remote <url>] [--api-key-file <f>] [--json]
mnemosyne config reload|get|set|migrate              # hidden: absent from --help, but real
```

`mnemosyne config migrate` re-exports the current environment **into
`config.yaml`** — because the file outranks env vars, that freezes those values
and later env changes stop having any effect. `config set` likewise writes the
file and **erases its comments** (verified: a hand-written header block
disappeared and the new key was inserted in alphabetical order). Both are
reasons to hand-edit `config.yaml`, which its own header invites.

## Code navigation

The submodule is a normal Python package: `mnemosyne/` (core),
`mnemosyne/core/sync.py` (surface sync), `sync_server.py` (relay HTTP server),
`beam.py` (the store), `core/annotations.py` and `core/triples.py`. Check for a
`.codegraph/` index before grepping — if one exists, `codegraph_explore` returns
verbatim source plus call paths in one call; if not, grep/read normally.
Integration code for the Hermes provider lives under `integrations/hermes/`
(it has its own `pyproject.toml`, tests, and bundled skill).
