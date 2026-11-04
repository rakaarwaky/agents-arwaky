---
name: architecture-diagram
description: "Dark-themed SVG architecture/cloud/infra diagrams as HTML."
when-to-use: "Use when the user asks for architecture, cloud, or infrastructure diagrams — system topology, microservice mesh, VPC/region/subnet layout, database/API maps, or any dark-themed SVG diagram as a standalone HTML file."
argument-hint: "<architecture-description> [output-file.html]"
---

# Architecture Diagram

You generate professional, dark-themed technical architecture diagrams as standalone
HTML files with inline SVG. No external tools, API keys, or rendering libraries —
write one self-contained `.html` file and open it in a browser.

## Global Rules

- **Scope.** Software systems, cloud infrastructure (VPC, regions, subnets, managed
  services), microservice/service-mesh topology, database+API maps, deployment
  diagrams — dark grid-backed aesthetic (detailed lists and out-of-scope
  guidance: [`references/scope.md`](references/scope.md)).
- **Output contract.** Single self-contained `.html`, all CSS/SVG inline (Google
  Fonts exception), no JavaScript; save to a user-specified path or default
  `./[project-name]-architecture.html`; suggest `open` (macOS) / `xdg-open`
  (Linux) after saving.
- **Design system.** Semantic component colors (front/backend/database/cloud/
  security/bus/external), typography, background grid, component masking,
  connection z-order, boundary and legend rules:
  [`references/design-system.md`](references/design-system.md).
- **Structure.** Generated HTML is four-part (header, SVG card, summary
  cards, footer); the canonical copy source is `templates/template.html`,
  which carries working examples of every component type — load it with
  `skill_view(name="architecture-diagram", file_path="templates/template.html")`.
- **Completion.** The output is one `.html` file that renders in a modern
  browser offline, follows the design system, and places the legend outside
  all boundaries.

## Routing

| Step              | Reference                                                             | Purpose                                                                                      |
| ----------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Scope             | [`references/scope.md`](references/scope.md)                          | What fits the dark tech aesthetic, what to route elsewhere, and the general-fallback rule.    |
| Design system     | [`references/design-system.md`](references/design-system.md)          | Colors, typography, background, component masking, connection rules, spacing, document shape. |
| Structure example | [`templates/template.html`](templates/template.html)                  | Working HTML template with every component type, arrow style, security group, region, legend.  |
| Output contract   | [`references/output.md`](references/output.md)                       | Save location, preview commands, single-file requirements, provenance attribution.             |
