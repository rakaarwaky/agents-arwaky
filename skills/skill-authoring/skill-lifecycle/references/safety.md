# Safety model (single home)

The pack states its safety model once, here, and every mutating command
applies it identically:

| | Read (`list/show/discover/validate/weed`) | Reversible write (`repair`, `new-category`, `move`, catalog rebuild, category rename) | Destructive-ish (`archive`, `merge`, `delete`) |
|---|---|---|---|
| **Default** | runs immediately | **`--dry-run` first**; apply with `--apply` | **`--dry-run` + approval gate** |
| **Agent mode** | any | Auto-Pilot | Ask first |
| **Undo** | n/a | `git checkout` of touched files | `git` snapshot before run (`skill-lifecycle` step 6, kept) + `_archive/` |
| **Delete** | never | never | **never the default**; `_archive/` first, delete only with explicit `--hard-delete` |
| **Unattended** | any | Auto-Pilot | `--evolution`: apply without the approval gate, `--dry-run` fallback when no snapshot is possible |

`skill-lifecycle`'s git-snapshot step is preserved (it is the only real
undo for a merge), and merged into the shared model so `skill-library
archive` gets it too.

The `--evolution` row covers scheduled or headless runs (a cron job, `/loop`,
a background task): destructive work is applied without an interactive
approval gate only when the git snapshot exists first; when no snapshot is
possible the run must fall back to `--dry-run` and report instead of
applying.

This table replaces the three earlier copies (`skill-librarian` Auto-Pilot
at `SKILL.md:84`, `skill-lifecycle` approval gate at `SKILL.md:96-104`,
`skill-design` interactive) — bodies link here rather than restating it.

**Category renames** are reversible writes (undo with `mv` back), but the
cross-reference update step is mandatory: after `mv skills/<old> skills/<new>`,
grep the skills tree for the old path and fix all broken references before
rebuilding the catalog. Skipping this step leaves silent dangling paths in
other skills' bodies and script invocations.