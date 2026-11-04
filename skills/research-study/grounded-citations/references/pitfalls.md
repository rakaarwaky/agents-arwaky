# Pitfalls — Grounded Citations

- **Registering after writing.** The ledger must be populated from tool
  output, not reconstructed from the draft — that reintroduces exactly the
  hallucinated-URL risk the numbering removes.
- **Renumbering mid-task.** Never hand-edit ids in a draft. Ids are ledger
  identities; if a draft cites `[4]`, `[4]` must stay that source. Run
  `reset` only between tasks.
- **Retyping URLs into the Sources block.** Always `render`. A hand-typed
  URL is an unverified claim.
- **Citing a search snippet as if you read the page.** A `web_search`
  description supports only what it literally says. Cite the extracted page
  when the claim needs the body — `web_extract` it first.
- **Relying on search engines for "which package/tool exists on this
  distro" questions.** Search engines (DuckDuckGo, Bing, Google) are either
  CAPTCHA-gated or return irrelevant results when accessed programmatically.
  `web_extract` on this deployment cannot fetch arbitrary URLs
  (search-only backend). Go directly to the authoritative source: for
  Debian/Deepin packages, query the package archive with
  `curl -s "https://packages.debian.org/sid/<pkg>"` or
  `apt-cache search <term>` in terminal; for a specific tool repo, hit the
  GitHub or GitLab page URL directly with `curl` or `web_extract`.
- **Over-citing.** Three ids on a sentence is the ceiling; a citation on
  every clause makes text unreadable and hides which source carries the
  load.
- **Citing the ledger in code/config artifacts.** Source comments belong in
  prose deliverables and doc headers, not inside generated code.
- **Parallel subagents.** Each subagent has its own working directory; point
  them all at one ledger with `--ledger` (or `HERMES_CITATION_LEDGER`) if
  their outputs get merged, otherwise their ids will collide.
- **Quoting from a snippet instead of the page.** Evidence quotes must come
  from the extracted page text, not a search-result description —
  `web_extract` first, save the text, then `quote --from` that file.
- **Paraphrasing into `quote --text`.** The verbatim check will reject it;
  the fix is to find the actual sentence, not to reword until something
  matches.
- **Using `[unverified]` as an escape hatch.** It marks the rare claim that
  genuinely cannot be sourced; if most sentences carry it, the task needed
  more retrieval, not more markers.
- **Hand-editing the Sources block.** Use `render --replace-in <draft>`;
  slicing the file yourself risks a stale or duplicated block that `verify`
  then flags.
