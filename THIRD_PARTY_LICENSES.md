# Third-Party Licenses & Attributions

This repository incorporates upstream open-source software as git submodules under `vendor/` and provides build automation and configuration glue under `tools/`. Below is a comprehensive record of third-party projects, their upstream sources, pinned revisions, and licenses.

---

## Submodule Inventory

| Component | Upstream Source | Pinned Commit / Ref | Upstream License |
|---|---|---|---|
| `vendor/context7` | [upstash/context7](https://github.com/upstash/context7) | `769c6cd2` | MIT License |
| `vendor/fetch-mcp` | [zcaceres/fetch-mcp](https://github.com/zcaceres/fetch-mcp) | `1ddb1a59` | MIT License |
| `vendor/anytype-mcp` | [anyproto/anytype-mcp](https://github.com/anyproto/anytype-mcp) | `4ba725d9` (`v1.2.10`) | MIT License |
| `vendor/codegraph` | [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) | `c6aaa203` | MIT License |
| `vendor/omniroute` | [diegosouzapw/OmniRoute](https://github.com/diegosouzapw/OmniRoute) | `8489c9f` (release/v3.8.52) | MIT License |

---

## Upstream Licenses

### 1. Context7

- **Project:** Context7
- **Author:** Upstash, Inc.
- **URL:** [https://github.com/upstash/context7](https://github.com/upstash/context7)
- **License:** MIT License

### 2. Fetch-MCP

- **Project:** Fetch MCP
- **Author:** Zach Caceres
- **URL:** [https://github.com/zcaceres/fetch-mcp](https://github.com/zcaceres/fetch-mcp)
- **License:** MIT License

### 3. Anytype MCP

- **Project:** Anytype MCP Server
- **Author:** Any Association
- **URL:** [https://github.com/anyproto/anytype-mcp](https://github.com/anyproto/anytype-mcp)
- **License:** MIT License (upstream NOTICE available at [github.com/anyproto/anytype-mcp](https://github.com/anyproto/anytype-mcp))

### 4. CodeGraph

- **Project:** CodeGraph
- **Author:** Colby McHenry
- **URL:** [https://github.com/colbymchenry/codegraph](https://github.com/colbymchenry/codegraph)
- **License:** MIT License

### 5. OmniRoute

- **Project:** OmniRoute
- **Author:** Diego Souza and contributors
- **URL:** [https://github.com/diegosouzapw/OmniRoute](https://github.com/diegosouzapw/OmniRoute)
- **Pinned at:** `8489c9f` (branch `release/v3.8.52`); runtime installed from npm `omniroute@3.8.51`
- **License:** MIT License
- **Note:** the submodule is the version SSOT only. The runtime comes from the published
  npm package rather than a source build, because upstream's `postinstall` compiles native
  SQLite bindings and the tarball already ships a built tree.