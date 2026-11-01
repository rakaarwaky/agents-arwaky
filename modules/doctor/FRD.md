# FRD — doctor

## Feature Overview

The doctor feature is a read-only host diagnostic: one protocol method covers both environment and tool readiness, and the aggregate exposes full diagnosis, tool readiness, and report rendering. The flow is `aa doctor` / `aa status` → doctor aggregate → env + tools runners → per-check pass/fail rows, one exit code. Probes never install, remove, or mutate anything.

## Functional Requirements

### FR-DOCTOR-001: Diagnose the host and its tools

**Description:** One diagnostic pass over the host environment (OS tooling, language toolchains, package managers, git, XDG resolvability) and the manifest tool readiness (binary/runner resolvable and launchable), reporting one pass/warn/fail row per probe plus one exit code.

#### Business Logic

- Probes are read-only — they never install, remove, or mutate.
- A missing toolchain marks that row FAIL; a row-level FAIL never fails the process.
- Only a hard failure yields a non-zero exit.
- Readiness means the executable resolves via the discovery order (PATH, XDG bin, source-ready for in-house tools); a missing tool is a row state, not a crash.

#### Edge Cases

- A toolchain present but too old → WARN with the found version.
- XDG home unset → affected rows FAIL with the env var named.
- An optional tool absent → SKIP row, not FAIL.
- A probe that hangs → killed after a bounded timeout and reported as a timeout row.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | the live host; the tool registry from the tool manifest; mode flags (`json`, mode) |
| **Output** | exit code plus a per-check pass/fail table on stdout, or the same rows as JSON |
| **Protocol** | IDoctorProtocol |
| **Method** | run(flags) |
| **Event** | — |
| **Error** | probe exceptions are captured per row; only an unrecoverable manifest read failure returns non-zero |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Healthy host | `aa doctor` | all-PASS table, exit 0 |
| Missing toolchain | `aa doctor` | that row FAIL, process exit 0 |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Row vs process exit | a row FAIL never fails the process; only hard fail → non-zero |

## Public Interface

| Aspect     | Detail            |
|------------|-------------------|
| Agent      | DoctorOrchestrator |
| Aggregate  | IDoctorAggregate   |
| Method     | run(flags)         |
| Request    | DoctorRequest (flags: json, mode) |
| Response   | DoctorResult (rows / exit code / JSON) |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals and scope                        | [PRD.md](../../PRD.md) |
| Backlog      | Task tracking and implementation status          | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies              | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra         | [ARCHITECTURE.md](../../ARCHITECTURE.md) |
