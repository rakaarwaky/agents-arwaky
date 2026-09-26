# PLAN — `modules/mcp` (FRD + kode)

**Status:** APPROVED · **Parent:** `../frd-redesign-modules-20260923.md`

---

## 1. File yang diubah

| File | Aksi |
|------|------|
| `modules/mcp/FRD.md` | Rewrite penuh (§3) |
| `modules/mcp/BACKLOG.md` | Sync scenario evidence = 6 |
| Kode (§4) | Protocol → 1 method; aggregate multi |

---

## 2. Target FRD

### Protocol API — tepat 1 baris

| Method | Input | Output | Error | Event | Description |
|--------|-------|--------|-------|-------|-------------|
| `execute` | `op`, `output?`, `server_id?` | config / listing / probe | non-zero | — | Satu method menaungi generate, list, probe |

### Aggregate API (`McpOrchestrator` / `McpAgent`)

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `list_servers` | — | table | Report tanpa menulis |
| `show_server` | `id?` | detail | Probe help/schema |
| `generate` | `output` | path | Generate config |
| `generate_alias` | alias, `output` | path | Bentuk alias *(opsional)* |
| `validate` | `output?` | ok/err | Validasi *(opsional)* |

### FR (3) · Scenarios (6)

| ID | Judul |
|----|--------|
| FR-MCP-001 | Generate config klien dari manifest |
| FR-MCP-002 | Report server tanpa menulis |
| FR-MCP-003 | Probe help / schema satu server |

---

## 3. Struktur FRD (wajib)

Pola HOW-TO; Protocol **1 baris**; 3 FR × 6 field; 6 scenario; Rule 8–9.

---

## 4. Kode yang harus diubah

### Current

| File | Simbol | Method |
|------|--------|--------|
| `modules/shared/src/contract_mcp_protocol.py` | `IMcpConfigProtocol` | `generate` |
| `modules/shared/src/contract_mcp_aggregate.py` | `IMcpAggregate` | `list_servers`, `show_server`, `generate_config` |
| `modules/mcp/src/agent_mcp_orchestrator.py` | `McpOrchestrator` | + `generate` |
| `modules/mcp/src/capabilities_mcp_generator.py` | `McpConfigGenerator` | implements **both** protocol + aggregate |
| `modules/mcp/src/surface_mcp_command.py` | `McpAction` | implements aggregate |
| `modules/mcp/src/root_mcp_container.py` | `McpContainer` | wire |
| `modules/shared/src/__init__.py` | export | 2 symbols |

### Target

| File | Aksi |
|------|------|
| `contract_mcp_protocol.py` | **Ganti** `generate` → **`IMcpProtocol.execute(op, output?, server_id?)`** — 1 method semua capability |
| `contract_mcp_aggregate.py` | **Pertahankan multi**; samakan nama dgn FRD (`generate` vs `generate_config` — **pilih salah satu** di FRD lalu rename kode) |
| `agent_mcp_orchestrator.py` | Implement aggregate multi; dispatch `execute` ke generator **internal** |
| `capabilities_mcp_generator.py` | **Hapus** implement `IMcpAggregate` (duplikasi surface); cukup internal `generate`/`list`/`show` **atau** implement `IMcpProtocol.execute` |
| `surface_mcp_command.py` | Tetap aggregate |
| `root_mcp_container.py` | Wire tetap |
| `__init__.py` | Rename export |

### Diff intent

```
BEFORE: IMcpConfigProtocol.generate + IMcpAggregate(3); generator implements both
AFTER:  IMcpProtocol.execute(...)              # 1 method
        IMcpAggregate.(multi)                  # orchestrator only
        generator = internal capability
```

---

## 5. Gate

```bash
aa check docs modules/mcp
lint-arwaky-cli scan modules/mcp
python3 -m modules.root_cli_entry check
python3 -m compileall -q modules/mcp
```
