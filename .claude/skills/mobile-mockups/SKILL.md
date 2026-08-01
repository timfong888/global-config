---
name: mobile-mockups
description: Generate and deliver high-fidelity mobile app mockups as full-size PNGs embedded inline in Linear issue comments. Use whenever producing UI mockups for mobile (Expo, React Native, Flutter) tasks. TRIGGER on: "generate mockup", "create mockup", "show mockup", "mockup for mobile", "embed mockup", "PNG mockup".
---

# Mobile Mockup Generation & Delivery

Use this skill whenever generating UI mockups for mobile app tasks. Covers rendering, sizing, and delivery standards so mockups are always visible inline — no attachment links to click.

---

## 1. Rendering Standard

Generate mockups as HTML files rendered to PNG via Playwright at **mobile viewport dimensions**.

### Required dimensions

| Target | Viewport (px) | Device scale |
|---|---|---|
| iPhone (default) | 390 × 844 | 2 (retina) |
| iPhone Pro Max | 430 × 932 | 3 |
| Android standard | 412 × 915 | 2 |

Always use **device scale ≥ 2** — this produces a physical PNG of 780 × 1688 px minimum, which renders at a readable size when embedded in Linear.

### Playwright render snippet

```python
from playwright.sync_api import sync_playwright

def render_mockup(html_path: str, out_path: str, width=390, height=844, scale=2):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=scale,
        )
        page.goto(f"file://{html_path}")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=out_path, full_page=False)
        browser.close()
```

- Use `full_page=False` to capture exactly the viewport (the device frame).
- If the design scrolls, use `full_page=True` and crop to the visible screen height in post.

---

## 2. HTML Mockup Template

Write mockups as self-contained HTML files (inline CSS, no external assets). Use the standard mobile shell below:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=390">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 390px;
    min-height: 844px;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
    background: #000;
    overflow: hidden;
  }
  /* --- app content below --- */
</style>
</head>
<body>
  <!-- screen content here -->
</body>
</html>
```

- Hard-code `width: 390px` on `body` — Playwright's viewport guarantees the frame, but the HTML must match.
- Embed all fonts via `@font-face` data URIs or use system fonts only.
- Use CSS variables for accent/theme colors so the same template can render multiple variants in a loop.

---

## 3. Multi-Variant Rendering

When a screen has color variants (e.g., per-category accent colors), render all variants in a single loop:

```python
variants = [
    {"name": "Social Dilemmas", "accent": "#E91E8C", "slug": "social-dilemmas"},
    {"name": "Tech & Future",   "accent": "#7C3AED", "slug": "tech-future"},
    {"name": "Moral Compass",   "accent": "#0D9488", "slug": "moral-compass"},
]

for v in variants:
    # inject CSS variable into HTML
    html = base_html.replace("--accent: #000;", f"--accent: {v['accent']};")
    html_file = f"/tmp/mockup_{v['slug']}.html"
    with open(html_file, "w") as f:
        f.write(html)
    render_mockup(html_file, f"/tmp/mockup_{v['slug']}.png")
```

---

## 4. Delivery: Embed Inline in Linear

**Never** just upload as attachments — always embed inline so mockups are visible without clicking.

### Step 1 — Upload each PNG to the Linear issue

```python
# Use the Linear MCP tool
mcp__linear__linear_uploadFileToIssue(
    issueId="SAT-NNN",
    filePath="/tmp/mockup_social-dilemmas.png",
    title="Unlock Screen — Social Dilemmas"
)
# → returns an upload URL
```

### Step 2 — Post a single comment with all mockups embedded

Compose one Markdown comment with all variants, each preceded by a heading and separated by `---`:

```markdown
### Social Dilemmas (magenta)
![Unlock Screen — Social Dilemmas](https://uploads.linear.app/.../image.png)

---

### Tech & Future (purple)
![Unlock Screen — Tech & Future](https://uploads.linear.app/.../image.png)

---

### Moral Compass (teal)
![Unlock Screen — Moral Compass](https://uploads.linear.app/.../image.png)
```

Post this as a single `mcp__linear__linear_createComment` call — one comment, all images inline.

**Do not** create one comment per image. **Do not** rely on `linear_uploadFileToIssue`'s `commentBody` parameter alone — compose the full multi-image comment manually.

---

## 5. Quality Checklist

Before posting, verify each rendered PNG:

- [ ] Physical size ≥ 780 × 1688 px (retina 2×) — run `file mockup.png` or check dimensions
- [ ] Background fills the full viewport (no white strips)
- [ ] Text is legible at Linear's default embedded image width (~600 px display)
- [ ] Accent color variants are visually distinct
- [ ] No clipped content at top/bottom of the viewport

If physical size is smaller than 780 px wide, re-render with a higher `device_scale_factor`.

---

## 6. Naming Convention

| File | Pattern |
|---|---|
| HTML source | `/tmp/mockup_<slug>.html` |
| PNG output | `/tmp/mockup_<slug>.png` |
| Linear title | `<Screen Name> — <Variant> (<color>)` |
| Image alt text | Same as Linear title |
