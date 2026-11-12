# Clone Repository

Clone a remote repository into the local working directory. Pure `git` — works identically with or without `gh`.

## Steps

1. **Pick the clone method** — HTTPS with credential helper or token, or SSH.

2. **Clone with `git`**:

   ```bash
   # HTTPS (credential helper or token-embedded URL)
   git clone https://github.com/owner/repo-name.git

   # Into a specific directory
   git clone https://github.com/owner/repo-name.git ./my-local-dir

   # Shallow (faster for large repos)
   git clone --depth 1 https://github.com/owner/repo-name.git

   # Specific branch
   git clone --branch develop https://github.com/owner/repo-name.git

   # SSH
   git clone git@github.com:owner/repo-name.git
   ```

3. **Clone with `gh`** (shorthand, resolves the URL for you):

   ```bash
   gh repo clone owner/repo-name
   gh repo clone owner/repo-name -- --depth 1
   ```

## Completion Criteria

- `ls` in the target directory shows the cloned repo (default branch checked out, `git remote -v` shows `origin`).
- For `--depth 1`, `git log --oneline | wc -l` returns 1.
