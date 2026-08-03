---
name: photo-compositing
description: Edit real photographs for interior design — add/swap furniture, materials, and decor while preserving room structure, perspective, and lighting. Uses fal.ai image editing via Composio MCP. Outputs images embedded inline as Linear comments.
whenToUse: Load when a ticket supplies real room photos and asks to visualize new products, furniture, layout changes, or material upgrades. Also called by agent-writing in image mode. TRIGGER on natural language like "composite", "edit this photo", "add this to the room", "interior design", "redecorate", "swap the furniture", "place this product in", "show it with the new".
---

# Skill: photo-compositing

Edit real photographs to visualize **interior design changes** — new furniture, materials, color
schemes, or layout rearrangements — while preserving the room's structural bones: walls,
windows, doors, floor plan, perspective, and lighting direction.

This skill never hallucinates geometry. **One source photo → one edited output.**
N source photos (different angles) → N edited outputs.

---

## Invocation

Call this skill directly via natural language in the ticket description/title:
- "Composite this [product/furniture] into my room photo"
- "Edit the attached photo to show [change]"
- "Interior design: add [item] to this space"

Or set the **`mode › photo-composite`** label on the Linear issue for deterministic routing.

---

## 1. Input requirements

**Hard requirements — block if missing:**
- At least one **source photograph** attached to the Linear issue or linked in its description
- A clear **edit description**: what to add, remove, swap, or change

**Block condition:** If no source photo is present, post:
```
> question: This ticket needs a source photograph of the room to composite into.
> Please attach one or more photos (different angles are fine) and reply to continue.
```
Set state → In Review, then stop. This block applies even with `auto:full` — a missing
source cannot be assumed without hallucinating the subject.

---

## 2. Model selection

Use `FAL_AI_RUN_MODEL_SYNC` via Composio for all image editing.
Before calling, run `FAL_AI_GET_MODELS` if unsure of the current endpoint ID — fal.ai
renames and versions models. The IDs below are correct as of 2026-08; verify at call time.

| Use case | Model ID | Notes |
|---|---|---|
| **Default (editing)** | `fal-ai/nano-banana-2/edit` | Google Nano Banana 2 — confirmed active; strong general-purpose image editing |
| **High-fidelity structure-preserve** | `fal-ai/flux-kontext/dev` | FLUX.1 Kontext — best-in-class for preserving context while making targeted edits; **non-commercial license** — only use if Tim has explicitly accepted BFL's license |
| **Fallback** | `GEMINI_GENERATE_IMAGE` (Composio) | Only when fal.ai tools are unavailable |

To call the default model:
```
FAL_AI_RUN_MODEL_SYNC
  model_id: fal-ai/nano-banana-2/edit
  input:
    image_url: <fal.ai-hosted URL of the uploaded source photo>
    prompt: <see §3 prompt template>
```

To upload the source photo first (if it's a Linear attachment, not already on fal.ai):
```
FAL_AI_UPLOAD_FILE
  file:
    name: source-photo.jpg
    mimetype: image/jpeg
    s3key: <s3 key returned from linear download or attachment fetch>
```
→ use the returned `access_url` as `image_url` in the edit call.

---

## 3. Prompt engineering for interior design

A good compositing prompt has three explicit layers:

```
PRESERVE (structural elements — do not change):
[walls / flooring / windows / doors / fixed architecture / ceiling / natural light direction]

EDIT (the specific change):
[product names, materials, colors, exact placement — be as specific as possible]

STYLE (room aesthetic to match):
[describe the existing style, e.g. "modern Scandinavian, warm neutrals, natural wood tones"]
```

### Prompt template

```
Preserve the existing room structure exactly: walls, flooring, windows, doors, ceiling,
and natural light direction are unchanged. Do not add new architectural elements or
change the camera perspective or viewpoint.

Edit: [describe precisely — e.g. "Replace the existing sofa with a deep teal velvet
three-seat sofa with tapered wooden legs. Add a round walnut coffee table centered in
front of it. Remove the current rug and replace with a cream boucle rug."]

The room aesthetic is [describe — e.g. "mid-century modern with warm neutrals, oak wood
tones, and warm indirect lighting"]. The new elements should feel natural and integrated
with this aesthetic — match the existing light quality, shadow direction, and material
finish.
```

### Per-angle additions

When editing multiple source photos (different angles), append one line per photo:
```
Camera position: [e.g. "from the doorway looking toward the far wall"]
Primary focus area: [e.g. "the seating area on the left half of the frame"]
```

---

## 4. Pipeline

After generating each edited image, run the `capability-image` stages:

| Stage | Action |
|---|---|
| **Generate** | `FAL_AI_RUN_MODEL_SYNC` per §2–3 |
| **Download** | Load `capability-image-download` skill — download to disk for native Read review |
| **Review** | Use Read tool to visually verify (see §5 quality checklist) |
| **Revise if needed** | Strengthen PRESERVE section and regenerate once if structure was altered |
| **Host** | Load `capability-image-host` skill — upload to Google Drive for durable URL |
| **Attach** | `mcp__linear__linear_createComment` with durable Drive URL embedded as `![alt](url)` (never the presigned fal.ai URL) |
| **Cost** | Load `capability-image-cost` skill — append cost line to the same comment |

**One image per comment.** Multiple angles → one comment per source photo.

---

## 5. Quality checklist

Before posting each edited image, verify via Read:

- [ ] **Room structure intact** — walls, floor, ceiling, windows, doors identical to source
- [ ] **Perspective unchanged** — no viewpoint shift or geometric distortion introduced
- [ ] **Lighting consistent** — new elements respect the room's existing light direction and shadow quality
- [ ] **Edit is visible** — the requested change is clearly present and identifiable
- [ ] **Scale correct** — new furniture/objects are proportional to the room

If a check fails → revise the prompt (max one revision pass) before posting.

---

## 6. Output comment format

```markdown
✅ **Interior design composite — [brief edit description]**

- **Edit:** [what was changed]
- **Source:** [number of source photos and angles]
- **Preserved:** room structure, perspective, lighting direction
- **Model:** fal-ai/nano-banana-2/edit

![Composite — [angle description]](https://drive.google.com/...)
```

Each source photo angle gets its own comment with the image embedded inline.

If no source photos → post the `> question:` block from §1 and set state → In Review.
