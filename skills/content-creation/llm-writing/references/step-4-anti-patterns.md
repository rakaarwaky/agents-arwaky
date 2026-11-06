# Step 4 — Antipatterns

## Issues fixed

| Category | Pattern | Fix |
|----------|---------|-----|
| Slop | `It is important to note that...`, `It's worth noting...` | Delete; state the fact. |
| Slop | Greeting, transition, marketing, idiom, sarcasm. | Delete or replace with literal statement. |
| Slop | `In order to` | `to` |
| Slop | `Please` in docs | Delete. |
| Slop | Hedging (`might`, `possibly`, `arguably`) with no real condition | Delete. |
| Slop | Filler: `actually`, `basically`, `just`, `really`. | Delete. |
| Slop | Introductions or summaries restating the body | Delete. |
| Slop | Emoji and exclamation marks in technical docs | Delete. |
| Concision | Same fact in 2+ places | Keep one owner (R1); reference it elsewhere. |
| Concision | Nominalization: `perform initialization of` | `initialize` |
| Concision | Passive hiding the actor: `errors are logged` | `the wrapper logs errors` |
| Concision | Relative clause on obvious content: `the file, which is located in the project,` | `the file` |
| Concision | Bullet restating its heading | Merge into heading or delete. |
| Concision | Buried goal. | Move goal/constraints top. |
| Concision | Long explanation. | Action/constraint first; why only if non-obvious. |
| Clarity | `it` / `this` / `that` with 2+ possible referents | Name the referent. |
| Clarity | Vague quantity: `some`, `several`, `fast` | Exact number or `UNKNOWN`. |
| Clarity | Vague name: `the config`, `the script` | Exact path or `UNKNOWN`. |
| Clarity | Two terms for one thing | Keep the exact source term; log `CONFLICT:` if sources disagree. |
| Clarity | Contradiction. | Resolve or log `CONFLICT:`. |