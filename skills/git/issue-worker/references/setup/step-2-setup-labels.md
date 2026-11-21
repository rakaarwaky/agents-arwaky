# Setup step 2 — Setup Standard Issue Labels (setup lane)

Ensure the standard labels required for issue tracking, triage, and resolution exist on the repository.

## Required label set

| Label | Color | Description |
|---|---|---|
| `triage` | `#FBCA04` | Unverified or freshly opened issue awaiting inspection |
| `in-progress` | `#1D76DB` | Issue actively being investigated or worked on by an agent |
| `fixed-on-main` | `#0E8A16` | Issue confirmed already fixed at HEAD on default branch |
| `spec-issue` | `#5319E7` | Task mapped from architectural specification documents |
| `wontfix` | `#FFFFFF` | Working as intended or decided not to address |

## Step 2.1 — Create missing labels

For each required label that does not exist in the repository, create it:

```bash
gh label create "<label>" \
  --repo <owner/repo> \
  --color "<color>" \
  --description "<description>" \
  --force
```

Using `--force` ensures existing labels with matching names update cleanly without erroring.

## Step 2.2 — Verify label creation

Confirm the label set is available:

```bash
gh label list --repo <owner/repo> --search "triage"
gh label list --repo <owner/repo> --search "in-progress"
```

## Next

Proceed to [step-3-automation.md](step-3-automation.md) to register the repository in Orca's event automation.
