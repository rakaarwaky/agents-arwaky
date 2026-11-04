# What to write

The `[ui.status_line]` table, by desired behavior.

**Goal:** a valid `[ui.status_line]` block for built-in items, a custom script, or off.

## Built-in

When they want the row and did not ask for a script:

```toml
[ui.status_line]
type = "builtin"
items = ["cwd", "model", "context"]
```

`items` are `cwd`, `model`, `context`, `cost`, `turn-timer`,
`session-name`, in the order listed. Omitting `items` means `cwd`,
`model`, `context`. Keep at least one.

## Custom script

When they asked for one, or for something the built-in items cannot
show:

```toml
[ui.status_line]
type = "command"
command = "~/.grok/statusline.sh"
```

Save the script under the same home as the config file, then `chmod +x`
it. Set `command` to that path. The block above is the default home;
substitute the resolved home when `GROK_HOME` is set. A `~/` prefix
expands to the home directory. `command` may be a shell line.

`refresh_interval` is seconds from 1 to 86400, and only with
`type = "command"`. Set it when the row must update while idle. A
timer run sets `trigger` to `refresh_interval`; any other run sets it
to `state`. Call the network on `refresh_interval` and read a cache on
`state`.

`padding` is 0 to 16 on either type. It insets the row. It does not
move it. The row's place is fixed: bottom of the full screen, under
the prompt info row in minimal mode. A script prints text. It does not
place or align that text.

## Off

```toml
[ui.status_line]
type = "disabled"
```

`off`, `none`, and `hidden` mean the same as `disabled`.

## Completion

- Exactly one `type` is set, from `builtin`, `command`, or `disabled`.
- `builtin` keeps at least one item; `command` points at an executable
  script under the config home; `refresh_interval` (if set) is 1–86400
  and only with `type = "command"`.
