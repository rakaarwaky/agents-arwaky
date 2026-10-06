# Video sourcing workflow for teaching sessions

## DuckDuckGo + oEmbed pipeline (non-browser, reliable)

Used for finding verified YouTube URLs that directly match the Vector Fundamentals module.

### Steps

1. **Targeted DuckDuckGo Lite search**:
   - `curl -s -A 'Mozilla/5.0' "https://lite.duckduckgo.com/lite/?q=\"Site:youtube.com Khan Academy \"Vector intro for linear algebra\"\"`
   - Save raw HTML.

2. **Extract candidate YouTube URLs**:
   - `grep -o 'youtube.com/watch?v=[A-Za-z0-9_-]\{11\}'`

3. **Verify each URL via oEmbed**:
   - `curl -s "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={id}&format=json"`
   - Confirm:
     - Title matches expected topic.
     - Author matches target channel (e.g., Khan Academy, 3Blue1Brown).
     - Duration <= budget (e.g., 15 min max per concept).

4. **Duration scrape (optional)**:
   - `curl -s "https://www.youtube.com/watch?v={id}" | grep -o '"lengthSeconds":"[0-9]*"' | head -1`
   - Convert seconds to minutes for budgeting.

5. **Record valid videos**:
   - Keep up to 6–8 videos per module (rotation prevents binge-watching one topic).
   - Format for manual copy‑paste into session inputs.

### Notes

- The fetch‑tool version (`mcp__fetch__fetch_markdown`) **fails** on YouTube URLs (returns browser lock error). Use the DuckDuckGo pipeline exclusively.
- The pipeline ensures the video description / metadata matches the requested educational goal.
- For modules where an external tutorial is required (e.g., vector magnitude, unit vector normalization), search for `"Khan Academy vector length magnitude unit vectors linear algebra"` or `"3Blue1Brown Vectors\"` and filter by author.

### Example workflow (current Vector Fundamentals module)

```bash
# Search 1: Khan Academy intro
https://lite.duckduckgo.com/lite/?q=site:youtube.com+Khan+Academy+"Vector+intro+for+linear+algebra"

# Search 2: Vector length + magnitude + unit vectors
https://lite.duckduckgo.com/lite/?q=site:youtube.com+Khan+Academy+vector+length+magnitude+unit+vectors+linear+algebra

# Search 3: 3Blue1Brown Vectors
https://lite.duckduckgo.com/lite/?q=site:youtube.com+3Blue1Brown+"Vectors+chapter+1"
```

Result yields:
- Khan Academy — "Vector intro for linear algebra" (br7tS1t2SFE) 5 min
- Khan Academy — "Adding vectors" (8QihetGj3pg) 7 min  
- 3Blue1Brown — "Vectors | Chapter 1, Essence of linear algebra" (fNk_zzaMoSs) 9 min
- Excellent Link Academy — "Introduction to Vectors: Definition, Representation & Unit Vector" (TXdT8UqkRnE) 27 min (for unit‑vector + position vectors)
- Mario’s Math Tutoring — "Vectors Introduction for Beginners" (BYARjX1neao) 6 min (early start)
- Professor Leonard — "Calculus 3 Lecture 11.1: An Introduction to Vectors" (tGVnBAHLApA) 27 min (3‑D extension)
- LearnHub — "Calculating Vector Magnitude & Unit Vectors in 3D" (ftSxSA3lhCc) 9 min
- Basis Academy — "Adding, Subtracting & Scaling Vectors — What It Looks Like" (w2W94EIBjk0) 6 min (visual operations)
- MerbsConnect — "Don’t Skip These Vector Basics!" (N0q7RjWzi9k) 29 min (full fundamentals summary)

All URLs pass oEmbed verification (title + author match). Use the concise list above.

### When to apply

- First teaching session of any module.
- Need to present core concepts without a browser (no interactive UI).
- Must work under stable, reproducible conditions across multiple sessions.

### Files referenced

- This file is referenced in `study-roadmap-builder/SKILL.md` under **Video sourcing for a session's input block**.