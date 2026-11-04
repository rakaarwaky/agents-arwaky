---
name: competitor-news-monitor
description: "Watch named companies for material news; cited digests. Use when monitoring a competitor set, tracking company launches, pricing, funding, partnerships, executive moves, or incidents, scheduling a recurring competitor-intelligence digest, or running the scheduled competitor-watch tick."
when-to-use: "Use when the user asks to monitor competitors, tell them when a named company changes pricing or launches a product, create a competitor intelligence digest, track funding/partnerships/executive moves/incidents, or when a cron tick fires for an existing competitor watch. Not for one-off company research (use web_search/web_extract) or plain feed reading (blogwatcher)."
argument-hint: "[create | tick] <companies-or-slug> [watch-slug] [--all-clear]"
version: 0.1.0
author: Ben Barclay (benbarclay), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Competitors, News, Market-Research, Monitoring]
    related_skills: [blogwatcher, rss-feeds, reddit-reading]
---

# Competitor News Monitor

Track a declared company set and report only material, new developments with primary-source evidence. This is not a generic page-diff watcher: it applies company-news categories, source hierarchy, event deduplication, and business significance. Setup runs once in the foreground; the recurring check runs as a `cronjob` tick (the `competitor-watch` automation blueprint scaffolds this).

## Global rules

- **Source failures are coverage gaps, not "no news."** Record them in the state file; do not advance the cutoff past a failed source.
- **Deduplicate by underlying event.** Ten articles about one launch is one event; keep independently sourced corroboration attached.
- **Separate measured facts from interpretation.** Hiring patterns and anonymous reports remain signals, not confirmed strategy.
- **Watch contract is the single source of truth.** Every materiality decision must replay consistently from the watch contract at `~/.hermes/competitor-watches/<watch-slug>.json`.
- **Digest cites primary sources only.** Every surfaced event links to at least one primary or reputable source.
- **Silence is valid.** When no material events, stay silent unless a periodic all-clear was requested.

## Routing

| Step | Reference | Purpose |
| --- | --------- | ------- |
| Setup: freeze watchlist, build source coverage, schedule | [`references/setup.md`](references/setup.md) | Watch contract fields, source tiers, cron job creation. |
| Tick: collect, deduplicate, assess, deliver | [`references/tick.md`](references/tick.md) | The four tick steps, pitfalls, and verification checklist. |
| Event category patterns and materiality scoring | [`references/patterns.md`](references/patterns.md) | Source hierarchy table, dedup rules, six-axis materiality scoring. |
| Tool integrations and fallbacks | [`references/integrations.md`](references/integrations.md) | Which tool for which data source; failure handling. |
