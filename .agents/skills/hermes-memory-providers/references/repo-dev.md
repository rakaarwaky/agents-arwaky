# Mnemosyne repo & dev context (local mirror)

Canonical: `skills/memory/mnemosyne/references/repo-dev.md`. BEAM is
the core store (working + episodic memory, triples/graph edges, sync
log); recall is vector + FTS5 hybrid; only `scope='global'` memories
sync. Codebase is vendored at `vendor/mnemosyne`. Load the canonical
file for schema, data model, and `skip_contexts` gating.
