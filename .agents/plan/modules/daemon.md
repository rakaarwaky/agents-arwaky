# PLAN — `modules/daemon` (FRD + kode)

**Status:** APPROVED · **Parent:** `../frd-redesign-modules-20260923.md`  
**Keputusan:** unit systemd **tetap di aggregate daemon** + Integration ke `service`.

---

## 1. File yang diubah

| File | Aksi |
|------|------|
| `modules/daemon/FRD.md` | Rewrite penuh (§3) |
| `modules/daemon/BACKLOG.md` | Sync scenario evidence = 8 |
| Kode (§4) | Protocol → 1 method; aggregate multi (+ unit ops) |

---

## 2. Target FRD

### Protocol API — tepat 1 baris

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `op`, `daemon_id?`, `unit?` | status / logs / result | non-zero | — | Satu method menaungi lifecycle, enum, unit |

### Aggregate API (`DaemonOrchestrator` / `DaemonAgent`)

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `list_known` | — | `[id]` | Enum daemon |
| `start` / `stop` / `restart` | `id` | result | Lifecycle |
| `status` | `id` | status | Running/absent |
| `logs` | `id` | lines | Tail log |
| `install_unit` / `remove_unit` / `unit_status` | unit | ok/status | Unit systemd |

### FR (4) · Scenarios (8)

| ID | Judul |
|----|--------|
| FR-DAEMON-001 | Manage lifecycle satu daemon |
| FR-DAEMON-002 | Authorize Anytype dengan API key |
| FR-DAEMON-003 | Enumerasi daemon yang dikelola |
| FR-DAEMON-004 | Pasang / lepas unit systemd daemon |

**Integration:** podman/systemd; `aa daemon …`; module service

---

## 3. Struktur FRD (wajib)

Pola HOW-TO; Protocol **1 baris**; 4 FR × 6 field; 8 scenario; Rule 8–9.

---

## 4. Kode yang harus diubah

### Current

| File | Simbol | Method |
|------|--------|--------|
| `modules/shared/src/contract_daemon_protocol.py` | `IDaemonStart/Stop/Status/Logs/RestartProtocol` | 5 leaf 1-method |
| | `IDaemonManager` | composite 5 |
| `modules/shared/src/contract_daemon_aggregate.py` | `IDaemonAggregate` | `start_daemon`…`restart_daemon` (5) — **tanpa** unit/enum di kontrak |
| `modules/daemon/src/agent_daemon_orchestrator.py` | `DaemonOrchestrator` | + `known_daemons`, `service_install/uninstall/status` |
| `modules/daemon/src/capabilities_anytype_daemon.py` | `AnytypeDaemonManager` | lifecycle + auth + space + unit |
| `modules/daemon/src/capabilities_9router_daemon.py` | `NinerouterDaemonManager` | lifecycle + models + unit |
| `modules/daemon/src/surface_daemon_command.py` | `DaemonAction` | 5 method aggregate |
| `modules/daemon/src/root_daemon_container.py` | `DaemonContainer` | wire |
| `modules/service/src/root_service_container.py` | `DaemonAggregateAdapter` | implements `IDaemonAggregate` |
| `modules/shared/src/__init__.py` | export | protocol + aggregate |

### Target

| File | Aksi |
|------|------|
| `contract_daemon_protocol.py` | **Hapus** 5 leaf + `IDaemonManager`. Sisakan **1** `IDaemonProtocol.execute(op, name, unit?)` |
| `contract_daemon_aggregate.py` | **Perluas** multi-method: `list_known`, `start`, `stop`, `restart`, `status`, `logs`, `install_unit`, `remove_unit`, `unit_status` (sesuaikan nama dgn FRD — boleh rename dari `*_daemon`) |
| `agent_daemon_orchestrator.py` | Implement aggregate penuh; `service_*` → map ke `install_unit`/… |
| `capabilities_*_daemon.py` | Managers = internal impl; **hapus** inheritance `IDaemonManager`; dukung dispatch `execute` **atau** tetap method internal |
| `surface_daemon_command.py` | Expand method surface |
| `root_daemon_container.py` | Re-wire |
| `root_service_container.py` (`DaemonAggregateAdapter`) | Sync nama method aggregate |
| `__init__.py` | Export baru / hapus leaf |

### Diff intent

```
BEFORE: 5 leaf + IDaemonManager + IDaemonAggregate(5, no unit in contract)
AFTER:  IDaemonProtocol.execute(...)          # 1 method
        IDaemonAggregate.(9 multi, +unit/+enum)
        managers = internal
```

---

## 5. Gate

```bash
aa check docs modules/daemon
lint-arwaky-cli scan modules/daemon modules/service
python3 -m modules.root_cli_entry check
python3 -m compileall -q modules/daemon modules/service
```
