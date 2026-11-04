# Inbox Triage Pitfalls

Failure modes to watch for while running the triage procedure in `references/procedure.md`.

- **Treating unread as synonymous with important.** Unread is a signal, not a classification; an unread reference note is not a reply.
- **Missing earlier unanswered questions in a long thread.** Retrieve the complete thread, not just the newest message — unanswered questions live upthread.
- **Drafting in a generic-professional voice.** Calibrate against the user's own sent replies (20–50, truncated); fall back to the incoming thread's register only when Sent is empty or inaccessible, and say so.
- **Treating a missing `Sent` folder as inaccessible.** Providers name it `Sent`, `Sent Messages`, `[Gmail]/Sent Mail`, or a localized name — list folders before declaring the fallback.
- **Retrying after SMTP succeeded but save-to-Sent failed.** A blind retry duplicates the mail. Inspect Sent before any retry on an ambiguous send error.
- **Claiming inbox zero when pagination or another folder was omitted.** State coverage gaps explicitly rather than rounding up.
