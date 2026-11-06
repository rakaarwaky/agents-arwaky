# LLM Writing — Rules

## Placement

| Info | Location |
|------|----------|
| Every task | Top: goal, constraints, commands, outputs. |
| One part | Section/sub-doc with exact reference. |
| Derivable | Delete. |

## Control Keywords

| Keyword | Meaning | Use |
|---------|---------|-----|
| `MUST` | Required behavior. | Capitalize only the keyword. |
| `NEVER` | Forbidden behavior. | State the exact alternative. |
| `ONLY` | Exclusive permission. | Name one allowed option. |
| `ALWAYS` | No exceptions. | Use sparingly. |
| `IF` / `THEN` / `ELSE` | Checkable condition. | Condition uses file, exit code, flag, or value. |

## Rule Row

| ID | Rule | Why | Check |
|----|------|-----|-------|
| Rn | `MUST` or `NEVER` action. | One short reason. | Exact checkable test. |

## Constraints

- One owner per fact.
- Delete derivable facts.
- Table cells ≤ 20 words.
- Backtick every control keyword.
- Use exact path, section, variable, or `UNKNOWN`.
- Log unresolved contradictions as `CONFLICT:`.
- Delete persuasion, warmth, entertainment, greetings, and narrative.