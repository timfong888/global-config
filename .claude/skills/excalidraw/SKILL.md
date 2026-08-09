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

Element JSON schema — every element requires the `"type"` discriminator (`"rectangle"`, `"ellipse"`, `"text"`, `"line"`, `"arrow"`) plus the versioning fields the loader checks: unique `id`, `version: 1`, `versionNonce` (any int), `seed` (any int), `isDeleted: false`, `boundElements: null`, `locked: false`. Then type-specific fields:

- **rectangle / ellipse**: `type`, `x, y, width, height, strokeColor, backgroundColor, fillStyle, strokeWidth, roughness, opacity, angle`
- **text**: `type: "text"`, adds `text, fontSize, fontFamily, textAlign, verticalAlign, baseline, width, height`
- **line / arrow**: `type`, `x, y, points: [[x0,y0],[x1,y1],...]`, plus `startArrowhead` / `endArrowhead` (`null` or `"arrow"`)

Before shipping a generated file, open it in the target loader (Obsidian's Excalidraw plugin, or excalidraw.com) to confirm it actually renders — a schema-valid but loader-rejected fixture fails silently otherwise.

Default canvas 800×600. Common layouts: flowchart = rectangles + arrows; hierarchy = rectangles at different y-levels + vertical lines; quadrant = two perpendicular lines + 4 labels; triangle/trilemma = 3 lines + vertex labels + a position-dot ellipse (vertices at `(cx, cy-s)`, `(cx-0.866s, cy+0.5s)`, `(cx+0.866s, cy+0.5s)`).

Write to `design/excalidraw/<name>.excalidraw.md` relative to the source document (create the dir
if needed), then return the embed: `![[name.excalidraw|500]]` (width 400-600 typical).

`<name>` comes from the user's request, so treat it as a filename, not a path. Require
`^[A-Za-z0-9][A-Za-z0-9._-]*$` — reject anything containing `/`, `\`, or `..` — then resolve the
target and confirm it is still inside `design/excalidraw` before writing:

```bash
[[ "$NAME" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || { echo "unsafe diagram name"; exit 1; }
OUT_DIR="$(cd "$(dirname "$SOURCE_DOC")" && pwd -P)/design/excalidraw"
mkdir -p "$OUT_DIR"
OUT_DIR="$(cd "$OUT_DIR" && pwd -P)"   # resolve any symlink in design/excalidraw itself
OUT="$OUT_DIR/$NAME.excalidraw.md"
[[ "$OUT" == "$OUT_DIR"/* ]] || { echo "output path escaped design/excalidraw"; exit 1; }
```

## Mode: export

Tool: `excalidraw-brute-export-cli` (Playwright-based, needs internet + Node 18+).

**This renders through excalidraw.com — the scene leaves the machine.** Say that to the user and
get explicit confirmation before exporting any diagram you didn't generate yourself from public
content. For confidential diagrams, don't use this path: render offline instead, either with
Obsidian's Excalidraw plugin ("Export as PNG/SVG" on the open drawing) or a local
`@excalidraw/excalidraw` + headless-browser script that never loads excalidraw.com.

Installing the CLI runs third-party code, so pin an exact version and confirm with the user before
installing. Prefer a project-local dependency with a reviewed lockfile (`npm ci`) over a global
install:

```bash
# one-time, after user confirmation — check `npm view excalidraw-brute-export-cli versions`
# and substitute the exact reviewed version for X.Y.Z
npm install --save-dev excalidraw-brute-export-cli@X.Y.Z   # then commit package-lock.json
npx --no-install excalidraw-brute-export-cli \
  -i input.excalidraw -o output.png \
  -f png -s 2 --headless
```

Flags: `-f png|svg`, `-s 1|2|3` (scale — use 2 for retina), `-b` include background (default transparent), `-d` dark mode, `-e` embed scene data in the image, `--headless`.

For `.excalidraw.md` inputs, don't grab the first ```` ```json ```` fence in the file — extract
specifically from inside the `%%...%%` / `# Drawing` block, into a unique temp file. The input path
may come from the user or a glob, so hold it in `INPUT`, confirm it resolves inside the workspace,
and always pass it quoted — an unquoted path that begins with `-` or contains whitespace changes
how `awk` parses its arguments:

```bash
INPUT="$1"
[ -f "$INPUT" ] || { echo "no such file: $INPUT"; exit 1; }
REAL_INPUT="$(cd "$(dirname -- "$INPUT")" && pwd -P)/$(basename -- "$INPUT")"
# Resolve any symlink in the input path itself
[ -L "$REAL_INPUT" ] && REAL_INPUT="$(readlink -f -- "$REAL_INPUT")"
[[ "$REAL_INPUT" == "$(pwd -P)"/* ]] || { echo "input outside workspace"; exit 1; }

TMP=$(mktemp)
awk '/^%%$/{n++; next} n==1' -- "$REAL_INPUT" \
  | awk '/^```json$/{f=1; next} /^```$/{f=0} f' > "$TMP"
npx --no-install excalidraw-brute-export-cli -i "$TMP" -o output.png -f png -s 2 --headless
rm "$TMP"
```

Batch — handle both `*.excalidraw` and `*.excalidraw.md`, routing the latter through the extraction step above, and derive the embed extension from `-f`:

```bash
for f in *.excalidraw *.excalidraw.md; do
  [ -e "$f" ] || continue
  case "$f" in
    *.excalidraw.md)
      TMP=$(mktemp)
      awk '/^%%$/{n++; next} n==1' -- "./$f" \
        | awk '/^```json$/{fl=1; next} /^```$/{fl=0} fl' > "$TMP"
      npx --no-install excalidraw-brute-export-cli \
        -i "$TMP" -o "${f%.excalidraw.md}.png" -f png -s 2 --headless
      rm "$TMP"
      ;;
    *.excalidraw)
      npx --no-install excalidraw-brute-export-cli \
        -i "./$f" -o "${f%.excalidraw}.png" -f png -s 2 --headless
      ;;
  esac
done
```

Report the output path/size and the markdown embed, matching whatever extension `-f` actually produced: `![Diagram Name](./path.png)` for `-f png`, `![Diagram Name](./path.svg)` for `-f svg`.
