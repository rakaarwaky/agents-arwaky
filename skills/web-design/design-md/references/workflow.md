# Workflow — Authoring / Lint / Diff / Export

The CLI is `@google/design.md` (Node). Use `npx` — no global install needed.

```bash
# Validate structure + token references + WCAG contrast
npx -y @google/design.md lint DESIGN.md

# Compare two versions, fail on regression (exit 1 = regression)
npx -y @google/design.md diff DESIGN.md DESIGN-v2.md

# Export to Tailwind v3 theme JSON (`tailwind` is a back-compat alias)
npx -y @google/design.md export --format json-tailwind DESIGN.md > tailwind.theme.json

# Export to a Tailwind v4 CSS @theme block (--color-*, --text-*, --radius-*, ...)
npx -y @google/design.md export --format css-tailwind DESIGN.md > theme.css

# Export to W3C DTCG (Design Tokens Format Module) JSON
npx -y @google/design.md export --format dtcg DESIGN.md > tokens.json

# Print the spec itself — useful when injecting into an agent prompt
npx -y @google/design.md spec --rules-only --format json
```

## Authoring a new DESIGN.md

1. **Ask the user** (or infer) the brand tone, accent color, and typography
   direction. If they provided a site, image, or vibe, translate it to the
   token shape above.
2. **Write `DESIGN.md`** in their project root using `write_file`. Always
   include `name:` and `colors:`; other sections optional but encouraged.
3. **Use token references** (`{colors.primary}`) in the `components:` section
   instead of re-typing hex values. Keeps the palette single-source.
4. **Lint it** (see below). Fix any broken references or WCAG failures
   before returning.
5. **If the user has an existing project**, also write Tailwind or DTCG
   exports next to the file (`tailwind.theme.json`, `tokens.json`).

## Exit codes and notes

All commands accept `-` for stdin. `lint` returns exit 1 on errors (warnings
alone exit 0). `export` exits 0 on a successful export regardless of lint
findings in the source — run `lint` separately to gate on those. Output is
JSON by default; parse it if you need to report findings structurally.

On Windows, the `design.md` bin name can collide with the `.md` file
association (silent no-op or the file opens in an editor). Use the dot-free
alias: `npx -y -p @google/design.md designmd lint DESIGN.md`.
