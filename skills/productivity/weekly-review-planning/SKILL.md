---
name: weekly-review-planning
description: "Weekly reset: commitments, stalled work, next-week plan. Use when running a weekly review of completed work and commitments, finding stalled projects and waiting items, or planning next week across calendar, tasks, and notes."
when-to-use: "Use when the user asks to run their weekly review, asks what they committed to and what is slipping, wants next week planned from calendar/tasks/notes, wants stale projects and waiting items found, or when a cron tick fires for a scheduled weekly review. Not for daily briefs or single-inbox triage."
argument-hint: "[--window <last-week> | --period <range>] [--horizon <weeks>] [systems]"
version: 0.1.0
author: Ben Barclay (benbarclay), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Weekly-Review, Planning, Tasks, Calendar, Productivity]
    related_skills: [obsidian, notion, airtable, google-workspace, email-inbox-triage]
---

# Weekly Review and Planning

Run a bounded weekly reset across the user's chosen systems. This is a concrete recurring task, not a generic productivity methodology — the `weekly-review` Automation Blueprint schedules it as a cron job.

## Global rules

- **Default to drafts and recommendations, not mutations.** No task, event, or note is changed without explicit approval in step 7.
- **Silence from others is not completion.** A waiting item without a reply stays open; do not infer closure.
- **Capacity comes from the calendar, not the task list.** Before proposing next week's plan, estimate fixed calendar load first.
- **The review covers both the completed week and the planning horizon.** Gaps in coverage are stated explicitly in section 7 of the report.
- **Every stalled flag must trace to a record.** Vague "feels stalled" is not a valid flag; name the record, event, or thread.

## Routing

| Step | Reference | Purpose |
| --- | --------- | ------- |
| Review steps 1–7: systems, calendar, inboxes, projects, waiting, plan, apply | [`references/review-steps.md`](references/review-steps.md) | The seven-step procedure with "Done when" criteria and pitfalls. |
| Report output shape | [`references/output-shape.md`](references/output-shape.md) | The seven-section report structure and section-level rules. |
