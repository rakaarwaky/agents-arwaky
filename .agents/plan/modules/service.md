# PLAN — `modules/service` (FRD + kode)

**Status:** APPROVED · **Parent:** `../frd-redesign-modules-20260923.md`

---

## 1. File yang diubah

| File | Aksi |
|------|------|
| `modules/service/FRD.md` | Rewrite penuh (§3) |
| `modules/service/BACKLOG.md` | Sync scenario evidence = 8 |
| Kode (§4) | Protocol → 1 method; aggregate multi |

---

## 2. Target FRD

### Protocol API — tepat 1 baris

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `op`, `unit` | status / logs / result | non-zero | — | Satu method menaungi drive, status, logs, usage |

### Aggregate API (`ServiceOrchestrator` / `ServiceAgent`)

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `status` | `unit` | status | Inspeksi status |
| `start` | `unit` | result | Start unit |
| `stop` | `unit` | result | Stop unit |
| `restart` | `unit` | result | Restart unit |
| `logs` | `unit` | lines | Tail log |
| `help` | — | usage | Usage + target valid |

### FR (4) · Scenarios (8)

| ID | Judul |
|----|--------|
| FR-SERVICE-001 | Drive unit systemd (start / stop / restart) |
| FR-SERVICE-002 | Inspeksi status unit |
| FR-SERVICE-003 | Tail log unit |
| FR-SERVICE-004 | Tampilkan usage + target valid |

---

## 3. Struktur FRD (wajib)

Pola HOW-TO; Protocol **1 baris**; 4 FR × 6 field; 8 scenario; Rule 8–9.

---

## 4. Kode yang harus diubah

### Current

| File | Simbol | Method |
|------|--------|--------|
| `modules/shared/src/contract_service_protocol.py` | `IServiceStatus/Start/Stop/Restart/Logs/HelpProtocol` | 6 leaf |
| | `IServiceManager` | composite 6 |
| `modules/shared/src/contract_service_aggregate.py` | `IServiceAggregate` | `status`, `start`, `stop`, `restart`, `logs`, `help` |
| `modules/service/src/agent_service_orchestrator.py` | `ServiceOrchestrator` | implements aggregate |
| `modules/service/src/capabilities_service_manager.py` | `ServiceManager` | implements `IServiceManager` |
| `modules/service/src/surface_service_command.py` | `ServiceAction` | implements aggregate |
| `modules/service/src/root_service_container.py` | `ServiceContainer` + `DaemonAggregateAdapter` | wire |
| `modules/shared/src/__init__.py` | export | protocol + aggregate |

### Target

| File | Aksi |
|------|------|
| `contract_service_protocol.py` | **Hapus** 6 leaf + `IServiceManager`. Sisakan **1** `IServiceProtocol.execute(op, unit)` |
| `contract_service_aggregate.py` | **Pertahankan multi** (sudah 6 — align nama dgn FRD) |
| `agent_service_orchestrator.py` | Implement aggregate; dispatch `execute` ke manager internal |
| `capabilities_service_manager.py` | **Hapus** inheritance `IServiceManager`; method tetap internal **atau** implement `execute` |
| `surface_service_command.py` | Tetap aggregate |
| `root_service_container.py` | Wire tetap |
| `__init__.py` | Export `IServiceProtocol` + aggregate; hapus leaf |

### Diff intent

```
BEFORE: 6 leaf + IServiceManager + IServiceAggregate(6)
AFTER:  IServiceProtocol.execute(...)     # 1 method
        IServiceAggregate.(6)             # tetap multi
        ServiceManager = internal
```

---

## 5. Gate

```bash
aa check docs modules/service
lint-arwaky-cli scan modules/service
python3 -m modules.root_cli_entry check
python3 -m compileall -q modules/service
```
