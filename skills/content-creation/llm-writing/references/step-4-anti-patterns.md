# Step 4 — Antipatterns

## AI slop

| Pattern | Fix |
|---------|-----|
| `It is important to note that...`, `It's worth noting...` | Delete; state the fact. |
| Greeting, transition, marketing, idiom, sarcasm. | Delete or replace with literal statement. |
| `In order to` | `to` |
| `Please` in docs | Delete. |
| Hedging (`might`, `possibly`, `arguably`) with no real condition | Delete. |
| Filler: "actually", "basically", "just", "really". | Delete. |
| Introductions or summaries restating the body | Delete. |
| Emoji and exclamation marks in technical docs | Delete. |

## Concision

| Pattern | Fix |
|---------|-----|
| Same fact in 2+ places | Keep one owner (R1); reference it elsewhere. |
| Nominalization: `perform initialization of` | `initialize` |
| Passive hiding the actor: `errors are logged` | `the wrapper logs errors` |
| Relative clause on obvious content: `the file, which is located in the project,` | `the file` |
| Repeated fact. | Keep one owner; reference it. |
| Bullet restating its heading | Merge into heading or delete. |
| Buried goal. | Move goal/constraints top. |
| Long explanation. | Action/constraint first; why only if non-obvious. |

## Clarity

| Pattern | Fix |
|---------|-----|
| `it` / `this` / `that` with 2+ possible referents | Name the referent. |
| Vague quantity: `some`, `several`, `fast` | Exact number or `UNKNOWN`. |
| Vague name: `the config`, `the script` | Exact path or `UNKNOWN`. |
| Two terms for one thing | Keep the exact source term; log `CONFLICT:` if sources disagree. |
| Contradiction. | Resolve or log `CONFLICT:`. |
