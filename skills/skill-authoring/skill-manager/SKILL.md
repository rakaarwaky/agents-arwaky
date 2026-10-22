---
name: skill-manager
description: Discovers and inspects skill guides in the agents-arwaky pack. Use when listing available skills or reading a skill's SKILL.md in the terminal.
metadata:
  tags: []
---

# Skill Manager (`aa skills`)

Read-only discovery and inspection of the `agents-arwaky` skill pack. There is
no provisioning step: agents read `skills/` directly, and harnesses get the
pack through `aa connect`.

## When to Use This Skill

Activate this skill when:

- Discovering what agent skills and tool capabilities exist within the
  `agents-arwaky` ecosystem.
- Reading a skill's guide (`SKILL.md`) in the terminal without opening files
  manually.

## Available Commands

| Command | Action | Example |
|---|---|---|
| `aa skills list` | List every skill in the pack with its description | `aa skills list` |
| `aa skills show <name>` | Print a skill's full `SKILL.md` to the terminal | `aa skills show fetch` |

Name matching for `show` accepts the frontmatter `name:`, the skill's
directory name, or a hyphen-free spelling (`fetch` → `fetch-mcp`).

## Skill Pack Layout

Skills live in the repo at `skills/`, organized by domain:

```
skills/
├── skill-authoring/       # How to author and maintain skills
├── software-development/  # Coding, testing, debugging, refactoring
├── ai-gateway/            # LLM API, model inventory, routing
├── automation/            # Browser, emulator, desktop control
├── code-quality/          # Linting, coverage, review, cleanup
├── creative/              # Images, video, 3D, design
├── devops/                # CI, services, profiles, hooks
├── documentation/         # Docs, slides, sheets
├── email/                 # Inbox triage, Himalaya CLI
├── github/                # PRs, issues, releases, CI
├── memory/                # LLM wiki
├── mlops/                 # Model serving, eval, hubs
├── note-taking/           # Obsidian, Anytype, Hermes plans
├── orchestration/         # Worktrees, subagents, workflows
├── productivity/          # Airtable, Notion, docs, meetings
├── research/              # ArXiv, papers, citations
└── web/                   # Scraping, X/Twitter
```

Each skill directory contains a `SKILL.md` with frontmatter (`name`,
`description`, `tags`) followed by the guide body. The frontmatter, name,
description, and category-shape constraints a skill must satisfy are the
rules in [`../_rules/skill-rules.md`](../_rules/skill-rules.md). The pack
is the single source of truth: edit a skill there and every connected
harness sees it.

## Harness Provisioning (connect, not install)

Provisioning skills to agent harnesses is handled by `aa connect`, not by a
skill command. When you connect a harness:

- **`aa connect <harness>` → harness skills dir:** the WHOLE folder becomes ONE
  SYMLINK to the pack (`<harness>/skills -> agents-arwaky/skills`). There is
  no per-skill provisioning step at all: add, remove, or edit a skill anywhere
  in the pack and every linked harness sees it instantly — self-improving
  agents (Hermes, Qwen Code) edit *through* the link, so their updates land in
  the repo and all harnesses share them; `git pull` propagates pack changes
  with zero re-provisioning. Only harnesses verified to follow the root
  symlink are linked (per-adapter `SKILL_LINK_VERIFIED`); others fall back to
  copies. `aa connect --copy-skills` forces copies everywhere; `aa disconnect`
  unlinks the root (restores an empty real dir) and never touches pack sources.
