# Audit — Frontmatter keys


Which keys are mandatory is a Global Rule; this table is the full key reference, including the optional ones.

| Field | Required | Notes |
| ----- | -------- | ----- |
| `name` | Yes | Validator rules `name-format`, `name-mismatch`. |
| `description` | Yes | Validator rules `description-*`. |
| `when-to-use` | Yes | Dedicated trigger phrases; Grok Build matches it together with `description`. |
| `argument-hint` | Yes | Slash-command autocomplete hint, e.g. `<command> [--flag]`. |
| `user-invocable` | Optional | Boolean, default `true`. `false` hides the skill from slash commands and the model's skill tool. |
| `disable-model-invocation` | Optional | Boolean, default `false`. `true` keeps the skill out of the model's listing; slash commands still run it. |
| `paths`, `model`, `effort`, `allowed-tools`, `license`, `compatibility`, `origin`, `metadata` | Optional | Grok Build controls. |
| anything else (`version`, `author`, `platforms`, ...) | Optional | Target-dependent; match the field set the destination validator enforces. |
