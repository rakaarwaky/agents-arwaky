# PLAN — `modules/doctor` (FRD + kode)

**Status:** APPROVED · **Parent:** `../frd-redesign-modules-20260923.md`

---

## 1. File yang diubah

| File | Aksi |
|------|------|
| `modules/doctor/FRD.md` | Rewrite penuh (§3) |
| `modules/doctor/BACKLOG.md` | Sync scenario evidence = 4 |
| Kode (§4) | Protocol → 1 method; aggregate multi |

---

## 2. Target FRD

### Protocol API — tepat 1 baris

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `flags` (`json`, mode) | report | hard fail → non-zero | — | Satu method menaungi diagnosis env + readiness |

### Aggregate API (`DoctorOrchestrator` / `DoctorAgent`)

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `diagnose` | flags | report | Full diagnosis |
| `readiness` | flags | rows | Tool readiness |
| `report` | report | text/JSON | Render |

*(atau pertahankan `doctor` + `status` sesuai surface CLI yang diinginkan — konsistenkan dgn FRD)*

### FR (2) · Scenarios (4)

| ID | Judul |
|----|--------|
| FR-DOCTOR-001 | Diagnosa environment host |
| FR-DOCTOR-002 | Diagnosa kesiapan tool |

**NFR:** row FAIL ≠ process fail; JSON stabil  
**Integration:** `aa doctor` / `aa status`

---

## 3. Struktur FRD (wajib)

Pola HOW-TO; Protocol **1 baris**; 2 FR × 6 field; 4 scenario; Rule 8–9.

---

## 4. Kode yang harus diubah

### Current

| File | Simbol | Method |
|------|--------|--------|
| `modules/shared/src/contract_doctor_protocol.py` | `IDoctorProtocol` | `run(json_mode)` |
| `modules/shared/src/contract_doctor_aggregate.py` | `IDoctorAggregate` | `doctor`, `status` |
| `modules/doctor/src/agent_doctor_orchestrator.py` | `DoctorOrchestrator` | `doctor`, `status` |
| `modules/doctor/src/capabilities_doctor_env.py` | `EnvDiagnosticRunner` | `run` |
| `modules/doctor/src/capabilities_doctor_tools.py` | `ToolsDiagnosticRunner` | `run` |
| `modules/doctor/src/surface_doctor_command.py` | `DoctorAction` | `doctor`, `status` |
| `modules/doctor/src/root_doctor_container.py` | `DoctorContainer` | wire |
| `modules/shared/src/__init__.py` | export | 2 symbols |

### Target

| File | Aksi |
|------|------|
| `contract_doctor_protocol.py` | Rename/align: **1 method** `IDoctorProtocol.execute(flags)` (ganti `run`) — **satu** protocol menaungi semua runner |
| `contract_doctor_aggregate.py` | **Pertahankan multi** `doctor`+`status`; **boleh tambah** `diagnose`/`readiness`/`report` bila FRD pakai nama itu — **samakan nama dgn FRD** |
| `agent_doctor_orchestrator.py` | Implement aggregate multi; dispatch ke runner via `execute` |
| `capabilities_doctor_*.py` | Rename `run` → `execute(flags)` implement protocol; atau tetap `run` internal tanpa protocol publik |
| `surface_doctor_command.py` | Ikut aggregate |
| `root_doctor_container.py` | Wire tetap |
| `__init__.py` | Sync nama |

### Diff intent

```
BEFORE: IDoctorProtocol.run() × 2 runners; IDoctorAggregate(doctor, status)
AFTER:  IDoctorProtocol.execute(flags)       # 1 method
        IDoctorAggregate.(multi, sama dgn FRD)
```

---

## 5. Gate

```bash
aa check docs modules/doctor
lint-arwaky-cli scan modules/doctor
python3 -m modules.root_cli_entry check
python3 -m compileall -q modules/doctor
```
