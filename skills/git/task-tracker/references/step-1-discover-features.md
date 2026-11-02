# Step 1 — discover features

Enumerate feature directories (`modules/`, `packages/`, `crates/` — whichever exist) and
the root spec docs. One discovery agent; output is a feature table:

```json
{"root": ["ROADMAP.md", "BACKLOG.md"], "features": [
  {"name": "tools", "dir": "modules/tools", "docs": ["modules/tools/FRD.md", "modules/tools/BACKLOG.md"]},
  {"name": "skills", "dir": "modules/skills", "docs": ["modules/skills/FRD.md", "modules/skills/BACKLOG.md"]}
]}
```

Also record the repo's State Definitions vocabulary per doc so later phases quote the
right state names.
