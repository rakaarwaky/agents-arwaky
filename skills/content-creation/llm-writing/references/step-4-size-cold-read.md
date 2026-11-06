# LLM Writing —  Size



| Tier   | Size limit   | Notes                             |
| ------ | ------------ | --------------------------------- |
| Small  | ≤ 300 words  | Single task, no sub-docs          |
| Medium | ≤ 1500 words | Multi-step workflow, ≤ 3 sub-docs |
| Large  | ≤ 3000 words | split further if exceeded         |

`Size before/after` is measured with `wc -w` on the target file and reported in the Output Contract for `improve` runs