# LLM Writing — Anti-Patterns

| Pattern | Fix |
|---------|-----|
| Greeting, transition, marketing, idiom, sarcasm. | Delete or replace with literal statement. |
| Filler: "actually", "basically", "just", "really". | Delete. |
| Vague reference. | Exact path, section, variable, or `UNKNOWN`. |
| Undefined term/acronym. | Define once at first use. |
| Placeholder `<TODO>` or `...`. | Fill value or write `UNKNOWN`. |
| Repeated fact. | Keep one owner; reference it. |
| Derivable fact. | Delete. |
| Long explanation. | Action/constraint first; why only if non-obvious. |
| Paragraph cell. | Shorten to ≤ 20 words. |
| Buried goal. | Move goal/constraints top. |
| Unstated output format. | State format, length, structure. |
| Contradiction. | Resolve or log `CONFLICT:`. |