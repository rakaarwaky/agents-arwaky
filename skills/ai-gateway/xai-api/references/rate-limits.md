# Rate Limits & Tiers

> Source: https://docs.x.ai/developers/rate-limits.md

Every team has per-model RPS + TPM limits. RPS is derived from RPM/60 — a full
minute's request budget cannot be spent in one second. 429 on breach.

## Tiers (cumulative spend since 2026-01-01; never downgrade)

| Tier | Spend threshold |
|---|---|
| 0 | $0 (default) |
| 1 | $50 |
| 2 | $250 |
| 3 | $1,000 |
| 4 | $5,000 |
| Enterprise | on request |

Check your team's live limits: https://console.x.ai/team/default/models

## Per-model RPS / TPM

| Model | RPS | TPM |
|---|---|---|
| grok-4.6 / grok-4.5 | T0: 150 → T4: 500 | T0: 50M → T4: 100M |
| grok-4.3 / grok-4.20-0309-* / grok-build-0.1 | T0: 37 → T4: 208 | T0: 10M → T4: 85M |
| grok-4.20-multi-agent-0309 | T0: 9 → T4: 56 | T0: 2.5M → T4: 21M |
| grok-imagine-image-* | T0: 6 → T4: 100 | — |
| grok-imagine-video* | T0: 10 → T4: 158 | — |

Voice/audio: limited by RPS + concurrent sessions (CST) instead of TPM.
- `grok-voice-think-fast-2.0`: CST T0:10 → T4:200.
- TTS: RPS T0:50 → T4:500, CST T0:100 → T4:500.
- STT: RPS T0:10 → T4:40, CST T0:100 → T4:500.

All token types count toward TPM: prompt, completion, reasoning, cached prompt, image,
audio, and tool-returned tokens.

## Practical 429 handling

- Exponential backoff on `429`; honour the `Retry-After` header when present.
- Batch jobs: use the Batch API (50% cheaper, off-peak) — `references` pricing page
  lists supported models; not every model accepts batch requests.
- Priority processing and prompt caching are separate guides under
  `/developers/advanced-api-usage/`.
- Regional endpoints: some teams get geo-pinned endpoints — see
  `/developers/advanced-api-usage/regions.md`.
- mTLS auth: available for enterprise — `/developers/advanced-api-usage/mtls.md`.

## Cost tracking

`/developers/cost-tracking.md` — per-key/per-model spend rollups via the
Management API (`/v1/management/billing`).
