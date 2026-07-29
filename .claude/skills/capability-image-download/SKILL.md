---
name: capability-image-download
description: Image download-to-disk stage — downloads a generated image from its short-lived hosted URL to a local path so Claude Code's native Read tool can review it before proceeding. Stage 2 of the capability-image pipeline.
whenToUse: Load this skill as stage 2 of the capability-image pipeline, after image generation and before native image review. Use whenever you need to visually inspect a generated image with the Read tool.
---

# Capability stage: download-to-disk (before native image review)

Part of the image-generation capability ([SAT-492](https://linear.app/sophia-xyz/issue/SAT-492),
child of the epic [SAT-481](https://linear.app/sophia-xyz/issue/SAT-481)). This is the
**download** stage of the pipeline documented in the `capability-image` skill
([SAT-491](https://linear.app/sophia-xyz/issue/SAT-491)): it sits **between image
generation and native image review**.

## Why this stage exists

Composio's `fal_ai` / `gemini` image-generation tools return a **hosted URL only**.
Claude Code's native `Read` tool — how a worker actually *looks at* a generated image
to judge it before proceeding — needs a **local filesystem path**; it cannot open a
remote URL. Without this stage, native review silently fails or gets skipped, so the
worker "reviews" an image it never saw.

## Procedure

Run this after each image is generated and before you `Read` it:

1. **Resolve the local target directory** `generated-images/SAT-<id>/`, where `<id>`
   is the Linear issue identifier the work belongs to (e.g. `generated-images/SAT-481/`).
   Create it if missing — `mkdir -p generated-images/SAT-<id>` — so a first-run on a
   fresh checkout doesn't fail on a missing directory.
2. **Download the hosted image URL to disk** at
   `generated-images/SAT-<id>/<filename>`. Choose a stable, descriptive `<filename>`
   (keep the source extension, e.g. `.png`/`.jpg`; disambiguate multiple variants,
   e.g. `hero-v1.png`, `hero-v2.png`). A plain `curl -fsSL <url> -o <path>` is enough;
   verify the file is non-empty before continuing.
3. **Pass the resulting local path to the review step** — hand
   `generated-images/SAT-<id>/<filename>` to Claude Code's `Read` tool, **not** the
   remote URL. The review reads the bytes on disk.

## Boundaries

- `generated-images/` is **gitignored** — these are transient working artifacts, not
  committed source. Never `git add` a downloaded image.
- This stage only gets an image onto local disk for review. **Durable hosting** for a
  Linear attachment (so the URL doesn't expire) is a separate stage — see the
  `capability-image-host` skill ([SAT-490](https://linear.app/sophia-xyz/issue/SAT-490)).
