# Skill CLI reference

The `npx skills` CLI is the package manager for the open agent skills ecosystem. Skills are modular packages that extend agent capabilities with specialized knowledge, workflows, and tools.

**Goal:** give the agent the exact command syntax and output shapes for searching, installing, and updating skills.

## `npx skills find`

```bash
npx skills find [query] [--owner <owner>]
```

Search for skills interactively or by keyword, optionally scoped to a GitHub owner.

Examples:
- User asks "how do I make my React app faster?" → `npx skills find react performance`
- User asks "can you help me with PR reviews?" → `npx skills find pr review`
- User asks "I need to create a changelog" → `npx skills find changelog`

## `npx skills add`

```bash
npx skills add <package>
```

Install a skill from GitHub or other sources.

## `npx skills update`

```bash
npx skills update
```

Update all installed skills.

**Browse skills at:** https://skills.sh/

## Completion

- `npx skills find`, `npx skills add`, and `npx skills update` each carry exact syntax and an example.
- Output shape for `find` is documented: interactive or keyword search, optional `--owner` scoping.
