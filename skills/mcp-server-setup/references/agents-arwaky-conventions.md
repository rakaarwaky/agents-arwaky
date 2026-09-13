# agents-arwaky collection conventions

User's personal collection at `/home/raka/SharedData/agents-arwaky` (HARD DISK, not SSD home —
user explicitly wants it there). GitHub: rakaarwaky/agents-arwaky.

## Wrapper rule (learned the hard way)

Top-level submodules MUST point at the user's OWN wrapper repos (`rakaarwaky/<name>`), never
directly at upstream. Upstream source is vendored as a NESTED directory inside the wrapper repo.

Correct pattern (contex7-arwaky, anytype-arwaky):

```
agents-arwaky/
└── anytype-arwaky/               # submodule -> github.com/rakaarwaky/anytype-arwaky
    ├── anytype-mcp/              # upstream (anyproto/*), vendored nested inside
    ├── scripts/install.sh        # local build -> dist/
    ├── <name>_arwaky_local.json  # MCP config snippet, ABSOLUTE paths to SharedData
    └── README.md                 # explains upstream origin
```

## Wrapper repo contents (per convention)

- Nested upstream dir (git history removed or kept as needed)
- `scripts/install.sh`: absolute `BASE_DIR="/home/raka/SharedData/agents-arwaky/<name>"`, builds
  into `dist/`. Note: bun is NOT installed on this machine — use npm/npx/esbuild equivalents.
- `<name>_arwaky_local.json` with absolute path to dist output
- README documenting layout, prerequisites, update procedure (`cd upstream && git pull && rebuild`)

## Workflow gotchas

- The HDD copy is the LIVE repo; the user may have uncommitted local changes there. Never clone a
  fresh copy over it — copy new work in and commit ONLY the new files unless told otherwise.
- git identity may be unset in fresh clones; set repo-local `user.name "rakaarwaky"` /
  `user.email "rakaarwaky@users.noreply.github.com"`.
- Pushes may hit divergence (remote has newer commits); resolve with merge, verify no content
  conflicts, push. `gh auth` is already logged in as rakaarwaky.
- After moving an MCP server's binary path, re-run `hermes mcp remove/add/test`.
