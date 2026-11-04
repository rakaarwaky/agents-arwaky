# Architecture Diagram — Output Contract

**Goal:** every diagram lands as one self-contained `.html` file that renders
offline, with the user told how to open it.

## Workflow

1. User describes their system architecture (components, connections, technologies)
2. Generate the HTML file following the design system
   ([`design-system.md`](design-system.md)), using the working examples in
   `templates/template.html`
3. Save with `write_file` to a `.html` file
4. User opens in any browser — works offline, no dependencies

## Save Location

Save to a user-specified path, or default to the current working directory:

```
./[project-name]-architecture.html
```

## Preview

After saving, suggest the user open it:

```bash
# macOS
open ./my-architecture.html
# Linux
xdg-open ./my-architecture.html
```

## Requirements

- **Single File:** One self-contained `.html` file
- **No External Dependencies:** All CSS and SVG must be inline (except Google Fonts)
- **No JavaScript:** Use pure CSS for any animations (like pulsing dots)
- **Compatibility:** Must render correctly in any modern web browser

## Completion

- Exactly one `.html` file exists at the target path.
- It renders correctly offline in a modern browser with no console errors.
- The user was told how to open it.
