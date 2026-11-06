# LLM Writing — Step 5: Size Tiers and Cold-Read Test

Phase: W6. Gating runs after drafting.


| Tier | Size limit | Notes |
|------|-----------|-------|
| Small | ≤ 500 words | Single task, no sub-docs |
| Medium | ≤ 1500 words | Multi-step workflow, ≤ 3 sub-docs |
| Large | ≤ 3000 words | System or library doc; split further if exceeded |

`Size before/after` is measured with `wc -w` on the target file and reported in the Output Contract for `improve` runs.


A subagent receives only the delivered text and the stated task, with no access to the source material. Pass = zero questions or assumptions. Cap at 2 rewrites; if still failing after 2, mark `UNVERIFIED`. No subagent tool available → `UNVERIFIED`.
