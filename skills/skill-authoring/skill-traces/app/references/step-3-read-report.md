# Step 3: Read report

Open `report.md`. Present the Overview plus the sections the chosen modes own — when
all three are on, that is sections 1-4 in one pass. The report comes first on its
own; curation questions belong to the next turn.

**Report shape** — what to present, in order:

- **Overview** — Problem (2–4 sentences: what the traces show the user repeating,
  correcting, or never using), Proposed change (the smallest set of skill edits that
  removes that repetition), Actions count (`<N> total — <a> new skills, <b> skill
  updates, <c> retirements, <d> need a decision`).

- **Section 1** — one row per repeated phrase: `| # | Phrase (quoted) | Sessions | Owner | Action |`.
  `--learn` owns the rows that carry a `create` action.

- **Section 2** — one row per stale-line claim:
  `| # | Skill (path) | Stale line (quoted) | Evidence (session ids) | Replacement | Action |`.
  `--evolve` owns the rows that carry an `edit` or `propose` action.

- **Section 3** — one row per unused skill:
  `| # | Skill (name, path) | Sessions loaded | Last used | Why safe | Action |`.
  `--unlearn` owns the rows that carry a `delete`, `ask`, or `group` action. When
  `manifest.json` -> `sessions_kept` is under 20 or the `params.days` window is
  under 7 days, this section is titled `## 3. Not seen in this window` and lists
  zero-use skills as information only; no retirement action is emitted.

- **Section 4** — recurring needs with no owner; no action ids; these are for the
  user to decide. `--learn` presents them.

**Unverified claims** (present only when a verifier section failed) and **Dropped
claims** (bullet list: claim, reason, which verifier) are shown but not acted on
unless the user asks; any action emitted for them carries `requires_confirmation:
true`.

A mode with no matching row in its section ends with `nothing to apply` and no
decision record; it does not block the other modes.

## Report and actions shapes

Skills-only. Two files in the run directory. `report.md` is for the user.
`actions.json` is for the apply step. Every action in `actions.json` must appear in
`report.md`, and every claim in sections 1–3 of `report.md` must be backed by a
verifier's Kept list.

### report.md

Write short sentences with one meaning each. No hedged summaries: a count is a
number, a path is a path.

```markdown
# Trace-learning report — <today>

## Overview
Problem: <2–4 sentences: what the traces show the user repeating, correcting, or never using>
Proposed change: <2–4 sentences: the smallest set of skill edits that removes that repetition>
Actions: <N> total — <a> new skills, <b> skill updates, <c> retirements, <d> need a decision

## 1. Repeated phrases -> skills
| # | Phrase (quoted) | Sessions | Owner | Action |
Owner is an existing skill (name, path) or NEW <name>. Action is the action id from actions.json.

## 2. Skills to update
| # | Skill (path) | Stale line (quoted) | Evidence (session ids) | Replacement | Action |

## 3. Unused -> delete or retire
| # | Skill (name, path) | Sessions loaded | Last used | Why safe | Action |
"Why safe" names what still does the job, or says `only copy — ask`, or
`referenced by <names> — ask`. A grouped action is one row that names the group
and lists its members in the Name cell.

## 4. Gaps
Recurring needs with no owner. No action ids; these are for the user to decide.

## Unverified claims
Only present when a verifier section failed: the claims from that section, listed
but not acted on unless the user asks; any action emitted for them carries
`requires_confirmation: true`.

## Dropped claims
Bullet list: claim, reason it was dropped (which verifier, what failed). Include
"previously rejected by the user" items here.

## Coverage
- sessions seen / kept / dropped by reason (from manifest.json)
- usage source: `usage.json` (per-skill `count`, `in_slash_mru`, `unused_loaded`,
  session ids) written by `stc traces materialize`; phrase source:
  `phrases.json` (`exact_prompts`, `prompt_stems_12_words`,
  `repeated_instruction_lines`)
- human turns read; sessions read by mappers vs total
- map or reduce slots lost; verifier sections that failed
- window and filters used (params from manifest.json)
- what this run could not see: headless sessions unless included, subagent
  sessions unless included, anything outside this machine's GROK_HOME
```

### actions.json

```json
{
  "run_dir": "<run_dir>",
  "generated_at": "<today>",
  "actions": [
    {
      "id": "A1",
      "kind": "skill",
      "action": "create | edit | delete | propose | ask | group",
      "target": "<name>",
      "path": "<absolute path of the SKILL.md the action touches>",
      "protected": "bundled | git-tracked | null",
      "referenced_by": ["<loaded skill names that mention this skill>"],
      "reversible": true,
      "requires_confirmation": false,
      "evidence": {
        "sessions": ["<session id>", "..."],
        "count": 0,
        "quote": "<exact phrase or stale line, at most 300 chars>"
      },
      "reason": "<one sentence>",
      "edit": {
        "anchor": "<exact substring of the current file, or \"\" for create>",
        "replacement": "<full replacement text, or full file content for create>",
        "mode": "replace | insert_after | append"
      }
    }
  ]
}
```

Field rules:

- `id` is `A1`, `A2`, … in report order.
- `kind` is always `skill` in this pipeline.
- `path` is exact: the SKILL.md file for the skill the action touches, or the skill
  directory for `delete`.
- `protected` is `bundled` for skills under `~/.grok/bundled/`, `git-tracked` for
  skills under a git repo, and null otherwise. A protected skill is never edited or
  deleted in place: the action is `propose`, with `requires_confirmation: true` and
  a `reason` that says where the fix belongs — a user-skill override with the same
  name for bundled, a pull request for git-tracked. `propose` carries an `edit`
  block so the apply step can write the override or the patch.
- `referenced_by` is derived from the loaded skill records; the run dir holds no
  `surfaces.json`. A `delete` whose `referenced_by` is non-empty is emitted as
  `ask`, and `reason` names the referrers.
- `requires_confirmation` is `true` for `ask`, `propose`, any `delete` of the only
  copy of a job, and any unverified claim.
- **Narrow windows prove nothing.** `manifest.json` -> `sessions_kept` under 20 or
  `params.days` under 7 means the run cannot show disuse. In that case section 3 is
  titled `## 3. Not seen in this window`, lists the zero-use skills as information
  only, emits no `delete`, `disable`, `ask`, or `group` action for them, and the
  Overview's retirements count is 0 with the reason quoted ("only N sessions kept,
  M-day window"). A skill unused in a few sessions from one folder may be the
  user's most-used skill elsewhere.
- **Grouping.** Unused skills that share a disposition (for example "12 zero-use
  bundled skills -> propose overrides" or "9 zero-use user skills -> ask") are one
  action with `kind: group`, `action` set to the shared disposition, `target` a
  short label, and an `items` array of `{name, path, protected, referenced_by,
  count, last_used}`. One decision is worth one row; 40 rows that each say "ask"
  are not 40 decisions. Never group across dispositions and never group anything
  with evidence of use (`count > 0`). A referenced zero-use skill is never a
  `delete`; its disposition is `ask`, so it joins the `ask` group with
  `referenced_by` filled in its item. The Overview's action count counts a group
  as one.
- `edit` is required for `create`, `edit`, and `propose`; omit it for `delete`,
  `ask`, and `group`.
- `create` writes `<user skills dir>/<name>/SKILL.md`. The `replacement` is the
  whole file: `---` frontmatter with `name` (matching the directory),
  `description` (what it does plus the trigger phrases observed in the traces),
  `user-invocable: true`, `origin: learn` (provenance the client reports as
  `skill_origin`; never omit it, never another value), then a body of imperative
  steps. Use the quoted phrases as the trigger list and the body.
