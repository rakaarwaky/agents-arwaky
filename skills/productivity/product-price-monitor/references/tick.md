# Product Price Monitor — Tick

**Goal:** an alert (or silence) is delivered and the state file is updated.

## 4. Fetch and normalize

Re-fetch the source. Convert currency only with a timestamped rate and retain the source currency. Separate base price, mandatory fees, shipping/taxes, total, and availability. Exclude volatile page metadata. A failed fetch means unknown state: report or skip, but never overwrite the last good observation with an error page. Done when the observation is comparable to the baseline or explicitly marked failed.

## 5. Compare and suppress duplicates

Alert on threshold entry, qualifying availability, material lower price, or recovery as requested. Store the last good observation and last alert fingerprint in the state file. Replaying the same offer must send no second alert; respect the cooldown. Done when the alert decision is deterministic against stored state.

## 6. Deliver or stay silent

When a condition is met, the alert includes: exact item/variant, observed all-in price and source currency, availability/terms, threshold, retrieval timestamp, source link, and important uncertainty. Never claim inventory is reserved. When nothing qualifies, stay silent — no "still watching" noise unless a periodic all-clear was requested. Done when the state file reflects this run.

## Pitfalls

- Comparing a base fare with an all-in threshold.
- Alerting on the wrong size, seller, cabin, dates, or room terms.
- Overwriting a last-known-good value with an error page.
- Polling aggressively enough to trigger blocking or violate site terms.
- Scheduling before a single foreground fetch has succeeded.

## Verification

- [ ] The watch contract pins the item so two variants cannot be confused.
- [ ] One foreground fetch succeeded before any job was created.
- [ ] Alert decisions replay deterministically from the state file; duplicates suppressed.
- [ ] Failed fetches never replaced last-known-good state.
- [ ] Alerts carry all-in price, source currency, timestamp, and source link.

## Completion

- The state file is updated with this run's observation.
- If an alert was sent, it carries all required fields and the source link.
- If no condition was met, silence (or all-clear) is the correct output.
