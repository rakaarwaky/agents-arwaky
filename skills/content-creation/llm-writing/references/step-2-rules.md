# Step 2 — Rules

| ID | Rule | Before | After |
|----|------|--------|-------|
| R1 | One owner per fact. State each fact once, at its most specific location. Elsewhere, reference the owner. | `Timeout is 30s. The retry timeout is 30 seconds.` | `Timeout is 30s. Retry reuses this timeout.` |
| R2 | Action-only sentences. Every sentence carries an action, decision, or constraint. Cut opener filler, hedging, restated introductions, and closing summaries that add nothing. | `It is worth noting that you should probably consider running the tests first.` | `Run tests first.` |
| R3 | Exact names. Use the exact path, command, flag, variable, or error string. If unknown, write `UNKNOWN`; never invent a value. | `update the config file` | ``update `config/app.yaml` `` or `update UNKNOWN path` |
| R4 | Control keywords visible. Backtick every keyword the reader must act on or must not change: flags, env vars, mode names, config keys. If two sources disagree on a term, log `CONFLICT: <term>: <a> vs <b>`. | `Run in improve mode with the create flag disabled.` | ``Run with `--improve`  `--create`.`` |
| R5 | No new facts. A rewrite adds no fact, name, number, date, quote, or citation not in the source or supplied by the user. Specificity comes from the source, not the rewrite. | `This is fast and reliable (99.9% uptime, used by 10k teams).` | `This is fast and reliable.` |
| R6 | Preserve voice. If the user or source supplies a tone, keep it. Copy with no voice reads as machine-made as copy full of filler. | Replacing `We rewrote pricing` with `Pricing was updated.` | `We rewrote pricing.` |