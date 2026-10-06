# Harness Comparison Dimensions — Decision Guide

Use this when auditing or comparing coding agent harnesses. For each dimension, ask the specific question below and note the evidence.

## 1. Agent Loop / Conversation Management

**Question:** How does the harness compose turns, handle continuation, and recover from errors?

- Look for: conversation_loop, turn_recovery, agent loop, session management
- Evidence: how compaction is triggered, whether partial turns are rolled back on failure

## 2. Tool Suite

**Question:** What tools are registered, and are they native or wrappers around existing CLIs?

- Look for: tool registry, tool implementations, tool naming conventions
- Evidence: list of tool names (read, write, edit, bash, grep, glob, search, web, plan, task, etc.)
- Flag: tools that are thin shells around a subprocess call to an existing CLI carry less engineering weight than native implementations

## 3. Codebase Intelligence

**Question:** Does the harness understand code structure beyond text search?

- Look for: LSP client, codebase graph, symbol index, cross-reference engine
- Evidence: dedicated crates/modules for language server integration, index construction, navigation
- Example: a native codebase-graph crate vs an external tool invoked over MCP

## 4. Context Management & Compaction

**Question:** How does the harness manage growing context windows during long sessions?

- Look for: compaction, context_compressor, conversation_compression, token estimation
- Evidence: is compaction lossy or lossless? Does it preserve structural information (file paths, symbols)?
- This is the single biggest factor in long-session coding quality.

## 5. Subagent Delegation

**Question:** Can the harness spawn parallel subagents with isolated state?

- Look for: subagent, delegate, worktree, async delegation
- Evidence: how subagents are created, how results are merged, whether they share filesystem state

## 6. Workspace / Isolation

**Question:** How does the harness isolate agent work from the main project?

- Look for: worktree, btrfs, overlay, Docker, sandbox, chroot
- Evidence: is isolation at the filesystem level (worktree) or process level (sandbox)?
- Note: workspace isolation protects against accidental damage; it does not improve coding ability. Do not let it dominate a capability verdict.

## 7. Edit Mechanics

**Question:** How are file edits applied — fuzzy patch, exact line replace, LSP edit, or raw write?

- Look for: patch_tool, search_replace, apply_patch, edit tool implementation
- Evidence: what happens when the exact text to replace is not found? Does it fall back to fuzzy matching?
- Check: undo/rollback mechanism, diff tracking (hunk tracker)

## 8. Permissions & Safety

**Question:** How does the harness control what tools can do?

- Look for: permission_mode, approval gate, sandbox profiles, deny rules, hooks
- Evidence: ask/auto/always-approve modes; whether deny rules can override always-approve
- Flag: hooks that can deny tool calls even under always-approve are a genuine safety feature

## 9. Mid-Turn Steering

**Question:** Can the user intervene mid-turn without aborting the whole session?

- Look for: out-of-band message handling, interjection, mid-turn steering
- Evidence: how the harness processes a user message that arrives while a tool call is in progress

## 10. Cross-Session Memory

**Question:** Does the harness persist facts across sessions?

- Look for: memory, episodic storage, long-term facts
- Evidence: storage format (SQLite, JSON), retrieval mechanism, scope (per-session vs global)

## Reporting Shape

Per dimension, report: what each harness does, the source evidence (path/crate), and which side is stronger — plus a confidence note when evidence is thin. End with the dimensions that actually decide coding quality (usually edit mechanics, context compaction, and codebase intelligence) rather than leading with LOC totals.
