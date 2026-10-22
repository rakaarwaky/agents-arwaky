let meta = #{
    name: "task-tracker",
    description: "Map AES spec-document states into modular GitHub tracking issues",
    phases: [
        #{ title: "Discover", detail: "one agent enumerates the in-scope spec docs" },
        #{ title: "Scan", detail: "one scanner agent per doc, fan-out" },
        #{ title: "Verify", detail: "one verifier agent per incomplete row" },
        #{ title: "Issue", detail: "batched modular issue creation, dry-run default" },
    ],
};

let doc_schema = #{
    "type": "object", "required": ["docs"],
    "properties": #{ "docs": #{ "type": "array", "items": #{ "type": "string" } } },
};
let rows_schema = #{
    "type": "object", "required": ["rows"],
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
                    "source_doc": #{ "type": "string" },
                    "row_text": #{ "type": "string" },
                },
            },
        },
    },
};
let verdict_schema = #{
    "type": "object", "required": ["verdict"],
    "properties": #{
        "verdict": #{ "type": "string" },
        "evidence": #{ "type": "string" },
        "issue": #{ "type": "string" },
        "reason": #{ "type": "string" },
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

// args: { repo_root, dry_run (default true), state_label (default task-tracker), batch (default 6) }
let a_root = ();
let a_dry = ();
let a_label = ();
let a_batch = ();
if type_of(args) == "map" {
    a_root = args.repo_root;
    a_dry = args.dry_run;
    a_label = args.state_label;
    a_batch = args.batch;
} else if type_of(args) == "string" {
    a_root = json_text_field(args, "repo_root");
    a_dry = json_text_field(args, "dry_run");
    a_label = json_text_field(args, "state_label");
    a_batch = json_text_field(args, "batch");
}
if a_root == () { pause("verification", "Pass args.repo_root — the AES repo to track (e.g. internal/qwen-web-arwaky)."); }
let repo_root = a_root.to_string();
let dry_run = if a_dry == () { true } else { a_dry.to_string() != "false" };
let state_label = if a_label == () { "task-tracker" } else { a_label.to_string() };
let batch = if a_batch == () { 6 } else { parse_int(a_batch.to_string()) };

// --- Phase 1: Discover ---
phase("Discover");
let disc_prompt = "Enumerate the in-scope spec documents in " + repo_root
    + ". A spec doc qualifies when it sits at the repo root or under modules/, packages/, or crates/, "
    + "and contains a state table or a row table with a State column. "
    + "Run: cd " + repo_root + " && grep -rl -E '^#+ *State [Dd]efinitions' . --include='*.md' "
    + "then filter out scratch, session, and skill-template directories: .git, .qwen-web, .qwen-web-arwaky, "
    + ".qwen, .agents, node_modules, target, dist, __pycache__, htmlcov, vendor, skills, references, "
    + "workspaces-bad, workspaces-good. Prompt scratch files and skill reference templates quote the words "
    + "'State Definitions' without being specs — never include them. "
    + "Then walk modules/, packages/, and crates/ (whichever exist) and add every feature BACKLOG.md, FRD.md, "
    + "and DESIGN.md even when that file holds no definitions table itself — its backlog table may still "
    + "carry a State column. Return repo-relative paths, one per entry. An empty list is valid only if the "
    + "repo has no spec docs at all.";
let disc = agent(disc_prompt, #{
    label: "discover-docs",
    capability_mode: "read-only",
    output_schema: doc_schema,
});
if disc == () || !disc.success || disc.output.docs == () {
    log("Discovery failed — no document list; run cannot proceed to Scan");
    complete(#{ summary: "discovery failed", docs: [] });
}
let docs = disc.output.docs;

// --- Phase 2: Scan (one agent per doc) ---
phase("Scan");
let scan_jobs = [];
for d in docs {
    let p = "You are a read-only scanner. Read " + d + " in full (single read). "
        + "Extract its State Definitions table, then every table row whose headers include "
        + "ID and State. Return one JSON object per row: "
        + "{\"id\":\"...\",\"title\":\"...\",\"state\":\"<verbatim state>\",\"priority\":\"P0|P1|P2|—\",\"health\":\"...|—\",\"source_doc\":\"<repo-relative path>\",\"row_text\":\"<verbatim row>\"}. "
        + "State must appear verbatim in the source row; never infer or normalize. "
        + "Rows without a state value get state unknown. Empty rows array is valid only after reading the whole file.";
    scan_jobs.push(#{ prompt: p, label: "scan:" + d, capability_mode: "read-only", output_schema: rows_schema });
}
let scan_results = parallel(scan_jobs);

let all_rows = [];
let i = 0;
for sr in scan_results {
    if sr != () && sr.success && sr.output.rows != () {
        for r in sr.output.rows {
            r.source_doc = docs[i];
            r.class = "pending";
            all_rows.push(r);
        }
    }
    i += 1;
}

// Classify locally: incomplete states.
let incomplete_states = ["Idea", "Refinement", "Ready", "In Progress", "Blocked", "In Review", "QA", "Deferred"];
let todo_rows = [];
let skipped_rows = [];
for r in all_rows {
    let inc = false;
    for k in 0..incomplete_states.len() {
        if r.state == incomplete_states[k] { inc = true; }
    }
    if r.state == "unknown" {
        skipped_rows.push(r);
        log("row " + r.id + " has no state value in " + r.source_doc + " — skipped");
    } else if inc {
        r.class = "incomplete";
        todo_rows.push(r);
    } else {
        skipped_rows.push(r);
    }
}

// --- Phase 3: Verify (batch incomplete rows against GitHub + git) ---
phase("Verify");
let verdicts = [];
let total_batches = (todo_rows.len() + batch - 1) / batch;
for b in 0..total_batches {
    let lo = b * batch;
    let hi = lo + batch;
    if hi > todo_rows.len() { hi = todo_rows.len(); }
    let vjobs = [];
    for jj in lo..hi {
        let r = todo_rows[jj];
        let vp = "Verify one spec row against git and GitHub. Row: id " + r.id
            + ", state " + r.state + ", doc " + r.source_doc + ". "
            + "Run: gh issue list --state open --search \"" + r.id + " in:title\" --json number,title; "
            + "and gh pr list --state merged --search \"" + r.id + "\" --json number,mergedAt. "
            + "If the row claims a commit, confirm it with git merge-base --is-ancestor <sha> HEAD in " + repo_root + ". "
            + "Verdicts: open (no open issue, work unfinished) | exists (open issue #N already tracks it) "
            + "| doc_sync (work provably done — merged PR or release — but the doc still says " + r.state + ") "
            + "| skip (Done/Released with reproducing evidence). Cite the exact evidence string. "
            + "No writes, no issue creation.";
        vjobs.push(#{ prompt: vp, label: "verify:" + r.id, capability_mode: "read-only", output_schema: verdict_schema });
    }
    let vres = parallel(vjobs);
    let k = 0;
    for v in vres {
        if v != () && v.success && v.output != () {
            let verdict = v.output.verdict;
            if verdict == "open" || verdict == "doc_sync" {
                let entry = #{
                    row: todo_rows[lo + k].id,
                    doc: todo_rows[lo + k].source_doc,
                    state: todo_rows[lo + k].state,
                    verdict: verdict,
                    evidence: v.output.evidence,
                };
                verdicts.push(entry);
            }
        }
        k += 1;
    }
    log("verified batch " + (b + 1) + " — " + verdicts.len() + " actionable verdicts so far");
}

// --- Phase 4: Issue (modular, batched, dry-run default) ---
phase("Issue");
let dry_word = if dry_run {
    "DRY RUN: print each would-be issue (title, body, labels) without calling gh issue create."
} else {
    "Create each issue with gh issue create."
};
let created = [];
let total_ibatches = (verdicts.len() + batch - 1) / batch;
for t in 0..total_ibatches {
    let lo = t * batch;
    let hi = lo + batch;
    if hi > verdicts.len() { hi = verdicts.len(); }
    let row_list = "";
    for u in lo..hi {
        let entry = verdicts[u];
        row_list += entry.row + " (" + entry.verdict + ": " + entry.evidence + "), ";
    }
    row_list = row_list.sub_string(0, row_list.len() - 2);
    let ip = "You are an issuer. In " + repo_root + ", handle these rows: " + row_list + ". "
        + "For verdict open: create one modular issue titled [<feature>] <row id> — <task summary>. "
        + "For verdict doc_sync: title [DOC-SYNC] <row id> — <doc path> still reports <state>. "
        + "Body per SKILL.md: field table, verbatim task, evidence, 'Tracking only' footer. "
        + "Labels: " + state_label + ", state:<state>, doc-sync for doc_sync verdicts. "
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
    + " | actionable verdicts: " + verdicts.len().to_string()
    + " | issued: " + created_count.to_string()
    + " | mode: " + mode_str;
log(complete_msg);
complete(#{
    summary: complete_msg,
    docs: docs,
    rows_scanned: all_rows.len(),
    actionable: verdicts,
    issued: created,
    mode: mode_str,
});
