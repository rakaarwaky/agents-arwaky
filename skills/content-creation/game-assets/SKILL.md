---
name: game-assets
description: "Game art and 3D models with the Imagine tools: sprites, sprite sheets, animation cycles and FX, tilesets and seamless terrain, character turnarounds and variants, UI, HUD, icons, logos; textured 3D models (.glb) from an image for Three.js, Unity, Godot or Unreal."
when-to-use: "Any game asset or game art, 2D or 3D; a 3D model, mesh or GLB from a picture; \"make this 3D\"; /game-assets."
argument-hint: "<sprite|animation|tileset|character|ui-icon|glb-3d-model> [threejs|unity|godot|unreal] [style]"
---

# Game Assets

You generate engine-ready game art and 3D models. One skill, six references —
read [`assets.md`](assets.md) first for every request, then the one reference
that matches the ask.

## Global Rules

- **Read `assets.md` first.** It holds the engine-ready defaults users never
  state, the spec checklist, style anchoring, and the read-back verification
  that apply to all game art.
- **Route to the matching reference** (table below). The routing table is the
  single home for "which reference" — never mix two references for one request
  without the user asking.
- **Engine-ready output.** Exact pixel sizes, transparent backgrounds where the
  engine expects them, consistent scale and lighting across a set, file names
  the engine can index.
- **Anchor style once.** Reuse the style anchor; never let a set drift between
  generations.
- **Read back what was generated.** Verify before declaring done; flag defects
  honestly (wrong frame count, baked shadows, mismatched palette) instead of
  describing intent.
- **Prompt craft and tool choice** (`image_gen` vs `image_edit` vs
  `reference_to_video`) live in the Grok Build `imagine` tool family — load
  the imagine tooling when the request is about how to phrase a generation
  rather than what a game needs from it.
- **y-up engine mounting** for finished `.glb` so controls, camera, and
  facing agree is the `threejs-frame-conventions` tooling in Grok Build.

## Routing

| Request | Read |
|---------|------|
| anything that moves: walk/run cycles, attacks, idles, FX, flags, fire, animation sheets | [`animation.md`](animation.md) |
| a recurring character: turnarounds, poses, outfits, palette swaps, consistency across shots | [`characters.md`](characters.md) |
| tiles, tilesets, autotiles, seamless terrain or ground textures | [`tilesets.md`](tilesets.md) |
| UI, HUD, buttons, icons, item art, logos, title screens | [`ui-icons.md`](ui-icons.md) |
| a 3D model, mesh or GLB from a picture or a generated image | [`3d.md`](3d.md) (its helper is `scripts/three_d.py`) |
| core defaults, spec checklist, style anchoring, read-back verification | [`assets.md`](assets.md) |

## Completion

- The generated asset matches the engine-ready defaults in `assets.md`.
- The asset is readable back (frame count, palette, scale) without defects.
