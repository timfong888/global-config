---
name: capability-image
description: Shared image-generation capability pipeline (generate → download → host → attach → report cost). A capability invoked by any track (coding, writing, admin) when a ticket needs generated or edited images. Uses fal_ai as default provider with open-weight models; Google Drive for durable hosting.
whenToUse: Load this skill when any Linear agent poller track needs to generate, edit, download, host, or attach an image to a Linear issue. Not a standalone track — it composes with coding, writing, and admin tracks.
---

# Capability: image generation (generate → download → host → attach → report cost)

A **capability profile**, not a fourth track ([SAT-491](https://linear.app/sophia-xyz/issue/SAT-491),
child of the epic [SAT-481](https://linear.app/sophia-xyz/issue/SAT-481)). The
`/linear-agent-poll` tick still routes every issue into exactly one **track** —
coding, writing, or admin — and dispatch is unchanged. This profile is the shared,
reusable pipeline any of those tracks invokes **when a ticket's scope calls for
generated images**, so a worker doesn't reinvent the
generate/download/host/attach/report-cost steps each time.

Reuse, don't reimplement: an image-related ticket keeps its own track's guardrails
(coding branches+PRs, writing drafts, admin trust boundaries) and just follows this
pipeline for the image work itself.

## When to invoke

Invoke this capability when a ticket asks you to **create, edit, or regenerate an
image** — e.g. a hero image for a draft (writing), a diagram/asset committed or linked
by a coding change (coding), or an image attached to a Linear issue for reference
(any track). If the ticket has no image work, ignore this profile.

## Tools

Image generation runs through **Composio**:

- **`fal_ai`** — Fal.AI image generation. **Default provider** for both generation and
  editing/compositing (see model priority below).
- **`gemini`** — Gemini image generation (`nano-banana`). **Fallback only** — use it
  when `fal_ai` is unavailable or the ticket explicitly asks for it, not as the default.

Both return a **hosted URL only** (no local bytes, and the URL is short-lived), which
is exactly why the download and host stages below exist.

### Model priority (SAT-531)

Prioritize **open-weight, commercially-safe models** over Gemini `nano-banana`, per the
[SAT-531](https://linear.app/sophia-xyz/issue/SAT-531) research
(`~/Documents/remoteObsidian1025/02-AI-Tools/linear-agent-system/SAT-531-open-model-alternatives.md`
has the full comparison/sourcing; the decision itself is captured here so it's the live
default, not something a worker has to go dig up):

- **Editing / compositing an existing photo** (the harder, load-bearing case —
  SAT-521's identity-preserving real-photo edits): default to **Qwen-Image-Edit-2511**
  (Apache 2.0) via `fal_ai` (`fal-ai/qwen-image-2/edit` or the current equivalent
  endpoint — confirm the exact model id at call time, fal.ai renames/versions these).
  Only fall back to Gemini `nano-banana` if Qwen-Image-Edit-2511 errors out, isn't
  reachable, or the ticket calls for it specifically.
- **Pure text-to-image generation** (no existing photo to edit): default to
  **Qwen-Image 2.0** (Apache 2.0) unconditionally. Use **FLUX.1 [schnell]** (also
  Apache 2.0) instead only when the ticket explicitly calls for speed/predictability
  over the small quality edge — that's an opt-in override, not a second default a
  worker picks between on its own.
- Both are reached through the **existing** `fal_ai` Composio tool — no new
  integration, just a different model argument on the same call.
- **Licensing gate:** only Apache-2.0 (or equivalently unrestricted) open-weight
  models are defaults. **FLUX.1 Kontext [dev]** benchmarks well but ships under BFL's
  non-commercial license — treat it as an evaluated fallback only, gated on either
  accepting that license risk or budgeting for BFL's paid commercial license; never
  default to it silently.
- This is a **model-choice change, not a billing fix** — every model above, open or
  not, is still hosted and billed through the same `fal_ai` account. If `fal_ai` calls
  fail with a billing/lock error, that's the SAT-521/SAT-530 balance issue, not a
  reason to fall back to Gemini.

## The pipeline

Five stages, in order. The middle/final stages are documented in their own stage files
(each its own reviewable change) and are summarized here:

1. **Generate.** Produce the image via Composio `fal_ai` (default — see model priority
   above for which model to pass) or, as a fallback, `gemini`, per the ticket's
   prompt/spec. You get back a hosted URL.

2. **Download to disk** — see the `capability-image-download` skill
   ([SAT-492](https://linear.app/sophia-xyz/issue/SAT-492)). Claude Code's native
   `Read` tool needs a **local path** to review an image; it cannot open a remote URL.
   Download the hosted URL to `generated-images/SAT-<id>/<filename>` (created if
   missing, gitignored) and hand that local path to `Read` for native visual review
   before proceeding.

3. **Host durably** — see the `capability-image-host` skill
   ([SAT-490](https://linear.app/sophia-xyz/issue/SAT-490)). The `fal_ai` / `gemini`
   URL is a short-lived presigned link (~1–6h) that will 404. Upload the image to the
   connected **`{GDRIVE_ACCOUNT}`** Drive (configured in workspace `CLAUDE.md`;
   Satchel default: `timfong888-gdrive`) via `GOOGLEDRIVE_UPLOAD_FROM_URL`, set sharing
   so the URL stays viewable, and use that **durable** Drive URL downstream — only needed
   when the image will be **attached to / referenced from Linear** (or anywhere the link
   must outlive the presigned window).

4. **Attach.** Pass the **durable** Drive URL from stage 3 (never the presigned
   `fal_ai` / `gemini` link) to `LINEAR_CREATE_ATTACHMENT` so the Linear attachment
   doesn't break later.

5. **Report cost & running balance** (stage 5) — see the `capability-image-cost` skill
   ([SAT-533](https://linear.app/sophia-xyz/issue/SAT-533)). After the image is
   generated/edited, append one line to that same image's comment (never a separate
   comment — one image per comment, so cost lines stay traceable per image)
   stating that image's generation cost and the cumulative balance spent so far. Stage
   5 always needs a comment to append to; if the image is a genuine one-off that skips
   stages 2–4 (never reviewed or attached), post a minimal top-level comment for it
   anyway so the cost line has somewhere to land — the ledger's running balance still
   has to account for every generation call, shown or not.

Skip a stage only when it genuinely doesn't apply: stage 2 is needed whenever you must
*review* the image; stages 3–4 are needed whenever the image must *persist in Linear*.
Stage 5 runs whenever an image is actually generated/edited (it's the cost of that
call) — it never has a reason to be skipped, since every generation call has a cost to
report even when the image itself isn't reviewed or attached.
