# Finding skills — end-to-end workflow

Use this reference when the user is looking for functionality that might exist as an installable skill. It covers the domain/task split, the leaderboard check, quality verification before recommending, and how to present options.

**Goal:** the agent can find, verify, and present a skill recommendation without guessing or relying on search results alone.

## Step 1: Understand what they need

When a user asks for help with something, identify:

1. The domain (e.g., React, testing, design, deployment)
2. The specific task (e.g., writing tests, creating animations, reviewing PRs)
3. Whether this is common enough that a skill likely exists

## Step 2: Check the leaderboard first

Before running a CLI search, check the [skills.sh leaderboard](https://skills.sh/) to see if a well-known skill already exists for the domain. The leaderboard ranks skills by total installs, surfacing the most popular and battle-tested options.

For example, top skills for web development include:
- `vercel-labs/agent-skills` — React, Next.js, web design (100K+ installs each)
- `anthropics/skills` — Frontend design, document processing (100K+ installs)

## Step 3: Search for skills

If the leaderboard doesn't cover the user's need, run:

```bash
npx skills find [query] [--owner <owner>]
```

## Step 4: Verify quality before recommending

Do not recommend a skill based solely on search results. Always verify:

1. **Install count** — Prefer skills with 1K+ installs. Be cautious with anything under 100.
2. **Source reputation** — Official sources (`vercel-labs`, `anthropics`, `microsoft`) are more trustworthy than unknown authors.
3. **GitHub stars** — Check the source repository. A skill from a repo with <100 stars should be treated with skepticism.

## Step 5: Present options to the user

When you find relevant skills, present them to the user with:

1. The skill name and what it does
2. The install count and source
3. The install command they can run
4. A link to learn more at skills.sh

## Completion

- Domain, task, and likelihood triage is documented in Step 1.
- Leaderboard check precedes any CLI search (Step 2).
- Quality criteria are concrete: install count ≥ 1K preferred, <100 cautious; official sources preferred; <100 stars = skepticism (Step 4).
- Presentation format names exactly what to show the user (Step 5).
