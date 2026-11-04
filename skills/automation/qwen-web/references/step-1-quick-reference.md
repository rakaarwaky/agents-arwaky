# Step 1 — Quick reference: MCP tools & CLI commands

**Goal:** you can map every qwen-web use case to its MCP tool or `qwa` CLI command.

## Commands

| Action | MCP Tool | CLI Command (`qwa` / `qwen-web-arwaky`) |
| :--- | :--- | :--- |
| Direct text prompt | `process_direct_prompt` | `qwa prompt direct -t "<prompt>" [-o <out>]` |
| Prompt file only | `process_prompt_file_only` | `qwa prompt file -i <prompt.md> [-o <out>]` |
| Prompt with attachment | `process_prompt_with_attachment` | `qwa prompt attach -i <prompt.md> -a <file> [-o <out>]` |
| Check session health | `check_session` | `qwa doctor [--smoke] [--deep]` |
| Manual login / CAPTCHA | `setup_session` | `qwa session login` |
| Reset session | `delete_session` | `qwa session remove <id>` |
| Initialize workspace | `init_workspace` | `qwa init [--dir <dir>]` |

> **File conventions:** Place inputs under `.qwen-web-arwaky/input/` (or `.qwen-web/input/`) and outputs under `.qwen-web-arwaky/output/`. Always append a timestamp to output filenames (e.g., `arch_review_$(date +%Y%m%d_%H%M%S).md` in CLI or `YYYYMMDD_HHMMSS` in MCP) to prevent overwriting results from previous runs.

---

## Completion

- Every use case in [step-2-use-cases.md](step-2-use-cases.md) is covered by one of the command rows above.
