# PLAN — `modules/config` (FRD + kode)

**Status:** APPROVED · **Parent:** `../frd-redesign-modules-20260923.md`  
**Catatan:** Agent **wajib dirancang** meski kode belum punya orchestrator.

---

## 1. File yang diubah

| File | Aksi |
|------|------|
| `modules/config/FRD.md` | Rewrite penuh (§3) |
| `modules/config/BACKLOG.md` | Sync scenario evidence = 12 |
| Kode (§4) | Protocol → 1 method; **bangun** ConfigAgent aggregate |

---

## 2. Target FRD

### Protocol API — tepat 1 baris

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `op`, `path`, `payload?` | result / snapshot | non-zero | — | Satu method menaungi load, save, mutasi, inspect |

### Aggregate API (`ConfigAgent` — BARU)

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `load` | `path` | data + format | Baca + detect |
| `save` | `path`, `data`, `fmt?` | ok | Tulis aman |
| `merge_servers` | `path`, `servers` | ok | Merge MCP |
| `set_env` | `path`, `pairs` | ok | Upsert env |
| `remove_entries` | `path`, `keys` | ok | Hapus entri |
| `inspect` | `path` | snapshot | Read-only |
| `help` | — | usage | Usage |

### FR (6) · Scenarios (12)

| ID | Judul |
|----|--------|
| FR-CONFIG-001 | Load konfigurasi dan deteksi format |
| FR-CONFIG-002 | Save tanpa merusak komentar / urutan |
| FR-CONFIG-003 | Merge server MCP ke konfigurasi |
| FR-CONFIG-004 | Set pasangan env key |
| FR-CONFIG-005 | Hapus entri server / env |
| FR-CONFIG-006 | Inspeksi isi konfigurasi (read-only) |

**NFR:** round-trip fidelity; dry-run tidak menulis; JSON/JSONC/TOML  
**Integration:** `aa config …` (dirancang); shared config kernel

---

## 3. Struktur FRD (wajib)

Pola HOW-TO; Protocol **1 baris**; 6 FR × 6 field; 12 scenario; Rule 8–9.

---

## 4. Kode yang harus diubah

### Current

| File | Simbol | Method |
|------|--------|--------|
| `modules/shared/src/contract_config_protocol.py` | `IConfigLoadProtocol` | `load_file` |
| | `IConfigSaveProtocol` | `save_file` |
| | `IConfigDetectFormatProtocol` | `detect_format` |
| | `IConfigRemoveMcpProtocol` | `remove_mcp_servers` |
| | `IConfigRemoveEnvKeysProtocol` | `remove_env_keys` |
| | `IConfigListMcpProtocol` | `list_mcp_servers` |
| | `IConfigMergeMcpProtocol` | `merge_mcp_servers` |
| | `IConfigSetEnvKeysProtocol` | `set_env_keys` |
| | `IConfigWriter` | composite 3 |
| | `IConfigModifier` | composite 5 |
| `modules/config/src/capabilities_config_engine.py` | `ConfigWriter` | implements Writer |
| | `ConfigModifier` | implements Modifier |
| `modules/config/src/root_config_container.py` | `ConfigContainer` | wire Writer+Modifier |
| **Belum ada** | `agent_config_orchestrator.py` | — |
| **Belum ada** | `contract_config_aggregate.py` | — |
| **Belum ada** | surface `aa config` | — |
| `modules/shared/src/__init__.py` | export | ~10 contract symbols |

### Target

| File | Aksi |
|------|------|
| `contract_config_protocol.py` | **Hapus** 8 leaf + 2 composite. Sisakan **1** `IConfigProtocol.execute(op, path, payload)` |
| `contract_config_aggregate.py` | **BUAT BARU** — `IConfigAggregate` multi: `load`, `save`, `merge_servers`, `set_env`, `remove_entries`, `inspect`, `help` |
| `agent_config_orchestrator.py` | **BUAT BARU** — `ConfigOrchestrator` / `ConfigAgent` implements aggregate; dispatch ke Writer/Modifier internal |
| `capabilities_config_engine.py` | `ConfigWriter` + `ConfigModifier` tetap concrete; **hapus** inheritance protocol leaf → dukung `execute` **atau** dipanggil hanya dari orchestrator |
| `surface_config_command.py` | **BUAT BARU** — surface `aa config` implement aggregate |
| `root_config_container.py` | Wire engine → orchestrator → surface |
| `surface` router di `root_cli_entry.py` | Daftarkan `aa config` bila memang surface baru |
| `__init__.py` | Export `IConfigAggregate` + `IConfigProtocol`; hapus export leaf lama |
| Callers leaf | Grep `IConfigWriter\|IConfigModifier\|IConfigLoadProtocol\|…` → pindah ke aggregate/orchestrator |

### Diff intent

```
BEFORE: 8 one-method leaf + IConfigWriter + IConfigModifier; no agent
AFTER:  IConfigProtocol.execute(...)           # 1 method
        IConfigAggregate.(multi) + ConfigAgent # BARU
        ConfigWriter/ConfigModifier = internal impl
```

---

## 5. Gate

```bash
aa check docs modules/config
lint-arwaky-cli scan modules/config
python3 -m modules.root_cli_entry check
python3 -m compileall -q modules/config modules/shared
```
