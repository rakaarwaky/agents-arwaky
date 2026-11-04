# Typed browser page rung

For page content in a supported GUI browser, the same `computer_use` tool
exposes namespaced `cua_browser_*` actions. They do not collide with other
browser tools. The contract is capability-based:

1. Discover the exact native browser `(pid, window_id)` with `list_windows` or
   native capture, then call `cua_browser_state` with both values.
2. Continue only when it returns `status:"ok"`, `binding_quality:"exact"`, and
   `mutation_allowed:true`. Select an opaque `tab_id` from that response.
3. Call `cua_browser_state` with the `tab_id` for a fresh `semantic_v2`
   snapshot. Use only refs from that newest snapshot and only for their
   declared actions.
4. Use the matching namespaced action (`cua_browser_click`,
   `cua_browser_type`, `cua_browser_navigate`, or `cua_browser_pointer`).
   Trusted input is the default. `input_route="dom_event"` is an explicit
   trust downgrade; never choose it silently after a refusal.
5. Every mutation invalidates refs. Take a fresh state snapshot before another
   typed action. Never chain actions from remembered refs.

`cua_browser_prepare` is a separate approved setup action. Driver-owned
`isolated_new`/`isolated_named` profiles require explicit `allow_launch=true`.
An `existing_profile` is decided by cua-driver's immutable permission mode.
Prefer `isolated_new` unless the task genuinely needs the user's signed-in
session — attaching to an existing profile exposes its live pages, cookies,
and storage over the browser protocol.

Authorization paths for `existing_profile`:

1. **Config grant (standard and unrestricted modes).** When
   `computer_use.grant_existing_profile: true` is set, the runtime is
   launched pre-authorized in standard mode (`--grant existing-profile`) and
   Hermes applies the same host-side floor in unrestricted mode. If it is not
   set, both modes fail closed. Tell the user to flip that config key and
   restart the session if they want this; do not retry or work around it.
2. **Bounded manifest.** When `computer_use.permission_mode: bounded` is
   configured with a reviewed `capability_manifest`, prepares inside the
   manifest's scope succeed without prompts and everything else fails closed.

Explicit Hermes YOLO (`--yolo`, `/yolo`, or `approvals.mode: off`) launches an
unrestricted runtime with no runtime Cua approval prompts, but it does not
substitute for `grant_existing_profile: true`.

These settings belong to runtime launch. The agent cannot add or change them
after the runtime starts. Without the applicable grant or bounded manifest,
`existing_profile` fails closed. Report the refusal and name the config key;
do not retry, downgrade trust, or work around it.

Every MCP transport owns a private lifecycle session inside the runtime. The
public session name only labels cursor identity and session-scoped state. It
does not select, share, or keep a runtime alive.

Use the native capture/AX/pixel/foreground ladder for browser chrome, browser
permission UI, OS prompts, native dialogs, extension surfaces, unsupported
engines, and any typed route that cannot prove exact binding or mutation
permission. `cua_browser_dialog` covers page JavaScript dialogs only.

## Key shortcuts vary per platform

Use the host's idiomatic modifier:

| Common action | macOS | Windows / Linux |
|---|---|---|
| Save | `cmd+s` | `ctrl+s` |
| New tab | `cmd+t` | `ctrl+t` |
| Close tab / window | `cmd+w` | `ctrl+w` |
| Copy / paste | `cmd+c` / `cmd+v` | `ctrl+c` / `ctrl+v` |
| Address bar | `cmd+l` | `ctrl+l` |
| App switcher | `cmd+tab` | `alt+tab` |

When in doubt, capture and look for menu hints, or ask the user which
shortcut to use.
