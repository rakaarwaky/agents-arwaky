---
name: research-paper-writing
description: "Write ML papers for NeurIPS/ICML/ICLR: design→submit."
metadata:
  hermes:
    tags: [Research, Paper Writing, Experiments, ML, AI, NeurIPS, ICML, ICLR, ACL, AAAI, COLM, LaTeX, Citations, Statistical Analysis]
    category: research
    related_skills: [arxiv, subagent-driven-development, plan]
    requires_toolsets: [terminal, files]
---
# Research Paper Writing Pipeline

End-to-end pipeline for producing publication-ready ML/AI research papers targeting **NeurIPS, ICML, ICLR, ACL, AAAI, and COLM**. This skill covers the full research lifecycle: experiment design, execution, monitoring, analysis, paper writing, review, revision, and submission.

This is **not a linear pipeline** — it is an iterative loop. Results trigger new experiments. Reviews trigger new analysis. The agent must handle these feedback loops.

<!-- ascii-guard-ignore -->
```
┌─────────────────────────────────────────────────────────────┐
│                    RESEARCH PAPER PIPELINE                  │
│                                                             │
│  Phase 0: Project Setup ──► Phase 1: Literature Review      │
│       │                          │                          │
│       ▼                          ▼                          │
│  Phase 2: Experiment     Phase 5: Paper Drafting ◄──┐      │
│       Design                     │                   │      │
│       │                          ▼                   │      │
│       ▼                    Phase 6: Self-Review      │      │
│  Phase 3: Execution &           & Revision ──────────┘      │
│       Monitoring                 │                          │
│       │                          ▼                          │
│       ▼                    Phase 7: Submission               │
│  Phase 4: Analysis ─────► (feeds back to Phase 2 or 5)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
<!-- ascii-guard-ignore-end -->

---

## When To Use This Skill

Use this skill when:
- **Starting a new research paper** from an existing codebase or idea
- **Designing and running experiments** to support paper claims
- **Writing or revising** any section of a research paper
- **Preparing for submission** to a specific conference or workshop
- **Responding to reviews** with additional experiments or revisions
- **Converting** a paper between conference formats
- **Writing non-empirical papers** — theory, survey, benchmark, or position papers (see [references/paper-types.md](references/paper-types.md))
- **Designing human evaluations** for NLP, HCI, or alignment research
- **Preparing post-acceptance deliverables** — posters, talks, code releases

## Core Philosophy

1. **Be proactive.** Deliver complete drafts, not questions. Scientists are busy — produce something concrete they can react to, then iterate.
2. **Never hallucinate citations.** AI-generated citations have ~40% error rate. Always fetch programmatically. Mark unverifiable citations as `[CITATION NEEDED]`.
3. **Paper is a story, not a collection of experiments.** Every paper needs one clear contribution stated in a single sentence. If you can't do that, the paper isn't ready.
4. **Experiments serve claims.** Every experiment must explicitly state which claim it supports. Never run experiments that don't connect to the paper's narrative.
5. **Commit early, commit often.** Every completed experiment batch, every paper draft update — commit with descriptive messages. Git log is the experiment history.

**Draft autonomously by default** (abstract, intro, methods, experiments, related work — flag uncertainties inline). Block for input only when: target venue unclear, multiple contradictory framings, results seem incomplete, or explicitly asked to review first.

---

## Pipeline Checklist

Work phase by phase; load the linked reference file when you enter each phase.

1. **Phase 0 — Project Setup.** Explore repo, organize `paper/ experiments/ code/ results/`, set up git, name the one-sentence contribution, draft a TODO list, estimate compute.
   → [references/phases-0-1-setup-lit-review.md](references/phases-0-1-setup-lit-review.md)
2. **Phase 1 — Literature Review.** Seed papers → breadth-first then depth search → verify every citation programmatically → organize related work.
   → [references/phases-0-1-setup-lit-review.md](references/phases-0-1-setup-lit-review.md) + [references/citation-workflow.md](references/citation-workflow.md) + [references/sources.md](references/sources.md)
3. **Phase 2 — Experiment Design.** Map claims to experiments, design baselines, define the eval protocol, write runner scripts (+ human eval if needed).
   → [references/phases-2-4-experiments.md](references/phases-2-4-experiments.md) + [references/experiment-patterns.md](references/experiment-patterns.md) + [references/human-evaluation.md](references/human-evaluation.md)
4. **Phase 3 — Execution & Monitoring.** Launch, monitor (cron pattern), handle failures, commit results, keep an experiment journal.
   → [references/phases-2-4-experiments.md](references/phases-2-4-experiments.md)
5. **Phase 4 — Analysis.** Aggregate, test significance, find the story, build figures/tables, decide: more experiments or write. Bridge with `experiment_log.md`.
   → [references/phases-2-4-experiments.md](references/phases-2-4-experiments.md)
6. **Refinement strategy.** Pick autoreason vs critique-and-revise vs single pass via the decision table (model tier × task constraint).
   → [references/phases-2-4-experiments.md](references/phases-2-4-experiments.md) + [references/autoreason-methodology.md](references/autoreason-methodology.md)
7. **Phase 5 — Paper Drafting.** Section-by-section order, LaTeX scaffolding, abstract/intro formulas, related-work positioning.
   → [references/phase5-paper-drafting.md](references/phase5-paper-drafting.md) + [references/writing-guide.md](references/writing-guide.md)
8. **Phase 6 — Self-Review & Revision.** Simulate reviews (ensemble + visual + claim-verification passes), prioritize, revise, write rebuttals.
   → [references/phases-6-7-review-submit.md](references/phases-6-7-review-submit.md) + [references/reviewer-guidelines.md](references/reviewer-guidelines.md)
9. **Phase 7 — Submission.** Conference, anonymization, and formatting checklists; compilation; venue-specific requirements; resubmission/conversion; camera-ready; arXiv; code packaging.
   → [references/phases-6-7-review-submit.md](references/phases-6-7-review-submit.md) + [references/checklists.md](references/checklists.md)
10. **Phase 8 — Post-Acceptance.** Poster, talk/spotlight, blog/social.
    → [references/phases-8-hermes-appendix.md](references/phases-8-hermes-appendix.md)
11. **Non-empirical variants.** Theory, survey, benchmark, position papers; workshops and short papers.
    → [references/paper-types.md](references/paper-types.md)
12. **Hermes tooling.** Related skills, tool usage patterns, memory/todo/cron conventions, experiment/reviewer templates.
    → [references/phases-8-hermes-appendix.md](references/phases-8-hermes-appendix.md)

## References

| File | Read it when |
|------|--------------|
| `references/phases-0-1-setup-lit-review.md` | Project setup and literature review procedure |
| `references/phases-2-4-experiments.md` | Experiment design, execution, analysis, refinement, log template |
| `references/phase5-paper-drafting.md` | Section-by-section drafting procedure |
| `references/phases-6-7-review-submit.md` | Self-review, revision, and submission steps |
| `references/phases-8-hermes-appendix.md` | Post-acceptance, Hermes integration, templates |
| `references/citation-workflow.md` | Citation search and verification workflow |
| `references/experiment-patterns.md` | Reusable experiment design patterns |
| `references/autoreason-methodology.md` | Iterative refinement prompts and scoring |
| `references/human-evaluation.md` | Human eval design for NLP/HCI/alignment |
| `references/reviewer-guidelines.md` | What reviewers check; self-review rubric |
| `references/checklists.md` | Submission and formatting checklists |
| `references/paper-types.md` | Theory, survey, benchmark, position papers |
| `references/writing-guide.md` | Prose-level style rules |
| `references/sources.md` | Key external sources |
