# PLAN — Redesain FRD `modules/*` (TARGET, bukan mirror kode)

> **Status:** APPROVED. Eksekusi per fitur: `.agents/plan/modules/<feature>.md`.  
> **Belum ada FRD yang ditulis/diedit** sampai perintah implementasi.  
> **Prinsip:** Spec = desain ulang besar. Kode sekarang **tidak** jadi acuan jumlah/orientasi API.  
> Setiap fitur **wajib** punya agent/aggregate dalam spesifikasi — ketiadaan di kode ≠ ketiadaan di FRD.

---

## A. Konvensi desain (disepakati)

| Layer | Aturan |
|--------|--------|
| **Protocol API** | **Tepat 1 method per fitur.** Satu method yang menaungi **semua** capability fitur itu — **1 baris total** (bukan N baris per capability, bukan multi-method). |
| **Aggregate API** | **Banyak method.** Surface agent/orchestrator yang **kita rancang** (boleh dan seharusnya beda dari kode hari ini). |
| **FR** | Perilaku testable / capability — **bukan** nama class, file, atau simbol implementasi. |
| **Agent** | Setiap fitur **punya** aggregate/agent di FRD. |
| **FRD vs kode** | FRD = target refactor; **jangan** snapshot implementasi sekarang. |
| **BACKLOG** | Evidence menyusul **setelah** FRD di-approve. |

---

## B. Plan per fitur (10)

> Protocol di tiap fitur = **1 baris**. Capability muncul di **FR** dan di **Aggregate**.

### 1. `backup` — `FR-BACKUP`

**Agent:** `BackupAgent`

**Protocol (1 method total):**

| Method | Input | Output |
|--------|-------|--------|
| `execute` | op, tool, dest/archive | result |

**Aggregate:** `backup`, `restore`, `list_archives`, `status_store`, `help`

**FR**

| ID | Judul |
|----|--------|
| FR-BACKUP-001 | Archive state XDG sebuah tool |
| FR-BACKUP-002 | Restore tool dari archive |
| FR-BACKUP-003 | List archive yang tersedia |
| FR-BACKUP-004 | Laporkan status store backup |
| FR-BACKUP-005 | Tampilkan usage backup |

- **Scenarios:** 5 (1/FR)  
- **NFR:** exit fidelity; list read-only; gagal storage → non-zero  
- **Integration:** filesystem XDG, cloud storage (opsional), root CLI  

---

### 2. `check` — `FR-CHECK`

**Agent:** `CheckAgent`

**Protocol (1 method total):**

| Method | Input | Output |
|--------|-------|--------|
| `execute` | scope (`all\|docs\|skill`) | exit + findings |

**Aggregate:** `check`, `check_docs`, `check_skill`, `summary`

**FR**

| ID | Judul |
|----|--------|
| FR-CHECK-001 | Audit invarian dokumen |
| FR-CHECK-002 | Audit loadability skill pack |
| FR-CHECK-003 | Dispatch scope ke jalur audit yang tepat |

- **Scenarios:** 6 (2/FR)  
- **NFR:** strict-only; determinism; runtime gate < 2 menit  
- **Integration:** root CLI `aa check`, shared doc/skill engines  

---

### 3. `config` — `FR-CONFIG`  ⚠️ **agent wajib dirancang (belum ada di kode)**

**Agent:** `ConfigAgent`

**Protocol (1 method total):**

| Method | Input | Output |
|--------|-------|--------|
| `execute` | op, path, payload | result / snapshot |

**Aggregate:** `load`, `save`, `merge_servers`, `set_env`, `remove_entries`, `inspect`, `help`

**FR**

| ID | Judul |
|----|--------|
| FR-CONFIG-001 | Load konfigurasi dan deteksi format |
| FR-CONFIG-002 | Save tanpa merusak komentar / urutan |
| FR-CONFIG-003 | Merge server MCP ke konfigurasi |
| FR-CONFIG-004 | Set pasangan env key |
| FR-CONFIG-005 | Hapus entri server / env |
| FR-CONFIG-006 | Inspeksi isi konfigurasi (read-only) |

- **Scenarios:** 12 (2/FR)  
- **NFR:** round-trip fidelity; dry-run tidak menulis; JSON / JSONC / TOML  
- **Integration:** root CLI `aa config …` (**dirancang**), shared config kernel  

---

### 4. `daemon` — `FR-DAEMON`

**Agent:** `DaemonAgent`

**Protocol (1 method total):**

| Method | Input | Output |
|--------|-------|--------|
| `execute` | op, daemon_id / unit | status / logs / result |

**Aggregate:** `list_known`, `start`, `stop`, `restart`, `status`, `logs`, `install_unit`, `remove_unit`, `unit_status`

**FR**

| ID | Judul |
|----|--------|
| FR-DAEMON-001 | Manage lifecycle satu daemon |
| FR-DAEMON-002 | Authorize Anytype dengan API key |
| FR-DAEMON-003 | Enumerasi daemon yang dikelola |
| FR-DAEMON-004 | Pasang / lepas unit systemd daemon |

- **Scenarios:** 8 (2/FR)  
- **Default desain:** unit systemd **di aggregate daemon** + Integration ke `service`  
- **Integration:** podman / systemd, root CLI `aa daemon …`  

---

### 5. `doctor` — `FR-DOCTOR`

**Agent:** `DoctorAgent`

**Protocol (1 method total):**

| Method | Input | Output |
|--------|-------|--------|
| `execute` | flags (`json`, mode) | report |

**Aggregate:** `diagnose`, `readiness`, `report`

**FR**

| ID | Judul |
|----|--------|
| FR-DOCTOR-001 | Diagnosa environment host |
| FR-DOCTOR-002 | Diagnosa kesiapan tool |

- **Scenarios:** 4 (2/FR)  
- **NFR:** row FAIL ≠ process fail (kecuali hard fail); JSON mode stabil  

---

### 6. `harness` — `FR-HARNESS`

**Agent:** `HarnessAgent`

**Protocol (1 method total):**

| Method | Input | Output |
|--------|-------|--------|
| `execute` | op, targets | result / resolved |

**Aggregate:** `resolve_targets`, `all_targets`, `connect`, `disconnect`, `provision_skills`

**FR**

| ID | Judul |
|----|--------|
| FR-HARNESS-001 | Connect harness (MCP, env, router, skills) |
| FR-HARNESS-002 | Disconnect harness bersih |
| FR-HARNESS-003 | Provision skill pack ke harness |
| FR-HARNESS-004 | Resolve id / alias / `--all` → target kanonik |

- **Scenarios:** 8 (2/FR)  

---

### 7. `mcp` — `FR-MCP`

**Agent:** `McpAgent`

**Protocol (1 method total):**

| Method | Input | Output |
|--------|-------|--------|
| `execute` | op, output / server_id | config / listing / probe |

**Aggregate:** `list_servers`, `show_server`, `generate`, `generate_alias`, `validate`

**FR**

| ID | Judul |
|----|--------|
| FR-MCP-001 | Generate config klien dari manifest |
| FR-MCP-002 | Report server tanpa menulis |
| FR-MCP-003 | Probe help / schema satu server |

- **Scenarios:** 6 (2/FR)  

---

### 8. `service` — `FR-SERVICE`

**Agent:** `ServiceAgent`

**Protocol (1 method total):**

| Method | Input | Output |
|--------|-------|--------|
| `execute` | op, unit | status / logs / result |

**Aggregate:** `status`, `start`, `stop`, `restart`, `logs`, `help`

**FR**

| ID | Judul |
|----|--------|
| FR-SERVICE-001 | Drive unit systemd (start / stop / restart) |
| FR-SERVICE-002 | Inspeksi status unit |
| FR-SERVICE-003 | Tail log unit |
| FR-SERVICE-004 | Tampilkan usage + target valid |

- **Scenarios:** 8 (2/FR)  

---

### 9. `skill` — `FR-SKILL`

**Agent:** `SkillAgent`

**Protocol (1 method total):**

| Method | Input | Output |
|--------|-------|--------|
| `execute` | op, skill / target | listing / audit / result |

**Aggregate:** `list`, `check`, `show`, `install`, `uninstall`, `sync`

**FR**

| ID | Judul |
|----|--------|
| FR-SKILL-001 | Provision skill ke project |
| FR-SKILL-002 | Audit loadability pack |
| FR-SKILL-003 | Query skill (list / show) |
| FR-SKILL-004 | Install / uninstall lewat surface CLI |
| FR-SKILL-005 | Sync ulang pack |

- **Scenarios:** 10 (2/FR)  

---

### 10. `tools` — `FR-TOOLS`

**Agent:** `ToolsAgent`

**Protocol (1 method total):**

| Method | Input | Output |
|--------|-------|--------|
| `execute` | op, spec / query / args | result / exit |

**Aggregate:** `list`, `resolve`, `install`, `update`, `uninstall`, `run`, `executable_path`

**FR** *(judul tanpa simbol basi / tanpa nama implementasi)*

| ID | Judul |
|----|--------|
| FR-TOOLS-001 | Install tool terdaftar |
| FR-TOOLS-002 | Update tool terdaftar |
| FR-TOOLS-003 | Uninstall tool beserta path owned |
| FR-TOOLS-004 | Run tool dengan fidelity exit code |
| FR-TOOLS-005 | Resolve query → spesifikasi tool |
| FR-TOOLS-006 | Discover kesiapan & path tool |

- **Scenarios:** 8 (2/FR)  

---

## C. Bentuk tulis per FRD (setelah approve)

```markdown
## API Contract

### Protocol API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| <Tepat 1 baris — 1 method menaungi semua capability fitur> | … | … | … | … | … |

### Aggregate API

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| <banyak baris — surface agent> | … | … | … | … | … |
```

**Eksekusi nanti (belum sekarang):**

1. Tulis 10 × `modules/<feature>/FRD.md` sesuai plan ini **saja** (tidak ubah kode).  
2. Per file: `aa check docs modules/<feature>` harus 0 finding.  
3. Sinkron BACKLOG **Scenario evidence** = jumlah scenario di FRD.  
4. Gate akhir: `aa check` + `aa check docs` + `aa check skill`.

---

## D. Sign-off (review di sini)

| # | Pertanyaan | Default plan |
|---|------------|--------------|
| 1 | Protocol **tepat 1 baris `execute` per fitur** (semua capability di 1 method)? | **ya** |
| 2 | config aggregate 7 method (§B.3) — oke? | **ya** |
| 3 | daemon unit systemd tetap di aggregate daemon? | **ya** |
| 4 | Jumlah FR / scenario per tabel §B — oke? | **ya** |

**Status:** APPROVED — plan per fitur **lengkap (FRD + inventaris kode)** di `.agents/plan/modules/<feature>.md`.
