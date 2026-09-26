# PLAN — `modules/skill` (FRD + kode)

**Status:** APPROVED · **Parent:** `../frd-redesign-modules-20260923.md`

---

## 1. File yang diubah

| File | Aksi |
|------|------|
| `modules/skill/FRD.md` | Rewrite penuh (§3) |
| `modules/skill/BACKLOG.md` | Sync scenario evidence = 10 |
| Kode (§4) | Protocol → 1 method; aggregate multi |

---

## 2. Target FRD

### Protocol API — tepat 1 baris

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `op`, `skill?`, `target?` | listing / audit / result | non-zero | — | Satu method menaungi provision, audit, query, remove, sync |

### Aggregate API (`SkillOrchestrator` / `SkillAgent`)

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `list` | `target?` | table | List skill |
| `check` | `target?` | audit | Audit loadability |
| `show` | `name` | doc | Detail skill |
| `install` | scope, `target` | result | Provision |
| `uninstall` | `target`, `--prune?` | result | Hapus copy |
| `sync` | `target` | result | Sync pack |

### FR (5) · Scenarios (10)

| ID | Judul |
|----|--------|
| FR-SKILL-001 | Provision skill ke project |
| FR-SKILL-002 | Audit loadability pack |
| FR-SKILL-003 | Query skill (list / show) |
| FR-SKILL-004 | Install / uninstall lewat surface CLI |
| FR-SKILL-005 | Sync ulang pack |

---

## 3. Struktur FRD (wajib)

Pola HOW-TO; Protocol **1 baris**; 5 FR × 6 field; 10 scenario; Rule 8–9.

---

## 4. Kode yang harus diubah

### Current

| File | Simbol | Method |
|------|--------|--------|
| `modules/shared/src/contract_skill_protocol.py` | `ISkillInstallProtocol` | `install` |
| | `ISkillPruneProtocol` | `prune` |
| | `ISkillAuditProtocol` | `audit` |
| | `ISkillListProtocol` | `cmd_list` |
| | `ISkillCheckProtocol` | `cmd_check` |
| | `ISkillShowProtocol` | `cmd_show` |
| | `ISkillInstallCmdProtocol` | `cmd_install` |
| | `ISkillUninstallCmdProtocol` | `cmd_uninstall` |
| | `ISkillProvisioner` | composite install+prune+audit |
| | `ISkillRegistry` | composite 5 cmd |
| `modules/shared/src/contract_skill_aggregate.py` | `ISkillAggregate` | `list_skills`, `check_skills`, `install_skills`, `uninstall_skills`, `show_skill`, `sync_skills` |
| `modules/skill/src/agent_skill_orchestrator.py` | `SkillOrchestrator` | implements aggregate |
| `modules/skill/src/capabilities_skill_pack.py` | `SkillPackProvisioner` | `ISkillProvisioner` |
| `modules/skill/src/capabilities_skill_registry.py` | `SkillRegistry` | `ISkillRegistry` |
| `modules/skill/src/surface_skill_command.py` | `SkillRegistryAdapter` | `ISkillRegistry` |
| `modules/skill/src/root_skill_container.py` | `SkillContainer` | wire |
| `modules/skill/src/utility_skill_pack.py` | pack helpers | (utility — tidak disentuh kecuali export) |
| `modules/shared/src/__init__.py` | export | ~10 symbols |

### Target

| File | Aksi |
|------|------|
| `contract_skill_protocol.py` | **Hapus** 8 leaf + 2 composite. Sisakan **1** `ISkillProtocol.execute(op, skill?, target?)` |
| `contract_skill_aggregate.py` | **Pertahankan multi**; **samakan nama** dgn FRD (`list`/`check`/`show`/`install`/`uninstall`/`sync` — rename dari `*_skills`/`show_skill` bila perlu) |
| `agent_skill_orchestrator.py` | Implement aggregate multi; dispatch `execute` ke provisioner/registry internal |
| `capabilities_skill_pack.py` | **Hapus** inheritance `ISkillProvisioner`; internal impl |
| `capabilities_skill_registry.py` | **Hapus** inheritance `ISkillRegistry`; internal impl **atau** implement `execute` |
| `surface_skill_command.py` | Sinkron ke aggregate / adapter registry internal |
| `root_skill_container.py` | Wire |
| `__init__.py` | Export baru; hapus leaf |

### Diff intent

```
BEFORE: 8 leaf + ISkillProvisioner + ISkillRegistry + ISkillAggregate(6)
AFTER:  ISkillProtocol.execute(...)         # 1 method
        ISkillAggregate.(6, align FRD)      # multi
        pack/registry = internal
```

---

## 5. Gate

```bash
aa check docs modules/skill
lint-arwaky-cli scan modules/skill
python3 -m modules.root_cli_entry check
python3 -m compileall -q modules/skill
```
