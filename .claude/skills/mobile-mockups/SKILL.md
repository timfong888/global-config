---
name: mobile-mockups
description: Generate high-fidelity mobile UI mockups as full-size PNGs embedded inline in Linear issue comments. Renders HTML at mobile viewport dimensions via Playwright so mockups appear as inline images — no attachment links. Use for mobile app screens, UI proposals, and designs a coding agent needs to implement.
whenToUse: Load when a ticket asks for a mobile or web UI mockup, screen design, UI proposal, or visual reference for implementation. TRIGGER on natural language like "mockup", "UI design", "show me the screen", "what should it look like", "create a design for", "high fidelity", "design spec". Also triggered by the "mode › ui-mockup" label.
---

# Skill: mobile-mockups

Generate **high-fidelity mobile UI mockups** as full-size PNGs embedded inline in Linear
comments — visible without clicking, reusable as implementation specs for coding agents.

---

## Invocation

Call this skill via natural language in the ticket:
- "Create a high-fidelity mockup for [screen]"
- "Design the [feature] screen for the mobile app"
- "UI mockup: show what [flow] should look like"
- "Create a design spec so the coding agent can implement [feature]"

Or set the **`mode › ui-mockup`** label on the Linear issue for deterministic routing.

---

## 1. Rendering standard

Render all mockups as HTML files → PNG screenshots via Playwright.

### Required dimensions

| Target | Viewport (px) | Device scale | Physical PNG size |
|---|---|---|---|
| iPhone (default) | 390 × 844 | 2 | 780 × 1688 px |
| iPhone Pro Max | 430 × 932 | 3 | 1290 × 2796 px |
| Android standard | 412 × 915 | 2 | 824 × 1830 px |

Always use **device scale ≥ 2** — Linear embeds images at ~600 px display width, so
under-scale produces blurry text.

### Playwright render (Python)

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

Use `full_page=False` to capture exactly the viewport. If the design scrolls, use
`full_page=True` and note it in the comment.

Save HTML source to `/tmp/mockup-<SAT-id>-<slug>.html`
Save PNG output to `/tmp/mockup-<SAT-id>-<slug>.png`

---

## 2. Design quality bar

The output must be good enough for a coding agent to implement from it. Each mockup must
achieve **all** of the following:

**Visual hierarchy**
- Clear primary action (bold, color-contrasted, large tap target ≥ 44 × 44 px)
- Obvious information hierarchy: title > subtitle > body > meta
- Adequate whitespace — no crowded or cramped layouts

**Typography**
- Use system font stack: `-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif`
- Minimum body text 14 px; minimum label/caption 12 px
- Line height ≥ 1.4 for body, 1.2 for headings

**Color and contrast**
- Text-to-background contrast ≥ 4.5:1 (WCAG AA)
- Use exact hex values from the project's theme file if one is readable (e.g. `constants/theme.ts`, `tailwind.config.js`)
- If no theme file is available, establish a coherent palette (2 neutrals + 1 accent + white/black)
- Document the palette used as CSS custom properties at the top of the `<style>` block

**Interactivity cues**
- Buttons have visible active/pressed states (CSS `:active` with slight darken/scale)
- Tappable list items have a subtle background on `:hover`
- Disabled states visually distinct from enabled

**Implementation completeness**
- Every UI element visible in the mockup has an exact CSS class or value — no "TBD" or placeholder colors
- Include a **design spec block** in the Linear comment listing: primary color, font sizes, spacing scale, border radius, and shadow style

---

## 3. HTML mockup template

Self-contained HTML only — no CDN links, no external images. Must render offline.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=390">
<style>
  :root {
    --bg: #F9FAFB;
    --surface: #FFFFFF;
    --primary: #6366F1;        /* fill with project accent */
    --primary-dark: #4F46E5;
    --text: #111827;
    --text-secondary: #6B7280;
    --border: #E5E7EB;
    --radius: 12px;
    --shadow: 0 1px 3px rgba(0,0,0,.1), 0 1px 2px rgba(0,0,0,.06);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 390px;
    min-height: 844px;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    font-size: 16px;
    line-height: 1.5;
    overflow-x: hidden;
  }

  /* status bar */
  .status-bar {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 20px 6px;
    font-size: 12px; font-weight: 600; letter-spacing: .2px;
  }

  /* nav bar */
  .nav-bar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 20px 12px; background: var(--surface);
    border-bottom: 1px solid var(--border);
  }
  .nav-title { font-size: 17px; font-weight: 600; }

  /* --- add your screen-specific styles below --- */
</style>
</head>
<body>

  <!-- Status bar -->
  <div class="status-bar">
    <span>9:41</span>
    <span>●●●● WiFi 🔋</span>
  </div>

  <!-- Nav bar -->
  <div class="nav-bar">
    <span>← Back</span>
    <span class="nav-title">Screen Title</span>
    <span>···</span>
  </div>

  <!-- Screen content here -->

</body>
</html>
```

**Adapt the frame** for non-phone targets: browser window → full-width card layout;
tablet → 768 px wide body; web app → no status/nav bar chrome.

---

## 4. Multi-variant rendering

When the screen has theme variants (e.g. per-category accent colors), render all in a loop:

```python
variants = [
    {"slug": "variant-a", "primary": "#6366F1", "name": "Default"},
    {"slug": "variant-b", "primary": "#E91E8C", "name": "Accent Pink"},
]

base_html = open("/tmp/mockup-base.html").read()
for v in variants:
    html = base_html.replace("--primary: #6366F1;", f"--primary: {v['primary']};")
    html_file = f"/tmp/mockup-SAT-NNN-{v['slug']}.html"
    with open(html_file, "w") as f:
        f.write(html)
    render_mockup(html_file, f"/tmp/mockup-SAT-NNN-{v['slug']}.png")
```

---

## 5. Delivery: embed inline in Linear

Never post as attachment links — always embed so images appear inline without clicking.

### Step 1 — Upload each PNG

```python
# issueId: from session context (issue_identifier field) or mcp__linear__linear_getIssueById
mcp__linear__linear_uploadFileToIssue(
    issueId="<full UUID or SAT-NNN>",
    filePath="/tmp/mockup-SAT-NNN-<slug>.png",
    title="<Screen Name> — <Variant>"
)
# returns an upload URL like https://uploads.linear.app/.../image.png
```

### Step 2 — Post one comment with all mockups

Compose a single Markdown comment:

```markdown
### [Variant A Name]
![Screen — Variant A](https://uploads.linear.app/.../image-a.png)

---

### [Variant B Name]
![Screen — Variant B](https://uploads.linear.app/.../image-b.png)
```

Post via `mcp__linear__linear_createComment` — one comment, all images inline.
Do **not** create one comment per image.

### Step 3 — Append design spec

In the same comment (or a follow-up), append the implementation spec:

```markdown
---
**Design spec for implementation**

| Property | Value |
|---|---|
| Primary color | `#6366F1` |
| Background | `#F9FAFB` |
| Surface | `#FFFFFF` |
| Border radius | `12px` |
| Body font size | `16px` |
| Label font size | `14px` |
| Spacing scale | `4 / 8 / 12 / 16 / 24 / 32 px` |
| Shadow | `0 1px 3px rgba(0,0,0,.1)` |
| Tap target minimum | `44 × 44 px` |
```

---

## 6. Quality checklist

Before posting, verify each PNG:

- [ ] Physical width ≥ 780 px (`file mockup.png` reports dimensions)
- [ ] Background fills full viewport — no white strips at top/bottom
- [ ] Text is legible at ~600 px display width (Linear's embed size)
- [ ] Status bar and nav bar chrome visible
- [ ] Primary action button is prominent and tappable-sized
- [ ] Contrast ≥ 4.5:1 on body text (eyeball check: can you read it easily at a glance?)

If physical width < 780 px: re-render with `device_scale_factor=3`.

---

## 7. Handback comment format

```markdown
✅ **[Screen name] mockup — [N] variant(s)**

- **Screens:** [list what was mocked up]
- **Viewport:** 390 × 844 (iPhone default, 2× retina)
- **Design spec:** below

[embedded images]

---
**Design spec for implementation**
[spec table]

(by Claude)
```
