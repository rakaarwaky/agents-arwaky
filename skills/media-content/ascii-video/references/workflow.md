# ASCII Video — Build Workflow

The 4-step build sequence for every ASCII video project. Steps 1 and 2 must complete before any code is written; Step 4 gates the full render.

## Step 1: Creative Vision

Before any code, articulate the creative concept:

- **Mood/atmosphere**: What should the viewer feel? Energetic, meditative, chaotic, elegant, ominous?
- **Visual story**: What happens over the duration? Build tension? Transform? Dissolve?
- **Color world**: Warm/cool? Monochrome? Neon? Earth tones? What's the dominant hue?
- **Character texture**: Dense data? Sparse stars? Organic dots? Geometric blocks?
- **What makes THIS different**: What's the one thing that makes this project unique?
- **Emotional arc**: How do scenes progress? Open with energy, build to climax, resolve?

Map the user's prompt to aesthetic choices. A "chill lo-fi visualizer" demands different everything from a "glitch cyberpunk data stream."

## Step 2: Technical Design

- **Mode** — which of the 6 modes in `SKILL.md`
- **Resolution** — landscape 1920x1080 (default), portrait 1080x1920, square 1080x1080 @ 24fps
- **Hardware detection** — auto-detect cores/RAM, set quality profile. See `references/optimization.md`
- **Sections** — map timestamps to scene functions, each with its own effect/palette/color/shader config
- **Output format** — MP4 (default), GIF (640x360 @ 15fps), PNG sequence

## Step 3: Build the Script

Single Python file. Component order (with references):

1. Hardware detection + quality profile — `references/optimization.md`
2. Input loader — mode-dependent; `references/inputs.md`
3. Feature analyzer — audio FFT, video luminance, or synthetic
4. Grid + renderer — multi-density grids with bitmap cache; `references/architecture.md`
5. Character palettes — multiple per project; `references/architecture.md` § Palettes
6. Color system — HSV + discrete RGB + harmony generation; `references/architecture.md` § Color
7. Scene functions — each returns `canvas (uint8 H,W,3)`; `references/scenes.md`
8. Tonemap — adaptive brightness normalization; `references/composition.md`
9. Shader pipeline — `ShaderChain` + `FeedbackBuffer`; `references/shaders.md`
10. Scene table + dispatcher — time → scene function + config; `references/scenes.md`
11. Parallel encoder — N-worker clip rendering with ffmpeg pipes
12. Main — orchestrate full pipeline

## Step 4: Quality Verification

- **Test frames first**: render single frames at key timestamps before full render
- **Brightness check**: `canvas.mean() > 8` for all ASCII content. If dark, lower gamma
- **Visual coherence**: do all scenes feel like they belong to the same video?
- **Creative vision check**: does the output match the concept from Step 1? If it looks generic, go back
