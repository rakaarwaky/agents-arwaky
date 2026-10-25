---
title: Category Rules
role: reference
---

# Category Rules

## Folder shape

Category folders live directly under the skills root. Skills live one level below a category.

Correct:

```text
skills-root/automation/my-skill/SKILL.md
skills-root/web/page-reader/SKILL.md
skills-root/productivity/task-tracker/SKILL.md
```

Incorrect:

```text
skills-root/my-skill/SKILL.md
skills-root/automation/subcategory/my-skill/SKILL.md
skills-root/web/scraping/deep/page-reader/SKILL.md
```

The loader expects one category level and one skill level. Do not create nested subcategories inside a category folder.

## DESCRIPTION.md

Each category should have a `DESCRIPTION.md` file with frontmatter only.

Example:

```markdown
---
description: Skills for document creation, presentations, spreadsheets
---
```

No body content is required. The description helps the Librarian decide where skills belong.

## When to create a category

Create a new category when:

- The skill topic does not clearly belong to an existing category.
- At least two skills will live in the category, or a large category is being split.
- The category name describes a durable domain, not a one-off task.
- The existing category is too broad and its description no longer captures all contents.

Do not create a new category for a single skill unless the domain is clearly distinct and more related skills are expected soon.

## Naming

Category names follow the same shape rule the checker enforces for skill names:
the `name-format` and `category-depth` rules in
[`../../../../modules/skills/_rules/skill-rules.md`](../../../../modules/skills/_rules/skill-rules.md).

Valid:

```text
automation
ai-gateway
note-taking
software-development
```

Invalid:

```text
-Automation
automation-
auto--mation
Automation
```

## Renaming a category

There is no `aa skills` subcommand that renames a category in place. The procedure is:

1. `mv skills/<old-name> skills/<new-name>`
2. Update `skills/<new-name>/DESCRIPTION.md` if the scope changed
3. `rmdir skills/<old-name>` if the old directory was not removed by the `mv`
4. Grep the entire skills tree for the old path and fix all cross-references (see `skill-library` SKILL.md, “Rename a category” section)
5. `aa skills catalog && aa skills validate`

The grep step is non-optional: other skills’ bodies, `DESCRIPTION.md` routing tables, and script invocations (`python3 skills/<old>/<skill>/...`) will all be broken silently.
