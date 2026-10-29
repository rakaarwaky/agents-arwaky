# Input scenarios — drag & drop, scroll, focus, screenshots

## Drag & drop

Prefer element indices:

```text
computer_use(action="drag", from_element=3, to_element=17)

```text

For a rubber-band selection on empty canvas, use coordinates:

```text
computer_use(action="drag",
             from_coordinate=[100, 200],
             to_coordinate=[400, 500])

```text

## Scroll

Scroll the viewport under an element (most common):

```text
computer_use(action="scroll", direction="down", amount=5, element=12)

```text

Or at a specific point:

```text
computer_use(action="scroll", direction="down", amount=3, coordinate=[500, 400])

```text

## Managing what's focused

`list_apps` returns running apps with bundle IDs / process names, PIDs,
and window counts. `focus_app` routes input to an app without raising
it. You rarely need to focus explicitly — passing `app=...` to
`capture` / `click` / `type` will target that app's frontmost window
automatically.

## Delivering screenshots to the user

When the user is on a messaging platform (Telegram, Discord, etc.) and
you took a screenshot they should see, save it somewhere durable and
use `MEDIA:/absolute/path.png` in your reply. cua-driver's screenshots
are PNG or JPEG bytes (mimeType is on the response); write them out
with `write_file` or the terminal (`base64 -d`).

On CLI, you can just describe what you see — the screenshot data stays
in your conversation context.

