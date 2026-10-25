# SOUL.md / context-file injection scan

`agent/prompt_builder.py: _scan_context_content()` runs `tools/threat_patterns.py:
scan_for_threats(content, scope="context")` over every context file that enters the system
prompt (SOUL.md, AGENTS.md, .cursorrules, subdirectory hints). On ANY match the file is
**blocked outright** — its whole body is replaced by
`[BLOCKED: <file> contained potential prompt injection (<pattern_ids>). Content not loaded.]`
and the persona silently stops existing. There is no config flag to downgrade this to a warning.

## Gate after every persona edit

```bash
cd ~/.hermes/hermes-agent && ./venv/bin/python -c \
  "import sys; sys.path.insert(0,'.'); \
   from tools.threat_patterns import scan_for_threats; \
   print(scan_for_threats(open('PATH/TO/SOUL.md').read(), scope='context'))"
```

`[]` = loads. Non-empty = blocked; the returned ids name the offending patterns.
Use the public `scan_for_threats` — the `_scan_for_threats` spelling is an import alias that
lives inside prompt_builder and is not importable (guessing it yields an ImportError).

## Evidence that a persona died this way

- The system prompt of the live session literally shows the `[BLOCKED: ...]` placeholder.
- `grep 'Context file.*blocked' ~/.hermes/profiles/<p>/logs/agent.log` (mirrored in
  `errors.log`, at WARNING with the pattern id). Absence of a block line means the file
  loaded fine and the cause lies elsewhere.

## Phrases that trip it (scope=context patterns)

Persona prose describing the agent's identity is exactly the vocabulary the scanner hunts in
*scraped* content, so innocuous boundary lines self-trip:

| pattern id | shape that fires |
|---|---|
| `role_pretend` | `pretend … you are` / `pretend … to be` (e.g. "never pretend to be human") |
| `role_hijack` | `you are now a|an|the …` |
| `identity_override` | `name yourself X` |
| `remove_filters` | `respond|answer|reply without restrictions|filters|limitations` |
| `bypass_restrictions` | `act as if you have no restrictions|limits|rules` |
| `fake_update` | `you have been updated|upgraded|patched to` |
| `leak_system_prompt` | `output … system|initial prompt` |
| `deception_hide` | `do not tell the user` |
| `prompt_injection` | `ignore previous/all/above instructions`, `system prompt override`, `disregard … rules` |
| `html_comment_injection` | `<!-- … ignore|override|system|secret|hidden … -->` |
| c2 tells | `register as a node`, `heartbeat/beacon/check-in to|with`, `pull tasks`, `connect to the network` |

`ignore … instructions` and friends are scope=`all`, so they hit scraped web content too —
never quote them verbatim in a skill or persona either.

## Rewrite, don't fight the scanner

Keep the meaning, drop the trigger verb: "never pretend to be human" -> "never claim to be
human"; "answer without restrictions" -> "answer with no editorialising"; "you are now a
mirror" -> "the stance is a cold mirror". Do not add an exemption to core for persona files —
the scan exists precisely because SOUL.md-shaped text is what injections mimic.

## Activation lag

The system prompt is byte-stable for the life of a conversation (prompt caching), so a fixed
SOUL.md takes effect only in a NEW session. Never judge the fix from the current session's
replies; say so and have the user `/new`.
