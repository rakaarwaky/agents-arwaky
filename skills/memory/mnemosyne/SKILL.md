---
name: mnemosyne
description: Local SQLite memory with sync and recall. Use when storing episodic memories, facts, triples.
metadata:
  tags:
    - memory
    - sqlite
    - knowledge-graph
    - cross-harness
    - episodic
    - triples
---

# Mnemosyne — Universal Agent Memory Layer

Mnemosyne is the unified, 100% local, zero-cloud memory system for
`agents-arwaky`: one SQLite-backed source of truth for facts, user preferences,
architecture decisions, and task continuity, reachable from every harness either
as MCP tools (`mnemosyne_remember`, `mnemosyne_recall`, …) or as the
`mnemosyne` CLI.

Load the reference file only when you are working on the memory system itself:
`references/repo-dev.md` (repo, sync server, memory databases, CI, release
policy, gotchas).

---

## Durable memory rule

Decide **per harness**, not by habit. Before ANY memory write ask: *"Is this
durable — would I want it next session?"* If no (current todo list, temp flag),
keep it in ephemeral/session state. If yes, route it to the store that harness
actually reads:

| Harness | Where durable memory goes |
|---|---|
| **Hermes** | **Mnemosyne** — `mnemosyne_remember` / `mnemosyne store`. Hermes' legacy `memory` tool is a last resort: it has a tiny character cap and no vector recall, so use it only for ephemeral session state, and never for user preferences, credentials, or project conventions. |
| **Qwen Code** | Its **native file-based memory**: `~/.qwen/memories/` (cross-project, about the user) and `~/.qwen/projects/<project-slug>/memory/` (this project only) — one frontmatter file per memory in a type subdirectory, plus a one-line pointer in that directory's `MEMORY.md`. Do not "fix" this by also writing to Mnemosyne; the harness reads its own files. |
| Any other harness with its own memory contract (AGENTS.md-style instructions, a native memory dir, a plugin) | Follow **that** harness's native mechanism. Reach for Mnemosyne only for a fact that must be shared *across* harnesses. |

Rules that hold on every harness:

- **Never duplicate a fact into two stores.** One store is authoritative per
  harness; a second copy silently rots and then contradicts itself on recall.
  Migrating: save to the new store first, then remove the old entry, so nothing
  is lost and nothing is doubled.
- **Scope is the durability switch**: `scope="global"` for anything that must
  outlive the conversation (and, on Hermes, is the only scope sync ever
  replicates); `scope="session"` for conversation-local notes. On this host
  `config.yaml` ships `default_scope: session`, so state the scope explicitly
  instead of relying on a default.
- **Importance is the recall switch**: ≥0.7 for anything you want retrieved
  later, ≥0.9 for identity and standing user preferences. Passive aging is not
  deletion — correct a known-wrong fact with `mnemosyne_update`, or
  `mnemosyne_invalidate` it (optionally naming the `replacement_id` so the chain
  is traceable), or hard-delete with `mnemosyne_forget`.
- **Wrong-tool reflex is a known failure mode**: if you catch yourself writing a
  durable fact to a legacy/harness-local memory store (or a file-based memory
  store to Mnemosyne), cancel the call, redo it against the table above, and
  clean up the stray entry.
- Ephemeral scratchpad (`mnemosyne_scratchpad_write`) is for in-task notes only;
  it is not durable storage.

## 🧠 Core Memory Types

1. **Episodic & Semantic Memories** — long-term facts, decisions, learnings,
   context. Retrieval is hybrid: dense vector similarity + FTS5/BM25 keyword
   rank + importance (+ optional temporal boost), weights tunable per query.
2. **Temporal Triples & Knowledge Graph** — `(subject, predicate, object)` with
   validity windows (`valid_from`, `valid_until`); `as_of` queries replay what
   was true on a past date. `mnemosyne_triple_add` **supersedes** the prior fact
   with the same subject+predicate by default (that is how a fact ends — there is
   no separate "close the interval" call); pass `supersede=false` only for
   genuinely multi-valued predicates.
3. **Canonical self-facts** — one authoritative value per `(category, name)`
   slot (identity, voice, standing preferences), so restating cannot produce two
   contradicting copies; a new body supersedes the old one, which is kept as
   history (`mnemosyne_recall_canonical … include_history=true`).
4. **Scratchpad (Working Memory)** — fast, ephemeral notes across tool steps.
5. **Shared Multi-Agent Memory** — a separate surface DB of `global` rows
   visible to every agent and replicated by `mnemosyne sync` (the sync/surface
   model is the thing most people get wrong → `references/repo-dev.md`).

## 🛠️ MCP Tool Reference (`mnemosyne`)

Tool names are `mnemosyne_*` on Hermes (provider-registered) and may arrive
prefixed by your MCP client (e.g. `mcp__mnemosyne__recall`). Do not hardcode a
tool count — enumerate what your client exposes.

- **Read / write memories** — `mnemosyne_remember` (`content`, `importance`
  0.0–1.0, `scope` `session`|`global`, `source`, `veracity`, `valid_until`,
  `metadata`, `extract_entities`, `extract`), `mnemosyne_recall` (`query`,
  `limit`, per-query `vec_weight`/`fts_weight`/`importance_weight`/
  `temporal_weight`, `query_time`, `explain`), `mnemosyne_get`,
  `mnemosyne_update`, `mnemosyne_invalidate`, `mnemosyne_forget`,
  `mnemosyne_batch` (atomic `remember`/`update`/`forget`/`invalidate` list,
  `dry_run` available).
- **Canonical slots** — `mnemosyne_remember_canonical`,
  `mnemosyne_recall_canonical`, `mnemosyne_forget_canonical`.
- **Triples & graph** — `mnemosyne_triple_add`, `mnemosyne_triple_query`
  (case-insensitive subject; `as_of` for point-in-time), `mnemosyne_graph_query`
  (BFS from a seed id, `max_hops`/`edge_type`/`min_weight`),
  `mnemosyne_graph_link`.
- **Shared surface** — `mnemosyne_shared_remember`, `mnemosyne_shared_recall`,
  `mnemosyne_shared_forget`, `mnemosyne_shared_stats`.
- **Scratchpad** — `mnemosyne_scratchpad_write`, `_read`, `_clear`.
- **Maintenance & trust** — `mnemosyne_stats`, `mnemosyne_sleep`
  (consolidation; `all_sessions=true` / `force` / `dry_run`),
  `mnemosyne_diagnose` (deps, DB state, vector-readiness; `repair_vec_working`),
  `mnemosyne_hygiene_audit` (ranked noise candidates; dry-run only) →
  `mnemosyne_hygiene_clean` (needs `confirm=true`; `delete`|`archive`|`flag`),
  `mnemosyne_validate` (attest/update/invalidate/delete a memory you did not
  author; records validator + note).

There is no `mnemosyne_triple_end`: end a fact by re-adding it superseded, or
give it a `valid_until`.

## 💻 CLI Usage (`mnemosyne`, or `aa tool run mnemosyne`)

Arguments are **positional** — there is no `--tags`, and **no `remember`
subcommand** (`store` is the verb):

```bash
mnemosyne doctor            # dependency + install check
mnemosyne diagnose          # DB / vector-search readiness (--dry-run, --repair-vec-working)
mnemosyne store "User prefers concise answers and standard library over dependencies." preference 0.9
mnemosyne recall "user preference style" 5
mnemosyne update <id> "corrected text" 0.8
mnemosyne delete <id>
mnemosyne stats
mnemosyne sleep
mnemosyne bank list         # logical banks; they are rows, not directories
mnemosyne mcp               # start the MCP server (stdio; --transport sse|streamable-http)
```

Other verbs worth knowing: `export [file.json] [--include-sync-events]`,
`import <file.json>` (idempotent), `import-hindsight`, `hygiene audit|clean`,
`reindex`, `backup`/`restore`/`verify`/`backups`, `sync`, `sync-init`,
`sync-serve`, `sync-status`, `sync-generate-key`, `profile`, `repair`,
`migrate`, `version`.

Two CLI traps, both verified on this build:

1. **`mnemosyne config` exists but is hidden** — `--help` does not list it, yet
   `mnemosyne config reload|get|set|migrate` all work. Use `config get <key>` to
   read the effective value.
2. **`config set <key> <value>` rewrites `config.yaml` and drops its comments**
   (the file's own header explaining precedence is the first casualty). Prefer
   editing the YAML in place, which its header explicitly invites
   ("edit freely, hot-reload with `mnemosyne config reload`").

## 🔒 Storage & XDG Paths

- **Data dir (everything lives here):**
  `${XDG_DATA_HOME:-$HOME/.local/share}/mnemosyne/` → `mnemosyne.db` (WAL mode,
  so `-shm`/`-wal` sidecars appear while a server holds it open), `config.yaml`,
  and `banks/`. Banks are **logical** (list them with `mnemosyne bank list`;
  only `default` — the main DB itself — exists on this host); `banks/` stays
  empty until something creates a named bank, so do not infer the bank set from
  a directory listing. There is **no** `${XDG_CONFIG_HOME}/mnemosyne/` on this
  host — do not look for config there.
- **Precedence:** `config.yaml` > env var > built-in default, and the file pins
  `data_dir: ~/.local/share/mnemosyne`. That pin means `MNEMOSYNE_DATA_DIR`
  (which `aa connect` injects into harness `.env` files) does **not** relocate
  the store by itself — edit `data_dir` in `config.yaml` instead. Many keys need
  a process restart (`mnemosyne config reload` for a live provider).
- **Launchers:** `~/.local/bin/mnemosyne` and `~/.local/bin/mnemosyne-mcp` are
  285-byte **uv wrappers**, not pipx venvs and not copies: each execs
  `uv run --extra mcp --directory "$AGENTS_ARWAKY_ROOT/vendor/mnemosyne"
  mnemosyne …` (`AGENTS_ARWAKY_ROOT` defaults to `/home/raka/agents-arwaky`).
  So editing the vendor checkout changes what the installed command runs, and
  every invocation prints a harmless
  `warning: VIRTUAL_ENV=… does not match the project environment path .venv`
  line from uv.
- Hermes-side state (`~/.hermes/mnemosyne/data/`) and the provider-plugin install
  are covered by the `hermes-memory-providers` skill.

## References

- `references/repo-dev.md` — load for any dev/devops task on the mnemosyne repo
  itself: BEAM schema, the sync/surface data model, test + lint + CI workflow,
  release policy, contributor norms, and issue-numbered gotchas.
- `hermes-memory-providers` skill — installing Mnemosyne as a Hermes memory
  provider, and the built-in MEMORY.md/USER.md contract it replaces.
