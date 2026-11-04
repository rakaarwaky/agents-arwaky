---
name: blogwatcher
description: "Monitor blogs and RSS/Atom feeds via blogwatcher-cli tool."
when-to-use: Use when the user wants to monitor blogs and RSS/Atom feeds, add or remove tracked blogs, scan for new articles, or manage read/unread articles via blogwatcher-cli.
argument-hint: "<add | scan | articles | blogs | remove | import | read | unread | read-all> [blog] [url] [--feed-url | --scrape-selector | --all | --blog NAME | --category CAT | --yes | --db PATH]"
metadata:
  tags:
    - RSS
    - Blogs
    - Feed-Reader
    - Monitoring
  homepage: "https://github.com/JulienTant/blogwatcher-cli"
---

# Blogwatcher

Track blog and RSS/Atom feed updates with the `blogwatcher-cli` tool.
Supports automatic feed discovery, HTML scraping fallback, OPML import, and
read/unread article management.

## Global rules

- **Auto-discovery.** RSS/Atom feeds are auto-discovered from blog homepages
  when no `--feed-url` is provided. Falls back to HTML scraping if RSS fails
  and `--scrape-selector` is configured.
- **Categories.** Categories from RSS/Atom feeds are stored and can be used
  to filter articles (`--category`).
- **Database.** Stored at `~/.blogwatcher-cli/blogwatcher-cli.db` by default
  (override with `--db` or `BLOGWATCHER_DB`).
- **OPML import.** Bulk-import blogs from OPML files exported by Feedly,
  Inoreader, NewsBlur, etc.

## Routing

| Step | Reference / Command | Purpose |
| ---- | ------------------- | ------- |
| Install | Go: `go install github.com/JulienTant/blogwatcher-cli/cmd/blogwatcher-cli@latest` · Docker: `docker run --rm -v blogwatcher-cli:/data ghcr.io/julientant/blogwatcher-cli` · Binary: `curl -sL https://github.com/JulienTant/blogwatcher-cli/releases/latest/download/blogwatcher-cli_<os>_<arch>.tar.gz \| tar xz -C /usr/local/bin blogwatcher-cli` | All releases: https://github.com/JulienTant/blogwatcher-cli/releases |
| Docker persistence | `docker run --rm -v blogwatcher-cli:/data -e BLOGWATCHER_DB=/data/blogwatcher-cli.db ghcr.io/julientant/blogwatcher-cli scan` (named volume) or host bind mount | Database lives at `/data/blogwatcher-cli.db` inside the container without this. |
| Migrate from old `blogwatcher` | `mv ~/.blogwatcher/blogwatcher.db ~/.blogwatcher-cli/blogwatcher-cli.db` | Binary name changed from `blogwatcher` to `blogwatcher-cli`. |
| Add blog | `blogwatcher-cli add "My Blog" https://example.com` (optional `--feed-url`, `--scrape-selector`) | Track a new blog. |
| List / remove | `blogwatcher-cli blogs` · `blogwatcher-cli remove "My Blog" --yes` | Manage tracked blogs. |
| Import OPML | `blogwatcher-cli import subscriptions.opml` | Bulk import. |
| Scan | `blogwatcher-cli scan` (all) · `blogwatcher-cli scan "My Blog"` (one) | Fetch new articles. |
| List articles | `blogwatcher-cli articles` (unread) · `--all` · `--blog "Name"` · `--category "Engineering"` | Filter by blog or category. |
| Mark read | `blogwatcher-cli read 1` · `blogwatcher-cli read-all` · `blogwatcher-cli read-all --blog "My Blog" --yes` | Manage read state. |
| Mark unread | `blogwatcher-cli unread 1` | Reopen an article. |
| Env vars | `BLOGWATCHER_DB`, `BLOGWATCHER_WORKERS` (default 8), `BLOGWATCHER_SILENT`, `BLOGWATCHER_YES`, `BLOGWATCHER_CATEGORY` | All flags can be set via environment variables with the `BLOGWATCHER_` prefix. |
| Discover all flags | `blogwatcher-cli <command> --help` | Per-command flag reference. |
