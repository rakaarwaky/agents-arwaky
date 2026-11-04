---
name: qwen-web
description: Automate Qwen AI Web (chat.qwen.ai) with the Qwen3.8-Max intelligence model — zero API keys, persistent browser sessions — and develop the qwen-web-arwaky repo source (TUI, slots, tests). Use when an AI agent needs to send prompts, review code, or analyze attachments via CLI/MCP tools, or edit the internal/qwen-web-arwaky source.
when-to-use: Use when the user runs /qwen-web, sends a prompt to Qwen AI Web, sends prompt files or attachments for Qwen analysis or code review with role templates, sets up or resets the Qwen browser session, initializes the qwen-web workspace, or asks to develop or fix the internal/qwen-web-arwaky repo.
argument-hint: "<prompt direct -t <text> | prompt file -i <file> | prompt attach -i <file> -a <file> | doctor [--smoke] [--deep] | session login | session remove <id> | init [--dir <dir>]> [-o <out-file>] [--headless|--no-headless] [--json]"
metadata:
  tags:
    - qwen
    - qwen-web
    - qwen-web-arwaky
    - python
    - textual
    - tui
    - uv
    - pytest
    - aes
    - automation
---

# Qwen Web Automation Skill Guide

You send prompts, prompt files, and attachments to **Qwen AI (`chat.qwen.ai`)**
and receive complete responses via MCP tools or the `qwa` CLI (`qwen-web-arwaky`),
or you develop and modify the `qwen-web-arwaky` repo source.

## Global rules

- **Timestamp every output filename.** Inputs live under
  `.qwen-web-arwaky/input/`, outputs under `.qwen-web-arwaky/output/`, and each
  output name gets a timestamp (`YYYYMMDD_HHMMSS`) so runs never overwrite each
  other.
- **Prefer attachments for context.** Keep the prompt file focused on
  instructions; pass code, logs, and schemas as attachments.
- **For complete code output, demand it.** Include an explicit output contract
  and the anti-truncation clause; keep the reasoning-before-code ordering.
- **Verify session health before work.** Call `check_session` (MCP) or run
  `qwa doctor` first; on `AuthRequiredError`/CAPTCHA, re-login with
  `setup_session` / `qwa session login` rather than retrying.
- **Never type passwords or 2FA codes** for the Qwen session; solve them
  manually via the visible browser login when a session reset is needed.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Step 1: Quick reference | [`references/step-1-quick-reference.md`](references/step-1-quick-reference.md) | MCP tool ↔ `qwa` CLI command mapping. |
| Step 2: Usage by use case | [`references/step-2-use-cases.md`](references/step-2-use-cases.md) | Six use cases: inline prompt, file, attachment, role templates, session, init. |
| Step 3: Prompt engineering | [`references/step-3-prompt-engineering.md`](references/step-3-prompt-engineering.md) | Rules for complete, un-truncated output. |
| Step 4: Error handling | [`references/step-4-error-recovery.md`](references/step-4-error-recovery.md) | Error → cause → recovery table. |
| Step 5: Development | [`references/step-5-dev.md`](references/step-5-dev.md) | Dev guide for the `qwen-web-arwaky` repo source. |
