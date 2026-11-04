# Step 2 — Usage by use case

**Goal:** you can pick the right use case (inline prompt, prompt file, attachment, role template, session, init) and run it.

### Use Case 1: Quick Inline Prompt / Question
Use for fast queries, factual explanations, or one-off code generation where no external files are needed.

**MCP:**
```json
{
  "prompt": "Explain the difference between optimistic and pessimistic locking in 3 concise bullet points with a brief Python example.",
  "headless": true
}
```

**CLI:**
```bash
qwa prompt direct -t "Explain optimistic vs pessimistic locking" -o .qwen-web-arwaky/output/locking_$(date +%Y%m%d_%H%M%S).md --headless
```

---

### Use Case 2: Complex Task from a Prompt File
Use for multi-step instructions, complex refactor specs, or long prompts authored in a Markdown file.

**MCP:**
```json
{
  "input_file": ".qwen-web-arwaky/input/refactor_task.md",
  "output_file": ".qwen-web-arwaky/output/refactor_result_20260911_133000.md",
  "headless": true
}
```

**CLI:**
```bash
qwa prompt file -i .qwen-web-arwaky/input/refactor_task.md -o .qwen-web-arwaky/output/refactor_result_$(date +%Y%m%d_%H%M%S).md --headless
```

---

### Use Case 3: Code Audit or Document Analysis with Attachment
Use when the prompt requires analyzing a codebase export, technical document, log file, or PDF spec (supported: `.pdf`, `.md`, `.txt` up to 100 MB).

**MCP:**
```json
{
  "prompt_file": ".qwen-web-arwaky/input/audit_spec.md",
  "attachment_file": ".qwen-web-arwaky/input/codebase_export.md",
  "output_file": ".qwen-web-arwaky/output/audit_findings_20260911_133000.md",
  "headless": true
}
```

**CLI:**
```bash
qwa prompt attach -i .qwen-web-arwaky/input/audit_spec.md -a .qwen-web-arwaky/input/codebase_export.md -o .qwen-web-arwaky/output/audit_findings_$(date +%Y%m%d_%H%M%S).md --headless
```

---

### Use Case 4: Standard Reviews Using Built-in Role Templates
Instead of writing a custom prompt file, you can pass a built-in role template name directly as the prompt input:
- `business-analyst`: Business problem, process model, acceptance criteria, stakeholder alignment, UAT.
- `system-analyst`: Technical behavior, data model, API contract, sequences, requirement traceability.
- `ui-ux-designer`: User journey, wireframes, design system, accessibility, interface states.
- `software-architect`: Module boundaries, integration patterns, scalability, standards, tech debt.
- `backend-engineer`: Server API, database schema, business rules, performance, backend tests.
- `frontend-engineer`: UI components, client state, API consumption, responsiveness, component tests.
- `product-engineer`: Delivery tracking, cross-team dependencies, blockers, demo prep, release readiness.
- `qa-engineer`: Test strategy, functional/regression, automation, defects, quality metrics.
- `security-engineer`: Threat model, auth standards, vuln scan, privacy/encryption, incident protocol.
- `devops-engineer`: CI/CD pipeline, infra provisioning, deployment/rollback, observability, incident response.

**MCP:**
```json
{
  "prompt_file": "backend-engineer",
  "attachment_file": "src/api/auth.py",
  "output_file": ".qwen-web-arwaky/output/auth_review_20260911_133000.md"
}
```

**CLI:**
```bash
qwa prompt attach -i backend-engineer -a src/api/auth.py -o .qwen-web-arwaky/output/auth_review_$(date +%Y%m%d_%H%M%S).md --headless
qwa prompt attach -i software-architect -a README.md -o .qwen-web-arwaky/output/arch_review_$(date +%Y%m%d_%H%M%S).md --headless
```

---

### Use Case 5: Session Setup & Authentication
Use to verify login status or authenticate a new browser session when cookies expire.

1. **Check session health:**
   - MCP: call `check_session`
   - CLI: `qwa doctor`
2. **Login / Re-authenticate (opens visible browser for login / CAPTCHA):**
   - MCP: call `setup_session`
   - CLI: `qwa session login`
3. **Reset session profile (if corrupted):**
   - MCP: `delete_session` with `{"confirm": true}`

---

### Use Case 6: Workspace Initialization
Use when provisioning `.qwen-web-arwaky/` workspace directories and sample configuration in a new project.

**MCP:**
```json
{
  "target_dir": "."
}
```

**CLI:**
```bash
qwa init [--dir .]
```

---

## Completion

- The prompt/attachment reached Qwen and the output file exists at the timestamped output path.
