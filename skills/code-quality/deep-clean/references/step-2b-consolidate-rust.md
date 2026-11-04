# Step 2b: File Consolidation — Rust

Language variant of step 2 for `target_lang = rust`. Carries Phase 2 detection patterns, consolidation workflow, final verification, commit, checklists, quick-reference commands, common mistakes, decision flowchart, dry-run mode, and tool reference.

## Phase 2: File Consolidation

### Detection Patterns: Same-Concept Files (Merge)

```rust
capabilities_world_to_camera.rs
capabilities_camera_to_world.rs
capabilities_camera_to_viewport.rs
// All do coordinate transforms → merge into capabilities_coordinate_mapper.rs
```

### Detection Patterns: Same-Feature Files (Merge)

```rust
capabilities_brush_cursor_drawer.rs
capabilities_drag_cursor_drawer.rs
capabilities_cursor_data_renderer.rs
// All render cursors → merge into capabilities_cursor_renderer.rs
```

### Detection Patterns: Same-Technology Adapters (Merge)

```rust
utility_ffmpeg_adapter.rs
utility_video_ffmpeg_adapter.rs
// Both use FFmpeg → merge into 1 adapter
```

### The Consolidation Pattern

#### Before Merge (Two Files)

```text
crates/<crate>/src/capabilities_<name1>.rs
  - StructA implements TraitA
  - Fields: field_a, field_b
  - Methods: method_a, helper_a

crates/<crate>/src/capabilities_<name2>.rs
  - StructB implements TraitB
  - Fields: field_c, field_d
  - Methods: method_b, helper_b
```

#### After Merge (One File)

```rust
use async_trait::async_trait;
use shared::...;

/// Unified struct combining StructA and StructB for [domain description].
pub struct UnifiedStruct {
    // Fields from BOTH old structs (merge all fields)
    field_a: TypeA,
    field_b: TypeB,
    field_c: TypeC,
    field_d: TypeD,
}

#[async_trait]
impl TraitA for UnifiedStruct {
    fn method_a(&self, ...) -> ... {
        self.do_method_a(...)  // wrapper calls do_* method
    }

    fn do_method_a(&self, ...) -> ... {
        // merged logic from old StructA
    }
}

#[async_trait]
impl TraitB for UnifiedStruct {
    fn method_b(&self, ...) -> ... {
        self.do_method_b(...)  // wrapper calls do_* method
    }

    fn do_method_b(&self, ...) -> ... {
        // merged logic from old StructB
    }
}

// Free functions — keep as standalone or make methods
fn helper_a(...) -> ... { ... }
fn helper_b(...) -> ... { ... }
```

### Phase 2 Workflow

#### Step 2.1: Detect Overlaps and Analyze Files

Group files by concept/feature/technology. Read each file to understand:

- What structs/classes exist
- What traits they implement
- What fields each struct has
- What methods each impl block has
- What free functions exist
- What imports are used

```bash
# Group files by capability name pattern
ls crates/<crate>/src/capabilities_*.rs

# Analyze both files
wc -l crates/<crate>/src/file1.rs crates/<crate>/src/file2.rs
grep -c "^pub struct" crates/<crate>/src/file1.rs
grep -c "^    fn \|^    pub fn " crates/<crate>/src/file1.rs
```

#### Step 2.2: Pick Target File

Select the file with the most logic (most lines, most methods, most fields) as the merge target.

#### Step 2.3: Merge Imports

Combine imports from all files, remove duplicates:

```rust
// From file1 + file2 — deduplicated
use async_trait::async_trait;
use shared::common::...;
use shared::import_rules::...;
use std::collections::{HashMap, HashSet};
```

#### Step 2.4: Merge Structs

Combine fields from all old structs into one struct:

```rust
pub struct UnifiedStruct {
    // Fields from StructA
    field_a: TypeA,
    field_b: TypeB,

    // Fields from StructB
    field_c: TypeC,
    field_d: TypeD,
}
```

**Merge carefully**: If both structs have the same field (e.g., `_config`), keep only one.

#### Step 2.5: Merge Impl Blocks

Put ALL methods into impl blocks. If multiple traits exist, create separate impl blocks for each trait.

**For each trait:**

- Trait method (public) → wrapper calling `do_*` method
- Internal implementation → `do_*` prefix

```rust
impl TraitA for UnifiedStruct {
    fn public_method(&self, ...) -> ... {
        self.do_public_method(...)  // calls internal method
    }

    fn do_public_method(&self, ...) -> ... {
        // actual logic from old StructA
    }
}

impl TraitB for UnifiedStruct {
    fn public_method(&self, ...) -> ... {
        self.do_public_method(...)  // calls internal method
    }

    fn do_public_method(&self, ...) -> ... {
        // actual logic from old StructB
    }
}
```

#### Step 2.6: Merge Free Functions

Keep free functions as standalone (outside impl block) or convert to methods:

```rust
// Option A: Keep as standalone free functions
fn helper_a(...) -> ... { ... }
fn helper_b(...) -> ... { ... }

// Option B: Convert to methods (if they need self)
impl UnifiedStruct {
    fn do_helper_a(&self, ...) -> ... { ... }
    fn do_helper_b(&self, ...) -> ... { ... }
}
```

#### Step 2.7: Update All References

Find and update ALL references across the codebase:

```bash
# Find all references to old names
grep -r "OldStructA\|OldStructB\|TraitA\|TraitB" crates/

# Update lib.rs exports
# Update root container wiring
# Update test files
```

#### Step 2.8: Delete Source File(s)

Remove the file(s) whose functionality was merged:

```bash
rm crates/<crate>/src/file2.rs
```

#### Step 2.9: Verify Phase 2

```bash
cargo check -p <crate-name> 2>&1 | grep -E "error|cannot find"
```

---

## Final Verification (Both Phases)

```bash
# Compilation check
cargo check -p <crate-name> --all-features 2>&1 | grep -E "^error"

# Test compilation
cargo test -p <crate-name> --no-run --all-features 2>&1 | grep -E "^error"

# Full test run
cargo test -p <crate-name> --all-features 2>&1 | tail -5

# Clippy clean
cargo clippy -p <crate-name> --all-features -- -D warnings 2>&1 | grep -E "^error|^warning"

# Check downstream crates
cargo check --workspace --all-features 2>&1 | grep -E "^error"
```

---

## Commit

```bash
git add -A
git commit -m "cleanup(<crate-name>): remove N dead items + merge M files (K lines)

Removed:
- X stubs
- Y thin wrappers
- Z duplicate functions
- W unused files

Consolidated:
- A files merged into B files

All cargo check/test/clippy passing with --all-features."
```

---

## Verification Checklist

### Phase 1: Dead Code Cleanup

- [ ] Git snapshot created before any changes
- [ ] Working on dedicated cleanup branch
- [ ] FRD / requirements read and MVP scope understood
- [ ] `cargo clippy --all-features` run as primary detection
- [ ] File-level scan uses multi-pattern detection (mod, use, path, glob, build.rs, tests)
- [ ] Each function evaluated against Fundamental Question
- [ ] `#[cfg(feature)]` and `#[cfg(test)]` items NOT auto-removed
- [ ] `#[allow(dead_code)]` items investigated, not auto-removed
- [ ] Proc macro / derive macro references checked
- [ ] Integration tests (`tests/`) checked for references
- [ ] Report generated showing keep/remove per file with reasons
- [ ] Approval gate honored: `--dry-run` → report only; headless → autonomous execution
- [ ] Traits updated when methods removed from impl
- [ ] `mod.rs` updated when modules deleted
- [ ] `cargo check -p <crate> --all-features` passes
- [ ] `cargo test -p <crate> --all-features` passes
- [ ] `cargo clippy -p <crate> --all-features -- -D warnings` passes
- [ ] `cargo check --workspace --all-features` passes (downstream crates)

### Phase 2: File Consolidation

- [ ] Files analyzed and overlaps confirmed
- [ ] Target file selected (most logic)
- [ ] Imports merged and deduplicated
- [ ] Structs combined into one struct with all fields
- [ ] All methods moved to impl blocks (trait impl + inherent impl)
- [ ] Free functions kept as standalone or converted to methods
- [ ] Source file(s) deleted
- [ ] All references updated (lib.rs, root container, tests)
- [ ] `cargo check -p <crate-name>` passes without warnings or errors

### Final

- [ ] Committed with descriptive message

---

## Quick Reference Commands

```bash
# === PHASE 1: PRIMARY DETECTION ===
cargo clippy -p <crate> --all-features -- -W dead_code -W unused_imports 2>&1
cargo udeps -p <crate> --all-features 2>&1

# === PHASE 1: FILE-LEVEL ORPHAN SCAN ===
# (Use the full script from Step 1.4 above)

# === PHASE 1: FUNCTION-LEVEL BLOAT ===
# Stubs:
rg "fn\s+\w+\([^)]*\)\s*(->\s*\S+)?\s*\{\s*(None|String::new|vec!\[\]|Ok\(\(\)\)|false|0)\s*\}" crates/<crate>/src/

# Thin wrappers (multiline):
rg -U "fn\s+\w+\([^)]*\)[^{]*\{\s*\n\s*(self\.\w+|&self\.\w+)\s*\n\s*\}" crates/<crate>/src/

# Duplicates:
grep -rn "fn " crates/<crate>/src/ | sed 's/.*fn \([a-z_0-9]*\).*/\1/' | sort | uniq -d

# cfg-gated code (DO NOT REMOVE):
rg "#\[cfg\(" crates/<crate>/src/

# allow(dead_code) (INVESTIGATE):
rg "#\[allow\(dead_code\)\]" crates/<crate>/src/

# === PHASE 2: OVERLAP DETECTION ===
ls crates/<crate>/src/capabilities_*.rs | xargs -n1 basename | sort
wc -l crates/<crate>/src/file1.rs crates/<crate>/src/file2.rs
grep -c "^pub struct" crates/<crate>/src/file1.rs
grep -c "^    fn \|^    pub fn " crates/<crate>/src/file1.rs

# === VERIFICATION ===
cargo check -p <crate> --all-features 2>&1 | grep "^error"
cargo test -p <crate> --all-features 2>&1 | tail -3
cargo clippy -p <crate> --all-features -- -D warnings 2>&1 | grep "^error"
cargo check --workspace --all-features 2>&1 | grep "^error"

# === ROLLBACK ===
git checkout HEAD~1 -- crates/<crate>/src/<file>.rs   # restore one file
git reset --hard HEAD~1                                  # nuclear option
```

---

## Common Mistakes (AVOID)

| Mistake | Why It's Dangerous | Prevention |
| -------------------------------------------------- | --------------------------------------------------------- | ----------------------------------------------- |
| Removing real MVP logic | Breaks required functionality | Fundamental Question + FRD cross-reference |
| Forgetting to update traits | Compilation errors in downstream crates | Always edit trait file when editing impl |
| Deleting files without updating `mod.rs` | Compilation error: "file not found for module" | Checklist item; grep for `mod <name>;` |
| Removing `contract_*.rs` / trait files | Breaks external crate consumers | Exception list; check `Cargo.toml` dependents |
| Skipping `--all-features` in verification | Misses breakage in cfg-gated code | Always use `--all-features` in check/test/clippy |
| Removing `#[cfg(test)]` code | Breaks `cargo test` | Run `cargo test --no-run` as verification step |
| Removing code behind `#[cfg(feature)]` | Breaks feature-gated builds | Check `Cargo.toml` `[features]` section first |
| Ignoring glob imports (`use super::*`) | File appears unused but is imported via glob | Check parent module for `*` imports |
| Ignoring proc macro / derive references | File is referenced via macro expansion, invisible to grep | Check `#[derive(...)]` and proc macro crates |
| Skipping git snapshot | Cannot rollback if cleanup breaks something | Step 1.1 is non-negotiable |
| Batch-removing "Maybe Unused" items | Glob imports or macros may reference them | Require manual review + explicit approval |
| Removing `#[allow(dead_code)]` items without asking | Developer had a reason to mark it | Investigate git blame / ask author |
| Consolidating files with dead code | Wastes effort merging code that should be deleted | Always run Phase 1 before Phase 2 |
| Forgetting to update lib.rs exports after merge | Compilation error: "unresolved import" | Grep for old module names after merge |
| Leaving orphan references after merge | Runtime errors from stale imports | Grep for old struct/trait names after merge |

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
│  │  │  └─ YES → KEEP (stop)
│  │  │
│  │  ├─ Is it behind #[cfg(feature/test)]?
│  │  │  └─ YES → KEEP unless feature is confirmed deprecated (stop)
│  │  │
│  │  ├─ Does it have #[allow(dead_code)]?
│  │  │  └─ YES → Investigate intent. Ask author. Do NOT auto-remove. (stop)
│  │  │
│  │  ├─ Is it referenced by proc macro / derive / build.rs / integration test?
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
│  │  └─ Execute removal → Update trait → Update mod.rs → Verify
│  │
│  └─ Phase 1 Complete → Proceed to Phase 2
│
├─ PHASE 2: FILE CONSOLIDATION
│  │
│  ├─ Do files share the same domain/concept/feature?
│  │  └─ NO → Skip consolidation for these files
│  │
│  ├─ YES → Merge into single file:
│  │  ├─ Pick target (most logic)
│  │  ├─ Merge imports (deduplicate)
│  │  ├─ Merge structs (combine fields)
│  │  ├─ Merge impl blocks (one per trait)
│  │  ├─ Merge free functions
│  │  ├─ Update all references
│  │  ├─ Delete source file(s)
│  │  └─ Verify compilation
│  │
│  └─ Phase 2 Complete → Final Verification
│
└─ FINAL VERIFICATION
   ├─ cargo check --all-features
   ├─ cargo test --all-features
   ├─ cargo clippy --all-features -- -D warnings
   ├─ cargo check --workspace --all-features
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
