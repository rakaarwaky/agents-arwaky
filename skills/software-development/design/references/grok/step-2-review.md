# Step 2: Review

Spawn the reviewer subagent to produce structured findings.

## Spawn

`spawn_subagent` parameters (Global Rules in SKILL.md apply):

- `description`: `"[reviewer] Review design doc"`
- Prompt body: `reviewer_persona_instructions` prepended, then:

```text
Review: <design_doc_file>
Summary: <summary_file>
Output: <review_file>

Read both files. Do not modify them. Write structured notes to Output.
Each issue needs: Severity, Section, Description, Suggestion, Status: open.

Evaluate:
- PR Plan: realistic, ordered, independently mergeable.
- Key Decisions: well-reasoned.
- Detail: enough for implementation.
```

## After Completion

Continue to Step 3.

## Host-claim pre-verification (orchestrator duty, not subagent duty)

Before dispatching the reviewer, the orchestrator should run a quick live probe of any external-system claim in the doc that is load-bearing (e.g. "the Flatpak binary is launchable from a host process", "this file path exists on this machine", "this CLI flag is supported by the installed browser version`). This is not the reviewer's job — the reviewer verifies internal code claims; the orchestrator verifies host-environment claims by actually running the command:

```bash
# example: probe a Flatpak-managed binary path before it lands in the design
ls -la /var/lib/flatpak/app/<app-id>/x86_64/stable/active/files/<binary> 2>/dev/null
# or: launch-test a binary via the target framework's minimal call
timeout 30 python3 -c "<minimal framework call with the candidate binary>" 2>&1 | head -5
```

Record the result (success/failure + actual path or flag) and pass it as a **ground-truth fact** in the writer/reviewer prompts, labelled "verified on this host — treat as fact, do not re-verify". This prevents the writer from encoding an unverified host assumption into the design doc and the reviewer from flagging it as "open question" when it is already resolved.

Do NOT probe claims that are clearly documentation-level (e.g. "the library version supports X"); only probe claims where the answer changes which code path the PR plan will take.