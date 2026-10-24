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
