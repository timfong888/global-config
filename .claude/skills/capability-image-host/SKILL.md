---
name: capability-image-host
description: Durable image hosting stage — uploads a generated image to Google Drive (timfong888-gdrive) before creating a Linear attachment, so the attachment URL doesn't expire. Stage 3 of the capability-image pipeline.
whenToUse: Load this skill as stage 3 of the capability-image pipeline, after image generation (and optionally local download) and before creating a Linear attachment. Required whenever an image will be attached to or referenced from Linear.
---

# Capability stage: durable hosting (before creating a Linear attachment)

Part of the image-generation capability ([SAT-490](https://linear.app/sophia-xyz/issue/SAT-490),
child of the epic [SAT-481](https://linear.app/sophia-xyz/issue/SAT-481)). This is the
**durable-host** stage of the pipeline documented in the `capability-image` skill
([SAT-491](https://linear.app/sophia-xyz/issue/SAT-491)): it sits **between image
generation (or local download) and creating a Linear attachment**.

## Why this stage exists

`LINEAR_CREATE_ATTACHMENT` needs a URL to attach. The hosted URLs that `fal_ai` /
`gemini` return are **short-lived presigned links** (roughly 1–6 hours) — any Linear
attachment built directly from one will eventually **404**, silently breaking the
attachment for future reference. Re-hosting the image on durable storage first gives
Linear a **non-expiring URL**.

## Procedure

Run this after the image is generated (and optionally downloaded locally per the
`capability-image-download` skill) and before `LINEAR_CREATE_ATTACHMENT`:

1. **Upload to durable storage.** Call `GOOGLEDRIVE_UPLOAD_FROM_URL` against the
   Composio-connected **`timfong888-gdrive`** Google Drive account, passing the
   generated image's hosted URL. This copies the bytes into Drive before the presigned
   link can expire. (Pin the Composio call to the `timfong888-gdrive` account so the
   upload lands in the right Drive.)
2. **Make the Drive URL shareable / non-expiring.** Confirm the uploaded file's
   sharing/permission level keeps its URL viewable — anyone-with-the-link view access
   — so the URL renders in the Linear attachment preview rather than showing a
   permission wall. If `GOOGLEDRIVE_UPLOAD_FROM_URL` does not set this itself, follow it
   with the Drive permission update before continuing.
3. **Attach the durable URL, not the presigned one.** Pass the resulting Drive
   shareable URL as the input to `LINEAR_CREATE_ATTACHMENT` — **never** the original
   `fal_ai` / `gemini` presigned link. The attachment now points at storage that
   won't expire.

## Boundaries

- Durable hosting is only about giving Linear a **non-expiring** attachment URL. Getting
  the image onto local disk for native `Read` review is a separate stage — see the
  `capability-image-download` skill ([SAT-492](https://linear.app/sophia-xyz/issue/SAT-492)).
- If the `timfong888-gdrive` connection is missing or the upload/permission step fails,
  do **not** fall back to attaching the presigned link (it will 404 later) — surface the
  gap rather than creating an attachment that silently breaks.
