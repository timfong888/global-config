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

Use `COMPOSIO_REMOTE_WORKBENCH` with `proxy_execute` to call fal.ai's queue API for all
image editing. The direct Composio tools (`FAL_AI_RUN_MODEL_SYNC`,
`FAL_AI_SUBMIT_ASYNC_JOB`, `FAL_AI_SUBSCRIBE_ASYNC_JOB`, `FAL_AI_UPLOAD_FILE`) are
**restricted or incompatible** in the Blocks agent environment — do not use them.

**FLUX.1 Kontext** is the correct model for interior design compositing — it was built
specifically for "edit *this* photo while preserving the scene" workflows and outperforms
general-purpose editors on structure-preserving tasks.

| Model | Endpoint | License | When to use |
|---|---|---|---|
| **FLUX.1 Kontext [dev]** | `fal-ai/flux-kontext/dev` | BFL non-commercial | **Default for Satchel / personal use.** Best context-preservation; free to run via fal.ai |
| **FLUX.1 Kontext [pro]** | `fal-ai/flux-pro/kontext` | BFL commercial | When production quality matters or the output is for a commercial product |
| **FLUX.1 Fill [dev]** | `fal-ai/flux/fill` | Apache 2.0 | Inpainting/masking workflow; fully open-source |
| **Qwen-Image-Edit-2511** | `fal-ai/qwen-image-2/edit` | Apache 2.0 | Fully open-source alternative if Kontext is unavailable; strong multimodal editor |
| **nano-banana-2/edit** | `fal-ai/nano-banana-2/edit` | Google proprietary | Fallback only — general-purpose Gemini-based editing; weaker structure preservation |

**Always verify endpoint IDs at call time** — fal.ai renames and versions models.
To list available models, run in `COMPOSIO_REMOTE_WORKBENCH`:
```python
required = {'fal-ai/flux-kontext/dev', 'fal-ai/flux-pro/kontext'}
found, cursor = set(), None
while True:
    params = f'?cursor={cursor}' if cursor else ''
    data, error = proxy_execute(method='GET', endpoint=f'https://api.fal.ai/v1/models{params}', toolkit='FAL_AI')
    if error or not data:
        raise RuntimeError(f"Model catalog unavailable — aborting before generation: {error}")
    for m in data.get('models', []):
        eid = m.get('endpoint_id', '')
        if 'kontext' in eid or 'edit' in eid:
            found.add(eid)
    cursor = data.get('next_cursor')
    if not cursor:
        break
missing = required - found
if missing:
    raise RuntimeError(f"Required model endpoint(s) not found in catalog: {missing}")
print(f"Verified endpoints: {found & required}")
```
If Kontext [dev] returns an error, try Qwen-Image-Edit before falling back to nano-banana-2.

### Uploading a source photo (Linear attachment → fal.ai-hosted URL)

`mcp__linear__linear_downloadAttachment` returns a **local file path** (e.g.
`/home/user/workspace/...`), not a URL or S3 key. To make the photo available to
fal.ai models, upload it via presigned URL in two steps:

**Step 1 — Get a presigned upload URL** (run in `COMPOSIO_REMOTE_WORKBENCH`):
```python
data, error = proxy_execute(
    method='POST',
    endpoint='https://rest.fal.ai/storage/upload/initiate',
    toolkit='FAL_AI',
    body={'file_name': 'source-photo.jpg', 'content_type': 'image/jpeg'}
)
if error or not data:
    raise RuntimeError(f"Failed to get upload URL: {error}")
upload_url = data['upload_url']
file_url = data['file_url']
print("upload_url=<redacted>")
print(f"file_url={file_url}")
```

**Step 2 — Upload the local file** (run via Bash tool — check exit code):
```bash
curl -sf --show-error -X PUT "<upload_url>" \
  -H "Content-Type: image/jpeg" \
  --data-binary @/path/to/downloaded/photo.jpg \
  -w "\nHTTP status: %{http_code}\n" -o /dev/null
```
If curl exits non-zero or the HTTP status is not 200, the upload failed — re-run
Step 1 to get a fresh presigned URL and retry.

Use `file_url` (not `upload_url`) as `image_url` in the edit call below. Adjust
`content_type` and `-H` header for PNG files (`image/png`).

### Running the edit model

Submit the job to fal.ai's async queue, then poll for completion. Split submit and
poll into **separate** `COMPOSIO_REMOTE_WORKBENCH` calls to stay within the 180-second
cell timeout.

**Step 1 — Submit the job** (run in `COMPOSIO_REMOTE_WORKBENCH`):

> **Note — body schema is model-specific:**
> - `fal-ai/flux-kontext/*`, `fal-ai/flux-pro/kontext`, and `fal-ai/qwen-image-2/edit`: use `image_url` (single string)
> - `fal-ai/nano-banana-2/edit`: use `image_urls` (list of strings)
> - `fal-ai/flux/fill` (inpainting): requires `image_url` **and** `mask_url` — handle separately; not covered by the generic submit flow below

```python
endpoint = 'fal-ai/flux-kontext/dev'  # adjust if using a fallback model
# Build model-specific body
if 'nano-banana-2' in endpoint:
    body = {'image_urls': ['<file_url from upload step>'], 'prompt': '<see §3 prompt template>'}
else:
    body = {'image_url': '<file_url from upload step>', 'prompt': '<see §3 prompt template>'}

data, error = proxy_execute(
    method='POST',
    endpoint=f'https://queue.fal.run/{endpoint}',
    toolkit='FAL_AI',
    body=body
)
if error or not data:
    raise RuntimeError(f"Job submit failed: {error}")
request_id = data['request_id']
print(f"request_id={request_id}")
```

**Step 2 — Poll until complete** (separate `COMPOSIO_REMOTE_WORKBENCH` call):
```python
import time
output_url = None
for attempt in range(30):
    time.sleep(5)
    status, error = proxy_execute(
        method='GET',
        endpoint=f'https://queue.fal.run/{endpoint}/requests/{request_id}/status',
        toolkit='FAL_AI'
    )
    if error or not status:
        print(f"Attempt {attempt+1}: transient error ({error}), retrying...")
        continue
    # Check for error fields even when status is COMPLETED — fal.ai can signal
    # per-request errors inside an otherwise-successful response envelope.
    if status.get('error') or status.get('error_type'):
        raise RuntimeError(f"Job error reported — try next model in priority table: {status}")
    state = status.get('status', 'unknown')
    if state == 'COMPLETED':
        result, fetch_error = proxy_execute(
            method='GET',
            endpoint=f'https://queue.fal.run/{endpoint}/requests/{request_id}',
            toolkit='FAL_AI'
        )
        if fetch_error or not result:
            # Transient result fetch failure — retry this attempt rather than switching models
            print(f"Attempt {attempt+1}: result fetch transient error ({fetch_error}), retrying...")
            continue
        output_url = result['images'][0]['url']
        print(f"Done: {output_url}")
        break
    elif state == 'FAILED':
        raise RuntimeError(f"Job failed — try next model in priority table: {status}")
    print(f"Attempt {attempt+1}: {state}")
else:
    raise RuntimeError(f"Poll exhausted after 30 attempts — re-run this cell to continue polling (request_id={request_id})")
```

If the poll cell times out at 180s, call `COMPOSIO_REMOTE_WORKBENCH` again with the
same polling code — `request_id` persists across cells in the notebook. If the job
returns FAILED or the model endpoint returns an error, swap the endpoint path to the
next model in the priority table above and re-submit.

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
| **Upload** | Upload source photo to fal.ai via presigned URL per §2 "Uploading a source photo" |
| **Generate** | Submit async job via `COMPOSIO_REMOTE_WORKBENCH` + `proxy_execute` per §2–3 |
| **Download** | Load `capability-image-download` skill — download to disk for native Read review |
| **Review** | Use Read tool to visually verify (see §5 quality checklist) |
| **Revise if needed** | Strengthen PRESERVE section and regenerate once if structure was altered |
| **Host** | Load `capability-image-host` skill — upload to Google Drive for durable URL |
| **Attach** | `mcp__linear__linear_createComment` with durable Drive URL embedded as `![alt](url)` (never the presigned fal.ai URL) |
| **Cost** | Load `capability-image-cost` skill — append cost line to the same comment |

**One image per comment.** Multiple angles → one comment per source photo.

> **HARD GATE — Attach step is non-optional.** The pipeline is **incomplete** unless
> every generated image is posted as a Linear comment via
> `mcp__linear__linear_createComment` with the durable Drive URL. Including the image
> link only in the assistant response does **not** satisfy this requirement.
>
> If the Attach step fails, retry once. If still failing:
> 1. Run the `capability-image-cost` skill to compute the generation cost.
> 2. Post a failure comment via `mcp__linear__linear_createComment` that includes
>    the image URL, the failure reason, and the cost line — preserving cost data
>    even when the image itself cannot be embedded.
> 3. If `mcp__linear__linear_createComment` is completely unavailable (tool error on
>    every attempt), create a minimal fallback cost comment via the assistant response
>    and note the Linear comment failure explicitly.
>
> The skill is considered failed if any image completes generation but no comment
> (full or fallback) is posted.

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
- **Model:** [endpoint used, e.g. fal-ai/flux-kontext/dev]

![Composite — [angle description]](https://drive.google.com/...)
```

Each source photo angle gets its own comment with the image embedded inline.

If no source photos → post the `> question:` block from §1 and set state → In Review.
