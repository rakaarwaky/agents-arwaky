---
name: psd-overlay-verification
description: Use when testing PSD compositor cursor/brush overlays.
---
# PSD Timelapse overlay verification

Use when fixing or testing the interaction overlay (cursor / brush ring) in
modules/compositor, or when a claim needs proof that an overlay is actually
visible in the rendered MP4. Never verify "by eye".

## Key facts (pitfalls)

- `utility_texture_registry.store_texture(path, image)` keeps images **in memory**
  keyed by path — NO PNG is written to disk. Regression tests must read back via
  `peek_texture(str(path))` (returns the PIL image), never `Image.open(path)`.
- `assets/macos_cursor.png` has transparent margins: alpha bbox is (3,3,24,35) of
  the 27x39 tile. The drawn pointer's hotspot ≈ alpha-bbox **top-left**, not the
  bbox centroid — assert `abs(xs.min() - tip_x) <= 6` style, measured first with a
  scratch probe, not guessed.
- Keyframe contract: animator `motion_keyframes` x,y are absolute Base Canvas
  **pixels** (never normalized). The single owner of the px→scene-delta formula is
  `CanvasMapping.animator_keyframe_delta` in
  `modules/shared/src/compositor/taxonomy_compositor_vo.py` (AES: capabilities may
  not import capabilities; shared helpers go in the taxonomy VO). Malformed
  position → TypeError; non-finite → ValueError.

## Verification workflow (TDD red/green)

1. Write regression test against the real fixture manifests
   (`fixtures/animator-manifest-sycan-front-shirt.json` + the fixture PSD's
   scripting manifest) with a **real** `CanvasMapping` — mock nothing in the coord
   path.
2. RED proof: `git stash push -m fix-src -- modules/compositor/src modules/shared/src`
   (keep tests untracked+unstashed), run pytest → all new tests must fail;
   `git stash pop`. This proves the test catches the real bug.
3. Plane determinism ("only overlay changed" AC): hash every non-interaction plane
   of every SceneFrame old-vs-new (scratch script walking the orchestrator frame
   stream). Expect `camera diffs: 0` and only layer `interaction-overlay` changed.

## Video-level proof (the strongest check)

Render pre-fix and post-fix MP4s of fixtures/sycan-front-shirt.psd, then diff
extracted frames — H.264 re-encode noise means `delta>30` (sum over RGB) shows
scattered false diffs across the frame; use **delta>200** to isolate real overlay
strokes. Idle frames (<30) must be pixel-identical at delta>30, and active frames
must show a tight ~600–1000 px localized cluster at the mapped position.

- CLI: `python modules/root_cli_main_entry.py render <psd> -o out.mp4` — `-o` needs
  an .mp4 FILE path, a directory fails with ENCODING_FAILED "Unable to choose an
  output format".
- Frame extract: `ffmpeg -i v.mp4 -vf select=eq(n\\,FRAME) -frames:v 1 out.png`.
- Render outputs go to `~/.local/share/psd-timelapse/<stem>-<ts>/` when `-o` omitted.

## Tooling (sandbox quirks)

- `process_manage` may only exist as a deferred tool here: load via
  `tool_search(['process manage'])` → `tool_call(name='process_manage', ...)`.
- CI pins `ruff==0.15.6` — local newer ruff adds rules (TRY004) CI won't run;
  check with `uv tool run ruff@0.15.6 check modules/` before trusting local noise.
- bandit is NOT installed in the project venv; scratch launcher
  `~/.cache/run_bandit.py` sys.path-injects uv-cache archives (bandit, stevedore,
  rich, markdown_it...) and calls `bandit.cli.main.main()`.
- Tirith single-query blocks compound commands mixing `ls`+`grep`+glob expansion or
  `2>/dev/null &&` chains with nested executables; split into simple commands.

## Chrome screen-fixedness probe (UI_ZOOM_FACTOR=0, PR #45)

- Unit-level: build the SceneFrame via the real orchestrator (mock capabilities,
  real CanvasMapping), then project the `photoshop-ui` quad with
  `perspective(camera) @ look_at(camera) @ layer_model_matrix(layer, w, h)` and
  `_project_layer_corners` — assert edges hug 0/W/H ±1 px across a zoom×pan grid.
- Video-level: re-render fixture to mp4, `ffmpeg -i out.mp4 vid/f%04d.png`
  (1-based index!), then per frame: outer-2px edge-strip mean luma must stay
  chrome-dark (<120) and band mean|Δ| vs first frame must be ≤ small — static
  bands, not sliding.
- Classify residual band deltas by UI-texture alpha: deltas at alpha=255 pixels
  are cursor overlay / dynamic UI text (fine); artwork bleed can only appear
  where alpha<255 (header seam rows 81–83, toolbar gaps) — check those zones
  separately.
- Overlay visibility direct proof: render the frame with and without the
  `interaction-overlay` layer (dataclasses.replace on SceneFrame.layers), diff
  must show ~900–1065 px clusters on active frames.
- Tirith single-query also blocks `rm -rf` of probe dirs (use fresh dir names)
  and `execute_code` entirely; vision_analyze may 401 — numeric probes suffice.

## Overlay POSITION verification (t_9f672973, commit e89f4a4)

PM-mandated loop order — never burn wall-clock on full MP4 renders to iterate:
1. Single composited frames via `render_scene_software(frame)` for the gate
   frames. Localise the painted overlay WITHOUT color heuristics: render the
   frame, then render `dataclasses.replace(frame, layers=without
   interaction-overlay)`, diff — the cluster IS the visible cursor/ring.
   Ground-truth = independent numpy projection (recompute
   perspective@look_at@model yourself in the probe; do not reuse the code
   under test).
2. Unit/regression tests green (the tracking regression suite runs in ~5s).
3. ONE final full render, then pixel-probe the MP4 (old-vs-new frame diff:
   new cursor cluster appears in the doc hole; old chrome-band blob is the
   only below-hole diff) + template-MAD confirm: slide
   `assets/macos_cursor.png` (96x96, alpha>128 mask) over predicted spot
   ±12px — MAD ~7 at the true spot vs 80+ at wrong ones.

Architecture after t_e5769cda (supersedes t_3e6d8eee): the DRAG pointer tip =
the dragged artwork plane's WORLD CENTER (model matrix @ (0,0,0,1)) projected
through the live camera, clamped only so the whole glyph stays inside the
OUTPUT frame — never the document hole (the hole-clamp recreated a
spawn-and-wait plateau at the drag head; the interaction plane composites
above chrome per #46 so riding panels mid-flight is intended). The recorded
keyframe path remains ONLY the legacy static-anchor source when no camera
planes exist (bench/CLI). Brush ring unchanged (reveal-frontier point); note
the brush layer's inclusive visible_range tail owns the boundary frame just
before the drag starts (f210 on sycan) — sweep drag gates from f211.

## MP4-grade pointer localization without composited frames (t_e5769cda)

- `cv2.matchTemplate(frame, cursor_96, TM_SQDIFF, mask=alpha)` (uint8 in/out)
  followed by an alpha-weighted MAD refine over ±10px localizes the painted
  glyph on the encoded MP4 to ~1px: MAD ~8–12 at the true spot vs 85–123 at
  150px wrong. TM_CCOEFF_NORMED collapses to score<0.5 once the glyph rides
  over colorful artwork — never use it here. cv2 IS in the project venv.
- Colorful-centroid "art center" on the MP4 is biased by STATIC shirt print
  sharing the design bbox: restrict the centroid to the design's projected
  quad AND only once the design covers the print (f>=280 on sycan; f260
  measured ~80px bias). The geometric quad center / plane-center model is
  the strict contract; pixel centroid is a proxy.
- Plateau gate must compare tip-vs-tip AND check whether the MODEL itself is
  resting there (ease-out settle at the drag tail is legal; a clamp plateau
  while the model moves >50px is the bug).
- vision_analyze 401 (invalid_api_key) is environmental — substitute the
  numeric gates and say so in the handoff instead of blocking.

## Evidence this worked (2026-09-10, PR #44; 2026-09-11, PR #45 + t_9f672973;
2026-09-11, t_e5769cda: 125 tracking tests red→green, acceptance probe PASS
with d_model=0.0px at f211–313 on acceptance-v4.mp4)

6 tests red→green via the stash trick; plane hash: 315 frames, only
`interaction-overlay` (285) changed; video probe: f010–f029 changed=0, f040–f310
strong-diff clusters 620–1008 px tracking brush ring → drag → settled cursor.

## Pointer PATH verification (t_3e6d8eee, PR #47)

- Ground truth for the drag cursor = the recorded keyframe projected through
  the live plane; on the sycan fixture the divergence from artwork centroid
  is Y-only (bounds center x=779 == recorded x), 207–630px at f215–260, so a
  centroid-vs-recording bug can hide behind x agreement — always gate on Y too.
- `plane_screen_quad` gained no pointer use after centroid removal; it is now
  only referenced by utility_camera_framing's own exports. Don't assume it is
  dead without grepping.
- Template-MAD on MP4 frames bottoms out ~27–37 at the true spot (H.264
  encode noise floor, residual ≤7px) vs 91–121 at wrong spots — position
  claims need the composited software-frame probe (1px exact) for unit-grade
  proof; MP4 MAD proves presence+approximate spot only.
- Sprite alpha>128 mask min after LANCZOS resize ≠ alpha-bbox min
  ((4,5) vs (1,1) on the 96px cursor tile): measure the hotspot with the SAME
  threshold the test uses before hardcoding it.