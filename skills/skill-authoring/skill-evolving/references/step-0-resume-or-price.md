# Step 0 — Resume or price

Run `aa skills trace-state get`. Exit code 3 means a run is pending — resume it instead of starting over.

Then run `aa skills trace-collect` for a one-line price per scope. The collector uses the hardcoded defaults from `taxonomy_skills_constant.py`:

- `since_last=True` — sessions since the last completed trace run
- `min_turns=3` — drop signals seen in fewer than 3 sessions
- `limit=0` — unlimited, keep all matching sessions
- `json=True` — emit JSON

This is step 0 because every subsequent step depends on the run dir and manifest it produces.
