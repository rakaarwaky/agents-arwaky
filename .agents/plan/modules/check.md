# PLAN — `modules/check` (FRD + kode)

**Status:** APPROVED · **Parent:** `../frd-redesign-modules-20260923.md`

---

## 1. File yang diubah

| File | Aksi |
|------|------|
| `modules/check/FRD.md` | Rewrite penuh (§3) |
| `modules/check/BACKLOG.md` | Sync scenario evidence = 6 |
| Kode (§4) | Protocol → 1 method; aggregate multi |

---

## 2. Target FRD

### Protocol API — tepat 1 baris

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `scope` (`all\|docs\|skill`) | exit + findings | non-zero gate | — | Satu method menaungi docs + skill audit |

### Aggregate API (`CheckOrchestrator` / `CheckAgent`)

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `check` | `scope` | exit + findings | Dispatch all/docs/skill |
| `check_docs` | — | exit + findings | Audit invarian dokumen |
| `check_skill` | — | exit + findings | Audit skill pack |
| `summary` | findings | ringkasan | Ringkas findings |

### FR (3) · Scenarios (6)

| ID | Judul |
|----|--------|
| FR-CHECK-001 | Audit invarian dokumen |
| FR-CHECK-002 | Audit loadability skill pack |
| FR-CHECK-003 | Dispatch scope ke jalur audit yang tepat |

**NFR:** strict-only; determinism; gate < 2 menit  
**Integration:** `aa check`; shared doc/skill engines

---

## 3. Struktur FRD (wajib)

Pola HOW-TO; Protocol **1 baris**; 3 FR × 6 field; 6 scenario; Rule 8–9.

---

## 4. Kode yang harus diubah

### Current

| File | Simbol | Method |
|------|--------|--------|
| `modules/shared/src/contract_check_protocol.py` | `ICheckProtocol` | `run()` |
| `modules/shared/src/contract_check_aggregate.py` | `ICheckAggregate` | `check(only)` |
| `modules/check/src/agent_check_orchestrator.py` | `CheckOrchestrator` | `check(only)` |
| `modules/check/src/capabilities_check_docs.py` | `DocsCheckRunner` | `run`, `audit` |
| `modules/check/src/capabilities_check_skills.py` | `SkillsCheckRunner` | `run` |
| `modules/check/src/surface_check_command.py` | `CheckAction` | `check(only)` |
| `modules/check/src/root_check_container.py` | `CheckContainer` | wire runners |
| `modules/shared/src/__init__.py` | export | 2 contract symbols |

### Target

| File | Aksi |
|------|------|
| `contract_check_protocol.py` | **Ubah** `ICheckProtocol.run()` → **`ICheckProtocol.execute(scope)`** — 1 method menaungi semua scope |
| `contract_check_aggregate.py` | **Pertahankan** `check(scope)`; **boleh tambah** `check_docs`, `check_skill`, `summary` untuk surface FRD |
| `agent_check_orchestrator.py` | Dispatch `check(scope)` → runner; jika FRD punya `check_docs`/`check_skill`, tambah method thin wrapper |
| `capabilities_check_docs.py` / `capabilities_check_skills.py` | Implement **satu** `execute(scope)` **atau** tetap `run` internal; public protocol = `execute` saja |
| `surface_check_command.py` | Ikut aggregate |
| `root_check_container.py` | Wire tetap |
| `__init__.py` | Update export bila rename |

### Diff intent

```
BEFORE: ICheckProtocol.run() × 2 runners, ICheckAggregate.check(only)
AFTER:  ICheckProtocol.execute(scope)     # 1 method
        ICheckAggregate.check/check_docs/check_skill/summary  # multi
```

---

## 5. Gate

```bash
aa check docs modules/check
lint-arwaky-cli scan modules/check
python3 -m modules.root_cli_entry check
python3 -m compileall -q modules/check
```
