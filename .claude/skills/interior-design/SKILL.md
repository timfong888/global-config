---
name: interior-design
description: Generate visual mockup recommendations for home spaces using spatial psychology principles — vertical plane reclamation, depth layering, contrast lighting, asymmetrical styling, and the 80/20 curation rule. Load when asked to recommend changes to a room or create a visual mockup for home improvement.
whenToUse: Load when the user asks to create visual mockups, recommend changes to their home, suggest furniture arrangements, or improve a room's look. Applies to any home space (living room, bedroom, dining room, etc.).
---

# Interior Design: Visual Mockup Skill

Load the reference context before generating recommendations:
> **Context:** [`interior-design-principles.md`](.claude/context/interior-design-principles.md)

This skill produces **image-mode** output (visual mockups) guided by spatial psychology. It always routes through the **`capability-image`** skill pipeline for generation, download, hosting, and attachment.

---

## 1. Gather Inputs

Before generating, collect from the ticket or user message:

| Input | Required | Notes |
|---|---|---|
| **Photo(s) of the space** | Yes — hard block if missing | One mockup per supplied photo/angle. Never fabricate a viewpoint. |
| **Room type** | Yes | Living room, bedroom, dining room, etc. |
| **Specific pain point or goal** | Preferred | e.g. "feels small", "too dark", "looks cluttered" |
| **Budget tier** | Optional | Low (rearrange/re-style), Mid (soft furnishings), High (furniture replacement) |

If **no photo is supplied**: post a `> question:` asking for source photo(s) and stop. Do not generate without a real photo — that violates the no-hallucination rule for this mode.

---

## 2. Diagnose the Space

Before recommending, evaluate the supplied photo against each principle from the context reference:

1. **Vertical plane** — Is furniture clustered in a single 2–2.5 ft band? Are curtain rods on the window frame instead of near the ceiling?
2. **Horizontal depth** — Is furniture pushed flush against walls? Are all three landscape layers (background / middle / foreground) present?
3. **Lighting contrast** — Is there a single overhead "big light" with no directional or accent layer?
4. **Asymmetry** — Are decor objects arranged in even-numbered pairs? Is any surface over-styled or under-styled?
5. **Curation friction** — Does the space look like a showroom catalog (too coordinated)? Is there any lived-in personality?

Identify the **top 2–3 violations** — these become the mockup's focus. Don't fix everything at once; ranked improvements are more actionable.

---

## 3. Generate Recommendations

For each top violation, produce a concrete change:

**Vertical plane fixes:**
- Raise curtain rods to 2–4 inches below the ceiling line
- Add a tall bookcase or fluted wall panel to draw the eye upward

**Depth fixes:**
- Pull the sofa/bed 6 inches from the wall
- Add a foreground element (coffee table, bench, area rug) if none exists

**Lighting fixes:**
- Replace / supplement the overhead with a floor lamp at 45° + an accent light on a feature wall or shelf
- Name the three layers explicitly: ambient / task / accent

**Asymmetry fixes:**
- Regroup shelf or console decor into odd-number Vignette Triangles (tall + medium + flat)
- Break any symmetrical pair by removing or replacing one element

**Curation fixes:**
- Introduce one "friction" piece — a vintage lamp, worn leather throw, or natural texture — as the 20%

---

## 4. Produce the Mockup

After diagnosing and drafting recommendations, route to **`capability-image`** (load the skill):

**Prompt template for the image model:**

```
Photo of [room type]. Apply the following changes:
[List each concrete change from § 3]

Preserve the exact room geometry, wall positions, windows, flooring, and permanent fixtures.
Make only additive edits — do not alter the structure of the space.
Maintain the original photo's perspective and lighting direction as a base.

Style goal: [describe the target feel — e.g. "layered, lived-in warmth" or "calm minimal depth"]
```

Fill in the brackets from the ticket context. One edited mockup per supplied photo angle.

After generating:
1. **Download** the image (capability-image-download)
2. **Review** the downloaded image: confirm room geometry is preserved, no hallucinated walls or furniture
3. **Host** durably (capability-image-host)
4. **Attach** to the Linear issue and report cost (capability-image-cost)

---

## 5. Report Back

Post a concise handback comment structured as:

```
✅ Done — [room type] mockup with [N] changes applied.

**Violations fixed:**
- [Principle 1]: [what changed]
- [Principle 2]: [what changed]
- [Principle 3]: [what changed]

**Why it works:** [1–2 sentence spatial psychology rationale]

[Attached mockup image(s)]
(by Claude)
```

State → **In Review**.

If the user supplies multiple photos (multiple angles), produce one mockup per angle and list them separately.

---

## Quick Reference: Five Principles

| Principle | Key Number | Rule |
|---|---|---|
| Vertical plane | W/M eye path | Curtains 2–4" below ceiling; vertical elements |
| Horizontal depth | 6 inches | Float furniture from wall; 3-layer landscape |
| Lighting contrast | 45° angle | 3 layers: ambient + task + accent |
| Asymmetry | 3-5-7 | Odd-number Vignette Triangles (tall/medium/flat) |
| Curation | 80 / 20 | 80% structure, 20% friction/personality |
