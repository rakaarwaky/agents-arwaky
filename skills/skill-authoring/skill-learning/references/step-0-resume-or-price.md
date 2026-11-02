# Step 0 — Resume or price

Run `aa skills trace-state get`. Exit code 3 means a run is pending — resume it instead of starting over.

Then run `aa skills trace-collect` for a one-line price per scope. The collector writes a manifest into a fresh run dir; the subsequent steps read from that run dir.