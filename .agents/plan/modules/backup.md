# PLAN — `modules/backup` (FRD + kode)

**Status:** APPROVED · **Parent:** `../frd-redesign-modules-20260923.md`

---

## 1. File yang diubah

| File | Aksi |
|------|------|
| `modules/backup/FRD.md` | Rewrite penuh (§3) |
| `modules/backup/BACKLOG.md` | Sync scenario evidence = 5 |
| Kode (§4) | Collapse protocol → 1 method; aggregate tetap multi |

---

## 2. Target FRD

### Protocol API — tepat 1 baris

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `op`, `tool?`, `dest?`/`archive?` | result / list path | non-zero | — | Satu method menaungi archive, restore, list |

### Aggregate API (`BackupOrchestrator` / `BackupAgent`)

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `backup` | `tool`, `dest?` | archive result | Archive state XDG |
| `restore` | `tool`, `archive` | restored | Pulihkan archive |
| `list_archives` | — | `[path]` | Daftar archive |
| `help` | — | usage | Usage |

*(opsional target: `status_store` — boleh ditambah di redesign)*

### FR (5) · Scenarios (5)

| ID | Judul |
|----|--------|
| FR-BACKUP-001 | Archive state XDG sebuah tool |
| FR-BACKUP-002 | Restore tool dari archive |
| FR-BACKUP-003 | List archive yang tersedia |
| FR-BACKUP-004 | Laporkan status store backup |
| FR-BACKUP-005 | Tampilkan usage backup |

**NFR:** exit fidelity; list read-only; gagal storage → non-zero  
**Integration:** XDG; cloud (opsional); root CLI `aa backup`

---

## 3. Struktur FRD (wajib)

Pola HOW-TO: Reference → System Overview → FR×5 (6 field) → API Contract (Protocol **1 baris** + Aggregate) → Integration → NFR → Scenarios×5 → Assumptions → Glossary. Rule 8–9 (tanpa nama file/class).

---

## 4. Kode yang harus diubah

### Current

| File | Simbol | Method sekarang |
|------|--------|-----------------|
| `modules/shared/src/contract_backup_protocol.py` | `IBackupProtocol` | `backup` |
| | `IRestoreProtocol` | `restore` |
| | `IListArchivesProtocol` | `list_archives` |
| | `IBackupGateway` | composite 3 protocol |
| `modules/shared/src/contract_backup_aggregate.py` | `IBackupAggregate` | `backup`, `restore`, `list_archives`, `help` |
| `modules/backup/src/agent_backup_orchestrator.py` | `BackupOrchestrator` | implements aggregate |
| `modules/backup/src/capabilities_backup_tar.py` | `TarBackupGateway` | `IBackupGateway` |
| `modules/backup/src/capabilities_backup_gdrive.py` | `GdriveBackupGateway` | `IBackupGateway` |
| `modules/backup/src/surface_backup_command.py` | `BackupCommand` | implements aggregate |
| `modules/backup/src/root_backup_container.py` | `BackupContainer` | wire gateways → orch |
| `modules/shared/src/__init__.py` | export | 4 contract symbols |

### Target (redesign)

| File | Aksi |
|------|------|
| `contract_backup_protocol.py` | **Hapus** 3 leaf + composite. Sisakan **1 class** `IBackupProtocol` dengan **1 method** `execute(op, ...)` menaungi semua capability |
| `contract_backup_aggregate.py` | **Pertahankan** multi-method (`backup`/`restore`/`list_archives`/`status_store?`/`help`) — surface pemanggil |
| `agent_backup_orchestrator.py` | Implement `IBackupAggregate`; method tetap multi; dispatch internal ke gateway **tanpa** protocol leaf publik |
| `capabilities_backup_*.py` | Gateway boleh tetap multi-method **internal**; **hapus** inheritance `IBackupGateway` → cukup implement interface `execute` **atau** tetap concrete tanpa protocol FRD |
| `surface_backup_command.py` | Tetap implement aggregate multi |
| `root_backup_container.py` | Re-wire jika nama protocol berubah |
| `__init__.py` shared | Update `__all__` / `_layer_symbols` |
| Tests / callers | Grep `IBackupGateway\|IRestoreProtocol\|IListArchivesProtocol` → pindah ke aggregate/`execute` |

### Diff intent (ringkas)

```
BEFORE: IBackupProtocol + IRestoreProtocol + IListArchivesProtocol + IBackupGateway(3)
AFTER:  IBackupProtocol.execute(...)   # 1 method, semua capability
        IBackupAggregate.(multi)       # tidak berubah orientasi
```

---

## 5. Gate

```bash
aa check docs modules/backup
lint-arwaky-cli scan modules/backup   # atau scan modules/
python3 -m modules.root_cli_entry check
python3 -m compileall -q modules/backup
```
0 finding → sinkron BACKLOG.
