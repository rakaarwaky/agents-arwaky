---
name: product-price-monitor
description: "Watch product, flight, or listing prices; alert on target. Use when tracking a product/listing/flight/hotel price, setting a price or availability alert, handling currency and all-in totals across variants, or running the scheduled price-watch tick."
when-to-use: "Use when the user wants an alert when a price drops below a target, wants to watch flights, hotel rooms, tickets, or listings for a fare or availability condition, track inventory or booking windows, or when a cron tick fires for an existing price watch. Not for one-off price lookups (use web_search/web_extract)."
argument-hint: "[create | tick] <item-or-slug> [watch-slug] [--cooldown <duration>]"
version: 0.1.0
author: Ben Barclay (benbarclay), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Prices, Availability, Shopping, Travel, Alerts]
    related_skills: [maps]
---

# Product Price Monitor

Monitor a concrete purchasable item and alert on a normalized all-in price or availability condition. Handle variants, taxes, fees, currencies, stock, cancellation terms, and duplicate alerts explicitly. Setup runs once in the foreground; the recurring check runs as a `cronjob` tick (the `price-watch` automation blueprint scaffolds this).

## Global rules

- **Never overwrite last-known-good state with an error page.** A failed fetch means unknown state: record the failure, keep the previous observation.
- **The alert threshold is all-in unless the watch contract says otherwise.** Base fare ≠ all-in price; always separate and sum base, fees, shipping, taxes.
- **Deduplicate alerts by fingerprint.** Replaying the same offer must send no second alert; respect the cooldown in the watch contract.
- **The watch contract is the single source of truth.** Every alert decision must replay deterministically from `~/.hermes/price-watches/<watch-slug>.json`.
- **Silence is valid.** When no condition is met, stay silent unless a periodic all-clear was requested.

## Routing

| Step | Reference | Purpose |
| --- | --------- | ------- |
| Setup: define item, alert condition, baseline, schedule | [`references/setup.md`](references/setup.md) | Watch contract fields, baseline fetch, cron job creation. |
| Tick: fetch, normalize, compare, deliver | [`references/tick.md`](references/tick.md) | The three tick steps, pitfalls, and verification checklist. |
| Price normalization and item type specifics | [`references/pricing-models.md`](references/pricing-models.md) | All-in price components, currency handling, per-item-type pinning rules. |
