---
name: xdg-spec-compliance
description: "Audit and fix XDG Base Directory compliance in a repo (data/config/cache/state paths, 0700 dirs, 0600 secrets, precedence). Use when the app resolves paths with `expanduser`/`Path.home`, writes logs outside `$XDG_STATE_HOME`, or ships world-readable secrets."
when-to-use: "Use when auditing a repo's path resolution against the XDG Base Directory spec: relative/tilde rejection, precedence (shell env > XDG file > .env), dir and file permissions, and vendor subdirs."
argument-hint: "[<repo-root>]"
metadata:
  tags:
    - linux
    - xdg
    - packaging
    - security
    - python
    - bash
---

# XDG Base Directory Compliance

Audit and fix a repo's path resolution against the XDG Base Directory spec: run the four-step audit order, check the seven rules projects break, and fix the installer, tests, and provisioner where each rule fails.

## Global Rules

- **Quote the spec, don't reason from memory.** The authoritative text is v0.8 at https://specifications.freedesktop.org/basedir/latest/ — three rules are routinely guessed wrong; the rules reference is the single home.
- **Reproduce before claiming.** Relative/tilde env values and mkdir umask inheritance are invisible to reading alone; the audit order reference ends in a repro step, and no claim rests on reading alone.
- **Clean up probe junk.** Any file the repro dumps into the repo is removed before the run is done; `git status` must be clean at the end.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Audit order | [`references/audit-order.md`](references/audit-order.md) | The four cheapest-signal-first checks: path grep, LOG/state location, write/read split, repro. |
| The rules projects break | [`references/rules.md`](references/rules.md) | The seven spec rules: absolute-only, empty/unset default, 0700 dirs, 0600 secrets, precedence, vendor subdir, `XDG_RUNTIME_DIR`. |
| Bash installer | [`references/bash-installer.md`](references/bash-installer.md) | Installer rules: absoluteness helper, 0700 tree, venv install, entry points. |
| Test it without touching the user's home | [`references/testing-sandbox.md`](references/testing-sandbox.md) | The import-time sandbox, the asserts, the fake-green guards, and the lazy log handler. |
| Destructive provisioning | [`references/destructive-provisioning.md`](references/destructive-provisioning.md) | Stale-dir rename instead of `rmtree`, and the symlink exfiltration rule. |
