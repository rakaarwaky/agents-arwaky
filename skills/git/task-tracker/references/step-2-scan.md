# Step 2 — spawn one scanner subagent per feature

**Default path: run the deterministic scanner script** (no LLM subagent; one
host call per run, matching the workflow's script path):

```bash
python3 <this-skill>/scripts/scan.py --repo-root <repo-root> --discovery <discovery.json>
```

`<discovery.json>` is the Step-1 discovery output written to a temp file. The
script parses every in-scope doc's State Definitions table, row tables,
Next Action / Item cells (cell value only — prose outside the table is out
of scope), FR-id sets, and roll-up rows into one ScanOutput JSON. It also
parses the aes-docs entry shape: `### FR/DS/DT/PR-...` headings with their
`| Aspect | Detail |` tables under `## Backlog Status` (task rows keyed by
the entry's `State` / `Updated` rows; no `next_action` key — the shape has
no such column) and under `## Roadmap Status` (PR entries → roll-up claims,
feature resolved from the `Backlog` link). A
non-zero exit is a hard stop: fix the scanner and re-run; the workflow does
**not** fall back to an LLM scanner.

**`--legacy` path (rollback escape):** one read-only scanner subagent per
feature plus one for `root`. A feature scanner owns its feature's whole doc
set plus the roadmap roll-up row for that feature; it must not read other
features' docs. Splitting by feature keeps every FR ID and its backlog
equivalent in one agent's context, which is what makes the orphan check
possible. The scanner prompt (verbatim cell-value constraint for the Next
Action cell) and output shape are the legacy form:

```text
You are a read-only scanner for the feature "<feature>" in <repo-root>.
Read each of these files in full: <abs paths>.
1. Extract each file's State Definitions table; list the state names it defines. If a
   file has none, note that and continue — rows still count.
2. Extract every table row whose headers include ID (or Feature / Branch) and State.
   Also capture the doc-level "State: <value>" line at the top of a feature backlog.
3. Extract the FR ID set this feature owns: every FR-<SCOPE>-NNN declared in its FRD,
   and every FRD Ref cell in its backlog rows.
4. If the roadmap has a Feature Roll-up table, extract this feature's roll-up row
   verbatim (all cells, including State, Health, Next, Updated).
5. For each task row output one JSON object:
   {"id":"<row id>","title":"<item text>","state":"<verbatim state>","priority":"<P0/P1/P2 or —>","health":"<health or —>","fr_refs":["<FR-…>"],"source_doc":"<repo-relative doc path>","row_text":"<verbatim row text>"}
   State must appear in the source row verbatim. Do not infer, fill in, or normalize
   state values. A row without a state column value is {"id":...,"state":"unknown"}.
6. Also output the FR set:
   {"fr_declared":["FR-…"],"fr_referenced":["FR-…"],"rollup_row":"<verbatim row or null>"}
7. Return {"rows":[…],"fr":{…}}. An empty rows array is valid only after reading every
   file in full.
```

Wait on all handles. Collect rows; dedupe on `(id, source_doc)`.
