# LLM Writing — Step 3: System and Process Patterns

Structures for text that describes a system, workflow, or dependency chain.

**Goal:** every system description ships machine-readable structure — diagram, dependency map, state machine, data flow, or invariants — with real identifiers, not prose.

## Element Table

| Element | Format | Required content |
|---|---|---|
| Diagram | Mermaid in a `mermaid` code block | Node labels = real identifiers (module, path, service, step) |
| Dependency map | Table: Component, Depends on, Depended on by | Both directions, so impact analysis needs no source reading |
| State machine | Table: From, Event, Guard (boolean), To, Action | Every transition has an exact guard condition |
| Data flow | Ordered table: Step, Source, Transform, Sink | Name the file or function at each step |
| Invariants | Table: ID, Invariant, Enforced by | Name the enforcing test, check, or type |

## Completion

- Every system, workflow, or dependency chain in the text has one of the five elements above.
- All node labels and table cells are real identifiers from the source, not generic placeholders.
- No state machine transition without a boolean guard; no invariant without its enforcer.
