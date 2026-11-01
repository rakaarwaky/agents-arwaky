# FRD — service

## Feature Overview

The service feature exposes typed control methods (`start`, `stop`, `restart`) and inspection methods (`status`, `logs`, `help`) through two capability protocols. `ServiceOrchestrator.execute(ServiceRequest)` is the single aggregate entry point; it dispatches to those methods. Lifecycle, status, and logs are routed through the injected daemon aggregate; help prints local usage. Daemon managers own the host service operations and deploy assets.

## Functional Requirements

### FR-SERVICE-001: Drive daemon systemd units

**Description:** The control capability's typed `start`, `stop`, and `restart` methods act on the named target or all managed daemons; the service aggregate dispatches the corresponding request.

#### Business Logic

- An unknown target is a clear error naming the valid set.
- `all` fans out over every known daemon; one failing unit does not abort the others — each is reported independently.

#### Edge Cases

- Unit not installed on the host → that target reports a unit-missing result, others proceed.
- No systemd on the host → a top-level clear failure, not per-unit noise.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | target from the aggregate — `omniroute`, `9router`, `anytype`, or `all` (default `all`) |
| **Output** | `ExitCode`; one reported line per driven unit |
| **Protocol** | IServiceProtocol |
| **Method** | start/stop/restart |
| **Event** | — |
| **Error** | non-zero with the unit and the systemctl error captured; no raw exceptions cross the surface |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| `aa service start 9router` | drives only the 9router unit | OmniRoute keeps its state |

#### Metric

| Target Metric | Value |
|---------------|-------|
| No false abort | one failing unit in `all` does not stop the others |

### FR-SERVICE-002: Inspect, tail logs, and show usage (read-only)

**Description:** The inspection capability's typed `status` and `logs` methods query the daemon aggregate without side effects; `help` prints the CLI usage line and valid action/target set.

#### Business Logic

- Status is read-only — it never starts, stops, or restarts anything; a stopped unit is a valid reported state, not an error.
- Logs is read-only; a stopped unit's logs are still valid to tail.
- Usage lists exactly the supported actions (`status`, `start`, `stop`, `restart`, `logs`, `help`) and targets (`omniroute`, `9router`, `anytype`, `all`).

#### Edge Cases

- A daemon stopped → reported stopped, exit reflects the probe without raising.
- No journal access → the limitation is reported, not raised.
- A target with no log file yet → clear no-logs note, non-zero.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | none (status, help) / target — `omniroute` (default), `9router`, or `anytype` (logs) |
| **Output** | `ExitCode`; a state table on stdout (status); log lines on stdout (logs); usage text on stdout (help) |
| **Protocol** | IServiceProtocol |
| **Method** | status/logs/help |
| **Event** | — |
| **Error** | read probes that fail are reported, not raised; probe/tail failures are reported messages with a non-zero exit |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| `aa service status` | reports every unit's state | nothing is changed |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Read-only status/logs | `status`/`logs` never change unit state |

## Public Interface

| Aspect     | Detail            |
|------------|-------------------|
| Agent      | ServiceOrchestrator |
| Aggregate  | IServiceAggregate   |
| Method     | execute(request)  |
| Request    | ServiceRequest (op, target?, logs_target?) |
| Response   | ServiceResponse (ExitCode) |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals and scope                        | [PRD.md](../../PRD.md) |
| Backlog      | Task tracking and implementation status          | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies              | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra         | [ARCHITECTURE.md](../../ARCHITECTURE.md) |
