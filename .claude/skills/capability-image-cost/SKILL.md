---
name: capability-image-cost
description: Image cost accounting stage — after each generated/edited image, appends one cost line to its comment showing that image's cost and the cumulative running balance. Uses tool-reported cost when available, falls back to a documented DEFAULT_COST_USD constant.
whenToUse: Load this skill as stage 5 of the capability-image pipeline, after an image is generated or edited. Always runs whenever a generation call is made — every image has a cost to report.
---

# Capability stage: cost + running balance (after each image)

Part of the image-generation capability ([SAT-533](https://linear.app/sophia-xyz/issue/SAT-533),
child of the epic [SAT-481](https://linear.app/sophia-xyz/issue/SAT-481)). This is the
**cost-accounting** stage of the pipeline documented in the `capability-image` skill
([SAT-491](https://linear.app/sophia-xyz/issue/SAT-491)): it sits **after an image is
generated/edited and alongside posting that image's comment** (either stage 1 Generate
or, on an iteration, a repeat of it).

## Why this stage exists

Before this stage there was no visibility into what an image job cost. The ask
(SAT-533): after each generated/edited image, show **(a)** that image's own generation
cost and **(b)** the cumulative balance spent across every tracked generation, so a
reviewer sees the running spend as they review the images.

## Cost source (in order of preference)

1. **The tool call's own reported cost, preferred over the fallback.** If the Composio
   `fal_ai` / `gemini` response for that generation includes a cost field that is a
   finite, non-negative number, use it directly — it always takes priority over the
   `DEFAULT_COST_USD` fallback below.
2. **Otherwise, the `DEFAULT_COST_USD` fallback.** Neither Composio tool reliably
   reports a cost today (there is no live billing API wired into this repo), so when
   the response has no usable cost — missing, non-numeric, negative, `NaN`, or
   infinite — fall back to a documented per-image constant (`DEFAULT_COST_USD`, see
   `tests/lib/image_cost_ledger.py` in the linear-agent-poller repo). This is an
   **explicit assumption**: a placeholder price, not a real fal.ai/Gemini quote. Swap
   it for a live cost lookup once one exists.

The reported cost always takes priority over `DEFAULT_COST_USD` — the fallback only
ever applies when there is nothing valid to prefer. A fallback cost is always flagged
`estimated: true` rather than silently presented as if it were real — the distinction
between a reported cost and a guess must never be lost.

## Running balance

The running balance is the **cumulative sum of every recorded cost**, in order,
including the entry just posted. It is folded over an append-only ledger of prior
entries for the job (see `tests/lib/image_cost_ledger.py::build_ledger` in the
linear-agent-poller repo); this profile doesn't mandate a specific storage location,
only that costs already spent are always included in the total shown on the next image.
Once **any** cost folded into the running total was estimated, the total itself is also
marked approximate — a sum that includes one guess is itself a guess.

## Display line

Each image's post gets **one extra line** appended to its comment body — the **same**
comment the image itself is posted in, not a new one. This doesn't change the
SAT-482 one-image-per-comment convention, it just adds a line to that comment:

```
💰 Cost: $0.08 · Total spent: $1.24
```

or, when the cost (or any part of the running total) was estimated:

```
💰 Cost: ~$0.05 (estimated) · Total spent: ~$1.21
```

## Boundaries

- This stage only decides **what cost line to display and how to compute it**. It does
  not call `fal_ai` / `gemini` itself (see the `capability-image` skill stage 1
  Generate), and it does not change where/how the image comment itself is posted.
- `DEFAULT_COST_USD` is a placeholder, not a real price list. If a real per-model cost
  source becomes available (a live fal.ai billing API, a Gemini pricing response
  field), prefer it over the constant — the constant only exists to keep this stage
  useful in the meantime.
