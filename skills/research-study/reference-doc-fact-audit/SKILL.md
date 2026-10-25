---
name: reference-doc-fact-audit
description: Audit a study reference doc for factual errors, then fix.
version: "1.0"
author: hermes-agent
license: MIT
metadata:
  tags:
    - Research
    - Fact-check
    - Math
    - Documentation
    - Study
  related_skills:
    - study-roadmap-builder
    - grounded-citations
    - no-mistakes
---

# Reference Doc Fact Audit

## When to Use

Use when the user asks you to audit, fact-check, verify, or fix a study or technical
reference document the agent or a model wrote earlier. The user asks in skeptical terms
("make sure all this is fact, no hallucination, no assumption"). Assume the document
contains errors until each claim has been recomputed.

## Read the whole file before editing

`read_file` truncates long files and returns a dedup no-op on a second read, so
paginating it can silently hide the sections you still need. Read the full file in one
call instead:

```python
with open("/abs/path/DOC.md") as f:
    lines = f.readlines()
for i, line in enumerate(lines, start=1):
    print(f"{i}| {line.rstrip()}")
```

Slice the range to print chunks. Numbered lines make the fix targets unambiguous.

## Verify every numeric claim by execution

Never eyeball arithmetic and never carry a number forward from memory. Recompute every
worked example and every exercise answer in code, and print one labeled result line per
claim so the whole verification table lands in a single tool call. Use
`fractions.Fraction` for exact values and `math.sqrt` only for irrational comparisons.

```python
import math
from fractions import Fraction as F

a, b = (1, 2, 3), (4, -1, 2)
dot = sum(x * y for x, y in zip(a, b))          # 8
proj = F(dot, sum(y * y for y in b))             # 8/21, exact
results.append(f"proj_a onto b = {proj} b = {[proj * y for y in b]}")
```

Cover each section's worked example, each exercise, each stated identity, and every
numeric total the prose asserts (axiom counts, dimensions, list lengths, basis sizes).

## Dedupe findings and confirm each before reporting

A single wrong passage can surface twice, and a reported finding can be a false positive.
Before writing the report:

- Map each finding to the exact line range, then merge findings that share a range.
- For a suspected broken link, check whether it is a real markdown link (`[text](path)`)
  or a backticked plain-text filename mention. A backticked mention is not a link and
  needs no fix.
- For a sign or scalar difference, check whether it is a scalar multiple of the correct
  answer. `span{(2,-1)}` and `span{(-2,1)}` are the same subspace; a sign flip is not an
  error worth reporting.

State the corrected value in the report. "Wrong" without the correct value is not
actionable, and the user will have to redo your work.

## Fixing a wrong exercise

When an exercise is unsatisfiable as written, replace it with one that is true and has a
checkable answer. Do not silently change numbers inside the exercise and hope the claim
now holds; recompute the replacement before saving it. Preserve the section's original
skill: an orthogonality exercise stays an orthogonality exercise.

When the error is a count or an incomplete list (missing axioms, missing terms), add the
missing entries AND correct the number the prose states. A list of eight labelled "ten" is
the same defect as the wrong count.

## Verify the fixes landed

Re-read the file after patching and assert both that each fix is present and that the
superseded wrong text is gone. A patch that adds correct text without removing the wrong
text leaves the document contradicting itself.

```python
checks = {
    "dual basis corrected": "e₁* = (1/2, 1/2)" in content,
    "wrong values gone": "e₁*(1, 0) = 1, e₁*(0, 1) = 1" not in content,
}
```

## Pitfalls

- **Trust the document's own worked arithmetic over your memory.** LLM-written reference
  docs carry errors precisely where they assert a confident numeric result. Recompute even
  the claims that look trivially right, especially a "Show these are orthogonal" exercise.
- **Keep numeric literals in plain tuples, never inside f-strings.** Mixing a tuple and a
  list in arithmetic raises `TypeError`; an unbalanced brace in math notation like
  `{(-2,1)}` inside an f-string raises `SyntaxError` at parse time. Interpolate module-level
  tuples; do not write the math in the format string.
- **Batch all verification into one `execute_code` call.** One call per section burns
  turns and loses the comparison table. Accumulate labeled strings, print them joined.
- **Do not report a plan to fix as a fix.** Apply the patches, then report what landed.
- **Count the real edits in the summary.** If some findings were false positives or
  duplicate one edit, say so plainly rather than padding the change list.

## Depth

`references/common-math-errors.md` lists the specific traps LLM-written math reference
docs fall into, with the verified correct form for each. Read it when auditing a document
covering vector spaces, linear maps, or inner product spaces.