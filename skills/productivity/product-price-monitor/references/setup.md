# Product Price Monitor — Setup

**Goal:** a watch contract with a live baseline observation exists and a cron job is scheduled for the tick.

## 1. Define the exact item

Record source URL/provider, product/listing ID where available, variant, quantity, location, dates, travelers/guests, membership/login assumptions, condition, seller, and acceptable substitutes. Done when two variants cannot be confused.

## 2. Define the alert condition

Specify currency, all-in vs pre-tax price, maximum price, availability/stock rule, shipping, refundability, cabin/room/ticket class, cooldown, and notification destination. Done when synthetic examples have deterministic alert decisions.

## 3. Establish a live baseline, then schedule

Fetch a bounded live result with `web_extract` or `browser_navigate` and record retrieval time, source price, fees/taxes, availability, and terms. Do not schedule until one foreground fetch works. Write the watch contract (item, condition, baseline observation) to a state file under `~/.hermes/price-watches/<watch-slug>.json`, then create the job:

```text
cronjob(action="create",
        schedule="every 6h",
        prompt="Load the product-price-monitor skill and run the tick for the watch contract at ~/.hermes/price-watches/<watch-slug>.json.",
        deliver=<user's destination>)
```

Pick a cadence that respects rate limits and site terms. Done when the baseline matches the exact item contract and the job exists.

## Completion

- The watch contract file exists at `~/.hermes/price-watches/<watch-slug>.json` with all fields filled.
- At least one foreground fetch succeeded before the cron job was created.
- The alert condition is deterministic: given the baseline and a synthetic price, the alert decision is unambiguous.
