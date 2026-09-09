---
name: ui-mockup
description: Generate an inline HTML before/after mockup whenever proposing or implementing UI changes. Triggered automatically on any UI proposal, component redesign, or visual revision task.
triggers:
  - any task involving UI changes, component redesign, layout revision, or visual improvements
  - before creating a PR that modifies visual components
  - when asked to "mockup", "show me", "what will it look like", or "preview" a UI change
---

# UI Mockup Skill

Whenever you propose or implement a UI change, you **must** generate and serve an inline HTML mockup showing the before and after states side by side.

## When to trigger

- Any task that modifies visual components, layouts, colors, or interaction patterns
- Before or alongside creating a PR for UI changes
- When the user asks for a preview, mockup, or "what will it look like"
- After any revision to a previously proposed UI design

## Required deliverable

You must produce **all three** of the following:

### 1. Served HTML mockup (required)

Create a self-contained HTML file at `/home/user/workspace/mockup-<TICKET-ID>.html` and serve it:

```bash
nohup bash -c 'python3 -m http.server 7890 --directory /home/user/workspace' > /tmp/7890.log 2>&1 &
```

Then register the port:
```
mcp__blocks-internal-mcp__register_running_server_port  port: 7890
```

### 2. Before / After comparison layout

The HTML must include:
- **Left panel** — "Before" state with red label `✕ Before`, showing the original UI
- **Right panel** — "After" state with green label `✓ After (PR #N)`, showing the proposed UI
- **Change annotations** below each panel listing what changed and why, using color-coded badges:
  - `+` green badge — new additions
  - `~` blue badge — modifications
  - `✕` red badge — removals/problems fixed
- Use the app's **exact theme colors** (read `constants/theme.ts` before building the mockup)
- The mockup must be interactive — hover/active states should be visible so the user can feel the interaction model

### 3. Inline summary in your response

In the same message where you deliver the mockup, include a compact table of changes:

```markdown
| Element | Before | After |
|---|---|---|
| ... | ... | ... |
```

## HTML mockup template structure

```html
<!DOCTYPE html>
<html>
<head>
  <!-- Dark background (#1A1A2E or app background), system font stack -->
  <!-- All styles inline in <style> block — no external deps -->
</head>
<body>
  <h1>TICKET-ID — Issue Title</h1>
  <p class="issue-label">App Name · Screen · Component</p>

  <div class="comparison">
    <!-- Left: Before phone frame -->
    <div class="phone-wrap">
      <div class="phone-label label-before">✕ Before</div>
      <div class="phone"><!-- screen content --></div>
      <div class="annotations"><!-- problem list --></div>
    </div>

    <!-- Arrow -->
    <div class="divider">→</div>

    <!-- Right: After phone frame -->
    <div class="phone-wrap">
      <div class="phone-label label-after">✓ After (PR #N)</div>
      <div class="phone"><!-- screen content with changes --></div>
      <div class="annotations"><!-- change list --></div>
    </div>
  </div>
</body>
</html>
```

## Rules

- Never skip the mockup step, even for "small" visual changes — a one-line color change still warrants a before/after
- Match exact hex values from `constants/theme.ts` (or equivalent theme file) — do not approximate
- Interactive states (hover, active/pressed) must be implemented with CSS transitions so the user can actually feel the UX
- The mockup must be self-contained — no CDN links, no external images — it must render offline
- If the app has no phone/mobile UI, adapt the frame to the actual target (browser window, card, modal, etc.)
