---
name: linear-image-pipeline
description: Generate or edit an image and get it durably attached to a Linear issue with a cost line — generate, download to disk for native review, re-host on a durable URL (subject to the chosen host's own retention policy), attach, report cost + running balance. Use whenever a task needs a generated/edited image delivered into Linear, not as a standalone image generator.
---

# linear-image-pipeline

Ported from `github.com/timfong888/linear-agent-poller` (`profiles/capability-image*.md`). A **capability**, not a track of its own — whatever workflow needed the image (a coding change, a draft, an admin ticket) keeps its own rules and just calls this pipeline for the image work itself. Ignore this skill if there's no image work.

## Generate

Run image generation through Composio: **`fal_ai`** is the default provider for both generation and editing/compositing; **`gemini`** (`nano-banana`) is a fallback only, used when `fal_ai` is unavailable or explicitly requested. Both return a **hosted-but-short-lived URL** (roughly 1–6h) — that's why the download and host stages below exist. "`fal_ai` unavailable" means a transient provider/transport failure (timeout, 5xx, endpoint moved) — it does **not** cover a billing, auth, quota, or licensing failure; those are account/config problems, not outages, so surface them (per the billing bullet below) rather than silently routing around them to Gemini.

**Model choice within `fal_ai`:** prefer open-weight, commercially-unrestricted models over Gemini. Confirm the resolved model id's **current** license and commercial-use terms against fal.ai's own listing immediately before generating — a static "Apache 2.0" label below is a starting default, not something to trust unverified at call time, since fal.ai renames/re-terms these endpoints. If you can't confirm the current license for the resolved endpoint, don't generate with it — fall back per the rules below instead of assuming the label here still holds.
- **Editing/compositing an existing photo** (the harder, identity-preserving case) → default to a current Qwen image-edit model (Apache 2.0) via `fal_ai`; confirm the exact model id at call time since fal.ai renames/versions endpoints. Fall back to Gemini only if the Qwen call errors or the ticket asks for it specifically.
- **Pure text-to-image** (nothing to edit) → default to Qwen-Image 2.0 (Apache 2.0). Use FLUX.1 [schnell] (also Apache 2.0) only when the ask explicitly wants speed over the small quality edge — an opt-in override, not a second default to pick between freely.
- **Licensing gate:** only Apache-2.0/equivalent open-weight models are defaults. FLUX.1 Kontext [dev] benchmarks well but ships under a non-commercial license — evaluated fallback only, never a silent default.
- A `fal_ai` billing/lock/auth/quota error is an account-config issue, not a reason to silently fall back to Gemini — surface it.

## Download to disk (before native review)

A native `Read`-style review tool needs a local path, not a remote URL. Sanitize `<issue-id>` and `<descriptive-name>` before building the path — reject path separators and `..`, reduce each to a plain basename — and confirm the resolved path still falls under `generated-images/` before creating anything, the same guard the `linear-ticket` skill applies to a ticket id used as a path segment. Download the hosted URL to `generated-images/<issue-id>/<descriptive-name>.<ext>` (create the directory if missing, gitignore it — never commit these), capping the download at a sane size (a few tens of MB) and aborting if that's exceeded. Verify the download actually succeeded and is image data, not just non-empty: check the HTTP response succeeded, confirm the content type is an image MIME type, and only then hand that **local path** to the review step — an error page or truncated payload saved to disk and "reviewed" is worse than an obvious failure. Skip this stage only when the image is never reviewed before attaching.

## Host durably (before attaching to Linear)

The `fal_ai`/`gemini` URL will 404 once its presigned window expires, so re-host before creating a Linear attachment:

- **Prefer Linear's own native file-upload path** (`prepare_attachment_upload` + `create_attachment_from_upload`, or equivalent — i.e. an `uploads.linear.app` asset) when the session's Linear access exposes it. It's simpler (no separate storage account), is the path confirmed reliable for images that need to **render inline** in a Linear comment/description, and — unlike the fallback below — doesn't require making the image publicly link-accessible. An externally-hosted link (Drive, catbox, tmpfiles, …) has repeatedly failed to render inline even when reachable directly.
- If native upload isn't available, fall back to uploading to a connected durable-storage account (e.g. Google Drive via an upload-from-URL action). This fallback makes the file **anyone-with-the-link** viewable, which is effectively public — treat it as acceptable only for images you're confident are non-sensitive; **if sensitivity is unclear, treat the image as sensitive** and require native upload rather than defaulting to this fallback, surfacing the gap instead. **It's also unverified for inline rendering** — treat it as attachment-only, not a substitute for native upload where inline display matters.
- Either way: attach the **durable** URL, never the original `fal_ai`/`gemini` presigned link. If the durable-hosting step itself fails, surface the gap — don't attach a link you know will break.

## Attach

Create the Linear attachment against the issue using the durable URL from the previous stage.

## Report cost + running balance

After each generated/edited image, append **one line** to that same image's comment (not a new comment):

```text
💰 Cost: $0.08 · Total spent: $1.24
```

or, if any part of the number is a fallback rather than a real quote:

```text
💰 Cost: ~$0.05 (estimated) · Total spent: ~$1.21
```

**Cost source, in order:** (1) the generation call's own reported cost, if it's a finite non-negative number; (2) otherwise a documented placeholder default, explicitly flagged `estimated`. If this repo carries the poller's `tests/lib/image_cost_ledger.py`, its `DEFAULT_COST_USD` constant is the canonical fallback value — use it rather than inventing a number; if that file isn't present, pick one explicit constant, document it in this repo alongside the rest of this config, and reuse the same value on every fallback rather than re-guessing per call. The running balance is the cumulative sum of every recorded cost for the job so far, including the one just posted — one entry per generation call, so a retried or re-run call for the same image adds a new entry only if it actually re-ran the generation, never a second time for the same result; once any entry folded into it was estimated, mark the total approximate too. This stage never has a reason to be skipped — every generation call has a cost to report, whether or not the image itself was reviewed or attached.
