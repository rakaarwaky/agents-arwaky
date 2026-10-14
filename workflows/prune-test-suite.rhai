let meta = #{
    name: "prune-test-suite",
    description: "Audit every qwen-web-arwaky test module for quality-over-quantity prunes: redundant, duplicate, tautological, or low-signal tests",
    when_to_use: "Cutting low-value tests or reviewing test-suite health.",
    phases: [
        #{ title: "Audit", detail: "one auditor per test module dir" },
        #{ title: "Rank", detail: "consolidate into a ranked prune list" },
    ],
};

let verdict_schema = #{
    "type": "object",
    "required": ["module_dir", "total_tests", "verdicts"],
    "properties": #{
        "module_dir": #{ "type": "string" },
        "total_tests": #{ "type": "integer" },
        "verdicts": #{
            "type": "array",
            "maxItems": 40,
            "items": #{
                "type": "object",
                "required": ["test_id", "action", "reason"],
                "properties": #{
                    "test_id": #{ "type": "string" },
                    "action": #{ "type": "string", "enum": ["cut", "merge", "keep", "promote"] },
                    "reason": #{ "type": "string" },
                },
            },
        },
    },
};

let dir_module = [
    "modules/browser/tests",
    "modules/cli/tests",
    "modules/config/tests",
    "modules/jobs/tests",
    "modules/logging/tests",
    "modules/mcp/tests",
    "modules/prompt/tests",
    "modules/session/tests",
    "modules/shared/tests",
    "modules/swarm/tests",
    "modules/update/tests",
    "tests",
];

let root = "/home/raka/agents-arwaky/internal/qwen-web-arwaky";

phase("Audit");
let jobs = [];
let i = 0;
for d in dir_module {
    let prompt = "You are auditing the qwen-web-arwaky test module: " + d + "\n";
    prompt += "Repo root: " + root + "\n";
    prompt += "Goal: quality over quantity. Decide which tests to CUT (delete) or MERGE, and which to KEEP or PROMOTE.\n";
    prompt += "Run 'uv run python -m pytest " + d + " --collect-only -q' (with UV_PROJECT_ENVIRONMENT=$HOME/.local/share/qwen-web/venv) to enumerate the real test ids, then READ each test file (read_file / grep) before judging - never answer from memory.\n";
    prompt += "Rubric for a CUT: a test that (a) duplicates the assertion of another test in the same module, (b) asserts nothing about real behavior (tautological / trivially-true / only checks a constant), (c) only pins a hard-coded value with no behavior behind it, or (d) is a doctored 'happy path' that a stronger test already covers.\n";
    prompt += "Rubric for a MERGE: two tests that exercise the same code path and could be one parametrized test.\n";
    prompt += "PROMOTE: a test that looks trivial but is actually the only guard for a security/edge/crash path - keep it and say why.\n";
    prompt += "Keep at most ~1/4 of the module's tests flagged as cut/merge; this is pruning, not a rewrite. Every verdict must carry a one-line reason and the exact test id.\n";
    prompt += "Do not edit any file - read-only. Return the verdict object for module '" + d + "'.\n";
    jobs.push(#{
        prompt: prompt,
        label: "audit:" + d,
        capability_mode: "read-only",
        output_schema: verdict_schema,
    });
    i += 1;
}
let results = parallel(jobs);

let cuts = [];
let merges = [];
let promotes = [];
let total_tests = 0;
for r in results {
    if r != () && r.success && r.output.verdicts != () {
        if r.output.total_tests != () { total_tests = total_tests + r.output.total_tests; }
        for v in r.output.verdicts {
            if v.action == "cut" { cuts.push(#{ module_dir: r.output.module_dir, test_id: v.test_id, reason: v.reason }); }
            else if v.action == "merge" { merges.push(#{ module_dir: r.output.module_dir, test_id: v.test_id, reason: v.reason }); }
            else if v.action == "promote" { promotes.push(#{ module_dir: r.output.module_dir, test_id: v.test_id, reason: v.reason }); }
        }
    }
}

phase("Rank");
let rank_prompt = "Below is the raw list of proposed test prunes across the qwen-web-arwaky suite. ";
rank_prompt += "CUTS: " + json_encode(cuts) + "\n";
rank_prompt += "MERGES: " + json_encode(merges) + "\n";
rank_prompt += "PROMOTES (do not cut): " + json_encode(promotes) + "\n";
rank_prompt += "Rank the CUTS highest-first by confidence and risk: a high-confidence cut is one whose removal cannot plausibly lose a real regression guard. ";
rank_prompt += "Flag any cut that a PROMOTE already justified. Return a short numbered list of the top 15 cuts to execute first, each with its test id, module, and one-line risk note.\n";
let rank_job = agent(
    rank_prompt,
    #{ label: "rank-prunes", capability_mode: "read-only" }
);

let ranking = if rank_job != () && rank_job.success { rank_job.output } else { "(ranking subagent failed - see raw cuts)" };
let report = "Quality-over-quantity prune audit for qwen-web-arwaky\n\n";
report += "Modules: " + dir_module.len().to_string() + "  |  tests inspected: " + total_tests.to_string() + "\n";
report += "Proposed cuts: " + cuts.len().to_string() + "  |  merges: " + merges.len().to_string() + "  |  promotes (keep): " + promotes.len().to_string() + "\n\n";
report += "## Ranked top cuts\n" + ranking + "\n\n";
report += "## Full proposed cuts\n" + json_encode(cuts) + "\n\n";
report += "## Proposed merges\n" + json_encode(merges) + "\n\n";
report += "## Protected tests (promoted)\n" + json_encode(promotes) + "\n";
let path = write_scratch_file("prune-report.md", report);
complete(#{ path: path, report: report, cuts: cuts, merges: merges, promotes: promotes, ranking: ranking });
