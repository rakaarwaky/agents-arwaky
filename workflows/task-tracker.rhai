let meta = #{
    name: "task-tracker",
    description: "Zero-trust: map AES spec states into modular GitHub tracking issues, one subagent per feature, every issue closing to a row advance to Done",
    phases: [
        #{ title: "Discover", detail: "one agent enumerates features and their spec docs" },
        #{ title: "Scan", detail: "one scanner subagent per feature, each owning its FR-id set" },
        #{ title: "Verify", detail: "one verifier subagent per feature; every Done row is re-checked, roll-up reconciled" },
        #{ title: "Issue", detail: "batched modular issue creation, one Closing condition per body, dry-run default" },
    ],
};

let feature_schema = #{
    "type": "object", "required": ["root", "features"],
    "properties": #{
        "root": #{ "type": "array", "items": #{ "type": "string" } },
        "features": #{
            "type": "array",
            "items": #{
                "type": "object", "required": ["name", "dir", "docs"],
                "properties": #{
                    "name": #{ "type": "string" },
                    "dir": #{ "type": "string" },
                    "docs": #{ "type": "array", "items": #{ "type": "string" } },
                },
            },
        },
    },
};
let scan_schema = #{
    "type": "object", "required": ["rows", "fr", "rollup_row"],
    "properties": #{
        "rows": #{
            "type": "array",
            "items": #{
                "type": "object", "required": ["id", "state", "source_doc"],
                "properties": #{
                    "id": #{ "type": "string" },
                    "title": #{ "type": "string" },
                    "state": #{ "type": "string" },
                    "priority": #{ "type": "string" },
                    "health": #{ "type": "string" },
                    "fr_refs": #{ "type": "array", "items": #{ "type": "string" } },
                    "source_doc": #{ "type": "string" },
                    "row_text": #{ "type": "string" },
                    "next_action": #{ "type": "string" },
                },
            },
        },
        "fr": #{
            "type": "object",
            "properties": #{
                "fr_declared": #{ "type": "array", "items": #{ "type": "string" } },
                "fr_referenced": #{ "type": "array", "items": #{ "type": "string" } },
            },
        },
        "rollup_row": #{ "type": "string" },
    },
};
let verdict_schema = #{
    "type": "object", "required": ["verdicts", "rollup_verdicts"],
    "properties": #{
        "verdicts": #{
            "type": "array",
            "items": #{
                "type": "object", "required": ["row", "verdict", "evidence", "closing_condition"],
                "properties": #{
                    "row": #{ "type": "string" },
                    "verdict": #{ "type": "string" },
                    "evidence": #{ "type": "string" },
                    "closing_condition": #{ "type": "string" },
                },
            },
        },
        "rollup_verdicts": #{
            "type": "array",
            "items": #{
                "type": "object", "required": ["feature", "verdict", "closing_condition"],
                "properties": #{
                    "feature": #{ "type": "string" },
                    "verdict": #{ "type": "string" },
                    "evidence": #{ "type": "string" },
                    "closing_condition": #{ "type": "string" },
                },
            },
        },
    },
};
let issue_schema = #{
    "type": "object", "required": ["results"],
    "properties": #{
        "results": #{
            "type": "array",
            "items": #{
                "type": "object", "required": ["row", "action", "closing_condition"],
                "properties": #{
                    "row": #{ "type": "string" },
                    "action": #{ "type": "string" },
                    "url": #{ "type": "string" },
                    "number": #{ "type": "string" },
                    "closing_condition": #{ "type": "string" },
                },
            },
        },
    },
};

// The engine delivers args as a JSON string; a hosted caller may deliver a map.
// json_text_field reads a flat JSON scalar out of the string shape, so both work.
fn json_text_field(js, key) {
    let needle = "\"" + key + "\":";
    let nlen = needle.len();
    let slen = js.len();
    if slen <= nlen { return (); }
    let pos = 0 - 1;
    let i = 0;
    while i < slen - nlen {
        let matched = true;
        let j = 0;
        while j < nlen {
            if js.sub_string(i + j, 1) != needle.sub_string(j, 1) { matched = false; }
            j += 1;
        }
        if matched { pos = i + nlen; i = slen; }
        i += 1;
    }
    if pos < 0 { return (); }
    while pos < slen && js.sub_string(pos, 1) == " " { pos += 1; }
    if pos >= slen { return (); }
    if js.sub_string(pos, 1) == "\"" {
        pos += 1;
        let out = "";
        while pos < slen && js.sub_string(pos, 1) != "\"" {
            out += js.sub_string(pos, 1);
            pos += 1;
        }
        return out;
    }
    let out2 = "";
    while pos < slen && js.sub_string(pos, 1) != "," && js.sub_string(pos, 1) != "}" && js.sub_string(pos, 1) != " " {
        out2 += js.sub_string(pos, 1);
        pos += 1;
    }
    return out2;
}

// args: { repo_root (required), dry_run (optional), batch (optional), trust_mode (optional: "trust" | "no-trust", default "no-trust") }
let a_root = ();
let a_dry = ();
let a_batch = ();
let a_trust = ();
if type_of(args) == "map" {
    a_root = args.repo_root;
    a_dry = args.dry_run;
    a_batch = args.batch;
    a_trust = args.trust_mode;
} else if type_of(args) == "string" {
    a_root = json_text_field(args, "repo_root");
    a_dry = json_text_field(args, "dry_run");
    a_batch = json_text_field(args, "batch");
    a_trust = json_text_field(args, "trust_mode");
}
if a_root == () { pause("verification", "Pass args.repo_root — the absolute path to the AES repo to track."); }
let repo_root = a_root.to_string();
let dry_run = if a_dry == () { false } else { a_dry.to_string() == "true" || a_dry.to_string() == "1" };
let trust_mode = if a_trust == () { "no-trust" } else { a_trust.to_string() };
if trust_mode != "trust" && trust_mode != "no-trust" {
    pause("verification", "Invalid trust_mode: " + trust_mode + " — must be 'trust' or 'no-trust'");
}
let state_label = "task-tracker";
let batch = if a_batch == () { 6 } else { parse_int(a_batch.to_string()) };

// --- Phase 1: Discover (features, not docs) ---
phase("Discover");
let disc_prompt = "Enumerate the spec-document groups of " + repo_root + " as one JSON object "
    + "{\"root\":[...repo-relative paths...],\"features\":[{\"name\":\"<feature>\",\"dir\":\"<modules|packages|crates>/<feature>\",\"docs\":[...]}...]}. "
    + "A feature is each directory under modules/, packages/, or crates/ (whichever exist); its docs are the "
    + "spec documents inside that directory: BACKLOG.md, FRD.md, DESIGN.md, plus any other .md holding a "
    + "State Definitions table or a row table with an ID and State column. Root docs are the spec .md files at "
    + "the repo root (ROADMAP.md, BACKLOG.md, PRD.md, DESIGN.md — whichever exist). "
    + "Exclude: any path whose first segment starts with a dot (.git, .agents, .grok, .venv, .tox, "
    + ".pytest_cache, .mypy_cache, .ruff_cache, .idea, .vscode, and every other dot-prefixed directory); "
    + "build and template paths matching node_modules|target|dist|__pycache__|htmlcov|coverage|junit|vendor|skills|"
    + "references|workspaces-bad|workspaces-good. Prompt scratch files and skill reference templates that quote "
    + "'State Definitions' without being specs are never included. "
    + "Feature name is the directory basename in lowercase. "
    + "Use: ls modules packages crates 2>/dev/null at the repo root, then list the .md files in each feature "
    + "directory. An empty features array is valid only if no feature directory has spec docs.";
let disc = agent(disc_prompt, #{
    label: "discover-features",
    capability_mode: "read-only",
    output_schema: feature_schema,
});
if disc == () || !disc.success {
    log("Discovery failed — no feature table; run cannot proceed to Scan");
    complete(#{ summary: "discovery failed", features: [] });
}
let root_docs = if type_of(disc.output.root) == "array" { disc.output.root } else { [] };
let features = if type_of(disc.output.features) == "array" { disc.output.features } else { [] };
log("discovered " + features.len().to_string() + " features and " + root_docs.len().to_string() + " root docs");

// --- Phase 2: Scan (one subagent per feature) ---
// Each feature scanner owns the feature's FR-id set and its roadmap roll-up row, so
// the FR ↔ backlog orphan check has all its inputs in one agent's context.
phase("Scan");
let groups = [];
for f in features {
    groups.push(#{ name: f.name, dir: f.dir, docs: f.docs });
}
groups.push(#{ name: "root", dir: ".", docs: root_docs });

let scan_jobs = [];
for g in groups {
    let docs_joined = "";
    for d in g.docs { docs_joined += d + " "; }
    let p = "You are a read-only scanner bound to the feature \"" + g.name + "\" in " + repo_root
        + ". Read each of these files in full: " + docs_joined
        + "Never read another feature's documents. "
        + "1. Extract each file's State Definitions table; list the state names it defines. "
        + "2. Extract every table row whose headers include ID and State; capture the doc-level "
        + "\"State: <value>\" line at the top of a feature backlog. "
        + "3. Extract the Next Action cell value (or Item cell value if Next Action is absent) "
        + "from each table row — capture ONLY the text between the | delimiters of that column in the "
        + "row; prose outside the table (Current Condition, etc.) is out of scope. "
        + "Trim leading/trailing whitespace. Include it as \"next_action\" in the output JSON. "
        + "4. Collect the FR-id set: every FR-<SCOPE>-NNN declared in the FRD headings and every FRD Ref "
        + "cell cited by the backlog rows. "
        + "5. If the roadmap has a Feature Roll-up table, extract THIS feature's roll-up row verbatim, all cells. "
        + "Emit one JSON object per task row: "
        + "{\"id\":\"...\",\"title\":\"...\",\"state\":\"<verbatim state>\",\"priority\":\"P0|P1|P2|—\","
        + "\"health\":\"...|—\",\"fr_refs\":[\"FR-…\"],\"source_doc\":\"<repo-relative path>\",\"row_text\":\"<verbatim row>\","
        + "\"next_action\":\"<verbatim next action or item text>\"}. "
        + "State must appear verbatim in the source row; never infer or normalize. "
        + "Rows without a state value get state unknown. Empty rows array is valid only after reading every file in full. "
        + "Return {\"rows\":[…],\"fr\":{\"fr_declared\":[…],\"fr_referenced\":[…]},\"rollup_row\":\"<verbatim row or empty>\"}.";
    scan_jobs.push(#{ prompt: p, label: "scan:" + g.name, capability_mode: "read-only", output_schema: scan_schema });
}
let scan_results = parallel(scan_jobs);

let all_rows = [];
let fr_sets = [];
let rollups = [];
let i = 0;
let scan_list = if type_of(scan_results) == "array" { scan_results } else { [] };
for sr in scan_list {
    let gname = groups[i].name;
    if sr != () && sr.success && sr.output != () {
        let got_rows = if type_of(sr.output.rows) == "array" { sr.output.rows } else { [] };
        for r in got_rows {
            r.source_doc = if r.source_doc == "" { groups[i].docs[0] } else { r.source_doc };
            r.feature = gname;
            r.class = "pending";
            all_rows.push(r);
        }
        let fr_out = sr.output.fr;
        fr_sets.push(#{
            feature: gname,
            fr_declared: if fr_out != () && fr_out.fr_declared != () { fr_out.fr_declared } else { [] },
            fr_referenced: if fr_out != () && fr_out.fr_referenced != () { fr_out.fr_referenced } else { [] },
        });
        if sr.output.rollup_row != () && sr.output.rollup_row != "" {
            rollups.push(#{ feature: gname, row: sr.output.rollup_row });
        }
    }
    i += 1;
}
log("scanned " + all_rows.len().to_string() + " rows across " + groups.len().to_string() + " feature groups");

// --- Phase 3: Classify (local, zero-trust with trust_mode support) ---
phase("Classify");
let classified_rows = [];
let rollup_classifications = [];
for g in groups {
    // Filter rows for this feature
    let feature_rows = [];
    for r in all_rows {
        if r.feature == g.name {
            feature_rows.push(r);
        }
    }
    
    // Classify each row based on trust_mode
    // Next Action is checked for ALL rows regardless of trust_mode (skill spec).
    // A Done row under trust mode is accepted for STATE, but its Next Action
    // (if it has descriptive content) still needs verification.
    for r in feature_rows {
        let row_state = r.state.to_string();
        let next_action = r.next_action.to_string();
        let classification = "";
        let next_action_check = ();
        
        // Check next_action first (applies regardless of trust_mode).
        // Skip ONLY when the cell is a single word that is none / None / <skip> / empty.
        // Multi-word cells ("None — every row is Done") or any other content must be
        // verified: the Next Action column still has descriptive content that owes
        // a tracking or doc-sync issue.
        let na_trimmed = next_action;
        // Strip leading/trailing whitespace
        let j2 = 0;
        let nlen2 = na_trimmed.len();
        while j2 < nlen2 && na_trimmed.sub_string(j2, 1) == " " { j2 += 1; }
        let j3 = nlen2 - 1;
        while j3 >= j2 && na_trimmed.sub_string(j3, 1) == " " { j3 -= 1; }
        let na_clean = if j3 >= j2 { na_trimmed.sub_string(j2, j3 - j2 + 1) } else { "" };
        let na_words = 0;
        if na_clean != "" { na_words = 1; }
        let k = 0;
        while k < na_clean.len() {
            if na_clean.sub_string(k, 1) == " " { na_words += 1; }
            k += 1;
        }
        let na_lower_exact = na_clean == "none" || na_clean == "None" || na_clean == "NONE" || na_clean == "<skip>" || na_clean == "";
        if na_lower_exact {
            classification = "skip_next_action";
        } else {
            // Next Action has descriptive content — needs verification regardless of state/trust
            next_action_check = #{
                action_text: r.next_action,
                needs_verification: true
            };
        }
        
        // State-based classification (provisional — Phase 4 determines final verdict)
        if classification == "" {
            if row_state == "Done" {
                if trust_mode == "trust" {
                    if next_action_check != () {
                        // Done + trust + Next Action content: verifier must check the
                        // Next Action action (next_action_complete or next_action_pending).
                        // State itself is accepted at face value.
                        classification = "next_action_check";
                    } else {
                        classification = "skip";
                    }
                } else {
                    if next_action_check != () {
                        classification = "unverified_with_next_action";
                    } else {
                        classification = "unverified";
                    }
                }
            } else if row_state == "Ready" || row_state == "In Progress" || row_state == "In Review" {
                classification = "incomplete";
            } else {
                classification = "incomplete";  // Default for unknown states
            }
        }
        
        classified_rows.push(#{
            row: r,
            classification: classification,
            next_action_check: next_action_check,
            evidence: r.row_text
        });
    }
    
    // Roll-up classification for this feature
    let feature_rollup = ();
    for rup in rollups {
        if rup.feature == g.name {
            feature_rollup = rup.row;
            break;
        }
    }
    
    // Compute effective state from backlog rows
    let effective_state = "Done";
    for r in feature_rows {
        let rs = r.state.to_string();
        if rs == "In Progress" {
            effective_state = "In Progress";
            break;
        } else if rs == "In Review" && effective_state != "In Progress" {
            effective_state = "In Review";
        } else if rs == "Ready" && effective_state == "Done" {
            effective_state = "Ready";
        }
    }
    
    // Extract claimed state from rollup row (simplified - would need parsing)
    let claimed_state = "Done";  // Placeholder - would parse from rollup_row
    
    let rollup_verdict = "match";
    if claimed_state == "Done" && effective_state != "Done" {
        rollup_verdict = "rollup_mismatch";
    } else if (claimed_state == "In Progress" || claimed_state == "In Review") && effective_state == "Done" {
        rollup_verdict = "rollup_mismatch";  // Under-claimed
    }
    
    rollup_classifications.push(#{
        feature: g.name,
        claimed: claimed_state,
        effective: effective_state,
        verdict: rollup_verdict,
        offending_rows: feature_rows
    });
}

log("classified " + classified_rows.len().to_string() + " rows with trust_mode=" + trust_mode);

// --- Phase 4: Verify (one subagent per feature, zero-trust) ---
// No row is exempt: Done rows are proof demands, the roll-up is reconciled
// against each feature's effective state, and FR orphans are flagged in both directions.
phase("Verify");
let verdicts = [];

// Build all verifier jobs first, then fan out in parallel (Engine Fix 2).
// The previous sequential `for g in groups { agent(...) }` serialized 12+
// verifier LLM calls; parallel matches the Scan phase pattern.
let verify_jobs = [];
for g in groups {
    // Build feature-specific classified rows for the verifier
    let feature_classified = [];
    for cr in classified_rows {
        if cr.row.feature == g.name {
            feature_classified.push(cr);
        }
    }
    
    let vp = "Verify the feature \"" + g.name + "\" against ACTUAL CODE ONLY. Trust mode: " + trust_mode + ". "
        + "In 'no-trust' mode, Done rows are proof demands and must be verified against source code; "
        + "in 'trust' mode, Done rows are accepted at face value for STATE only. "
        + "BOTH MODES: for ANY row whose Next Action cell contains descriptive text "
        + "(not none, not <skip>, not empty), you MUST check whether that action is already "
        + "implemented in code + tests. If yes → verdict next_action_complete (set Next Action to none). "
        + "If no → verdict next_action_pending (implement the action, then set Next Action to done). "
        + "This applies to Done rows under trust mode as well — trust mode only skips STATE verification, "
        + "never Next Action verification. "
        + "The only evidence that counts is the source code and test files in the feature's own tree. "
        + "For every row in the feature's BACKLOG: "
        + "(1) Read the row's item text and its Actual Condition cell. "
        + "(2) Open the files under " + g.dir + "/src/ and " + g.dir + "/tests/ that the row's description refers to "
        + "(use the FR id, the row title, and the described behavior to locate them). "
        + "(3) Confirm the described behavior is actually implemented in the current code: "
        + "the function/class/flag/config exists, the logic matches the claim, and at least one test exercises it. "
        + "A row claiming Done passes only if all three proofs are present in its Actual Condition cell: "
        + "(1) the exact verification command, (2) its pass/fail result, (3) the implementing commit SHA — "
        + "and the code and tests you just read prove the behavior. "
        + "A hash in the row's evidence cell is NOT proof; a merged-PR number is NOT proof. "
        + "A row claiming a shipped release additionally requires release evidence: run "
        + "gh release view <tag> (in the tracked repo, gh release view v6.4.0) and confirm it reports a "
        + "published release; a tag cited in the doc is a claim, the command output is the proof. "
        + "If the code does not implement what the row claims, verdict is \"unverified\" and the evidence field "
        + "names the specific file and the missing or wrong behavior. "
        + "For tracking-issue dedupe: gh issue list --state open --search \"<row id> in:title\" --json number,title "
        + "(an open issue makes the verdict \"exists\"; nothing open makes it \"open\"). "
        + "Roll-up reconciliation: recompute the feature's effective state from its backlog rows — worst state "
        + "wins, ranked In Progress > In Review > Ready > Done; any non-Done row makes the feature non-Done. "
        + "If the roadmap roll-up claims Done while the effective state is less, verdict "
        + "\"rollup_mismatch\" for the roll-up row. "
        + "Legacy state names (Idea, Refinement, Blocked, QA, Released, Deferred) are mapped to the simplified "
        + "four: Idea/Refinement/Blocked/Deferred to Ready or In Progress when work started; QA to In Review; "
        + "Released to Done (plus release evidence: gh release view <tag> reports a published release). "
        + "FR orphan check: every FR id declared in the FRD must be cited by at least one backlog row and "
        + "vice versa; either direction failing is verdict \"fr_orphan\" for that FR id. "
        + "NEXT ACTION VERIFICATION: For rows with next_action_check.needs_verification == true, "
        + "check if the action described in next_action_check.action_text is already implemented in code/tests. "
        + "  - If the action is ALREADY COMPLETE (code + test exist): verdict is \"next_action_complete\" with "
        + "    closing_condition to update the row's Next Action to \"none\". "
        + "  - If the action is NOT COMPLETE: verdict is \"next_action_pending\" with "
        + "    closing_condition to implement the action and set Next Action to \"done\". "
        + "Verdicts per row: open (code does not implement the work, no open issue tracks it) | "
        + "exists (an open issue #N already tracks this row — cite the issue number) | "
        + "doc_sync (code implements the work but the doc still reports an incomplete state) | "
        + "unverified (Done claim whose code evidence is absent or does not match the claim) | "
        + "skip (Done with code evidence that fully confirms it — the only skip path) | "
        + "fr_orphan | next_action_complete | next_action_pending | skip_next_action. "
        + "Cite the file paths and line ranges you read in the evidence field. "
        + "CRITICAL: every verdict object MUST include a non-empty closing_condition field — "
        + "the exact observable check whose fulfillment advances the row to Done. "
        + "Format it as one line: '<file paths> implement <behavior>, exercised by <test path>; "
        + "<test command> passes → set row <row-id> State to Done in <source-doc>, evidence cell "
        + "rewritten to commit SHA + command output'. The <source-doc> path is mandatory — the issuer "
        + "prints it into the body's Source line and Advance. "
        + "For open: the implementation path + test file + verification command that proves the work. "
        + "For doc_sync: the exact doc edit (file, cell, new state value) that aligns the doc with reality. "
        + "For unverified: the code change + test that closes the failed verification check. "
        + "For rollup_mismatch: which side to correct (advance backlog rows or lower roll-up) and the evidence. "
        + "For fr_orphan: the backlog row to add that cites the orphan FR, and the state it takes. "
        + "For next_action_complete: the doc edit to set Next Action to 'none' in <source-doc>. "
        + "For next_action_pending: the implementation path + test file + verification command for the action, "
        + "then doc edit to set Next Action to 'done' in <source-doc>. "
        + "Closing condition is a check, never a status: no 'should be done', only paths, behavior, and a command. "
        + "No writes, no issue creation.";
    verify_jobs.push(#{
        prompt: vp,
        label: "verify:" + g.name,
        capability_mode: "read-only",
        output_schema: verdict_schema,
        _feature_name: g.name,
    });
}
let verify_results = parallel(verify_jobs);
for vr in verify_results {
    let res = vr;
    if res != () && res.success && res.output != () {
        let gname = res._feature_name;
        let got_verdicts = if type_of(res.output.verdicts) == "array" { res.output.verdicts } else { [] };
        for v in got_verdicts {
            v.feature = gname;
            verdicts.push(v);
        }
        let got_rollups = if type_of(res.output.rollup_verdicts) == "array" { res.output.rollup_verdicts } else { [] };
        for rv in got_rollups {
            rv.kind = "rollup";
            if rv.row == () { rv.row = rv.feature + " roll-up"; }
            verdicts.push(rv);
        }
    }
}
log("verified " + verdicts.len().to_string() + " verdicts across " + groups.len().to_string() + " features");

// --- Phase 4: Issue (modular, batched, dry-run default) ---
phase("Issue");

// Core invariant: every actionable verdict must carry a closing_condition that can
// advance its row to Done. A verdict without one is a structural gap (pending-infra):
// it is reported against the invariant, never issued.
let missing_cc = 0;
let pending_infra = [];
for v in verdicts {
    let is_skip_verdict = v.verdict == "skip" || v.verdict == "skip_next_action";
    if !is_skip_verdict && (v.closing_condition == () || v.closing_condition == "") {
        missing_cc += 1;
        let bad_row = if v.row != () { v.row } else { "roll-up" };
        pending_infra.push(bad_row);
        log("WARNING: row " + bad_row + " has no closing_condition — pending-infra: cannot advance to Done");
    }
}

let actionable = [];
for v in verdicts {
    let is_actionable = v.verdict == "open" || v.verdict == "doc_sync" || v.verdict == "unverified"
        || v.verdict == "rollup_mismatch" || v.verdict == "fr_orphan" || v.verdict == "exists"
        || v.verdict == "next_action_complete" || v.verdict == "next_action_pending";
    if is_actionable {
        if v.closing_condition != () && v.closing_condition != "" {
            actionable.push(v);
        }
    }
}
let created = [];
let total_ibatches = (actionable.len() + batch - 1) / batch;
for t in 0..total_ibatches {
    let lo = t * batch;
    let hi = lo + batch;
    if hi > actionable.len() { hi = actionable.len(); }
    let row_list = "";
    for u in lo..hi {
        let entry = actionable[u];
        let row_id = if entry.row != () { entry.row } else { entry.feature + " roll-up" };
        row_list += row_id + " (" + entry.verdict + ": " + entry.evidence
            + ", closing_condition: " + entry.closing_condition + "), ";
    }
    row_list = row_list.sub_string(0, row_list.len() - 2);
    let dry_word = if dry_run {
        "DRY RUN: print each would-be issue (title, body including its Closing condition, labels) without calling gh issue create."
    } else {
        "Create each issue with gh issue create."
    };
    let ip = "You are an issuer. In " + repo_root + ", handle these verdicts: " + row_list + ". "
        + "For verdict open: create one modular issue titled [<feature>] <row id> — <task summary> "
        + "(root rows use [BACKLOG]). "
        + "For verdict doc_sync: title [DOC-SYNC] <row id> — <doc path> still reports <state>. "
        + "For verdict unverified: title [DOC-SYNC] <row id> — <state> claimed but evidence failed: <check>. "
        + "For verdict rollup_mismatch: title [DOC-SYNC] <feature> roll-up — claims <state>, backlog says "
        + "<effective state>. "
        + "For verdict fr_orphan: title [DOC-SYNC] <feature> FR <fr id> — has no backlog row. "
        + "Body per SKILL.md: field table, verbatim task, verbatim evidence, Verification section with the "
        + "exact commands run, Roll-up check section, a '## Closing condition' section, and the 'Tracking only' "
        + "footer. Build that section three fields: **Check:** the closing_condition verbatim (it names the "
        + "paths, behavior, test command, and source doc); **Advance:** when the check passes, set the row "
        + "State to Done in the source doc named in the Check and write commit SHA + command output into its "
        + "evidence cell — every FR ID the row cites advances with it; **Proof:** close with commit link + "
        + "command output, no proof no close. "
        + "A created issue with no Closing condition section is a violation — do not emit it. "
        + "Labels: " + state_label + ", state:<state>, p0/p1/p2, plus doc-sync for doc_sync/unverified/"
        + "rollup_mismatch, and fr_orphan classes. No other labels — the four title formats and this label set are the whole vocabulary. "
        + "For verdict exists: append a freshness comment to the recorded issue that restates its closing "
        + "condition — the check and the Done advance — action commented. "
        + "Return {row, action, url, number, closing_condition} per row, closing_condition copied from the "
        + "body's Check. No branch, no PR, no code edit, no file write. "
        + dry_word;
    let res = agent(ip, #{
        label: "issue-batch-" + (t + 1),
        capability_mode: if dry_run { "read-only" } else { "execute" },
        output_schema: issue_schema,
    });
    if res != () && res.success && res.output.results != () {
        for rr in res.output.results { created.push(rr); }
    }
}

let created_count = created.len();
let mode_str = if dry_run { "dry-run" } else { "live" };
// Invariant check: count issued rows that carry a closing_condition
let cc_issued = 0;
for c in created {
    if c.closing_condition != () && c.closing_condition != "" { cc_issued += 1; }
}
let invariant_ok = (cc_issued == created_count) && (missing_cc == 0);
let inv_str = if invariant_ok { "true" } else { "false" };
let complete_msg = "rows scanned: " + all_rows.len().to_string()
    + " | verdicts: " + verdicts.len().to_string()
    + " | actionable: " + actionable.len().to_string()
    + " | issued: " + created_count.to_string()
    + " | with_closing_condition: " + cc_issued.to_string()
    + " | missing_closing_condition: " + missing_cc.to_string()
    + " | pending_infra: " + pending_infra.len().to_string()
    + " | invariant_ok: " + inv_str
    + " | mode: " + mode_str;
log(complete_msg);
complete(#{
    summary: complete_msg,
    features: features,
    rows_scanned: all_rows.len(),
    verdicts: verdicts,
    issued: created,
    with_closing_condition: cc_issued,
    missing_closing_condition: missing_cc,
    pending_infra: pending_infra,
    invariant_ok: inv_str,
    mode: mode_str,
});
