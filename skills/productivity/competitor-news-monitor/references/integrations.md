# Competitor News Monitor — Tool Integrations

**Goal:** know which tools to call for each data source type and how to handle failures.

## web_search / web_extract

- Use for official newsrooms, pricing pages, regulatory filings, and press.
- `web_search` for discovery; `web_extract` for reading a specific URL.
- A 404 or paywall is a coverage gap, not "no news" — record it in the state file.

## blogwatcher (optional, stateful)

- Use for RSS/Atom feeds of newsrooms and blogs.
- `blogwatcher-cli` tracks read/unread state; pair with the watch contract.
- If not available, fall back to `web_extract` on the feed URL.

## cronjob

- Create one job per watch-slug; the job prompt must reference the watch contract path.
- Cadence is user-chosen (weekly, daily); document it in the watch contract.

## Completion

- Each tool is available or a fallback is documented.
- The cron job prompt is testable (a single run of the prompt loads the skill and executes the tick).
