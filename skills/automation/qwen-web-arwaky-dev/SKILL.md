---
name: qwen-web-arwaky-dev
description: "Edit qwen-web-arwaky repo source (TUI, slots, tests). Not sending prompts."
metadata:
  tags:
    - python
    - textual
    - tui
    - uv
    - pytest
    - aes
    - qwen-web-arwaky
---

# Developing qwen-web-arwaky

Repo: `~/agents-arwaky/internal/qwen-web-arwaky` — AES layered layout
(`modules/<layer>/src/...`), flat tests at repo root. Scope: editing this
repo's source. For *using* the finished tool (MCP prompt processing, session
login) see the `qwen-web` skill instead.

## Environment

- Run everything through `uv run` from the repo root: `uv run pytest ...`,
  `uv run python -c "..."`. The project venv is Python 3.13; the host
  `python3` is a different interpreter with **none** of the project deps.
- Never conclude a library is missing (or present) from a bare `python3 -c
  "import x"` outside `uv run` — it only proves the host interpreter lacks it.
  The same applies to `podman exec <container> python3 -c ...`: that is a
  separate image, not the dev env.
- `pytest` is a dev dep a freshly-created `.venv` may lack, so `uv run pytest`
  fails with `Failed to spawn: pytest`. Fix: `uv add --dev pytest`.

## Verification loop after any source edit

1. Syntax gate: `uv run python -m py_compile <each changed file>`.
2. Targeted tests for the touched module (`uv run pytest tests/unit_<stem>.py`).
3. Full gate: `uv run pytest tests/ -m "not e2e and not slow" -x -q`
   (`e2e`/`slow` markers are declared in `pytest.ini`; e2e needs live network
   plus a logged-in Qwen session).

Test files use flat prefix naming at repo root — `unit_<module>_<subject>.py`,
`integration_<module>.py`, `contract_*.py`, `smoke_*.py`. There is **no**
`modules/<x>/tests/` tree; find the right file with `ls tests/ | grep <stem>`
instead of assuming a per-module test directory.

## Verifying in the Podman container

The runtime truth lives in the `qwen-web-arwaky` Podman container (image built
from `Containerfile`). `scripts/podman.sh` wraps it: `start`, `stop`, `status`,
`shell`, `run [args...]`, `test`, `lint`, `build`, `login`, `doctor`, `prompt`.

- **`build` recreates the container.** `podman build` makes a NEW image but the
  OLD container keeps the OLD image — `podman start` never re-points it. So after
  editing source, a bare `build` left `podman.sh run`/`test` on stale code (host
  file said 5, container reported 2). `scripts/podman.sh build` therefore calls
  `recreate_container` (rm -f old, then start) — keep that behaviour if you edit
  the script. Symptom check: `podman inspect <c> --format '{{.Created}}'` OLDER
  than `podman inspect localhost/qwen-web-arwaky:latest --format '{{.Created}}'`
  = stale container.
- **Login survives rebuilds.** Auth lives in a host volume
  (`/home/raka/.local/share/containers/storage/volumes/qwen-web-arwaky/_data/share/qwen_session`),
  mounted to `/root/.local/share/qwen-web/qwen_session` (= `DEFAULT_SESSION`).
  `podman rm -f <container>` deletes only the container; the volume and Qwen
  session persist. Never warn that a rebuild loses login — it does not.
- **`tests/` is NOT in the image.** `Containerfile` ends with
  `pip install . && rm -rf /build`, so `scripts/podman.sh test` fails with
  `file or directory not found: tests/`. Run them via one of:
  - copy in (container already up):
    `podman cp tests <c>:/root/tests && podman cp pytest.ini <c>:/root/pytest.ini &&
    podman exec <c> bash -c "cd /root && pytest tests/ -m 'not e2e and not slow' -q"`
  - bind-mount a throwaway container, overriding the `qwa` ENTRYPOINT (else
    `podman run ... qwa pytest` → `invalid choice: 'pytest'`):
    `podman run --rm --net=host --entrypoint pytest -v $PWD:/work:Z -w /work qwen-web-arwaky tests/ -m 'not e2e and not slow' -q`
- **Root-bypasses-chmod pitfall.** The container runs as uid 0, so a test that
  `chmod 0o000` a file and expects a read failure will not fail (root ignores
  DAC). Guard it: `if os.getuid() == 0: pytest.skip("root bypasses filesystem
  permission checks")`. That is a test-env artifact, not a production bug — do
  not chase the code under test.

`git status --short` then `git diff` first — a previous session's edits are
usually already on disk uncommitted, so the job is *completing* them, not
redoing them.

Then verify **completeness**, not just that it compiles. An interrupted UI
change reliably lands the widget + CSS + import but not the event handler, so
the control renders and silently does nothing. For every new widget the diff
adds, grep for its handler/consumer (`on_select_changed`, `on_button_pressed`,
`@on(`, and the widget's `id` string) and confirm a branch actually matches
that id before calling the feature done.

## AES architecture compliance (lint-arwaky gate)

Run `la scan` (or `lint-arwaky-cli scan`) from the repo root after edits. The
repo enforces AES layer boundaries; the violations that bite during UI work:

- **AES406 SURFACE_ROLE** — a `surface_*` file exceeds **50 control-flow
  statements** (counted by the linter, not by naive `grep` — your line counter
  will disagree). Fix by extracting the heavy logic into a **capability** class,
  never by shrinking variable names. `_run_slot` + `_dispatch_batch` are the usual
  culprits in `surface_cli_tui_app.py`.
- **AES403 CAPABILITY_ROLE** — a `capabilities_*` file has no class that
  inherits from a parent protocol. The file must define at least one class
  extending an `I*Protocol` from `contract_core_protocol.py`.
- **AES202 MANDATORY_IMPORT** — a `capabilities_*` file does not import its
  protocol. `from modules.shared.src.contract_core_protocol import IXxxProtocol`
  is mandatory for that layer.
- **AES203 UNUSED_IMPORT** — remove unused imports; the linter fails the build
  gate on them.

Extraction recipe (when AES406 fires on a surface):

1. Add an abstract protocol `IXxxProtocol(ABC)` to
   `modules/shared/src/contract_core_protocol.py` with the method(s) you will
   move; append its name to that file's `__all__`.
2. Create `modules/core/src/capabilities_xxx.py` with a class
   `XxxResolver(IXxxProtocol)` implementing those methods. Return domain results
   as frozen `@dataclass` value objects (e.g. `SlotRunPlan` / `SlotInputError`)
   rather than raising — the surface only forwards an error message. Import the
   protocol (AES202) and ensure a class inherits it (AES403).
3. In the surface, instantiate the resolver once in `__init__`
   (`self._slot_config = XxxResolver()`) and call
   `self._slot_config.<method>(...)`, handling a `SlotInputError` (or similar)
   return by logging. The surface keeps only widget I/O + delegation.
4. Re-scan until **Total: 0 violations**. The user expects *all* violations
   cleared (including ones predating your edits), not just the ones you added.

Verify extraction did not change behaviour: `uv run pytest tests/ -m "not e2e
and not slow"`; the moved logic is pure, so unit-test the capability method
directly with `uv run python -c` + `Path(tempfile.mkdtemp())`.

## Textual TUI conventions (`modules/cli/src/surface_cli_tui_app.py`)

- Slot count is derived, not declared per place:
  `NUM_SLOTS = max(2, int(DEFAULT_MAX_WORKERS))`, with `DEFAULT_MAX_WORKERS`
  in `modules/shared/src/taxonomy_common_constant.py`. Changing that one
  constant scales tabs, keybindings and the worker pool — never hardcode a
  slot count or write per-slot `action_*` methods. Emit bindings from a
  comprehension and funnel the actions through one `_switch_to_slot(n)`.
- `Select` wiring: handler is
  `def on_select_changed(self, event: Select.Changed)`; dispatch on
  `event.select.id` (parse the slot number from the id suffix), read
  `event.value`, and guard for `None` (returned when `allow_blank=True` and
  the user clears it). Cross-fill a sibling field with
  `self.query_one(f"#input-...-{slot}", Input).value = ...`.
- Prompt-template dropdown options come from `PROMPT_TEMPLATE_MANIFEST`
  (role -> `{title, dimensions}`). The dropdown only needs to write the
  **role string** into the prompt Input: `_run_slot` already branches on
  `is_prompt_role(value)` -> `materialize_role_template(role)`, so a role name
  and a file path share one field. Do not materialize template content in the
  UI layer.
- **Prompt-template display policy: dropdown label = role title ONLY**
  (`meta['title']`). Do NOT concatenate `title — dimensions` as the Select
  option label: that bloats the list with long wrapped lines the user did not
  ask for. Options are one line each: `Architect`, `Backend`, `Frontend`,
  `Business Analyst`. Dimensions stay as metadata context for Qwen's review,
  not as dropdown chrome.

## Output-path policy: timestamp always present

`resolve_pipeline_output_path()` in
`modules/core/src/utility_core_config_factory.py` is the single source of
truth for output naming — used by the orchestrators and every surface (CLI,
MCP, TUI). Policy (current, user-driven): **timestamp is always appended** to
the output filename, in all cases:

- no `output_file` → `DEFAULT_OUTPUT/{prompt_stem}_{YYYYmmdd-HHMMSS}.md`
- `output_file` is a directory → `{dir}/{prompt_stem}_{ts}.md`
- `output_file` exists → `{parent}/{stem}_{ts}{suffix}` (never overwrite)
- `output_file` does not yet exist → still `{parent}/{stem}_{ts}{suffix}`

Rule: when the user says "timestamp must always appear", edit
`resolve_pipeline_output_path`, not the TUI `_run_slot` override logic.
The TUI should hand the raw user path into the orchestrator and let the
central function apply the policy — duplicating the rule in two layers is the
bug, not the fix. Verify the four cases by invoking the function directly with
`uv run python -c` + a temp dir (`Path(tempfile.mkdtemp())`); do not trust the
TUI code path to prove the policy.

## Attachment workflow: host paths need a mount, not a lecture

Container filesystem is isolated from the host. A host absolute path typed into
the TUI (e.g. `/home/raka/.../.agents/finding/cli_v5.2.2.md`) fails inside the
container UNLESS that host path is bind-mounted. `scripts/podman.sh` declares
mounts in the `VOLUMES` variable; **check it first** before telling the user
their path is unreachable. Recurring attachment hotspot: user keeps finding
files at
`/home/raka/agents-arwaky/internal/qwen-web-arwaky/.agents/finding/`;
when that folder appears, add a VOLUME line to `podman.sh`:

```bash
VOLUMES="... \
         -v "\${REPO_ROOT}/.agents/finding:/root/.local/share/qwen-web/finding:Z""

```text

so the folder appears inside the container at
`/root/.local/share/qwen-web/finding/` and the TUI file picker can browse it.

**Never hardcode an absolute host path in a VOLUME line.** `scripts/podman.sh`
already computes `REPO_ROOT` from the script's own location
(`SCRIPT_DIR` → parent). Any mount that points at the repo or a subfolder of
it must use `${REPO_ROOT}/<relative-path>`. A hardcoded `/home/raka/...`
absolute path is both a review nitpick and will silently break the moment the
repo is relocated or a different user clones it. The same rule applies to any
other host path you add as a mount — prefer a variable over a literal when one
is available.

Pattern: when a user names an absolute host path as their attachment spot, add
it as a VOLUME; the answer to "my path doesn't work in container" is not
"impossible" but "that path isn't mounted yet — add it."

### Attachment-stem preference

When the user supplies an attachment, the output filename must be derived from
the **attachment's stem**, not the prompt's stem. When there is no attachment,
fall back to the prompt's stem. In both cases the timestamp is still appended.

Encode this by plumbing `attachment_path` through
`resolve_pipeline_output_path` (the central function, not a TUI override) —
duplicating the attachment-vs-prompt decision in the TUI is the bug, not the
fix. Verify with `uv run python -c` + `Path(tempfile.mkdtemp())` that the
function returns the attachment stem when `attachment_path` is given.
