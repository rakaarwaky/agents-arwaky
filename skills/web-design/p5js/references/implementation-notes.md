# p5.js Critical Implementation Notes

## Performance — Disable FES First

The Friendly Error System (FES) adds up to 10x overhead. Disable it in every production sketch:

```javascript
p5.disableFriendlyErrors = true;  // BEFORE setup()

function setup() {
  pixelDensity(1);  // prevent 2x-4x overdraw on retina
  createCanvas(1920, 1080);
}
```

In hot loops (particles, pixel ops), use `Math.*` instead of p5 wrappers — measurably faster:

```javascript
// In draw() or update() hot paths:
let a = Math.sin(t);          // not sin(t)
let r = Math.sqrt(dx*dx+dy*dy); // not dist() — or better: skip sqrt, compare magSq
let v = Math.random();        // not random() — when seed not needed
let m = Math.min(a, b);       // not min(a, b)
```

Never `console.log()` inside `draw()`. Never manipulate DOM in `draw()`. See `references/troubleshooting.md` § Performance.

## Seeded Randomness — Always

Every generative sketch must be reproducible. Same seed, same output.

```javascript
function setup() {
  randomSeed(CONFIG.seed);
  noiseSeed(CONFIG.seed);
  // All random() and noise() calls now deterministic
}
```

Never use `Math.random()` for generative content — only for performance-critical non-visual code. Always `random()` for visual elements. If you need a random seed: `CONFIG.seed = floor(random(99999))`.

## Generative Art Platform Support (fxhash / Art Blocks)

For generative art platforms, replace p5's PRNG with the platform's deterministic random:

```javascript
// fxhash convention
const SEED = $fx.hash;              // unique per mint
const rng = $fx.rand;               // deterministic PRNG
$fx.features({ palette: 'warm', complexity: 'high' });

// In setup():
randomSeed(SEED);   // for p5's noise()
noiseSeed(SEED);

// Replace random() with rng() for platform determinism
let x = rng() * width;  // instead of random(width)
```

See `references/export-pipeline.md` § Platform Export.

## Color Mode — Use HSB

HSB (Hue, Saturation, Brightness) is dramatically easier to work with than RGB for generative art:

```javascript
colorMode(HSB, 360, 100, 100, 100);
// Now: fill(hue, sat, bri, alpha)
// Rotate hue: fill((baseHue + offset) % 360, 80, 90)
// Desaturate: fill(hue, sat * 0.3, bri)
// Darken: fill(hue, sat, bri * 0.5)
```

Never hardcode raw RGB values. Define a palette object, derive variations procedurally. See `references/color-systems.md`.

## Noise — Multi-Octave, Not Raw

Raw `noise(x, y)` looks like smooth blobs. Layer octaves for natural texture:

```javascript
function fbm(x, y, octaves = 4) {
  let val = 0, amp = 1, freq = 1, sum = 0;
  for (let i = 0; i < octaves; i++) {
    val += noise(x * freq, y * freq) * amp;
    sum += amp;
    amp *= 0.5;
    freq *= 2;
  }
  return val / sum;
}
```

For flowing organic forms, use **domain warping**: feed noise output back as noise input coordinates. See `references/visual-effects.md`.

## createGraphics() for Layers — Not Optional

Flat single-pass rendering looks flat. Use offscreen buffers for composition:

```javascript
let bgLayer, fgLayer, trailLayer;
function setup() {
  createCanvas(1920, 1080);
  bgLayer = createGraphics(width, height);
  fgLayer = createGraphics(width, height);
  trailLayer = createGraphics(width, height);
}
function draw() {
  renderBackground(bgLayer);
  renderTrails(trailLayer);   // persistent, fading
  renderForeground(fgLayer);  // cleared each frame
  image(bgLayer, 0, 0);
  image(trailLayer, 0, 0);
  image(fgLayer, 0, 0);
}
```

## Performance — Vectorize Where Possible

p5.js draw calls are expensive. For thousands of particles:

```javascript
// SLOW: individual shapes
for (let p of particles) {
  ellipse(p.x, p.y, p.size);
}

// FAST: single shape with beginShape()
beginShape(POINTS);
for (let p of particles) {
  vertex(p.x, p.y);
}
endShape();

// FASTEST: pixel buffer for massive counts
loadPixels();
for (let p of particles) {
  let idx = 4 * (floor(p.y) * width + floor(p.x));
  pixels[idx] = r; pixels[idx+1] = g; pixels[idx+2] = b; pixels[idx+3] = 255;
}
updatePixels();
```

See `references/troubleshooting.md` § Performance.

## Instance Mode for Multiple Sketches

Global mode pollutes `window`. For production, use instance mode:

```javascript
const sketch = (p) => {
  p.setup = function() {
    p.createCanvas(800, 800);
  };
  p.draw = function() {
    p.background(0);
    p.ellipse(p.mouseX, p.mouseY, 50);
  };
};
new p5(sketch, 'canvas-container');
```

Required when embedding multiple sketches on one page or integrating with frameworks.

## WebGL Mode Gotchas

- `createCanvas(w, h, WEBGL)` — origin is center, not top-left
- Y-axis is inverted (positive Y goes up in WEBGL, down in P2D)
- `translate(-width/2, -height/2)` to get P2D-like coordinates
- `push()`/`pop()` around every transform — matrix stack overflows silently
- `texture()` before `rect()`/`plane()` — not after
- Custom shaders: `createShader(vert, frag)` — test on multiple browsers

## Export — Key Bindings Convention

Every sketch should include these in `keyPressed()`:

```javascript
function keyPressed() {
  if (key === 's' || key === 'S') saveCanvas('output', 'png');
  if (key === 'g' || key === 'G') saveGif('output', 5);
  if (key === 'r' || key === 'R') { randomSeed(millis()); noiseSeed(millis()); }
  if (key === ' ') CONFIG.paused = !CONFIG.paused;
}
```

## Headless Video Export — Use noLoop()

For headless rendering via Puppeteer, the sketch **must** use `noLoop()` in setup. Without it, p5's draw loop runs freely while screenshots are slow — the sketch races ahead and you get skipped/duplicate frames.

```javascript
function setup() {
  createCanvas(1920, 1080);
  pixelDensity(1);
  noLoop();                    // capture script controls frame advance
  window._p5Ready = true;      // signal readiness to capture script
}
```

The bundled `scripts/export-frames.js` detects `_p5Ready` and calls `redraw()` once per capture for exact 1:1 frame correspondence. See `references/export-pipeline.md` § Deterministic Capture.

For multi-scene videos, use the per-clip architecture: one HTML per scene, render independently, stitch with `ffmpeg -f concat`. See `references/export-pipeline.md` § Per-Clip Architecture.

## Agent Workflow

When building p5.js sketches:

1. **Write the HTML file** — single self-contained file, all code inline
2. **Open in browser** — `open sketch.html` (macOS) or `xdg-open sketch.html` (Linux)
3. **Local assets** (fonts, images) require a server: `python -m http.server 8080` in the project directory, then open `http://localhost:8080/sketch.html`
4. **Export PNG/GIF** — add `keyPressed()` shortcuts as shown above, tell the user which key to press
5. **Headless export** — `node scripts/export-frames.js sketch.html --frames 300` for automated frame capture (sketch must use `noLoop()` + `_p5Ready`)
6. **MP4 rendering** — `bash scripts/render.sh sketch.html output.mp4 --duration 30`
7. **Iterative refinement** — edit the HTML file, user refreshes browser to see changes
8. **Load references on demand** — use `skill_view(name="p5js", file_path="references/...")` to load specific reference files as needed during implementation

## Annotated HTML Skeleton (Step 3)

For **animations, video export, or simple sketches** (non-interactive generative art):
use a bare single HTML file.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Project Name</title>
  <script>p5.disableFriendlyErrors = true;</script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.11.3/p5.min.js"></script>
  <!-- <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.11.3/addons/p5.sound.min.js"></script> -->
  <!-- <script src="https://unpkg.com/p5.js-svg@1.6.0"></script> -->  <!-- SVG export -->
  <!-- <script src="https://cdn.jsdelivr.net/npm/ccapture.js-npmfixed/build/CCapture.all.min.js"></script> -->  <!-- video capture -->
  <style>
    html, body { margin: 0; padding: 0; overflow: hidden; }
    canvas { display: block; }
  </style>
</head>
<body>
<script>
// === Configuration ===
const CONFIG = {
  seed: 42,
  // ... project-specific params
};

// === Color Palette ===
const PALETTE = {
  bg: '#0a0a0f',
  primary: '#e8d5b7',
  // ...
};

// === Global State ===
let particles = [];

// === Preload (fonts, images, data) ===
function preload() {
  // font = loadFont('...');
}

// === Setup ===
function setup() {
  createCanvas(1920, 1080);
  randomSeed(CONFIG.seed);
  noiseSeed(CONFIG.seed);
  colorMode(HSB, 360, 100, 100, 100);
  // Initialize state...
}

// === Draw Loop ===
function draw() {
  // Render frame...
}

// === Helper Functions ===
// ...

// === Classes ===
class Particle {
  // ...
}

// === Event Handlers ===
function mousePressed() { /* ... */ }
function keyPressed() { /* ... */ }
function windowResized() { resizeCanvas(windowWidth, windowHeight); }
</script>
</body>
</html>
```

Key implementation patterns:
- **Seeded randomness**: Always `randomSeed()` + `noiseSeed()` for reproducibility
- **Color mode**: Use `colorMode(HSB, 360, 100, 100, 100)` for intuitive color control
- **State separation**: CONFIG for parameters, PALETTE for colors, globals for mutable state
- **Class-based entities**: Particles, agents, shapes as classes with `update()` + `display()` methods
- **Offscreen buffers**: `createGraphics()` for layered composition, trails, masks

## Performance Targets

| Metric | Target |
|--------|--------|
| Frame rate (interactive) | 60fps sustained |
| Frame rate (animated export) | 30fps minimum |
| Particle count (P2D shapes) | 5,000-10,000 at 60fps |
| Particle count (pixel buffer) | 50,000-100,000 at 60fps |
| Canvas resolution | Up to 3840x2160 (export), 1920x1080 (interactive) |
| File size (HTML) | < 100KB (excluding CDN libraries) |
| Load time | < 2s to first frame |

## Creative Divergence (use only when user requests experimental/creative/unique output)

If the user asks for creative, experimental, surprising, or unconventional output, select the strategy that best fits and reason through its steps BEFORE generating code.

- **Conceptual Blending** — when the user names two things to combine or wants hybrid aesthetics
- **SCAMPER** — when the user wants a twist on a known generative art pattern
- **Distance Association** — when the user gives a single concept and wants exploration ("make something about time")

### Conceptual Blending
1. Name two distinct visual systems (e.g., particle physics + handwriting)
2. Map correspondences (particles = ink drops, forces = pen pressure, fields = letterforms)
3. Blend selectively — keep mappings that produce interesting emergent visuals
4. Code the blend as a unified system, not two systems side-by-side

### SCAMPER Transformation
Take a known generative pattern (flow field, particle system, L-system, cellular automata) and systematically transform it:
- **Substitute**: replace circles with text characters, lines with gradients
- **Combine**: merge two patterns (flow field + voronoi)
- **Adapt**: apply a 2D pattern to a 3D projection
- **Modify**: exaggerate scale, warp the coordinate space
- **Purpose**: use a physics sim for typography, a sorting algorithm for color
- **Eliminate**: remove the grid, remove color, remove symmetry
- **Reverse**: run the simulation backward, invert the parameter space

### Distance Association
1. Anchor on the user's concept (e.g., "loneliness")
2. Generate associations at three distances:
   - Close (obvious): empty room, single figure, silence
   - Medium (interesting): one fish in a school swimming the wrong way, a phone with no notifications, the gap between subway cars
   - Far (abstract): prime numbers, asymptotic curves, the color of 3am
3. Develop the medium-distance associations — they're specific enough to visualize but unexpected enough to be interesting
