# PLAN — `modules/tools` (FRD + kode)

**Status:** APPROVED · **Parent:** `../frd-redesign-modules-20260923.md`  
**Catatan:** FR tanpa simbol basi; title = perilaku.

---

## 1. File yang diubah

| File | Aksi |
|------|------|
| `modules/tools/FRD.md` | Rewrite penuh (§3) |
| `modules/tools/BACKLOG.md` | Sync scenario evidence = 8 |
| Kode (§4) | Protocol → 1 method; aggregate multi |

---

## 2. Target FRD

### Protocol API — tepat 1 baris

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `op`, `spec?`, `query?`, `args?` | result / exit | non-zero | — | Satu method menaungi install, update, uninstall, run, resolve, discover |

### Aggregate API (`ToolsOrchestrator` / `ToolsAgent`)

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `list` | — | table | Registered tools |
| `resolve` | `query` | spec | Query → spec |
| `install` | `spec\|all` | result | Install |
| `update` | `spec\|all` | result | Update |
| `uninstall` | `spec\|all` | result | Uninstall + owned paths |
| `run` | `spec`, `args` | exit | Exit fidelity |
| `executable_path` | `spec` | path | Discover path |

### FR (6) · Scenarios (8 total)

| ID | Judul |
|----|--------|
| FR-TOOLS-001 | Install tool terdaftar |
| FR-TOOLS-002 | Update tool terdaftar |
| FR-TOOLS-003 | Uninstall tool beserta path owned |
| FR-TOOLS-004 | Run tool dengan fidelity exit code |
| FR-TOOLS-005 | Resolve query → spesifikasi tool |
| FR-TOOLS-006 | Discover kesiapan & path tool |

**NFR:** exit fidelity; idempotent install; discover read-only  
**Integration:** SSOT manifest; runners cargo/uv/bun; `aa tool …`

---

## 3. Struktur FRD (wajib)

Pola HOW-TO; Protocol **1 baris**; 6 FR × 6 field; **8** scenario total; Rule 8–9.

---

## 4. Kode yang harus diubah

### Current

| File | Simbol | Method |
|------|--------|--------|
| `modules/shared/src/contract_tools_protocol.py` | `IToolInstallProtocol` | `install` |
| | `IToolUpdateProtocol` | `update` |
| | `IToolUninstallProtocol` | `uninstall` |
| | `IToolRunProtocol` | `run` |
| | `IToolResolveProtocol` | `resolve` |
| | `IToolIsRegisteredProtocol` | `is_registered` |
| | `IToolSatisfiedProtocol` | `satisfied` |
| | `IToolIsPinSatisfiedProtocol` | `is_pin_satisfied` |
| | `IToolAdapterInstallProtocol` | `install` |
| | `IToolAdapterUpdateProtocol` | `update` |
| | `IToolOwnedPathsProtocol` | `owned_paths` |
| | `IToolAdapterFacade` | composite 7 |
| `modules/shared/src/contract_tools_aggregate.py` | `IToolsAggregate` | `list_tools`, `resolve_spec`, `install`, `update`, `uninstall`, `run_tool`, `executable_path` |
| `modules/tools/src/agent_tools_orchestrator.py` | `ToolsOrchestrator` | implements aggregate |
| `modules/tools/src/capabilities_tools_installer.py` | `InstallerCapability` | `IToolInstallProtocol` |
| `modules/tools/src/capabilities_tools_updater.py` | `UpdaterCapability` | `IToolUpdateProtocol` |
| `modules/tools/src/capabilities_tools_uninstaller.py` | `UninstallerCapability` | `IToolUninstallProtocol` |
| `modules/tools/src/capabilities_tools_runner.py` | `RunnerCapability` | `IToolRunProtocol` + `discover`/`execute` |
| `modules/tools/src/capabilities_tools_adapter.py` | `ToolAdapterFacade` | `IToolAdapterFacade` |
| `surface_tools_command.py` / `root_tools_container.py` | surface/container | — |
| `modules/shared/src/__init__.py` | export | ~13 symbols |

### Target

| File | Aksi |
|------|------|
| `contract_tools_protocol.py` | **Hapus** 11 leaf + `IToolAdapterFacade`. Sisakan **1** `IToolsProtocol.execute(op, spec?, query?, args?)` |
| `contract_tools_aggregate.py` | **Pertahankan multi**; **samakan nama** dgn FRD (`list`/`resolve`/`install`/`update`/`uninstall`/`run`/`executable_path` — rename `list_tools`→`list`, `resolve_spec`→`resolve`, `run_tool`→`run` bila FRD pakai itu) |
| `agent_tools_orchestrator.py` | Implement aggregate; dispatch `execute` ke capability internal |
| `capabilities_tools_*.py` | **Hapus** inheritance leaf/`IToolAdapterFacade`; methods = internal **atau** dukung `execute` |
| `RunnerCapability.discover` | Masuk aggregate `executable_path` / FR-006 — **bukan** protocol terpisah |
| `surface_tools_command.py` | Ikut aggregate |
| `root_tools_container.py` | Wire |
| `__init__.py` | Export baru; hapus leaf lama |
| Callers | Grep `IToolInstallProtocol\|IToolAdapterFacade\|…` → pindah aggregate |

### Diff intent

```
BEFORE: 11 leaf + IToolAdapterFacade + IToolsAggregate(7, old names)
AFTER:  IToolsProtocol.execute(...)            # 1 method
        IToolsAggregate.(7, align FRD names)   # multi
        installer/updater/uninstaller/runner/adapter = internal
```

---

## 5. Gate

```bash
aa check docs modules/tools
lint-arwaky-cli scan modules/tools
python3 -m modules.root_cli_entry check
python3 -m compileall -q modules/tools modules/shared
```
