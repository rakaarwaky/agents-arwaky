# Improve — Step 3: Frontmatter keys

**Goal:** you can state which frontmatter keys the target skill's `SKILL.md` must carry, which are optional Grok Build controls, and which are target-dependent, from the complete key reference.

Which keys are mandatory is a Rule; this table is the full key reference, including the optional ones.

| Field | Required | Notes |
| ----- | -------- | ----- |
| `name` | Yes | Validator rules `name-format`, `name-mismatch`. |
| `description` | Yes | Validator rules `description-*`. Keep it on one line (quoted when needed); a `>-` block scalar that runs straight into the `# Title` heading is dropped by the `sdc` parser and fires `missing-description`. |
| `when-to-use` | Yes | Dedicated trigger phrases; Grok Build matches it together with `description`. Same 1,024-char limit as `description` (Rules: Grok Build parser limits). |
| `argument-hint` | Yes | Slash-command autocomplete hint, e.g. `<command> [--flag]`. |
| `user-invocable` | Optional | Boolean, default `true`. `false` hides the skill from slash commands and the model's skill tool. |
| `disable-model-invocation` | Optional | Boolean, default `false`. `true` keeps the skill out of the model's listing; slash commands still run it. |
| `paths`, `model`, `effort`, `allowed-tools`, `license`, `compatibility`, `origin`, `metadata` | Optional | Grok Build controls. |
| anything else (`version`, `author`, `platforms`, ...) | Optional | Target-dependent; match the field set the destination validator enforces. |

## Completion

- Can state every mandatory key (`name`, `description`, `when-to-use`, `argument-hint`) and which optional keys apply to the target skill; `description`/`when-to-use`/`argument-hint` spelling verified against the Rules key reference.
