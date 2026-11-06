# Step 2 — Rules

## R1 — One owner per fact

State each fact once, at its most specific location. Elsewhere, reference the owner.

- Before: `Timeout is 30s. The retry timeout is 30 seconds.`
- After: `Timeout is 30s. Retry reuses this timeout.`

## R2 — Action-only sentences

Every sentence carries an action, decision, or constraint. Cut opener filler, hedging, restated introductions, and closing summaries that add nothing.

- Before: `It is worth noting that you should probably consider running the tests first.`
- After: `Run tests first.`

## R3 — Exact names

Use the exact path, command, flag, variable, or error string. If unknown, write `UNKNOWN`; never invent a value.

- Before: `update the config file`
- After: `update \`config/app.yaml\`` or `update UNKNOWN path`

## R4 — Control keywords visible

Backtick every keyword the reader must act on or must not change: flags, env vars, mode names, config keys. If two sources disagree on a term, log `CONFLICT: <term>: <a> vs <b>`.

- Before: `Run in improve mode with the create flag disabled.`
- After: `Run with \`--improve\`  \`--create\`.`
