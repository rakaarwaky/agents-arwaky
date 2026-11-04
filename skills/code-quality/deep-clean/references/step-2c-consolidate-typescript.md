# Step 2c: File Consolidation — TypeScript

Language variant of step 2 for `target_lang = typescript`. Carries Phase 2 detection patterns, consolidation workflow, final verification, commit, checklists, quick-reference commands, common mistakes, decision flowchart, dry-run mode, and tool reference.

## Phase 2: File Consolidation

### Detection Patterns: Same-Purpose Files (Merge)

```typescript
parser.ts
parser-utils.ts
parser-helpers.ts
// All parse-related → merge into parser.ts
```

### Detection Patterns: Same-Domain Files (Merge)

```typescript
validators-email.ts
validators-phone.ts
validators-url.ts
// All validate inputs → merge into validators.ts
```

### Detection Patterns: Split Functionality (Merge)

```typescript
services/user-creator.ts
services/user-updater.ts
services/user-deleter.ts
// All handle user CRUD → merge into services/user-service.ts
```

### The Consolidation Pattern

#### Before Merge (Two Files)

```text
packages/my-pkg/src/services/user-creator.ts
  - class UserCreator
  - Methods: create, validateInput

packages/my-pkg/src/services/user-validator.ts
  - class UserValidator
  - Methods: validateEmail, validateName
```

#### After Merge (One File)

```typescript
/** User service — handles creation, validation, and management. */

import { UserVO } from "../shared";

export class UserValidator {
  /** Validates user data before persistence. */
  validateEmail(email: string): boolean {
    // merged logic from UserValidator
    ...
  }

  validateName(name: string): boolean {
    // merged logic from UserValidator
    ...
  }
}

export class UserCreator {
  private readonly validator: UserValidator;

  constructor(validator: UserValidator) {
    this.validator = validator;
  }

  /** Creates a new user account. */
  create(data: Record<string, unknown>): UserVO {
    // merged logic from UserCreator
    ...
  }

  validateInput(data: Record<string, unknown>): boolean {
    // merged logic from UserCreator
    ...
  }
}
```

### Phase 2 Workflow

#### Step 2.1: Analyze File Responsibilities

Read files and identify related functionality:

```bash
# List classes/functions in files
grep -rn "^class \|^function \|^export " packages/*/src/ | sort
```

#### Step 2.2: Identify Consolidation Candidates

Files that should be merged:

- Multiple files with related classes (e.g., `parser.ts`, `parser-utils.ts`)
- Files that only import from each other
- Split functionality across multiple small files

#### Step 2.3: Pick Target File

Select the file with the most logic (most lines, most methods, most classes) as the merge target.

#### Step 2.4: Merge Related Code

Move classes/functions to target file:

```typescript
// Before: parser.ts and parser-utils.ts
// After: Single parser.ts with all related code
```

**Merge carefully**: If both files define the same class/function name, keep only one (prefer the more complete version).

#### Step 2.5: Update Imports

Fix all imports across the codebase:

```bash
# Find files importing from removed modules
grep -rn "from.*parser_utils" packages/
```

#### Step 2.6: Update Barrel File (`index.ts`)

```typescript
// Update index.ts — remove re-exports of deleted module
// Remove: export { UserValidator } from './services/user-validator';
// Add: export { UserValidator, UserCreator } from './services/user-service';
```

#### Step 2.7: Update `package.json`

```json
// Update package.json — remove references to deleted entry files if needed
// Update exports/main/types fields if the deleted file was an entry point
```

#### Step 2.8: Delete Source File(s)

Remove the file(s) whose functionality was merged:

```bash
rm packages/my-pkg/src/services/user-validator.ts
```

#### Step 2.9: Verify Phase 2

```bash
npx tsc --noEmit
npx vitest run
```

---

## Final Verification (Both Phases)

```bash
# Type check
npx tsc --noEmit --project packages/<pkg>/tsconfig.json 2>&1 | grep -E "error TS"

# Lint clean
npx eslint packages/<pkg>/src/ --max-warnings 0 2>&1 | grep -v "^$"

# Format clean
npx prettier --check packages/<pkg>/src/ 2>&1 | grep -v "All matched files"

# Tests pass
npx jest --passWithNoTests 2>&1 | tail -5
# OR: npx vitest run 2>&1 | tail -5

# Knip re-run
npx knip --workspace packages/<pkg> 2>&1 | head -20

# Check downstream packages
npx tsc --noEmit --project tsconfig.json 2>&1 | grep -E "error TS"
```

---

## Commit

```bash
git add -A
git commit -m "cleanup(<pkg>): remove N dead items + merge M files (K lines)

Removed:
- X stubs
- Y thin wrappers
- Z duplicate functions
- W unused files
- V unused imports / exports / types
- U commented-out code blocks
- T dead barrel re-exports

Consolidated:
- A files merged into B files

Formatted: prettier + eslint
All tsc / eslint / jest / knip passing."
```

---

## Verification Checklist

### Phase 1: Dead Code Cleanup

- [ ] Git snapshot created before any changes
- [ ] Working on dedicated cleanup branch
- [ ] FRD / requirements read and MVP scope understood
- [ ] `knip` run as primary unused file/export detection
- [ ] `tsc --noEmit --noUnusedLocals --noUnusedParameters` run for compiler-level detection
- [ ] `eslint --fix` run for lint + unused imports
- [ ] File-level scan uses multi-pattern detection (static import, dynamic import, path alias, barrel, package.json, tsconfig, config files, tests, string refs)
- [ ] Each function/type evaluated against Fundamental Question
- [ ] Decorator-registered code NOT removed
- [ ] `.d.ts` / `declare` / `declare global` NOT removed
- [ ] Side-effect imports NOT removed
- [ ] Dynamic `import()` / `require()` targets NOT removed
- [ ] `// @ts-ignore` / `// @ts-expect-error` / `// eslint-disable` items investigated, not auto-removed
- [ ] `@generated` files NOT manually edited or deleted
- [ ] Path aliases (`@/`, `~/`) resolved via tsconfig before marking as unused
- [ ] Report generated showing keep/remove per file with reasons
- [ ] Approval gate honored: `--dry-run` → report only; headless → autonomous execution
- [ ] Barrel files (`index.ts`) updated when modules deleted
- [ ] `package.json` `exports`/`main`/`types` updated when entry files deleted
- [ ] `tsc --noEmit` passes
- [ ] `eslint --max-warnings 0` passes
- [ ] `prettier --check` passes
- [ ] `jest` / `vitest` passes
- [ ] `knip` re-run shows no new issues
- [ ] Downstream packages build successfully (monorepo check)

### Phase 2: File Consolidation

- [ ] Files analyzed and consolidation candidates identified
- [ ] Target file selected (most logic)
- [ ] Related classes/functions merged into single file
- [ ] All imports updated to reflect new structure
- [ ] `index.ts` barrel file updated with new exports
- [ ] `package.json` updated if entry points changed
- [ ] Source file(s) deleted
- [ ] `tsc --noEmit` passes
- [ ] `jest` / `vitest` passes

### Final

- [ ] Committed with descriptive message

---

## Quick Reference Commands

```bash
# === PHASE 1: PRIMARY DETECTION ===
npx knip --workspace packages/<pkg>                              # unused files, exports, deps, types
npx tsc --noEmit --noUnusedLocals --noUnusedParameters -p packages/<pkg>/tsconfig.json  # compiler
npx eslint packages/<pkg>/src/ --fix --max-warnings 0            # lint + imports
npx prettier --check packages/<pkg>/src/                         # format check

# === PHASE 1: SECONDARY DETECTION ===
npx ts-prune --project packages/<pkg>/tsconfig.json              # unused exports
npx ts-unused-exports packages/<pkg>/tsconfig.json               # unused exports (alt)

# === PHASE 1: FILE-LEVEL ORPHAN SCAN ===
# (Use the full script from Step 1.4 above)

# === PHASE 1: FUNCTION-LEVEL BLOAT ===
# Stubs:
grep -rnP "(function\s+\w+\([^)]*\)\s*(:\s*\S+)?\s*\{\s*\})|=>\s*\{\s*\}" packages/<pkg>/src/ --include="*.ts"
grep -rn "throw new Error('Not implemented')" packages/<pkg>/src/ --include="*.ts"

# Thin wrappers:
grep -rnP "=>\s*\w+\.\w+\s*[;,]" packages/<pkg>/src/ --include="*.ts"

# Duplicates:
grep -rn "function " packages/<pkg>/src/ --include="*.ts" | \
  sed 's/.*function \([a-zA-Z_0-9]*\).*/\1/' | sort | uniq -d

# Commented-out code:
grep -rn "^//\s*\(function\|class\|const\|import\|export\|interface\|type\|enum\|return\)" \
  packages/<pkg>/src/ --include="*.ts"

# Decorator-registered (DO NOT REMOVE):
grep -rnB1 "class\|function" packages/<pkg>/src/ --include="*.ts" | \
  grep -E "@(Controller|Injectable|Component|Module|Entity|Guard|Pipe|Get|Post|Put|Delete)"

# @ts-ignore / eslint-disable (INVESTIGATE):
grep -rn "// @ts-ignore\|// @ts-expect-error\|// eslint-disable" packages/<pkg>/src/ --include="*.ts"

# === PHASE 2: OVERLAP DETECTION ===
grep -rn "^class \|^function \|^export " packages/*/src/ | sort
grep -rn "^from.*import\|^import.*from" packages/*/src/index.ts

# === FORMATTING ===
npx eslint packages/<pkg>/src/ --fix                  # lint auto-fix
npx prettier --write packages/<pkg>/src/              # format

# === VERIFICATION ===
npx tsc --noEmit -p packages/<pkg>/tsconfig.json      # typecheck
npx eslint packages/<pkg>/src/ --max-warnings 0       # lint clean
npx prettier --check packages/<pkg>/src/              # format clean
npx jest --passWithNoTests 2>&1 | tail -3             # tests pass
npx knip --workspace packages/<pkg>                   # no unused exports

# === ROLLBACK ===
git checkout HEAD~1 -- packages/<pkg>/src/<file>.ts   # restore one file
git reset --hard HEAD~1                                # nuclear option
```

---

## Common Mistakes (AVOID)


| Mistake                                            | Why It's Dangerous                                          | Prevention                                                       |
| -------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------------- |
| Removing real MVP logic                            | Breaks required functionality                               | Fundamental Question + FRD cross-reference                       |
| Removing decorator-registered code                 | Breaks NestJS/Angular/TypeORM routing, DI, entities         | Grep for decorators before removing any class/function           |
| Removing `.d.ts` / `declare` blocks                | Breaks ambient typing for entire project                    | Exception list; never auto-remove                                |
| Removing side-effect imports                       | Breaks polyfills, style injection, global registrations     | Check for `import './x'` pattern; investigate what the file does |
| Removing dynamic `import()` targets                | Runtime `MODULE_NOT_FOUND` / chunk load failure             | Grep for `import(` and `require(` string references              |
| Forgetting to update barrel `index.ts`             | `MODULE_NOT_FOUND` for downstream consumers                 | Always edit `index.ts` when deleting modules                     |
| Forgetting to update `package.json` exports        | Package entry point breaks                                  | Always check `exports`/`main`/`types` fields                     |
| Removing `// @ts-ignore` without investigating     | Exposes a real type error that was intentionally suppressed | Investigate git blame / ask author                               |
| Removing `// eslint-disable` without investigating | Exposes a lint issue that was intentionally suppressed      | Investigate why the rule was disabled                            |
| Removing path-aliased modules (`@/utils/x`)        | Module appears unused because grep misses alias resolution  | Resolve `tsconfig.json` paths before scanning                    |
| Removing `@generated` files                        | Breaks codegen pipeline; file is regenerated on next build  | Exception list; never manually edit/delete                       |
| Removing `export` from publicly consumed types     | Breaks downstream package compilation                       | Check monorepo consumers before de-exporting                     |
| Skipping `--noEmit` typecheck                      | Misses broken imports, missing types                        | Always run `tsc --noEmit` after cleanup                          |
| Batch-removing "Maybe Unused" items                | Dynamic imports or string refs may reference them           | Require manual review + explicit approval                        |
| Keeping commented-out code "for reference"         | Noise; git history preserves old code                       | Remove; use `git log` to recover if needed                       |
| Skipping git snapshot                              | Cannot rollback if cleanup breaks something                 | Step 1.1 is non-negotiable                                       |
| Removing enum members from public API              | Breaks downstream `switch` statements / comparisons         | Check monorepo consumers before removing members                 |
| Ignoring monorepo workspace references             | File unused in own package but imported by sibling          | Run `knip` at workspace root or check sibling imports            |
| Consolidating files with dead code                 | Wastes effort merging code that should be deleted           | Always run Phase 1 before Phase 2                                |
| Forgetting to update `index.ts` after merge        | `MODULE_NOT_FOUND` for downstream consumers                 | Grep for old module names after merge                            |
| Leaving orphan references after merge              | Runtime errors from stale imports                           | Grep for old class/function names after merge                    |


---

## Decision Flowchart

```text
START
│
├─ PHASE 1: DEAD CODE CLEANUP
│  │
│  ├─ Item flagged for removal
│  │  │
│  │  ├─ Is it in the Exceptions list?
│  │  │  (index.ts barrel, .d.ts, declare, @generated, migrations, etc.)
│  │  │  └─ YES → KEEP (stop)
│  │  │
│  │  ├─ Is it decorator-registered?
│  │  │  (@Controller, @Injectable, @Component, @Entity, @Module, @Guard, etc.)
│  │  │  └─ YES → KEEP (stop)
│  │  │
│  │  ├─ Is it a side-effect import or dynamic import() / require() target?
│  │  │  └─ YES → KEEP (stop)
│  │  │
│  │  ├─ Is it referenced by package.json exports / tsconfig paths / config files?
│  │  │  └─ YES → KEEP (stop)
│  │  │
│  │  ├─ Does it have @ts-ignore / @ts-expect-error / eslint-disable?
│  │  │  └─ YES → Investigate intent. Ask author. Do NOT auto-remove. (stop)
│  │  │
│  │  ├─ Is it a .d.ts file or declare global / declare module block?
│  │  │  └─ YES → KEEP (stop)
│  │  │
│  │  ├─ Is it @generated / @auto-generated?
│  │  │  └─ YES → KEEP. Do not manually edit. (stop)
│  │  │
│  │  ├─ Is it referenced by a test file (*.spec.ts, *.test.ts, __tests__/)?
│  │  │  └─ YES → KEEP (stop)
│  │  │
│  │  ├─ Is it consumed by a downstream package in the monorepo?
│  │  │  └─ YES → KEEP (stop)
│  │  │
│  │  ├─ Apply Fundamental Question:
│  │  │  ├─ "Required by FRD?" → KEEP
│  │  │  ├─ "Called by FRD-required method?" → KEEP
│  │  │  ├─ "Always there / might be useful / edge case?" → REMOVE
│  │  │  └─ Unclear? → Flag for manual review (do NOT auto-remove)
│  │  │
│  │  ├─ If Overengineered pattern:
│  │  │  └─ Pass 3-point test? → REMOVE. Fail any point? → KEEP + comment.
│  │  │
│  │  ├─ If formatting issue (unused import, line length, semicolons, quotes):
│  │  │  └─ Auto-fix with eslint/prettier (no approval needed for format-only changes)
│  │  │
│  │  └─ Execute removal → Update index.ts barrel → Update package.json → Verify
│  │
│  └─ Phase 1 Complete → Proceed to Phase 2
│
├─ PHASE 2: FILE CONSOLIDATION
│  │
│  ├─ Do files serve the same purpose / share the same domain?
│  │  └─ NO → Skip consolidation for these files
│  │
│  ├─ YES → Consolidate into single module:
│  │  ├─ Pick target (most logic)
│  │  ├─ Merge classes/functions
│  │  ├─ Update all imports
│  │  ├─ Update index.ts barrel file
│  │  ├─ Update package.json if needed
│  │  ├─ Delete source file(s)
│  │  └─ Verify compilation
│  │
│  └─ Phase 2 Complete → Final Verification
│
└─ FINAL VERIFICATION
   ├─ tsc --noEmit
   ├─ eslint --max-warnings 0
   ├─ prettier --check
   ├─ jest / vitest
   ├─ knip
   ├─ downstream packages build
   ├─ (--dry-run?) → stop; report only, no execution
   └─ Commit with descriptive message
```

---

## Dry-Run Mode

`--dry-run` is only active when the user explicitly passes it. When active:

1. Run Phase 1 Steps 1.1–1.6 (detection + analysis)
2. Run the Phase 2 overlap-detection step(s)
3. Generate the full report (Phase 1 Step 1.7 + Phase 2 findings)
4. **Do NOT execute any deletions, edits, or format changes** — report only
5. Present the report. No execution.

Without `--dry-run` the run is headless and autonomous: every step executes to completion without asking for permission; RISKY-tier items are recorded in the report's manual-review section rather than blocking the run.

---

## Tool Reference


| Tool                               | Replaces                         | Purpose                                                                             |
| ---------------------------------- | -------------------------------- | ----------------------------------------------------------------------------------- |
| `knip`                             | ts-prune, depcheck, unused-files | Unused files, exports, dependencies, types, enum members — all in one               |
| `tsc --noEmit`                     | (no equivalent)                  | Type checking; `--noUnusedLocals --noUnusedParameters` for compiler-level dead code |
| `eslint` + `@typescript-eslint`    | tslint, jshint                   | Lint, unused vars, import ordering, code quality rules                              |
| `prettier`                         | (no equivalent)                  | Code formatting (line length, semicolons, quotes, spacing)                          |
| `ts-prune`                         | (partial knip overlap)           | Unused exports detection (lighter weight, fewer features)                           |
| `ts-unused-exports`                | (partial knip overlap)           | Unused exports with tsconfig path alias support                                     |
| `jest --listTests` / `vitest list` | (no equivalent)                  | Verifies all test files can be resolved (catches broken imports)                    |


**Recommended config files:**

```jsonc
// .eslintrc.json (or eslint.config.js for flat config)
{
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint", "import"],
  "rules": {
    "@typescript-eslint/no-unused-vars": [
      "error",
      { "argsIgnorePattern": "^_" },
    ],
    "import/order": [
      "error",
      {
        "groups": [
          "builtin",
          "external",
          "internal",
          "parent",
          "sibling",
          "index",
        ],
        "alphabetize": { "order": "asc" },
      },
    ],
    "no-unused-vars": "off",
  },
}
```

```jsonc
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100,
  "tabWidth": 2,
}
```

```jsonc
// knip.json (or "knip" key in package.json)
{
  "workspaces": {
    "packages/<pkg>": {
      "entry": ["src/index.ts", "src/main.ts"],
      "project": ["src/**/*.ts"],
      "ignore": ["src/**/*.spec.ts", "src/**/*.test.ts", "src/**/__tests__/**"],
    },
  },
}
```

```jsonc
// tsconfig.json (relevant compiler options)
{
  "compilerOptions": {
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noUncheckedIndexedAccess": true,
    "paths": {
      "@/*": ["./src/*"],
    },
  },
}
```