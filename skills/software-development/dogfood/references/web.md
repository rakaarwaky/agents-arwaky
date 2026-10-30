# Web Target — Toolset and Workflow

Full web QA workflow using the `browser_*` toolset. This is the original dogfood
flow, preserved unchanged.

## Prerequisites

- Browser toolset: `browser_navigate`, `browser_snapshot`, `browser_click`,
  `browser_type`, `browser_vision`, `browser_console`, `browser_scroll`,
  `browser_back`, `browser_press`
- A target URL and testing scope from the user

## Explore rhythm

For each page or feature:

1. **Navigate:** `browser_navigate(url="...")`
2. **Snapshot:** `browser_snapshot()` — get the DOM / accessibility tree
3. **Console check:** `browser_console(clear=true)` — do this after every
   navigation and every significant interaction
4. **Visual + annotate:** `browser_vision(question="...", annotate=true)`
   — numbered `[N]` labels map to ref `@eN`
5. **Interact:** `browser_click(ref="@eN")`, `browser_type(ref="@eN", text="...")`,
   `browser_press(key="Tab")`, `browser_scroll(direction="down")`
6. **Verify:** re-check console + `browser_vision` for visual changes
7. **Evidence:** `browser_vision(question="...", annotate=false)` → save `screenshot_path`

## Tips

- Silent JS errors are among the most valuable findings — always check the console.
- Test form validation with invalid inputs (empty, too long, special chars, SQL injection patterns).
- Test keyboard navigation (Tab, Enter, Escape) for accessibility.
- Check empty states, 404 pages, and broken external links.
- Note layout issues visible in screenshots (overlapping elements, broken grids).
