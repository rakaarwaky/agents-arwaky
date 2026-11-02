# Gists

Manage GitHub Gists. Prefer `gh`; fall back to `curl` + REST only where `gh` lacks coverage (Global Rule: Prefer `gh`).

## Steps

1. **Create & list with `gh`**:

   ```bash
   gh gist create script.py --public --desc "Useful script"
   gh gist create notes.txt --secret --desc "private notes"
   gh gist list
   gh gist view <GIST_ID>
   gh gist delete <GIST_ID>
   ```

2. **curl fallback**:

   ```bash
   # Create a gist
   curl -s -X POST \
     -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/gists \
     -d '{
       "description": "Useful script",
       "public": true,
       "files": {
         "script.py": {"content": "print(\"hello\")"}
       }
     }'

   # List your gists
   curl -s -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/gists \
     | python3 -c "
   import sys, json
   for g in json.load(sys.stdin):
       files = ', '.join(g['files'].keys())
       print(f\"  {g['id']}  {g['description'] or '(no desc)':40}  {files}\")"
   ```

## Completion Criteria

- `gh gist list` includes the new gist; for `curl`, the `id` from the create response appears in a subsequent list.
- The gist is viewable at `https://gist.github.com/<gist_id>` (public) or via `gh gist view <id>` (secret).
