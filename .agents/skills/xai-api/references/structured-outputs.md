# Structured Outputs

> Source: https://docs.x.ai/developers/model-capabilities/text/structured-outputs.md

Request responses as schema-conforming JSON instead of free-form text. Two mechanisms:

1. `response_format` — primary, most flexible.
2. Tool calling — xAI always generates tool-call arguments that strictly conform to
   the tool's input JSON Schema (`strict` is implicitly always true).

## response_format

| Value | Behaviour |
|---|---|
| `{"type": "json_schema", "json_schema": {...}}` | Output must match the given schema. |
| `{"type": "json_object"}` | Any well-formed JSON. |
| `{"type": "text"}` | Default, free-form. |

Use Pydantic or Zod to author schemas.

## JSON Schema support

Draft 2020-12 works best; Draft-07 accepted.

Supported types: `string`, `number`, `integer`, `boolean`, `null`, `enum`, `const`,
`array`, `object`, `anyOf`, `oneOf` (same as `anyOf`), `allOf` (single subschema only),
`$ref`/`$defs` (non-circular).

`additionalProperties` defaults to **false** — set it to `true` explicitly to allow extras.
Nullable fields: use `{"type": ["string", "null"]}` or `anyOf` including `null`.
Fields not in `required` are optional.

Enforced string formats: `date`, `time`, `date-time`, `email`, `uuid`, `ipv4`, `ipv6`, `uri`.
Other `format` values are accepted but not enforced.

### Constraint limits (guaranteed up to)

| Keyword | Guaranteed limit |
|---|---|
| `minimum`/`maximum`/`exclusiveMinimum`/`exclusiveMaximum` | no limit |
| `minLength`/`maxLength` | 2,048 |
| `minItems`/`maxItems` | 256 |
| `minProperties`/`maxProperties` | 64 |

### Best-effort (accepted, not structurally enforced)

`not`, `if`/`then`/`else`, multi-subschema `allOf`, unlisted `format` values, and
constraints exceeding the limits above. Validate client-side when strict conformance matters.

### Rejected (return 400)

- `enum` or `anyOf` with zero variants.
- Properties with a schema of `true`/`false`.
- `maxContains`/`minContains`.
- `items` as an array (use `prefixItems` for tuple validation).

### Regex (`pattern`)

ECMA-262 subset: literals, character classes, `.`, anchors, quantifiers, groups,
backreferences. See the docs page for the exact supported set.
