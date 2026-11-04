# Product Price Monitor — Pricing Models

**Goal:** apply the correct price normalization and currency handling for each item type.

## Price normalization

The alert threshold is always all-in unless the watch contract explicitly says otherwise. Separate and track:

| Component | Notes |
| --- | --- |
| Base price | Pre-tax, pre-fee |
| Mandatory fees | Processing, service, booking fees |
| Shipping | Free above threshold or per-item |
| Taxes | VAT/GST, sales tax by region |
| Total (all-in) | The value compared against the threshold |

## Currency handling

- Convert to the watch contract's currency only with a timestamped FX rate.
- Retain the source currency alongside the converted value in the state file.
- A currency fluctuation alone is not an alert unless it crosses the threshold.

## Item type specifics

| Item type | Key fields to pin |
| --- | --- |
| Product | Variant, quantity, seller, condition, acceptable substitutes |
| Flight | Cabin class, dates, refundability, layovers |
| Hotel | Room type, dates, cancellation terms, breakfast inclusion |
| Ticket | Event date/venue, seat tier, transferability |
| Listing | Location, seller, view count threshold |

## Completion

- The state file stores the all-in price, source currency, and FX timestamp for every observation.
- Two variants of the same item cannot produce the same state file record.
