# Competitor News Monitor — Event Category Patterns

**Goal:** apply the source hierarchy, dedup rules, and materiality scoring framework consistently.

## Source hierarchy

Primary sources outrank everything else. When two sources disagree, prefer the primary source with the later timestamp.

1. Official newsroom / blog / changelog (highest authority)
2. Regulatory filings, investor relations
3. Reputable trade and financial press
4. Status / security pages
5. Community / Reddit (weak signal, not confirmed)
6. Job postings (weakest, indicative only)

## Deduplication

Collapse syndicated stories, rewrites, URL variants, press release coverage, and revised filings into one event. Keep independently sourced corroboration attached to the event record.

## Materiality scoring

Score against the watch contract's threshold on six axes:

| Axis | Question |
| --- | --- |
| Directness | Is this about a watched company? |
| Source authority | Primary or secondary? |
| Novelty | New event or repeat? |
| Customer / market impact | Affects users, pricing, or market share? |
| Strategic relevance | Changes competitive position? |
| Confidence | Confirmed or reported / anonymous? |

Separate measured facts from interpretation. Hiring patterns and anonymous reports remain signals, not confirmed strategy.

## Completion

- Every event in the state file has a materiality score and a source hierarchy rank.
- Duplicates have been collapsed; corroboration is attached.
