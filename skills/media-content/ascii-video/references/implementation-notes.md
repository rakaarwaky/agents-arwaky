# ASCII Video — Critical Implementation Notes and Performance Targets

## Brightness — Use `tonemap()`, Not Linear Multipliers

This is the #1 visual issue. ASCII on black is inherently dark. **Never use `canvas * N` multipliers** — they clip highlights. Use adaptive tonemap:

```python
def tonemap(canvas, gamma=0.75):
    f = canvas.astype(np.float32)
    lo, hi = np.percentile(f[::4, ::4], [1, 99.5])
    if hi - lo < 10: hi = lo + 10
    f = np.clip((f - lo) / (hi - lo), 0, 1) ** gamma
    return (f * 255).astype(np.uint8)
```

Pipeline: `scene_fn() → tonemap() → FeedbackBuffer → ShaderChain → ffmpeg`

Per-scene gamma: default 0.75, solarize 0.55, posterize 0.50, bright scenes 0.85. Use `screen` blend (not `overlay`) for dark layers.

## Font Cell Height

macOS Pillow: `textbbox()` returns wrong height. Use `font.getmetrics()`: `cell_height = ascent + descent`. See `references/troubleshooting.md`.

## ffmpeg Pipe Deadlock

Never `stderr=subprocess.PIPE` with long-running ffmpeg — buffer fills at 64KB and deadlocks. Redirect to file. See `references/troubleshooting.md`.

## Font Compatibility

Not all Unicode chars render in all fonts. Validate palettes at init — render each char, check for blank output. See `references/troubleshooting.md`.

## Per-Clip Architecture

For segmented videos (quotes, scenes, chapters), render each as a separate clip file for parallel rendering and selective re-rendering. See `references/scenes.md`.

## Performance Targets

| Component | Budget |
|-----------|--------|
| Feature extraction | 1-5ms |
| Effect function | 2-15ms |
| Character render | 80-150ms (bottleneck) |
| Shader pipeline | 5-25ms |
| **Total** | ~100-200ms/frame |
