---
name: local-service-api-ops
description: "Audit self-hosted localhost APIs. Use when probing health."
metadata:
  tags:
    - devops
    - api
    - localhost
    - services
    - safety
---

# Operating Self-Hosted Local Service APIs

For daemons the user runs themselves — memory banks, LLM gateways, vector stores,
databases with a REST surface — reached over `127.0.0.1`. The work is usually an
audit ("is this set up right?") or a repair, and the hazard is that these APIs
frequently expose a clear-all where you expect a delete-one.

## When to Use

- Auditing a localhost daemon: health, version, effective config, real state.
- Deciding whether a client-side config file is authoritative or inert.
- Any DELETE/PURGE against a service that stores accumulated user data.
- Before recommending a cleanup, dedupe, or purge of a running service's store.

## Procedure

1. **Identify the process and its owner config.** `ss -ltnp` for the port, then
   `systemctl --user cat <unit>` and `tr '\0' '\n' < /proc/<pid>/environ`. Whatever
   the daemon reads from its own environment is authoritative; the same keys in a
   client-side config file are inert.
2. **Establish the contract.** `GET /openapi.json` (or the equivalent) and read
   `paths`, `components.securitySchemes`, and any version field. Note which paths
   support which verbs — a path with `get` and `patch` still may not support
   `delete`.
3. **Check liveness and version skew.** `/health` then `/version`. Compare the
   server's version against the client library floor declared by whichever
   component drives it; a mismatch explains empty results and unexplained errors.
4. **Inspect real state before changing anything.** List endpoint, stats endpoint,
   and counters. Non-zero `pending`/`failed` operation counts mean work is backing
   up behind a slow dependency, not that storage is broken.
5. **Snapshot before every destructive call** — see the pitfall below. Export
   first; verify the export is non-empty, not `null`.
6. **Make the smallest change the diagnosis supports**, then re-read state and
   confirm the delta matches what you intended.

## Pitfalls

- **Read the operation `summary` before calling a delete.** An endpoint named
  `delete` may be scoped to a whole collection, ignore any id list you send in
  the body, and still return `success` with a `deleted_count` larger than you
  asked for. The id list being accepted into the request without error is not
  evidence it was honored — compare the reported count against what you sent.
- **A per-item GET/PATCH listing does not imply per-item DELETE exists.** Before
  concluding "I can remove just this one", confirm the verb exists on that path.
- **Take the snapshot first.** When the only deletion path is clear-all and there
  is no undo, trash, or recover route, an export taken beforehand is the only
  restore path. Restoring means the matching import endpoint, not manual
  reinsertion.
- **Suppress at read time instead of deleting.** Tag filters, type filters, and
  query scoping usually let you exclude an unwanted record without destroying it.
  Reach for deletion only when nothing else excludes it.
- **`localhost` can resolve to IPv6 first.** A daemon bound to `127.0.0.1` only
  will refuse a client that dialed `::1`. Pin the URL to `127.0.0.1` explicitly
  rather than relying on the default.
- **Config owned by the daemon belongs in the daemon's environment.** Duplicating
  those keys into a client config file leaves values that look authoritative and
  are not; remove them so the next reader is not misled.
- **Absent auth is not permission.** Check `components.securitySchemes`. A local
  daemon with no inbound auth means any local process can reach its destructive
  routes — worth telling the user plainly, since it changes how much the exposure
  matters.

## Reporting

State what was verified by an actual call, what changed, and what is left. When a
destructive mistake happened, say plainly what was lost, whether it rebuilds from
conversation logs, and which route can restore it — then name the guard that
prevents a repeat.

## References

- `references/hindsight-memory-bank.md` — Hindsight bank REST surface, recall score
  semantics, mode/LLM-ownership split, export-import restore.