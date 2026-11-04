# Step 3 — Prompt engineering for complete output

**Goal:** you can write prompts that return complete, un-truncated results.

## Rules

To ensure Qwen produces complete code without placeholders or omitted sections:

1. **Specify an explicit Output Contract:** Define exact required section titles and expected markdown formatting.
2. **Forbid truncation explicitly:** Include this clause in your prompt:
   > *"Output every file COMPLETE and VERBATIM inside fenced code blocks with language tags. Never use ellipses (`...`), placeholder comments (`// rest unchanged`), or omit code."*
3. **Reason first, code second:** Request an analysis or plan before the implementation code so the model thinks before writing.
4. **Put large context into attachments:** Keep the prompt file focused on instructions; provide code, logs, and schemas as attachments.
5. **Add a self-verification step:** Instruct the model to verify that no placeholders exist and all requested items are satisfied before completing.

---

## Completion

- The prompt carries an explicit output contract and the anti-truncation clause, large context is in attachments not the prompt, and the model's self-verification step confirms no placeholders remain.
