# Safety model (single home)

The pack states its safety model once, here, and every mutating command
applies it identically:

| | Read (`list/show/discover/validate/weed`) | Reversible write (`repair`, `new-category`, `move`, catalog rebuild) | Destructive-ish (`archive`, `merge`, `delete`) |
|---|---|---|---|
| **Default** | runs immediately | **`--dry-run` first**; apply with `--apply` | **`--dry-run` + approval gate** |
| **Agent mode** | any | Auto-Pilot | Ask first |
| **Undo** | n/a | `git checkout` of touched files | `git` snapshot before run (`skill-lifecycle` step 6, kept) + `_archive/` |
| **Delete** | never | never | **never the default**; `_archive/` first, delete only with explicit `--hard-delete` |

`skill-lifecycle`'s git-snapshot step is preserved (it is the only real
undo for a merge), and merged into the shared model so `skill-library
archive` gets it too.

This table replaces the three earlier copies (`skill-librarian` Auto-Pilot
at `SKILL.md:84`, `skill-lifecycle` approval gate at `SKILL.md:96-104`,
`skill-authoring` interactive) — bodies link here rather than restating it.