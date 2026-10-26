# DESIGN.md — Lint Rule Reference and Pitfalls

## Lint rule reference (the 9 rules, as of CLI 0.3.0)

- `broken-ref` (error) — `{colors.missing}` points at a non-existent token
- `contrast-ratio` (warning) — component `textColor` vs `backgroundColor`
  below WCAG AA (4.5:1)
- `missing-primary` (warning) — colors defined but no `primary` token
- `missing-typography` (warning) — colors defined but no typography tokens
- `orphaned-tokens` (warning) — color tokens never referenced by a component
- `section-order` (warning) — sections out of the canonical order
- `unknown-key` (warning) — top-level YAML key that looks like a typo of a
  schema key (`colours:` → `colors:`); custom extension keys stay silent
- `token-summary`, `missing-sections` (info) — counts and absent optional
  sections

When the user cares about accessibility, call this out explicitly in your
summary — WCAG findings are the most load-bearing reason to use the CLI.

## Pitfalls

- **Don't nest component variants.** `button-primary.hover` is wrong;
  `button-primary-hover` as a sibling key is right.
- **Hex colors must be quoted strings.** YAML will otherwise choke on `#` or
  truncate values like `#1A1C1E` oddly.
- **Negative dimensions need quotes too.** `letterSpacing: -0.02em` parses as
  a YAML flow — write `letterSpacing: "-0.02em"`.
- **Section order matters even though the linter only warns.** If the user
  gives you prose in a random order, reorder it to match the canonical list
  before saving — spec-compliant consumers expect it.
- **Typography sub-property typos are silently dropped.** As of CLI 0.3.0 a
  typo like `fontwight:` produces no finding and the value vanishes from
  exports — double-check sub-property names against the schema
  (`fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`,
  `fontFeature`, `fontVariation`).
- **`version: alpha` is the current spec version** (as of Jul 2026, CLI
  0.3.0). The spec is marked alpha — watch for breaking changes.
- **Token references resolve by dotted path.** `{colors.primary}` works;
  `{primary}` does not.
