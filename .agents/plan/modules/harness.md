# PLAN — `modules/harness` (FRD + kode)

**Status:** APPROVED · **Parent:** `../frd-redesign-modules-20260923.md`  
**Catatan:** path-leaf adapter = internal, **tidak** masuk FRD Protocol.

---

## 1. File yang diubah

| File | Aksi |
|------|------|
| `modules/harness/FRD.md` | Rewrite penuh (§3) |
| `modules/harness/BACKLOG.md` | Sync scenario evidence = 8 |
| Kode (§4) | Capability protocol → 1 method; path-leaves boleh tetap internal; aggregate multi |

---

## 2. Target FRD

### Protocol API — tepat 1 baris

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `op`, `targets`, `flags?` | result / resolved | non-zero | — | Satu method menaungi connect, disconnect, provision |

### Aggregate API (`HarnessOrchestrator` / `HarnessAgent`)

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `resolve_targets` | id/alias/`--all` | `[canonical]` | Resolve kanonik |
| `all_targets` | — | `[canonical]` | Semua harness |
| `connect` | targets, flags | per-target | Connect |
| `disconnect` | targets | per-target | Disconnect |
| `provision_skills` | targets | per-target | Provision pack |

### FR (4) · Scenarios (8)

| ID | Judul |
|----|--------|
| FR-HARNESS-001 | Connect harness (MCP, env, router, skills) |
| FR-HARNESS-002 | Disconnect harness bersih |
| FR-HARNESS-003 | Provision skill pack ke harness |
| FR-HARNESS-004 | Resolve id / alias / `--all` → target kanonik |

---

## 3. Struktur FRD (wajib)

Pola HOW-TO; Protocol **1 baris**; 4 FR × 6 field; 8 scenario; Rule 8–9 (tanpa nama path helper).

---

## 4. Kode yang harus diubah

### Current

| File | Simbol | Method |
|------|--------|--------|
| `modules/harness/src/contract_harness_protocol.py` | `IHarnessConnectProtocol` | `connect` |
| | `IHarnessDisconnectProtocol` | `disconnect` |
| | `IHarnessSkillsProtocol` | `provision_skills` |
| | path-leaves ×8 (`Home`, `ConfigFiles`, `EnvFiles`, `McpConfigFile`, `McpTargets`, `SkillsDir`, `SessionConfFiles`, `CredentialCandidates`) | 1 each |
| | `IHarnessAdapter` | composite 8 path |
| `modules/harness/src/contract_harness_aggregate.py` | `IHarnessAggregate` | `resolve_targets`, `connect`, `disconnect`, `provision_skills` |
| `modules/harness/src/agent_harness_orchestrator.py` | `HarnessOrchestrator` | + `all_targets` |
| `modules/harness/src/capabilities_harness_connector.py` | `HarnessConnector`, `BoundAdapter` | connect + bind path |
| `modules/harness/src/capabilities_harness_disconnector.py` | `HarnessDisconnector` | disconnect |
| `modules/harness/src/capabilities_harness_skills.py` | `HarnessSkills` | provision |
| `modules/harness/src/utility_*_adapter.py` ×5 | leaf adapters | path helpers |
| `surface_harness_command.py` / `root_harness_container.py` | surface/container | — |

### Target

| File | Aksi |
|------|------|
| `contract_harness_protocol.py` | **Collapse 3 capability protocol** → **1** `IHarnessProtocol.execute(op, targets, flags)` |
| | **Path-leaves + `IHarnessAdapter`:** opsional tetap sebagai **adapter internal** (bukan Protocol API FRD). Jika lint/AES izinkan, **pindah** ke `utility_*` / module-private; jika harus tetap `contract_*`, **rename** agar tidak dihitung “capability protocol” FRD |
| `contract_harness_aggregate.py` | **Pertahankan multi**; **tambah** `all_targets` ke kontrak aggregate (sekarang hanya di orchestrator) |
| `agent_harness_orchestrator.py` | Implement aggregate penuh |
| `capabilities_harness_*.py` | Connector/Disconnector/Skills = internal; **hapus** inheritance 3 capability protocol → dukung `execute` dispatch |
| `BoundAdapter` / adapters | Path surface tetap; **jangan** masuk FRD |
| `surface` / `root` | Re-wire bila rename protocol |
| `__init__.py` harness | Update `__all__` / `_layer_symbols` |

### Diff intent

```
BEFORE: IHarnessConnect + Disconnect + Skills (3) + 8 path-leaf + IHarnessAggregate(4)
AFTER:  IHarnessProtocol.execute(...)        # 1 capability method
        path-leaf = internal adapter (bukan FRD)
        IHarnessAggregate.(multi + all_targets)
```

---

## 5. Gate

```bash
aa check docs modules/harness
lint-arwaky-cli scan modules/harness
python3 -m modules.root_cli_entry check
python3 -m compileall -q modules/harness
```
