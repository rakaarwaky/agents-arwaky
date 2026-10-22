---
name: resume-session
description: >
  Resume or continue work from a recent Claude Code, Codex, or Cursor session.
  Use when the user switched from one of those tools, says "continue from
  Claude/Codex/Cursor" or "resume my Claude/Codex/Cursor session", or names a
  session by description, path, or native ID.
metadata:
  short-description: "Continue from a recent Claude Code / Codex / Cursor session"
  argument-hint: "[words describing the session | session id]"
---

Set `TOOL` from the tool the user switched from:

- Claude Code → `TOOL=claude`
- Codex CLI or Codex VS Code → `TOOL=codex`
- Cursor CLI or Cursor Desktop → `TOOL=cursor`

If the tool is not stated in the request or `$ARGUMENTS`, ask which tool the
session came from before proceeding.

Set `SHARED_DIR="${SKILL_DIR}/../../shared/resume-session"`. Read and follow
`${SHARED_DIR}/CORE.md`, using `$ARGUMENTS` unchanged as the optional session
reference.
