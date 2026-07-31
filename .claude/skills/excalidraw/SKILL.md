---
name: excalidraw
description: Generate or export Excalidraw diagrams. Generate mode builds a diagram programmatically from a text description; export mode renders .excalidraw/.excalidraw.md files to PNG or SVG for GitHub. Activate on "create excalidraw", "generate diagram", "draw excalidraw", "export excalidraw", "export wireframes", or "convert excalidraw to png".
---

# Excalidraw

## Modes

- `generate` — build a `.excalidraw.md` file programmatically from a description.
- `export` — render an existing `.excalidraw` / `.excalidraw.md` file to PNG or SVG.

## File format

`.excalidraw.md` is a markdown wrapper: frontmatter + a text-elements list (for search) + the raw scene JSON inside a `%%...%%` fence. The `.md` extension (rather than bare `.excalidraw`) is what makes Obsidian's Excalidraw plugin treat the file as a native drawing it can open in canvas view — keep it when the target vault uses that plugin; use plain `.excalidraw` (pure JSON, no wrapper) everywhere else.

````markdown
---
excalidraw-plugin: parsed
---
==⚠ Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu ==

# Text Elements
[searchable text content]

%%
# Drawing
```json
{ "type": "excalidraw", "version": 2, "source": "https://excalidraw.com", "elements": [...], "appState": {...} }
```
%%
````

## Mode: generate

Element JSON schema — every element needs a unique `id`, a `seed` (any int), `version: 1`, `isDeleted: false`, `boundElements: null`, `locked: false`, plus type-specific fields:

- **rectangle / ellipse**: `x, y, width, height, strokeColor, backgroundColor, fillStyle, strokeWidth, roughness, opacity, angle`
- **text**: adds `text, fontSize, fontFamily, textAlign, verticalAlign, baseline, width, height`
- **line / arrow**: `x, y, points: [[x0,y0],[x1,y1],...]`, plus `startArrowhead` / `endArrowhead` (`null` or `"arrow"`)

Default canvas 800×600. Common layouts: flowchart = rectangles + arrows; hierarchy = rectangles at different y-levels + vertical lines; quadrant = two perpendicular lines + 4 labels; triangle/trilemma = 3 lines + vertex labels + a position-dot ellipse (vertices at `(cx, cy-s)`, `(cx-0.866s, cy+0.5s)`, `(cx+0.866s, cy+0.5s)`).

Write to `design/excalidraw/<name>.excalidraw.md` relative to the source document (create the dir if needed), then return the embed: `![[name.excalidraw|500]]` (width 400-600 typical).

## Mode: export

Tool: `excalidraw-brute-export-cli` (Playwright-based; renders via excalidraw.com, needs internet + Node 18+).

```bash
npm install -g excalidraw-brute-export-cli   # one-time

excalidraw-brute-export-cli \
  -i input.excalidraw -o output.png \
  -f png -s 2 --headless
```

Flags: `-f png|svg`, `-s 1|2|3` (scale — use 2 for retina), `-b` include background (default transparent), `-d` dark mode, `-e` embed scene data in the image, `--headless`.

For `.excalidraw.md` inputs, extract the JSON from the `%%...%%` fence first:
```bash
grep -A 99999 '```json' input.excalidraw.md | tail -n +2 | grep -B 99999 '```' | head -n -1 > temp.excalidraw
excalidraw-brute-export-cli -i temp.excalidraw -o output.png -f png -s 2 --headless
rm temp.excalidraw
```

Batch: `for f in *.excalidraw; do excalidraw-brute-export-cli -i "$f" -o "${f%.excalidraw}.png" -f png -s 2 --headless; done`.

Report the output path/size and the markdown embed: `![Diagram Name](./path.png)`.
