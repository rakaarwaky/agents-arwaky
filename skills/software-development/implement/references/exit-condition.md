# Exit Condition


The **only** exit condition is **all reviewers** reporting **0 issues** of any severity in the same round. There is no iteration cap. Every issue — including nits, suggestions, and minor improvements — must be addressed before the loop terminates.

There is no per-reviewer exit — if the security reviewer has 0 issues but the general reviewer has 2, the implementer fixes those 2 and all reviewers re-review in the next round.
