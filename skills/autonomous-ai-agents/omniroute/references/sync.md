# 9router sync

9router (port 20128) stores its runtime data in SQLite at `~/.9router/db/data.sqlite`
(not the JSON export files). The JSON files in `config/` are exports/backups.

When syncing OmniRoute providers/models/combos into 9router's SQLite:

- The `combos` table has a `kind` column that must be `'llm'` (not null). A null
  `kind` crashes the dashboard combos page with `t.includes is not a function`.
- Combo `models` is stored as a JSON string in the `models` column.
- Provider connections in 9router share the same IDs as OmniRoute's, so sync by
  updating existing rows rather than inserting duplicates.
- 9router requires a restart (`systemctl --user restart 9router`) after DB edits.

**Frontend crash with models present:** Even with `kind='llm'`, the combos page
may still crash (`t.includes is not a function`) when any combo has models. The
root cause is in the pre-built Next.js frontend (`page-*.js`), not the data.
The frontend is a compiled bundle in `.next-cli-build/` — it cannot be patched
without the source. If the page breaks after a sync, remove models from combos
(temporarily set `models='[]'`) to restore dashboard access, then investigate
the frontend separately.

**Never delete `.next-cli-build/`:** The 9router app requires this pre-built
cache to start. Deleting it causes `Could not find a production build`. Restore
by reinstalling: `npm install -g 9router` (recreates the cache).
