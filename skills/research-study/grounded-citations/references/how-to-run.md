# How to Run — Grounded Citations

Resolve the pack root (it is symlinked under `~/.hermes`, `~/.qwen` and
`~/.config/opencode`):

```bash
for R in "${HERMES_HOME:-$HOME/.hermes}/skills" "$HOME/.qwen/skills" \
         "$HOME/.config/opencode/skills" "$HOME/agents-arwaky/skills"; do
  [ -f "$R/research/grounded-citations/scripts/sources.py" ] && break
done
S=$R/research/grounded-citations/scripts/sources.py

python "$S" reset                                  # start a clean ledger
python "$S" add https://example.com/a --title "A"  # prints: [1]
python "$S" add https://example.com/b --title "B"  # prints: [2]
python "$S" list                                   # ledger table
python "$S" render                                 # Sources: block
python "$S" verify draft.md                        # catch bad citations
```

## Quick Reference

| Action | Command |
|---|---|
| Fresh ledger for a new task | `sources.py reset` |
| Register a source, get its id | `sources.py add <url> [--title T]` |
| Register several at once | `sources.py add <url1> <url2> ...` |
| Register from JSON tool output | `sources.py ingest results.json` |
| Attach verbatim evidence to a source | `sources.py quote <id> --text "exact wording" --from page.txt` |
| Show ledger | `sources.py list [--json]` |
| Render the Sources block | `sources.py render [--style markdown\|plain\|footnotes\|bibtex\|evidence] [--only 1,3]` |
| Render only what a draft cites | `sources.py render --cited-in draft.md` |
| Rewrite a draft's Sources block in place | `sources.py render --replace-in draft.md` |
| Check a draft's citations | `sources.py verify draft.md [--strict] [--min-coverage 0.6] [--evidence]` |
