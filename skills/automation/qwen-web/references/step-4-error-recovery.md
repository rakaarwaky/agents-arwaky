# Step 4 — Error handling & recovery

**Goal:** you can read every qwen-web error and apply the matching recovery.

## Error table

| Error / Condition | Cause | Action |
| :--- | :--- | :--- |
| `AuthRequiredError` / `AUTH_REQUIRED` | Session expired or login needed | Call `setup_session` (MCP) or run `qwa session login` (CLI) to re-authenticate. |
| `OutputValidationError` (CAPTCHA) | Bot verification challenge | Run `setup_session` or `qwa session login` to solve challenge manually. |
| `NetworkTimeoutError` | Temporary network latency | Retry the request; if persistent, verify internet connection via `qwa doctor [--smoke] [--deep]`. |
| `FileValidationError` / `FILE_NOT_FOUND` | Missing, unreadable, or file > 100 MB | Verify file path, permissions, and ensure file size is under 100 MB. |
| `CircuitBreakerOpenError` | Repeated consecutive failures | Wait 30 seconds before sending next request. |
| `VALIDATION_ERROR` (MCP) | Invalid tool parameter | Check error `field` in response and correct the argument payload. |

---

## Completion

- The error hit was matched to the table above and its recovery applied (re-login, retry, doctor, or payload fix); the next request succeeds or the refusal is reported with the failing check named.
