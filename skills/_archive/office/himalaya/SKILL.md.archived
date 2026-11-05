---
name: himalaya
description: 'Himalaya CLI: IMAP/SMTP email from terminal.'
when-to-use: "Use when managing email from the terminal via IMAP/SMTP — listing folders, reading and searching messages, composing and sending replies, moving/copying/deleting mail, and managing flags and attachments."
argument-hint: "account configure|folder list|envelope list [--folder <name>] [--page N] [--page-size N]|message read <id>|message write|template send|message move <folder> <id>|message copy|message delete|flag add|flag remove|attachment download [--downloads-dir <dir>]"
version: 1.1.0
author: community
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, CLI, Communication]
    homepage: https://github.com/pimalaya/himalaya
prerequisites:
  commands: [himalaya]
---

# Himalaya Email CLI

Himalaya is a CLI email client that lets you manage emails from the terminal using IMAP, SMTP, Notmuch, or Sendmail backends.

This skill is separate from the Hermes Email gateway adapter. The gateway
adapter lets people email the agent and uses Hermes' built-in IMAP/SMTP
adapter; this skill lets the agent operate a mailbox from terminal tools and
requires the external `himalaya` CLI.

## Global rules

- **Always configure `folder.aliases` for any provider whose folder names don't match himalaya's canonical names.** Gmail is the common case — use the v1.2.0 `folder.aliases.X` syntax (plural, dotted keys, directly under `[accounts.NAME]`); the pre-v1.2.0 singular `alias` sub-section is silently ignored, which makes save-to-Sent fail *after* SMTP delivery succeeds and causes any retry-on-error caller to re-run SMTP — duplicate mail to recipients. Full mapping in `references/configuration.md`.
- **Store passwords securely** — `pass`, system keyring, or a command that outputs the password; never inline `auth.raw` except in throwaway tests.
- **Pipe non-interactive compose via `himalaya template send`**; interactive `$EDITOR` mode needs PTY + background and knowing the editor. Use `--output json` for structured output.
- **Inspect Sent before retrying a send error** — SMTP may have succeeded while save-to-Sent failed; a blind retry duplicates the mail.

## Routing

| Step | Reference | Purpose |
| --- | --- | --- |
| Configuration setup + IMAP/SMTP auth | [`references/configuration.md`](references/configuration.md) | Prerequisites, install, wizard or hand-written `config.toml`; Gmail/iCloud/notmuch/OAuth2/multi-account examples, and the `folder.aliases` block that prevents duplicate-mail on Gmail. |
| MML syntax for rich messages | [`references/message-composition.md`](references/message-composition.md) | Multipart, attachments, inline images, mixed content. |
| Common operations | [`references/operations.md`](references/operations.md) | Listing, reading, replying, forwarding, moving, flags, attachments, output formats, debugging. |
