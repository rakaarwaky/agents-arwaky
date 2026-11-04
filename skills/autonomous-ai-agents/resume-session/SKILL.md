---
name: resume-session
description: Resume or continue work from a recent Claude Code, Codex, or Cursor session. Use when the user switched from one of those tools, says continue from Claude-Codex-Cursor or resume my Claude-Codex-Cursor session, or names a session by description, path, or native ID.
when-to-use: Use when the user switched from Claude Code, Codex, or Cursor and wants to continue/resume a session by description, path, or native ID.
argument-hint: "[words describing the session | session id]"
metadata:
  short-description: "Continue from a recent Claude Code / Codex / Cursor session"
---

# Resume Session

Continue a recent Claude Code, Codex, or Cursor session in a fresh Grok session.

## Global rules

- **Determine the tool first.** Set `TOOL` from the tool the user switched from: Claude Code → `TOOL=claude`; Codex CLI or Codex VS Code → `TOOL=codex`; Cursor CLI or Cursor Desktop → `TOOL=cursor`. If the tool is not stated in the request or `$ARGUMENTS`, ask which tool the session came from before proceeding.

## Routing

| Step | Reference |
| ---- | --------- |
| Read and follow the full resume procedure (safety boundary, locating and reading the transcript, building the handoff, verification before continuing) | [`CORE.md`](CORE.md) — set `CORE_DIR="${SKILL_DIR}"` and pass `$ARGUMENTS` unchanged as the optional session reference |
