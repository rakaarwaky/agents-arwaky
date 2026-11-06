---
name: grill-me
description: Relentlessly interviews a plan or design until a shared understanding is reached.
when-to-use: "Use when asked to grill, interview, or stress-test a plan, design, or decision tree until every branch is resolved. Triggers: 'grill this plan', 'interview this design', 'stress-test my approach'."
argument-hint: "<plan or design to grill>"
disable-model-invocation: true
---

# Grill Me

## Rules

- **One-shot interview.** Walks every branch of the design tree, resolving dependencies between decisions one-by-one, until a shared understanding is reached. The full method lives in [`references/interview.md`](references/interview.md).
- **Codebase-first answers.** If a question can be answered by exploring the codebase, explore the codebase instead of asking.

## Routing

| File | Purpose |
|------|---------|
| [`references/interview.md`](references/interview.md) | The relentless interview method: branch walk, dependency resolution, codebase-first probing, and stop condition. |
