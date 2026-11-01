# Report Format

The shape of the final executed `skill-lifecycle report`:

```text
skill-lifecycle report — <audit root>

MERGED:
- <surviving folder>  <-  <dropped folder(s)>
    reason: <duplicate scope / shared domain>
    action:  <body merged | references/ created for scenarios: a, b | duplicates dropped>

KEPT SEPARATE:
- <skill A> vs <skill B>  —  reason: <distinct jobs, e.g. different completion criteria>

DELETED:
- <folder>  —  reason: <true duplicate of <survivor>, stale name collision, empty category cleanup>

ROLLBACK TARGET:
- <snapshot commit SHA or stash ref>

VERIFY:
- N skills remain, 0 shared names, all reference links resolve, all frontmatter parses
```
