---
name: mnemosyne
description: "Universal local AI memory layer for cross-harness persistence (Antigravity, Hermes, OpenCode). Query and store episodic memories, temporal knowledge graph triples, scratchpad working memory, and shared multi-agent state using SQLite."
version: 1.0.0
author: agents-arwaky
license: MIT
metadata:
  tags: [memory, sqlite, knowledge-graph, cross-harness, episodic, triples]
---

# Mnemosyne — Universal Agent Memory Layer

Mnemosyne is the unified, 100% local, zero-cloud memory system for `agents-arwaky`. It provides cross-harness persistence so that **Antigravity**, **Hermes**, and **OpenCode** share a single source of truth for facts, user preferences, architecture decisions, and task continuity.

---

## 🧠 Core Memory Types

1. **Episodic & Semantic Memories:**
   - Long-term facts, decisions, learnings, and context.
   - Hybrid retrieval: BM25/FTS5 keyword search combined with dense vector embeddings.

2. **Temporal Triples & Knowledge Graph:**
   - Explicit relational knowledge: `(subject, predicate, object)` with validity windows (`valid_from`, `valid_until`).
   - Query connected entities, dependency paths, and evolving truths over time.

3. **Scratchpad (Working Memory):**
   - Fast, ephemeral notes across tool steps within active tasks.

4. **Shared Multi-Agent Memory:**
   - Distinct namespace for memories visible and actionable across all harnesses and agents.

---

## 🛠️ MCP Tool Reference (`mnemosyne`)

### 1. Episodic & Long-Term Memory
- `mnemosyne_remember`: Store a memory with content, tags, importance, and optional bank.
  - Arguments: `content` (string, required), `tags` (array of strings), `importance` (float 0.0-1.0), `bank` (string).
- `mnemosyne_recall`: Retrieve memories relevant to a query using hybrid search.
  - Arguments: `query` (string, required), `k` (limit, default 5), `bank` (string), `threshold` (float).
- `mnemosyne_get`: Fetch a specific memory by its ID.
- `mnemosyne_update`: Update existing memory text or metadata.
- `mnemosyne_forget`: Delete or soft-delete a memory by ID.

### 2. Cross-Agent Shared Memory
- `mnemosyne_shared_remember`: Store memory directly into the shared multi-agent bank.
- `mnemosyne_shared_recall`: Query shared multi-agent knowledge.
- `mnemosyne_shared_forget`: Remove a shared memory entry.
- `mnemosyne_shared_stats`: Inspect counts and status of shared memories.

### 3. Knowledge Graph & Temporal Triples
- `mnemosyne_triple_add`: Add a semantic triple:
  - Example: `subject="agents-arwaky"`, `predicate="uses_harness"`, `object="hermes"`
- `mnemosyne_triple_query`: Search triples by subject, predicate, or object.
- `mnemosyne_triple_end`: Close the validity interval of a triple when facts change.
- `mnemosyne_graph_query`: Traverse graph nodes and outgoing/incoming relationships.
- `mnemosyne_graph_link`: Create an explicit connection between two memories.

### 4. Working Memory (Scratchpad)
- `mnemosyne_scratchpad_write`: Save fast notes for the current session.
- `mnemosyne_scratchpad_read`: Read current scratchpad contents.
- `mnemosyne_scratchpad_clear`: Clear working scratchpad.

### 5. Maintenance & Hygiene
- `mnemosyne_stats`: Get memory counts, bank distributions, and storage metrics.
- `mnemosyne_sleep`: Run offline memory consolidation, decay calculation, and graph refinement.
- `mnemosyne_diagnose`: Health check and database integrity check.

---

## 💻 CLI Usage (`aa run mnemosyne` or `mnemosyne`)

The CLI provides quick management from the command line:

```bash
# Health check
mnemosyne doctor

# Remember a fact
mnemosyne remember "User prefers concise answers and standard library over dependencies." --tags preference,style

# Recall memories
mnemosyne recall "user preference style"

# View memory statistics
mnemosyne stats

# Consolidate and sleep
mnemosyne sleep

# Start MCP server manually (stdio)
mnemosyne mcp
```

---

## 🔒 Storage & XDG Paths

All data is stored locally and securely in compliance with the XDG specification:
- **Database:** `${XDG_DATA_HOME:-$HOME/.local/share}/mnemosyne/mnemosyne.db`
- **Config & Banks:** `${XDG_CONFIG_HOME:-$HOME/.config}/mnemosyne/`
- **MCP Launcher:** `${XDG_BIN_HOME:-$HOME/.local/bin}/mnemosyne-mcp`
- **CLI Launcher:** `${XDG_BIN_HOME:-$HOME/.local/bin}/mnemosyne`
