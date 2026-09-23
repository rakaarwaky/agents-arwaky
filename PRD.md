# PRD — agents-arwaky

> Product Requirements Document. Describes WHAT this project does and WHY.
> Audience: Stakeholders, PM, Design, Engineering leads.
> Real condition lives in [BACKLOG.md](BACKLOG.md); this file is specification only.

## Problem Statement

An operator maintaining a polyglot AI-tool ecosystem (Rust linters, Python MCP
servers, npm/bun/pnpm upstreams, in-house agents, 2 daemons, and an agent-skill
pack) faces three daily failures. First, every tool needs its own install/update/
uninstall path, so adding one tool means a new script plus a new entry in a dozen
places. Second, AI coding harnesses (Hermes, OpenCode, Grok Build, Qwen Code)
each discover MCP servers and skills differently, so "connect everything" is
re-litigated by hand. Third, the architecture layering (7 AES layers, naming
conventions, per-tool XDG paths) is enforced in the agent's head, not in the
code — so drift accumulates silently and "is this repo consistent?" has no answer.

## Goals & Success Metrics

| # | Goal | Measurement | Target |
|---|------|-------------|--------|
| 1 | One-command tool lifecycle: install, update, uninstall of any registered tool resolves from a single manifest, not per-tool scripts scattered by hand | `aa tool install <id>` succeeds for every tool id in `config/manifest.json` on a clean host | 100% of manifest tools |
| 2 | One-command harness connection: MCP config and skill provisioning for every supported harness is generated and verified | `aa connect --all` exits 0 and `aa mcp list` reports every server in the manifest as reachable | 100% of servers |
| 3 | Architecture compliance is machine-checked: every module obeys AES 7-layer naming, flat shared layout, no contract in shared | `aa check` exits 0 on the tree | 0 errors |
| 4 | Real-condition is tracked per feature: a spec row and a backlog row exist together, and every `Done` claim cites a re-runnable command + commit | `aa check docs .` exits 0 | 0 errors |
| 5 | New-tool onboarding is a single-file data change: adding a tool to the manifest produces a working install/update/uninstall/runner | a new manifest entry passes `aa check` and `aa tool install <id>` without new module code | 1 tool = 0 new modules |

## User Personas

- **The operator on a fresh machine**: clones the repo, runs the provisioner, and
  gets a working multi-agent toolchain in under ten minutes. Done = `aa doctor`
  green and `aa check` passing with no manual path fixes.
- **The tool maintainer**: adds or upgrades one tool (often an upstream commit
  bump) and wants the lifecycle to be a data edit, not a script rewrite.
  Done = manifest entry + one capability module; no hand-edited scripts.
- **The agent harness user**: runs a coding agent and expects its MCP servers and
  skill packs to be pre-wired so the agent finds tools without per-harness setup.
  Done = `aa connect <harness>` produces a verified config the harness loads.
- **The AI agent editing this repo**: must work safely without a human re-telling
  it the conventions every session. Done = AGENTS.md + the `aa` gates keep it in
  bounds.

## Scope

- **In scope**: bare-metal host toolchain installation (Rust/cargo, Node/npm/pnpm,
  Bun, Python/uv), per-tool XDG data/cache layout, the unified `aa` orchestrator
  CLI, AES 7-layer module architecture, in-house agent submodules, pinned vendor
  submodules, the OmniRoute (host-native) and Anytype (Podman) daemons, the
  agent-skill pack, and doc-invariant gating.
- **Out of scope**: cloud provisioning, a package manager for the host itself,
  Windows/macOS host support (Linux-first), GUI tooling, and any feature that
  requires rewriting a pinned vendor's source (customizations live in in-house
  modules, never in `vendor/`).

## Feature Requirements (Prioritized)

### P0 — Must Have

- Register every tool in one machine-readable manifest as the single source of
  truth. Acceptance: `aa tool list` output equals the manifest's tool ids.
- Install / update / uninstall / run any registered tool via `aa tool`
  subcommands. Acceptance: `aa tool install <id>` then `aa tool run <id> --help`
  exits 0 on a clean host.
- Generate MCP client config and provision skills for a named harness. Acceptance:
  `aa connect <harness>` exits 0 and `aa mcp list` reports the servers.
- Enforce AES 7-layer architecture and flat shared layout. Acceptance: `aa check`
  exits 0 on the tree and fails on a layer violation.
- Track doc real-condition with invariants. Acceptance: `aa check docs .`
  exits 0 and reports `done-without-evidence` for an unevidenced row.

### P1 — Should Have

- Daemon lifecycle (OmniRoute host-native, Anytype Podman) with health, API-key, and space join/list.
  Acceptance: `aa anytype start` then `aa anytype health` reports ready.
- Document and skill-pack audit. Acceptance: `aa skill check` reports coverage
  and `aa check docs` reports invariants.
- Reset/clean of build artifacts and per-tool state. Acceptance: `aa clean`
  removes artifacts and `aa status` reflects the clean state.

### P2 — Nice to Have

- Version bump automation across the manifest and submodules. Acceptance: a
  version bump produces a consistent `version.txt` and manifest version.
- Cross-harness skill sync on session start. Acceptance: a `SessionStart` hook
  keeps the harness skill directory in sync with the pack.

## Non-functional Requirements (High-level)

| Category | Commitment | Detail lives in |
|----------|-----------|-----------------|
| Determinism | `aa check` and `aa check docs` produce identical findings on identical trees | `modules/check/FRD.md` |
| XDG hygiene | No tool writes persistent data outside its XDG dirs; repo root stays clean | `modules/shared` (kernel; no FRD — see HOW-TO-MAKE-FRD) |
| Security | No secrets committed; daemon credentials live in `.env`/XDG only | `modules/daemon/FRD.md` |
| Submodule integrity | Pinned submodule commits are never mutated by a tool run | `modules/AGENTS.md` precedence |

## Open Questions / Risks

| # | Question / Risk | Owner | Deadline | Status |
|---|-----------------|-------|----------|--------|
| 1 | `tools/` legacy tree still live in the main repo until the `refactor/aes-tools` branch merges; both entry points coexist | @raka | at branch merge | open |
| 2 | Config static files moved to `modules/shared/config/`; live `.env` files are not tracked — where do operator-local secrets live on a fresh clone? | @raka | before P1 | open |
| 3 | `aa check docs` only audits `modules/` + root; `skills/` sub-skill READMEs carry their own (weaker) section contract — do they need a separate gate? | @raka | before P2 | open |
