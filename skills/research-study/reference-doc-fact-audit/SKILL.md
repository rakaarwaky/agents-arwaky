---
name: reference-doc-fact-audit
description: Audit a study reference doc for factual errors, then fix.
when-to-use: Use when the user asks to audit, fact-check, verify, or fix a study or technical reference document the agent or a model wrote earlier.
argument-hint: "<audit | fix> <doc-path>"
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
---

# Reference Doc Fact Audit

Audit a study or technical reference document for factual errors, then fix
them. Assume the document contains errors until each claim has been
recomputed. The user asks in skeptical terms ("make sure all this is fact,
no hallucination, no assumption") — recompute, don't trust.

## Global rules

- **Read the whole file before editing.** `read_file` truncates long files
  and returns a dedup no-op on a second read, so paginating can silently hide
  sections you still need. Read the full file in one call:

  ```python
  with open("/abs/path/DOC.md") as f:
      lines = f.readlines()
  for i, line in enumerate(lines, start=1):
      print(f"{i}| {line.rstrip()}")
  ```

  Slice the range to print chunks. Numbered lines make fix targets
  unambiguous.
- **Recompute every numeric claim by execution.** Never eyeball arithmetic
  and never carry a number forward from memory. Use `fractions.Fraction`
  for exact values and `math.sqrt` only for irrational comparisons. Print
  one labeled result line per claim so the whole verification table lands in
  a single tool call. Cover each section's worked example, each exercise,
  each stated identity, and every numeric total the prose asserts (axiom
  counts, dimensions, list lengths, basis sizes).
- **Dedupe findings and confirm each before reporting.** Map each finding
  to the exact line range, then merge findings that share a range. A
  suspected broken link: check whether it is a real markdown link
  (`[text](path)`) or a backticked plain-text filename mention — a backticked
  mention is not a link and needs no fix. A sign or scalar difference: check
  whether it is a scalar multiple of the correct answer
  (`span{(2,-1)}` and `span{(-2,1)}` are the same subspace; a sign flip is
  not an error worth reporting). State the corrected value in the report —
  "wrong" without the correct value is not actionable.
- **Fixing a wrong exercise.** When an exercise is unsatisfiable as
  written, replace it with one that is true and has a checkable answer. Do
  not silently change numbers and hope the claim now holds; recompute the
  replacement before saving. Preserve the section's original skill. When the
  error is a count or an incomplete list, add the missing entries AND correct
  the number the prose states.
- **Verify the fixes landed.** Re-read the file after patching and assert
  both that each fix is present and that the superseded wrong text is gone.
  A patch that adds correct text without removing the wrong text leaves the
  document contradicting itself.

## Routing

| Step | Reference | Purpose |
| ---- | --------- | ------- |
| Read whole file | The Python snippet in Global rules (one `execute_code` call, numbered lines) | Get every section into view before editing. |
| Verify numeric claims | `execute_code` call — recompute every worked example and exercise answer; accumulate labeled strings, print them joined | One call, not one per section (burns turns and loses the comparison table). |
| Dedupe & confirm findings | Line-range mapping, markdown-link vs backtick check, scalar-multiple check | Reduce false positives before reporting. |
| Fix a wrong exercise | Replace with a true, checkable exercise; recompute before saving | Preserve the section's original skill; correct counts/lists too. |
| Verify fixes landed | Re-read + assert old wrong text is gone and new correct text is present | Catch self-contradictory documents. |
| Common math traps | [`references/common-math-errors.md`](references/common-math-errors.md) | Specific traps LLM-written math reference docs fall into, with the verified correct form for each. Read when auditing a document covering vector spaces, linear maps, or inner product spaces. |
| Pitfalls | Global rules (recompute, one-call verification, no f-string math, count real edits, report what landed not what was planned) | The discipline rules that keep the audit honest. |
