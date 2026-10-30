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

// Aggregated ScanOutput emitted by scan.py (the script path's scan host call).
let scan_out_schema = #{
    "type": "object", "required": ["rows"],
    "properties": #{
        "docs": #{ "type": "array" },
        "rows": #{
            "type": "array",
            "items": #{
                "type": "object",
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
                    "feature": #{ "type": "string" },
                    "updated": #{ "type": "string" },
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
        "warnings": #{ "type": "array", "items": #{ "type": "string" } },
    },
};

// ClassifiedOutput emitted by classify.py (the script path's classify host call).
let classify_out_schema = #{
    "type": "object", "required": ["rows"],
    "properties": #{
        "rows": #{
            "type": "array",
            "items": #{
                "type": "object",
                "properties": #{
                    "row_id": #{ "type": "string" },
                    "feature": #{ "type": "string" },
                    "classification": #{ "type": "string" },
                    "next_action_check": #{ "type": ["object", "null"] },
                    "effective_state": #{ "type": "string" },
                    "staleness_flag": #{ "type": "boolean" },
                    "closing_condition": #{ "type": ["string", "null"] },
                },
            },
        },
        "fr_orphans": #{
            "type": "array",
            "items": #{
                "type": "object",
                "properties": #{
                    "fr_id": #{ "type": "string" },
                    "feature": #{ "type": "string" },
                    "direction": #{ "type": "string" },
                    "target_doc": #{ "type": "string" },
                    "closing_condition": #{ "type": ["string", "null"] },
                },
            },
        },
        "rollup_mismatches": #{
            "type": "array",
            "items": #{
                "type": "object",
                "properties": #{
                    "feature": #{ "type": "string" },
                    "claimed": #{ "type": "string" },
                    "effective": #{ "type": "string" },
                    "verdict": #{ "type": "string" },
                    "closing_condition": #{ "type": ["string", "null"] },
                },
            },
        },
        "staleness_flags": #{ "type": "array" },
        "trust_mode": #{ "type": "string" },
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

// args: { repo_root (required), dry_run (optional), batch (optional), trust_mode (optional: "trust" | "no-trust", default "no-trust"),
//         legacy (optional, default false — the rollback escape: old per-feature LLM scanner + inline Rhai classify),
//         scripts_root (optional — directory holding scan.py/classify.py; default <repo_root>/skills/git/task-tracker/scripts) }
let a_root = ();
let a_dry = ();
let a_batch = ();
let a_trust = ();
let a_legacy = ();
let a_scripts = ();
if type_of(args) == "map" {
    a_root = args.repo_root;
    a_dry = args.dry_run;
    a_batch = args.batch;
    a_trust = args.trust_mode;
    a_legacy = args.legacy;
    a_scripts = args.scripts_root;
} else if type_of(args) == "string" {
    a_root = json_text_field(args, "repo_root");
    a_dry = json_text_field(args, "dry_run");
    a_batch = json_text_field(args, "batch");
    a_trust = json_text_field(args, "trust_mode");
    a_legacy = json_text_field(args, "legacy");
    a_scripts = json_text_field(args, "scripts_root");
}
if a_root == () { pause("verification", "Pass args.repo_root — the absolute path to the AES repo to track."); }
let repo_root = a_root.to_string();
let dry_run = if a_dry == () { false } else { a_dry.to_string() == "true" || a_dry.to_string() == "1" };
let legacy = if a_legacy == () { false } else { a_legacy.to_string() == "true" || a_legacy.to_string() == "1" };
let trust_mode = if a_trust == () { "no-trust" } else { a_trust.to_string() };
if trust_mode != "trust" && trust_mode != "no-trust" {
    pause("verification", "Invalid trust_mode: " + trust_mode + " — must be 'trust' or 'no-trust'");
}
let scripts_root = if a_scripts == () { repo_root + "/skills/git/task-tracker/scripts" } else { a_scripts.to_string() };
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

// --- Phase 2: Scan ---
// Default (script) path: a single host-call agent runs scan.py over the Discover
// output — deterministic markdown parsing, no per-feature LLM scanner subagent.
// --legacy (the rollback escape, see SKILL.md Rollout): the old one-scanner-per-
// feature LLM fan-out plus the inline Rhai classify, retained verbatim.
// Script failure pauses the run with the stderr report — no silent fallback.
phase("Scan");
let groups = [];
for f in features {
    groups.push(#{ name: f.name, dir: f.dir, docs: f.docs });
}
groups.push(#{ name: "root", dir: ".", docs: root_docs });

let all_rows = [];
let fr_sets = [];
let rollups = [];
let scan_out = ();

if legacy {
    // Legacy LLM scanner path: one read-only subagent per feature group. Each
    // scanner owns the feature's FR-id set and its roadmap roll-up row, so the
    // FR ↔ backlog orphan check has all its inputs in one agent's context.
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
} else {
    // Script path: one host-call agent runs the deterministic scanner. The
    // workflow engine's host-call mechanism is agent() (sibling convention:
    // prune-test-suite / work-on-issues have no shell host primitive); the
    // agent only transports the script's stdout — all table parsing is done
    // by scan.py, not by the model. The discovery JSON (the Discover phase's
    // feature_schema output) is written to a temp file first, as scan.py's
    // --discovery input.
    let discovery_obj = #{ root: root_docs, features: features };
    let scan_script = scripts_root + "/scan.py";
    let sp = "Run exactly these two steps with your terminal tool, nothing else:\n"
        + "1) Write this discovery JSON to a temp file: "
        + "python3 - <<'EOF'\nimport json\nd = " + json_encode(discovery_obj) + "\nopen('/tmp/task-tracker-discovery.json','w').write(json.dumps(d))\nEOF\n"
        + "2) Run the deterministic scanner: python3 " + scan_script
        + " --repo-root " + repo_root + " --discovery /tmp/task-tracker-discovery.json\n"
        + "Return the scanner's stdout — the ScanOutput JSON object — unmodified, as your structured answer. "
        + "Do not add, remove, or reorder fields; do not re-derive the tables yourself; do not read the spec "
        + "docs directly. If the scanner exits non-zero, do NOT fabricate output: say SCAN-FAIL and quote "
        + "the stderr. No repo edits, no other commands.";
    let scan_host = agent(sp, #{
        label: "scan-host",
        capability_mode: "execute",
        output_schema: scan_out_schema,
    });
    let scan_host_out = if scan_host != () && scan_host.success && scan_host.output != () { scan_host.output } else { () };
    if scan_host_out == () {
        // Agent-level failure (infra) or a non-zero script exit that the schema
        // rejected. No silent fallback to the LLM scanner: the operator must
        // see the failure and decide (fix scan.py, or relaunch with legacy: true).
        let detail = if scan_host != () && scan_host.success == false { "agent failed: " + scan_host.to_string() } else { "no output (script exited non-zero or agent dropped)" };
        pause("verification", "scan.py failed — the script path does not fall back to the LLM scanner ("
            + detail + "). Fix the scanner or relaunch with legacy: true, then resume.");
    }
    let rows_out = if type_of(scan_host_out.rows) == "array" { scan_host_out.rows } else { [] };
    for r in rows_out {
        r.class = "pending";
        all_rows.push(r);
    }
    let fr_out = if type_of(scan_host_out.fr) == "map" { scan_host_out.fr } else { #{ fr_declared: [], fr_referenced: [] } };
    fr_sets.push(#{
        feature: "scan",
        fr_declared: if fr_out.fr_declared != () { fr_out.fr_declared } else { [] },
        fr_referenced: if fr_out.fr_referenced != () { fr_out.fr_referenced } else { [] },
    });
    if type_of(scan_host_out.rollup_row) == "string" && scan_host_out.rollup_row != "" {
        rollups.push(#{ feature: "root", row: scan_host_out.rollup_row });
    }
    scan_out = scan_host_out;
}
log("scanned " + all_rows.len().to_string() + " rows across " + groups.len().to_string() + " feature groups");

// --- Phase 3: Classify ---
// Default (script) path: classify.py produces the deterministic pre-verifier
// buckets (state classification, Next Action word-count rule, effective
// state, FR orphans, roll-up mismatches, staleness flags) in one host call.
// --legacy retains the inline Rhai bucketing (the rollback escape).
phase("Classify");
let classified_rows = [];
let rollup_classifications = [];
let fr_orphan_findings = [];
let classify_obj = ();
if legacy {
    for g in groups {
        // Filter rows for this feature
        let feature_rows = [];
        for r in all_rows {
            if r.feature == g.name {
                feature_rows.push(r);
            }
        }

        // Classify each row based on trust_mode
        for r in feature_rows {
            let row_state = r.state.to_string().to_lowercase();
            let next_action = r.next_action.to_string().to_lowercase();
            let classification = "";
            let next_action_check = ();

            // Check next_action first (applies regardless of trust_mode)
            if next_action.contains("none") || next_action.contains("<skip>") {
                classification = "skip_next_action";
            } else if next_action != "" && next_action != "none" && next_action != "<skip>" {
                // Has a next action item
                next_action_check = #{
                    action_text: r.next_action,
                    needs_verification: true
                };
            }

            // Apply trust_mode for Done rows
            if row_state == "done" {
                if trust_mode == "trust" {
                    if classification == "" {
                        classification = "skip";
                    }
                } else {
                    // no-trust mode: Done rows need verification
                    if classification == "" {
                        classification = "unverified";  // Default for Done in no-trust mode
                    }
                }
            } else if classification == "" {
                // Non-Done rows
                if row_state == "ready" || row_state == "in progress" || row_state == "in review" {
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
            let rs = r.state.to_string().to_lowercase();
            if rs == "in progress" {
                effective_state = "In Progress";
                break;
            } else if rs == "in review" && effective_state != "In Progress" {
                effective_state = "In Review";
            } else if rs == "ready" && effective_state == "Done" {
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
} else {
    // Script path: one host-call agent runs classify.py over the scan JSON.
    // classify.py applies the doc-determinable part of the classification
    // table (including the Next Action word-count skip rule and the
    // effective-state / FR-orphan / roll-up checks); the LLM verifier owns
    // the judgment verdicts that follow. --trust-mode feeds the existing
    // trust_mode argument.
    // classify.py consumes the full scan JSON (rows + fr sets + rollup row)
    // as a file; bridge it via the same host-call transport (temp file,
    // script stdout relay) the Scan phase used.
    let classify_script = scripts_root + "/classify.py";
    let cp = "Run exactly these two steps with your terminal tool, nothing else:\n"
        + "1) Write this scan JSON to a temp file: "
        + "python3 - <<'EOF'\nimport json\nd = " + json_encode(scan_out) + "\nopen('/tmp/task-tracker-scan.json','w').write(json.dumps(d))\nEOF\n"
        + "2) Run the deterministic classifier: python3 " + classify_script
        + " --repo-root " + repo_root
        + " --scan-out /tmp/task-tracker-scan.json"
        + " --trust-mode " + trust_mode + "\n"
        + "Return the classifier's stdout — the classified JSON object — unmodified, as your structured answer. "
        + "Do not add, remove, or reorder fields; do not re-derive the buckets yourself. "
        + "If the classifier exits non-zero, do NOT fabricate output: say CLASSIFY-FAIL and quote the stderr. "
        + "No repo edits, no other commands.";
    let classify_host = agent(cp, #{
        label: "classify-host",
        capability_mode: "execute",
        output_schema: classify_out_schema,
    });
    classify_obj = if classify_host != () && classify_host.success && classify_host.output != () { classify_host.output } else { () };
    if classify_obj == () {
        let detail = if classify_host != () && classify_host.success == false { "agent failed: " + classify_host.to_string() } else { "no output (classifier exited non-zero or agent dropped)" };
        pause("verification", "classify.py failed — the script path does not fall back to inline Rhai classify ("
            + detail + "). Fix the classifier or relaunch with legacy: true, then resume.");
    }

    // Unify the classify.py output into the same classified_rows shape the
    // Verify phase consumes, so the verifier prompt is path-agnostic.
    let crows = if type_of(classify_obj.rows) == "array" { classify_obj.rows } else { [] };
    for cr in crows {
        // Find the matching scan row (by row_id) to attach source_doc/row_text.
        let matched_row = ();
        for r in all_rows {
            if r.id == cr.row_id {
                matched_row = r;
                break;
            }
        }
        let base_row = if matched_row != () { matched_row } else { #{
            id: cr.row_id,
            feature: cr.feature,
            state: "unknown",
            source_doc: "",
            row_text: "",
            next_action: "",
        } };
        classified_rows.push(#{
            row: base_row,
            classification: cr.classification,
            next_action_check: cr.next_action_check,
            evidence: if base_row.row_text != () && base_row.row_text != "" { base_row.row_text } else { cr.row_id },
            effective_state: cr.effective_state,
            staleness_flag: cr.staleness_flag,
            closing_condition: cr.closing_condition,
        });
    }
    let c_fr = if type_of(classify_obj.fr_orphans) == "array" { classify_obj.fr_orphans } else { [] };
    for fo in c_fr {
        fr_orphan_findings.push(#{
            feature: fo.feature,
            fr_id: fo.fr_id,
            direction: fo.direction,
            target_doc: fo.target_doc,
            closing_condition: fo.closing_condition,
        });
    }
    let c_rollups = if type_of(classify_obj.rollup_mismatches) == "array" { classify_obj.rollup_mismatches } else { [] };
    for rm in c_rollups {
        rollup_classifications.push(#{
            feature: rm.feature,
            claimed: rm.claimed,
            effective: rm.effective,
            verdict: rm.verdict,
            closing_condition: rm.closing_condition,
        });
    }
}
log("classified " + classified_rows.len().to_string() + " rows with trust_mode=" + trust_mode);

// --- Run-report phase 1 (Classify) ---
// docs/task-tracker-report.json is written in two phases (the §validate.py
// design): this Classify-phase write creates it with the count-table fields
// plus actionable_verdict_count; the Issue phase finalizes it with
// pending_infra + invariant_ok. A half-written file is a legitimate
// intermediate state that validate.py tolerates.
let n_incomplete = 0;
let n_doc_sync = 0;
let n_unverified = 0;
let n_fr_orphan = fr_orphan_findings.len();
let n_skipped = 0;
let n_closing_conditions = 0;
let actionable_verdict_count = 0;
for cr in classified_rows {
    let cls = cr.classification.to_string();
    let cc = cr.closing_condition;
    let has_cc = cc != () && cc != "" && cc != "—";
    if has_cc { n_closing_conditions += 1; }
    if cls == "incomplete" || cls == "next_action_pending" || cls == "next_action_complete" {
        n_incomplete += 1;
        // Classify-time actionable count: the deterministic verdicts that map
        // into the actionable set (open/doc_sync/unverified/rollup_mismatch/
        // fr_orphan/exists/next_action_complete/next_action_pending) with a
        // non-empty closing condition. fr_orphan/rollup_mismatch closing
        // conditions are verifier-owned (null at this stage), so only
        // doc-determinable rows count here; the Issue phase re-counts from
        // the final verdicts and overwrites this field.
        if has_cc { actionable_verdict_count += 1; }
    } else if cls == "doc_sync" {
        n_doc_sync += 1;
        if has_cc { actionable_verdict_count += 1; }
    } else if cls == "unverified" || cls == "proof_demand" || cls == "unverified_with_next_action" {
        n_unverified += 1;
        if has_cc { actionable_verdict_count += 1; }
    } else if cls == "skip" || cls == "skip_next_action" {
        n_skipped += 1;
    }
}
let report_phase1 = #{
    rows_scanned: all_rows.len(),
    incomplete: n_incomplete,
    doc_sync: n_doc_sync,
    unverified: n_unverified,
    fr_orphan: n_fr_orphan,
    skipped: n_skipped,
    created: 0,
    commented: 0,
    rollup_mismatches: rollup_classifications.len(),
    closing_conditions: n_closing_conditions,
    actionable_verdict_count: actionable_verdict_count,
};
let report_path = repo_root + "/docs/task-tracker-report.json";
let rp1_prompt = "Write this exact JSON to " + report_path + " (create docs/ if it does not exist, "
    + "replacing any existing file). No other file writes. The JSON, verbatim:\n"
    + json_encode(report_phase1);
agent(rp1_prompt, #{ label: "report-phase1", capability_mode: "execute" });
log("run-report phase 1 written to " + report_path + " (actionable_verdict_count=" + actionable_verdict_count.to_string() + ")");

// --- Phase 4: Verify (one subagent per feature, zero-trust) ---
// No row is exempt: Done rows are proof demands, the roll-up is reconciled
// against each feature's effective state, and FR orphans are flagged in both directions.
phase("Verify");
let verdicts = [];
let verify_jobs = [];
for g in groups {
    // Build feature-specific classified data for the verifier. Both paths
    // (legacy inline Rhai and classify.py) land in classified_rows; the
    // verifier consumes the same shape regardless of which ran.
    let feature_classified = [];
    for cr in classified_rows {
        if cr.row.feature == g.name {
            feature_classified.push(cr);
        }
    }
    let feature_orphans = [];
    for fo in fr_orphan_findings {
        if fo.feature == g.name {
            feature_orphans.push(fo);
        }
    }
    let feature_rollups = [];
    for rc in rollup_classifications {
        if rc.feature == g.name {
            feature_rollups.push(rc);
        }
    }
    let feature_payload = json_encode(#{
        classified_rows: feature_classified,
        fr_orphans: feature_orphans,
        rollup_classifications: feature_rollups,
    });

    let vp = "Verify the feature \"" + g.name + "\" against ACTUAL CODE ONLY. Trust mode: " + trust_mode + ". "
        + "In 'trust' mode: all Done rows are pre-classified as 'skip' and should not be re-verified. "
        + "In 'no-trust' mode: Done rows are proof demands and must be verified against source code. "
        + "The only evidence that counts is the source code and test files in the feature's own tree. "
        + "You receive pre-classified data below (deterministic buckets, FR-orphan findings, and roll-up "
        + "reconciliations computed before verification) — trust its classifications only as starting "
        + "points; confirm every claim against live code before emitting a verdict. ";
    vp += "PRE-CLASSIFIED DATA (JSON): " + feature_payload + " ";
    vp += "For every row in the feature's BACKLOG: "
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
        + "published release; a tag cited in the doc is a claim, the command output is the proof. ";
    vp += "If the code does not implement what the row claims, verdict is \"unverified\" and the evidence field "
        + "names the specific file and the missing or wrong behavior. "
        + "For tracking-issue dedupe: gh issue list --state open --search \"<row id> in:title\" --json number,title "
        + "(an open issue makes the verdict \"exists\"; nothing open makes it \"open\"). "
        + "Roll-up reconciliation: recompute the feature's effective state from its backlog rows — worst state "
        + "wins, ranked In Progress > In Review > Ready > Done; any non-Done row makes the feature non-Done. "
        + "If the roadmap roll-up claims Done while the effective state is less, verdict "
        + "\"rollup_mismatch\" for the roll-up row. ";
    vp += "Legacy state names (Idea, Refinement, Blocked, QA, Released, Deferred) are mapped to the simplified "
        + "four: Idea/Refinement/Blocked/Deferred to Ready or In Progress when work started; QA to In Review; "
        + "Released to Done (plus release evidence: gh release view <tag> reports a published release). "
        + "FR orphan check: every FR id declared in the FRD must be cited by at least one backlog row and "
        + "vice versa; either direction failing is verdict \"fr_orphan\" for that FR id. ";
    vp += "NEXT ACTION VERIFICATION: For rows with next_action_check.needs_verification == true, "
        + "check if the action described in next_action_check.action_text is already implemented in code/tests. "
        + "  - If the action is ALREADY COMPLETE (code + test exist): verdict is \"next_action_complete\" with "
        + "    closing_condition to update the row's Next Action to \"none\". "
        + "  - If the action is NOT COMPLETE: verdict is \"next_action_pending\" with "
        + "    closing_condition to implement the action and set Next Action to \"done\". ";
    vp += "Verdicts per row: open (code does not implement the work, no open issue tracks it) | "
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
        + "prints it into the body's Source line and Advance. ";
    vp += "For open: the implementation path + test file + verification command that proves the work. "
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
    });
}
// Run the verify jobs in waves of `batch` so the panel never exceeds the
// configured concurrency while still parallelizing across features.
let wave_no = 0;
let wave_start = 0;
while wave_start < verify_jobs.len() {
    let take = if verify_jobs.len() - wave_start < batch { verify_jobs.len() - wave_start } else { batch };
    let wave_jobs = verify_jobs.extract(wave_start, take);
    let res = parallel(wave_jobs);
    // Job indices within the wave map positionally onto groups (same
    // convention as the Scan phase), so the feature name comes from the
    // group, not from a field on the result.
    let wi = 0;
    let res_list = if type_of(res) == "array" { res } else { [] };
    for r in res_list {
        let gname = groups[wave_start + wi].name;
        if r != () && r.success && r.output != () {
            let got_verdicts = if type_of(r.output.verdicts) == "array" { r.output.verdicts } else { [] };
            for v in got_verdicts {
                v.feature = gname;
                verdicts.push(v);
            }
            let got_rollups = if type_of(r.output.rollup_verdicts) == "array" { r.output.rollup_verdicts } else { [] };
            for rv in got_rollups {
                rv.kind = "rollup";
                if rv.row == () { rv.row = rv.feature + " roll-up"; }
                verdicts.push(rv);
            }
        }
        wi += 1;
    }
    wave_start += take;
    wave_no += 1;
}
log("verified " + verdicts.len().to_string() + " verdicts across " + groups.len().to_string() + " features in " + wave_no.to_string() + " wave(s) of <= " + batch.to_string());

// --- Phase 5: Issue (modular, batched, dry-run default) ---
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
// Parallel issue fan-out (Engine Fix 2): all batch jobs are built up front and
// fanned out with parallel(), at most `batch` at a time (the `--batch`
// argument is the wave size, matching the Scan/Verify panels).
let created = [];
let total_ibatches = (actionable.len() + batch - 1) / batch;
let issue_jobs = [];
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
        + "(root rows use [BACKLOG]). ";
    ip += "For verdict doc_sync: title [DOC-SYNC] <row id> — <doc path> still reports <state>. "
        + "For verdict unverified: title [DOC-SYNC] <row id> — <state> claimed but evidence failed: <check>. "
        + "For verdict rollup_mismatch: title [DOC-SYNC] <feature> roll-up — claims <state>, backlog says "
        + "<effective state>. "
        + "For verdict fr_orphan: title [DOC-SYNC] <feature> FR <fr id> — has no backlog row. ";
    ip += "Body per SKILL.md: field table, verbatim task, verbatim evidence, Verification section with the "
        + "exact commands run, Roll-up check section, a '## Closing condition' section, and the 'Tracking only' "
        + "footer. Build that section three fields: **Check:** the closing_condition verbatim (it names the "
        + "paths, behavior, test command, and source doc); **Advance:** when the check passes, set the row "
        + "State to Done in the source doc named in the Check and write commit SHA + command output into its "
        + "evidence cell — every FR ID the row cites advances with it; **Proof:** close with commit link + "
        + "command output, no proof no close. "
        + "A created issue with no Closing condition section is a violation — do not emit it. ";
    ip += "Labels: " + state_label + ", state:<state>, p0/p1/p2, plus doc-sync for doc_sync/unverified/"
        + "rollup_mismatch, and fr_orphan classes. No other labels — the four title formats and this label set are the whole vocabulary. "
        + "For verdict exists: append a freshness comment to the recorded issue that restates its closing "
        + "condition — the check and the Done advance — action commented. "
        + "Return {row, action, url, number, closing_condition} per row, closing_condition copied from the "
        + "body's Check. No branch, no PR, no code edit, no file write. "
        + dry_word;
    issue_jobs.push(#{
        prompt: ip,
        label: "issue-batch-" + (t + 1),
        capability_mode: if dry_run { "read-only" } else { "execute" },
        output_schema: issue_schema,
    });
}
// Run the batch jobs in waves of `batch` so the panel never exceeds the
// configured concurrency while still parallelizing across batches.
let wave_no = 0;
let wave_start = 0;
while wave_start < issue_jobs.len() {
    let take = if issue_jobs.len() - wave_start < batch { issue_jobs.len() - wave_start } else { batch };
    let wave_jobs = issue_jobs.extract(wave_start, take);
    let res = parallel(wave_jobs);
    for r in res {
        if r != () && r.success && r.output != () && r.output.results != () {
            if type_of(r.output.results) == "array" {
                for rr in r.output.results { created.push(rr); }
            }
        }
    }
    wave_start += take;
    wave_no += 1;
}
log("issued " + created.len().to_string() + " rows in " + wave_no.to_string() + " wave(s) of <= " + batch.to_string());

// Deterministic ledger order (Engine Fix 2): the parallel issue fan-out
// completes out of order; the ledger reader consumes these results in a
// stable order (feature name ascending, then row id ascending) so the JSONL
// is identical regardless of completion order.
let sort_key = [];
for c in created {
    let fkey = if c.feature != () { c.feature.to_string() } else { "" };
    let rkey = if c.row != () { c.row.to_string() } else { "" };
    sort_key.push(#{ c: c, key: fkey + "/" + rkey });
}
// Stable insertion sort on key (strings compare lexicographically in Rhai).
let k = 0;
while k < sort_key.len() {
    let m = k;
    let i = k + 1;
    while i < sort_key.len() {
        if sort_key[i].key < sort_key[m].key { m = i; }
        i += 1;
    }
    let tmp = sort_key[m];
    sort_key[m] = sort_key[k];
    sort_key[k] = tmp;
    k += 1;
}
let created_sorted = [];
for sk in sort_key { created_sorted.push(sk.c); }

let created_count = created_sorted.len();
let mode_str = if dry_run { "dry-run" } else { "live" };
// Invariant check: count issued rows that carry a closing_condition
let cc_issued = 0;
for c in created_sorted {
    if c.closing_condition != () && c.closing_condition != "" { cc_issued += 1; }
}
let invariant_ok = (cc_issued == created_count) && (missing_cc == 0);
let inv_str = if invariant_ok { "true" } else { "false" };

// --- Run-report phase 2 (Issue) ---
// Finalize docs/task-tracker-report.json: add pending_infra (row ids) and
// invariant_ok, and overwrite actionable_verdict_count with the exact
// count of the final actionable list (verdict ∈ the actionable set AND
// closing_condition non-empty) — the value validate.py check 5 consumes.
let n_created = 0;
let n_commented = 0;
for c in created_sorted {
    if c.action == "created" { n_created += 1; }
    if c.action == "commented" { n_commented += 1; }
}
let report_phase2 = #{
    rows_scanned: all_rows.len(),
    incomplete: n_incomplete,
    doc_sync: n_doc_sync,
    unverified: n_unverified,
    fr_orphan: n_fr_orphan,
    skipped: n_skipped,
    created: n_created,
    commented: n_commented,
    rollup_mismatches: rollup_classifications.len(),
    closing_conditions: n_closing_conditions,
    actionable_verdict_count: actionable.len(),
    pending_infra: pending_infra,
    invariant_ok: invariant_ok,
};
let rp2_prompt = "Overwrite " + report_path + " with this exact JSON. No other file writes. The JSON, verbatim:\n"
    + json_encode(report_phase2);
agent(rp2_prompt, #{ label: "report-phase2", capability_mode: "execute" });
log("run-report phase 2 finalized at " + report_path + " (actionable_verdict_count=" + actionable.len().to_string()
    + ", pending_infra=" + pending_infra.len().to_string() + ", invariant_ok=" + inv_str + ")");

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
    issued: created_sorted,
    with_closing_condition: cc_issued,
    missing_closing_condition: missing_cc,
    pending_infra: pending_infra,
    invariant_ok: inv_str,
    mode: mode_str,
    report_path: report_path,
});
