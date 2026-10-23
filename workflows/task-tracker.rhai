let meta = #{
    name: "task-tracker",
    description: "Zero-trust: map AES spec states into modular GitHub tracking issues, one subagent per feature",
    phases: [
        #{ title: "Discover", detail: "one agent enumerates features and their spec docs" },
        #{ title: "Scan", detail: "one scanner subagent per feature, each owning its FR-id set" },
        #{ title: "Verify", detail: "one verifier subagent per feature; every Done/Released row is re-checked, roll-up reconciled" },
        #{ title: "Issue", detail: "batched modular issue creation, dry-run default" },
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
                "type": "object", "required": ["row", "verdict", "evidence"],
                "properties": #{
                    "row": #{ "type": "string" },
                    "verdict": #{ "type": "string" },
                    "evidence": #{ "type": "string" },
                },
            },
        },
        "rollup_verdicts": #{
            "type": "array",
            "items": #{
                "type": "object", "required": ["feature", "verdict"],
                "properties": #{
                    "feature": #{ "type": "string" },
                    "verdict": #{ "type": "string" },
                    "evidence": #{ "type": "string" },
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
                "type": "object", "required": ["row", "action"],
                "properties": #{
                    "row": #{ "type": "string" },
                    "action": #{ "type": "string" },
                    "url": #{ "type": "string" },
                    "number": #{ "type": "string" },
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

// args: { repo_root (required), dry_run (optional, default false — live runs unless --dry-run is passed) }
let a_root = ();
let a_dry = ();
let a_batch = ();
if type_of(args) == "map" {
    a_root = args.repo_root;
    a_dry = args.dry_run;
    a_batch = args.batch;
} else if type_of(args) == "string" {
    a_root = json_text_field(args, "repo_root");
    a_dry = json_text_field(args, "dry_run");
    a_batch = json_text_field(args, "batch");
}
if a_root == () { pause("verification", "Pass args.repo_root — the absolute path to the AES repo to track."); }
let repo_root = a_root.to_string();
let dry_run = if a_dry == () { false } else { a_dry.to_string() == "true" || a_dry.to_string() == "1" };
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
let root_docs = disc.output.root;
let features = disc.output.features;
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
        + "3. Collect the FR-id set: every FR-<SCOPE>-NNN declared in the FRD headings and every FRD Ref "
        + "cell cited by the backlog rows. "
        + "4. If the roadmap has a Feature Roll-up table, extract THIS feature's roll-up row verbatim, all cells. "
        + "Emit one JSON object per task row: "
        + "{\"id\":\"...\",\"title\":\"...\",\"state\":\"<verbatim state>\",\"priority\":\"P0|P1|P2|—\","
        + "\"health\":\"...|—\",\"fr_refs\":[\"FR-…\"],\"source_doc\":\"<repo-relative path>\",\"row_text\":\"<verbatim row>\"}. "
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
for sr in scan_results {
    let gname = groups[i].name;
    if sr != () && sr.success && sr.output != () {
        for r in sr.output.rows {
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

// --- Phase 3: Verify (one subagent per feature, zero-trust) ---
// No row is exempt: Done/Released rows are proof demands, the roll-up is reconciled
// against each feature's effective state, and FR orphans are flagged in both directions.
phase("Verify");
let verdicts = [];
let j = 0;
for g in groups {
    let vp = "Verify the feature \"" + g.name + "\" against ACTUAL CODE ONLY. ZERO TRUST: no state claim "
        + "— including Done and Released — is accepted on doc text, git history, or GitHub issues/PRs/releases. "
        + "The only evidence that counts is the source code and test files in the feature's own tree. "
        + "For every row in the feature's BACKLOG: "
        + "(1) Read the row's item text and its Actual Condition cell. "
        + "(2) Open the files under " + g.dir + "/src/ and " + g.dir + "/tests/ that the row's description refers to "
        + "(use the FR id, the row title, and the described behavior to locate them). "
        + "(3) Confirm the described behavior is actually implemented in the current code: "
        + "the function/class/flag/config exists, the logic matches the claim, and at least one test exercises it. "
        + "A row claiming Done/Released passes only if the code and tests you just read prove it. "
        + "A hash in the row's evidence cell is NOT proof; a merged-PR number is NOT proof; a release tag is NOT proof. "
        + "If the code does not implement what the row claims, verdict is \"unverified\" and the evidence field "
        + "names the specific file and the missing or wrong behavior. "
        + "For tracking-issue dedupe: gh issue list --state open --search \"<row id> in:title\" --json number,title "
        + "(an open issue makes the verdict \"exists\"; nothing open makes it \"open\"). "
        + "Roll-up reconciliation: recompute the feature's effective state from its backlog rows — worst state "
        + "wins, ranked Blocked > In Progress > Refinement > Ready > Idea > QA > In Review > Deferred > Done > "
        + "Released; any non-Done row makes the feature non-Done. If the roadmap roll-up claims Done/Released "
        + "while the effective state is less (or claims QA while every row is proven Done), verdict "
        + "\"rollup_mismatch\" for the roll-up row. "
        + "FR orphan check: every FR id declared in the FRD must be cited by at least one backlog row and "
        + "vice versa; either direction failing is verdict \"fr_orphan\" for that FR id. "
        + "Verdicts per row: open (code does not implement the work, no open issue tracks it) | "
        + "exists (an open issue #N already tracks this row — cite the issue number) | "
        + "doc_sync (code implements the work but the doc still reports an incomplete state) | "
        + "unverified (Done/Released claim whose code evidence is absent or does not match the claim) | "
        + "skip (Done/Released with code evidence that fully confirms it — the only skip path) | fr_orphan. "
        + "Cite the file paths and line ranges you read in the evidence field. No writes, no issue creation.";
    let res = agent(vp, #{
        label: "verify:" + g.name,
        capability_mode: "read-only",
        output_schema: verdict_schema,
    });
    if res != () && res.success && res.output != () {
        for v in res.output.verdicts {
            v.feature = g.name;
            verdicts.push(v);
        }
        for rv in res.output.rollup_verdicts {
            rv.kind = "rollup";
            if rv.row == () { rv.row = rv.feature + " roll-up"; }
            verdicts.push(rv);
        }
    }
    j += 1;
}
log("verified " + verdicts.len().to_string() + " verdicts across " + groups.len().to_string() + " features");

// --- Phase 4: Issue (modular, batched, dry-run default) ---
phase("Issue");
let actionable = [];
for v in verdicts {
    if v.verdict == "open" || v.verdict == "doc_sync" || v.verdict == "unverified"
        || v.verdict == "rollup_mismatch" || v.verdict == "fr_orphan" || v.verdict == "exists" {
        actionable.push(v);
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
        row_list += row_id + " (" + entry.verdict + ": " + entry.evidence + "), ";
    }
    row_list = row_list.sub_string(0, row_list.len() - 2);
    let dry_word = if dry_run {
        "DRY RUN: print each would-be issue (title, body, labels) without calling gh issue create."
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
        + "exact commands run, Roll-up check section, and the 'Tracking only' footer. "
        + "Labels: " + state_label + ", state:<state>, p0/p1/p2, plus doc-sync for doc_sync/unverified/"
        + "rollup_mismatch and deferred for Deferred rows. "
        + "For verdict exists: append a freshness comment to the recorded issue, action commented. "
        + "Return {row, action, url, number} per row. No branch, no PR, no code edit, no file write. "
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
let complete_msg = "rows scanned: " + all_rows.len().to_string()
    + " | verdicts: " + verdicts.len().to_string()
    + " | actionable: " + actionable.len().to_string()
    + " | issued: " + created_count.to_string()
    + " | mode: " + mode_str;
log(complete_msg);
complete(#{
    summary: complete_msg,
    features: features,
    rows_scanned: all_rows.len(),
    verdicts: verdicts,
    issued: created,
    mode: mode_str,
});
