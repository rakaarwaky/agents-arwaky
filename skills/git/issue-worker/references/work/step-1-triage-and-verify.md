# Step 1: Triage & Verify at HEAD

Perform zero-trust verification of all staged issues against the current repository state at HEAD. Close issues already fixed on main, identify duplicates, and resolve non-code ambiguities via a single interactive decision quiz.

## 1a: Zero-Trust Codebase Verification

Never trust issue labels, issue comments, audit dates, or a PR body's `Closes #N` statement alone. GitHub frequently fails to close issues automatically, or fixes land in unrelated PRs. Always inspect the current codebase at HEAD.

For each staged issue:

1. **Inspect Cited Code at HEAD**:
   ```bash
   # Check if cited problematic pattern or bug still exists in the code
   rg -n '<problematic-symbol-or-pattern>' <path-from-issue>
   ```
2. **Check Recent Commit History**:
   ```bash
   # Check if a fix was committed after the issue was opened
   git log --oneline --since="<issue-created-at>" -- <path-from-issue>
   ```
3. **Check Merged PRs**:
   ```bash
   gh pr list --state merged --json number,title,body --jq ".[] | select(.body|test(\"Closes #$NUM|Fixes #$NUM|Resolves #$NUM\")) | {number, title}"
   ```

## 1b: Classify Issue State

Assign each issue one of three verdicts:

| Verdict | Condition | Action |
|---------|-----------|--------|
| `fixed-on-main` | The cited bad pattern is gone, the correct implementation is present, or tests pass at HEAD. | Close immediately with an evidence comment (see 1c). |
| `duplicate` | Identical root cause to an existing earlier open issue. | Close referencing the canonical issue number. |
| `still-broken` | Symptom reproduces at HEAD or the cited faulty pattern is actively present. | Formulate reproduction command and advance to Step 2. |
| `needs-decision` | Requires architectural trade-offs, scope choices, or user preference. | Add to the decision quiz in 1d. |
| `false-positive-incomplete-source` | The report's own "missing material" note lists files that exist at HEAD, and the claim depends on that absent material. | Re-verify against the real file; if the defect is not present, discard the claim. Report the discard reason as "reviewer worked from an incomplete upload". |

## 1a-bis: Detect reports generated against incomplete source

A review or audit report produced from a partial upload (missing modules, omitted helper files, no line numbers) yields two classes of claim. Separate them before acting:

1. **Read the report's own material/missing-material section first.** Any claim that hinges on an artifact the report lists as "not supplied" is suspect — the reviewer could not have verified it. Confirm the artifact exists at HEAD (`ls <path>`, `rg -n '<symbol>' <path>`) before trusting the claim.
2. **A claim that cites a symbol the real code already validates is stale.** Example: a report says "`run.workflow` is never type-checked" while `merge_run` raises `SpecError` on a non-string — the reviewer missed the helper. Grep the named symbol and read the real implementation before accepting the claim.
3. **A claim that two in-repo artifacts disagree is usually real even from a partial upload.** Contradictions visible within supplied material (FRD Business Logic vs FRD Test row, FRD vs a supplied capability file) do not require the missing files — trust these.

Report the triage split explicitly: which claims are real-and-present, which are real-but-stale (fixed after the upload), and which are false-positives caused by the incomplete source. This is the "is this valid?" answer — a verdict per claim, not a single yes/no.

## 1c: Close Verified-on-Main Issues

When an issue is confirmed fixed at HEAD, close it immediately with verified evidence:

```bash
gh issue close <NUM> --reason completed --comment "Verified fixed at HEAD: <file:line> confirms correct behavior. Evidence: \`<repro-command>\` passed with output: <summary>."
```

Do not proceed to spawn worktrees for `fixed-on-main` or `duplicate` issues.

## 1d: Interactive Decision Quiz

If any issue has ambiguous requirements, breaking change implications, or multiple valid solution approaches, collect all questions across all issues into **one** interactive quiz before implementation:

- Ask all questions together in a single interaction.
- Frame each question clearly with concrete choices.
- Put the recommended option first with `(Recommended)`.
- Record user choices directly as binding constraints for subsequent task briefs.

Skip this quiz if all remaining issues have fully determined, unambiguous fixes.

Proceed to Step 2 (`step-2-grouping-and-planning.md`).
