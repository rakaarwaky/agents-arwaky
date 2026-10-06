---
name: report-linter-false-positive
description: "Linter false positive: file an issue, never patch the tool."
metadata:
  tags:
    - lint
    - false-positive
    - github
    - issue
    - bug-report
    - aes
    - architecture
  related_skills:
    - aes-lint-arwaky
    - aes-agent
---

# report-linter-false-positive

> **Purpose**: When a lint/scan finding is a tool false-positive, prove the repo code is
> already correct, then report the defect upstream. Never bend the linter to satisfy a
> wrong heuristic.
>
> **Audience**: Agents running an architecture or language gate that flags code which is
> actually already correct.
>
> **Standing user rule**: linter bugs are reported by a GitHub issue on the linter repo,
> not fixed inline. Editing the checker to clear a finding ships a workaround as if it
> were the fix and hides the real defect.

## When this applies

The gate reports a violation, but the flagged source is already correct - the checker's
heuristic is the thing that's wrong. Confirming the class: the repo code satisfies the
intended rule, so no repo-side edit can legitimately make the finding disappear. If a real
repo edit clears it, that is a normal fix, not this workflow.

## Procedure

1. **Reproduce and read the source the checker flags.** Confirm the code genuinely meets
   the rule's intent. Capture the exact line(s) and the finding text.
2. **Trace the checker's heuristic.** Read the linter source for the rule that fired and
   find the specific defect: which annotation form, keyword, or count it fails to handle.
   Name the function/file. This is what makes the issue actionable.
3. **Rule out every repo-side clear.** If reformatting, renaming, or adjusting the flagged
   file could satisfy the checker, that is a legitimate repo fix - do that instead and skip
   this workflow. Only proceed when the repo code is already correct and the checker is the
   thing that is wrong.
4. **Revert any linter-source edit.** If you already modified the linter to make the scan
   pass, undo it. A shortcut in the checker is never the deliverable. `git checkout -- .`
   in the linter submodule, then re-confirm the scan still reports the finding on correct
   repo code.
5. **File the issue on the linter repo.** One issue per distinct defect. Body = summary,
   minimal repro (file + finding text), root cause (function + why it mis-handles the
   form), and a proposed fix. Do not paste the whole transcript - distill to the rule.
6. **Document the residual finding.** In the repo, note that the remaining scan violation
   is a known upstream linter bug, cite the issue, and leave the (already-correct) code as
   is. Re-scan; the only remaining findings are the documented upstream ones.

## Pitfalls

- **Do not patch the linter to clear the scan.** Modifying the checker source so the gate
  passes hides the bug and makes the workaround look like the real fix. Revert any such
  edit; the repo code stays correct, the linter stays upstream-owned.
- **Confirm the repo code is actually correct first.** "The linter is wrong" is only true
  when the flagged code satisfies the rule's intent. If a repo edit clears it, that is a
  normal fix, not a false-positive to report.
- **One issue per distinct defect, not one mega-issue.** Separate checker bugs
  (e.g. a union-annotation mis-count vs. a whole-word scan vs. an under-count of split
  files) get separate issues so each has a single repro and a single root cause.
- **The issue must name the heuristic and the input form it mis-handles.** "False
  positive, fix it" is not actionable. Cite the checker function, the annotation/file
  shape it fails on, and a minimal repro.

## Verify

- [ ] Linter submodule is clean (`git status` in the linter repo shows no local edits).
- [ ] Repo source files are correct as written; no edits made to satisfy the checker.
- [ ] Each residual finding has a corresponding open issue on the linter repo.
- [ ] Re-scan: remaining violations equal exactly the documented upstream defects.
