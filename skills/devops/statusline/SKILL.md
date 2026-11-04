---
name: statusline
description: "Configure the optional Grok Build status-line row (`[ui.status_line]`). Use when the user wants built-in items (cwd, model, context), a custom command script, or the row disabled."
when-to-use: "Use when the user asks to configure the status line row: built-in items, a custom script path, refresh interval, padding, or off/disabled."
argument-hint: "[builtin | command <path> | disabled]"
---

# Status Line

Configure the optional Grok Build status-line row: pick built-in items, point it at a custom script, or turn it off, then land the edit in the one config file Grok reads.

## Global Rules

- **Write only the user config file.** `[ui.status_line]` belongs in the resolved user `config.toml`; repo-level `.grok/config.toml` cannot set the row. See `config-location.md` for the resolution rule.
- **Ask before writing when the user has not named the row.** The row is optional and off by default; a write without a request is a defect.
- **The table change takes effect at startup; the script change on the next run.** Tell the user which one applies.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Where to write | [`references/config-location.md`](references/config-location.md) | Config file resolution, the one-file rule, and the ask-vs-write decision. |
| What to write | [`references/table-values.md`](references/table-values.md) | `[ui.status_line]` blocks for built-in, command, and disabled, with `refresh_interval` and `padding` ranges. |
| Script contract | [`references/script-contract.md`](references/script-contract.md) | Stdin JSON fields, the 5 x 1024 stdout budget, timeouts, and link/ANSI rules. |
| After the edit | [`references/post-edit.md`](references/post-edit.md) | Effect timing, the rendered `[ui.status_line]` failure mode, and `grok inspect`. |
