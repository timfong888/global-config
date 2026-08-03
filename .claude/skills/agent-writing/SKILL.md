---
name: agent-writing
description: Writing/research handler for the Linear agent poller — classifies tickets into research, plan, write, or image output modes; routes to the matching skill; posts inline (short) or to a linked vault note (long). Image mode edits supplied photos via photo-compositing skill.
whenToUse: Load this skill when the linear-agent-poll tick routes an issue to the writing track (agent-writing label or inferred from description as writing, research, or planning work).
---

# Profile: agent-writing (writing / research / planning handler)

The writing/research handler for `/linear-agent-poll` (Satchel SAT-350). The tick
routes here when the picked-up issue carries the `agent-writing` label (or the
request is inferred as writing/research). You have already posted the pickup
comment and moved the issue to In Progress — this profile is step 6 ("Do the
work") and step 7 ("Report").

**Reuse, don't reimplement.** This profile only routes to existing skills and posts
the result back. Keep context lean: work from the ticket description + its comments
only — never load the whole project. Route web content through firecrawl's
`.firecrawl/` files, not the prompt. Sign every comment `(by Claude)`.

**Image capability.** If a writing ticket needs a generated or edited image (e.g. a
hero image for a draft), load the **`capability-image`** skill (Skill tool) and follow its pipeline
(generate → download → host → attach → report cost) rather than reinventing it — [SAT-491](https://linear.app/sophia-xyz/issue/SAT-491).
When image production *is* the primary deliverable (not a side asset), classify the
issue as the **image** output mode below and follow its flow — [SAT-523](https://linear.app/sophia-xyz/issue/SAT-523).

## 1. Classify the flow & self-label it

Decide which of four modes the ask wants, by its **end deliverable**:

| Mode | Question it answers | Output |
|---|---|---|
| **research** | "What's true / what's out there?" | Cited findings — themes, evidence, gaps |
| **plan** | "What should we do / how should this be structured?" | A structure — outline, options + trade-offs, recommendation, step sequence (NOT finished prose) |
| **write** | "Here is the finished thing to read." | Polished prose for a specific audience |
| **image** | "Show me the thing, edited from my photo." | Edited images — additive edits of a supplied photo (interior design compositing via `photo-compositing` skill) |
| **ui-mockup** | "Show me what this screen/UI should look like." | High-fidelity mobile/web UI screenshots embedded inline in Linear (via `mobile-mockups` skill) |

A request can chain (research → plan → write); **label it by the final
deliverable** and do the upstream phases as needed to get there.

**Inference leads; then make your reading legible by labeling the issue:**

- If the issue **already carries a `mode › *` label** → that is the human
  override. **Obey it.** If your own reading differs, post a one-line note:
  `Note: tagged mode › plan; I'd have read this as write — proceeding as plan. (by Claude)`
- If **no mode label** → apply the one you inferred via `LINEAR_UPDATE_ISSUE`,
  adding the child label to the issue's current `labelIds` (keep all existing
  labels). The label is now the interpretation of record, visible at a glance.
- Exactly one mode label per issue.

Mode label IDs (group `output-mode` = `806cc6b2-8ce0-41da-87d7-0a2a2d5a893e`):
- research `c0322e8b-27a2-4a55-9a8a-a7f345af778f`
- plan `76832ec1-f65e-41e9-8e74-1effb165dc52`
- write `e1e58446-ec85-4193-be25-b98f3a335869`
- image `cf7ba974-fd72-48b4-aa02-bb379d2f010e`
- ui-mockup (label to be created — set `mode › ui-mockup` on a ticket to force this mode; infer it from description phrases like "mockup", "UI design", "screen design", "what should the UI look like")

### Scoping & assumptions (per SAT-362)

Writing work is almost always **reversible** — a draft or report is *reviewable*,
not sent or published — so the default is **act with stated assumptions, not ask.**
When the mode or a load-bearing detail is unclear (write needs channel + audience +
length + key messages; research needs a specific-enough question):

1. **Climb the context ladder** before it becomes a question for Tim: the ticket +
   its links → **mem0** (Tim's decisions/preferences) → the vault via
   **document-mcp** (facts, specs, prior notes) → how similar past tickets were scoped.
2. **Still uncertain but reversible?** Take the most likely reading, make it
   legible — the `mode` label is itself a stated assumption; for anything beyond it
   add one line: `Proceeding on the assumption that … — reply if wrong and I'll
   redo. (by Claude)` — and **do the work**.
3. **Block only when expensive or irreversible** — a large `deep-research` run a
   wrong scope would waste, or content meant to go out without your review. Then
   post ONE batched `> question:`, set **Urgent**, stateId → In Review, end the tick.

Honor a per-ticket autonomy label if present: `auto:full` (never block — always act
with assumptions), `auto:confirm` (confirm before the expensive/irreversible step),
`auto:plan-first` (deliver the outline and confirm before the full draft).

## 2. Run the flow

**research** (default engine is lean + cheap):
1. `firecrawl:firecrawl-search` with `--scrape` → results land in `.firecrawl/`
   (keeps web text out of context); `firecrawl:firecrawl-scrape` for a named URL.
2. `research-synthesizer` over those files → a citation-rich report.
3. Escalate to `deep-research` **only** when the ticket says "deep/thorough" or the
   question is broad/open. If it wants clarifying questions, surface them as a
   single Linear `> question:` block — don't run blind.

**plan**:
- Produce a structured plan, not prose: frame the goal, lay out options / steps /
  sections with trade-offs, end with a recommendation. Use `public-writing`'s
  structuring discipline (SCQA / Minto pyramid) for the skeleton.
- Do light `firecrawl-search` first if the plan needs facts.

**write**:
- Prose / argument / memo → `public-writing`. Channel-formatted content →
  `marketing:draft-content`. Critique/revise a doc the ticket points at →
  `content:review-public-content`.
- Run the full pipeline as needed: research → outline → draft → tighten.
- `draft-content` is interactive — extract its inputs (channel, audience, length,
  key messages) from the ticket; ask via `> question:` only if a load-bearing one
  is missing. Neutral professional tone unless the ticket's project has a
  configured brand voice.

**image** (the deliverable is edited photos, not prose):
- **Expect an input photo.** This mode **edits a photo the ticket supplies** — never
  text-to-image from scratch. Look for at least one source photo attached to the issue
  or linked in its description/comments. If none is present, that's a **hard block**:
  post a `> question:` asking for the source photo(s) and stop — don't invent a subject.
  This one gap blocks **regardless of an `auto:full` autonomy label**: `auto:full`
  means "act with assumptions instead of asking," but a missing subject can't be
  assumed — fabricating one is exactly the hallucination this mode exists to prevent, so
  the no-hallucinate rule wins over the never-block default here.
- **Route to the `photo-compositing` skill.** It's built for exactly this: it feeds the
  real photograph into fal.ai's image editing API (`fal-ai/nano-banana-2/edit` by default)
  and makes **additive edits only** — preserving the existing scene (walls, perspective,
  lighting, permanent fixtures) and **not hallucinating** new structure. The skill contains
  the full prompt template, model selection table, and quality checklist.
- **One edited output per supplied angle — never a fabricated viewpoint.** The multiple
  angles come from the **input**, not from inventing geometry: edit *each* supplied photo
  into its own mock-up, so N source photos → N edited outputs. Because a genuine second
  viewpoint can't be synthesized from a single photo without hallucinating perspective
  (which this mode forbids), the ≥2-angle expectation is on the **source set**: the ask
  typically supplies at least two different angles, and when the supplied photos are
  significantly different you produce a **corresponding mock-up per angle**. If only one
  photo is supplied, produce one edited output; when the ticket wants more angles than
  were supplied, ask for the additional source photos rather than fabricating them.
- **Meet the aesthetic / organizational guidelines** the ticket (or its project/epic
  context) states — the skill's prompt template has explicit slots for materials,
  furniture, lighting/mood, and per-angle camera context; fill them from the ticket
  rather than leaving them generic.
- **Then run the shared `capability-image` skill pipeline for each output**:
  download to disk for native `Read` review (confirm the base photo's structure is
  preserved and nothing was hallucinated before proceeding), host durably, attach the
  durable URL to the issue, and report the image cost. This mode is an
  image-capability consumer — it doesn't reinvent those stages.

**ui-mockup** (the deliverable is a generated mobile/web UI design):
- **Route to the `mobile-mockups` skill.** This mode generates high-fidelity UI screens
  as full-size PNGs embedded inline in Linear comments — no clicking required to see them.
  The skill covers HTML template, Playwright rendering at retina resolution, multi-variant
  loops, and the inline comment delivery protocol.
- **No source photo required** — UI mockups are generated from scratch based on the
  ticket description, existing app theme, and any design references the ticket provides.
- **Coding-agent friendly** — every mockup comes with a design spec table (colors, font
  sizes, spacing, radius, shadows) so a coding agent can implement it directly.
- **Check for an existing theme file.** Before writing the HTML, look for
  `constants/theme.ts`, `tailwind.config.js`, or equivalent in the referenced repo.
  Use the exact hex values from the theme file if readable; otherwise establish a coherent
  palette and document it in the comment.

## 3. Size the output → choose destination

- **Short** (fits a comment — a few paragraphs, ≲ ~400 words) → post the full text
  inline in the result comment. No vault file.
- **Long** (multi-section report/plan, full article — anything you'd scroll) → write
  a vault note and link it:
  - research → `{VAULT_ROOT}/05-Index/research/SAT-<id>-<slug>.md`
  - plan / draft → the named project folder if the ticket clearly belongs to one
    (e.g. `{VAULT_ROOT}/10-Projects/<project>/…`); otherwise
    `{VAULT_ROOT}/02-AI-Tools/linear-agent-system/drafts/SAT-<id>-<slug>.md`
  - Frontmatter: `linear: SAT-<id>`, `type: research|plan|draft`, `created`,
    `status: draft`, source links.
  - Append a newest-on-top `[create]` line to
    `{VAULT_ROOT}/CLAUDE-CHANGELOG.md` for the new file.
  - **`VAULT_ROOT`** must be defined in the workspace `## Agent Poll Configuration` block
    of the project `CLAUDE.md` (e.g. `VAULT_ROOT: ~/Documents/remoteObsidian1025`).
    If unavailable (e.g. Blocks cloud environment where the local vault isn't mounted),
    post the full content inline as a Linear comment instead and note the vault path
    it *would* have been written to.
- **Image** → the deliverable isn't text, so it doesn't go inline or to a vault note:
  each edited image is **attached to the Linear issue** via the `capability-image` skill
  pipeline (durable-hosted attachment). The result comment describes what was edited and
  links the attachments.
- **UI mockup** → PNG screenshots embedded inline via the `mobile-mockups` skill delivery
  protocol. Images appear directly in Linear comments without clicking. A design spec
  table follows each image set.

## 4. Report & hand back (tick step 7)

Handback = set `stateId` to `STATE_IN_REVIEW` — never change the assignee (the human
keeps it throughout, per B6 in `linear-agent-poll`).

- **Short** → `✅ Done — <one-line framing>` + the full draft/answer inline. `(by Claude)`. State → In Review.
- **Long** → `✅ Done — <3–5 line summary>. Full <research|plan|draft>: <Markdown link to the vault note>.` `(by Claude)`. State → In Review.
- **Image** → `✅ Done — <what was edited, from which photo, how many angles>.` + the attached edited images. `(by Claude)`. State → In Review.
- **UI mockup** → `✅ Done — <screen name>, <N> variant(s).` + embedded PNG mockups + design spec table inline. `(by Claude)`. State → In Review.
- **Blocked / missing input** → `> question: <what you need>`, set **Urgent**, state → In Review, end the tick.

Render any cross-issue reference as a clickable Markdown link —
`[SAT-123](https://linear.app/sophia-xyz/issue/SAT-123)`, never a bare identifier.

---

### Legibility rules — comments and descriptions (SAT-596)

These apply to **every comment and ticket description** this profile writes. The reader
is on a phone. Five bad screens is a failed handback.

**Answer first.** Line 1 = the outcome or decision. The reader should be able to stop there.

**One idea per bullet, ≤ 20 words.** If a bullet needs a sub-clause, it needs two bullets.
N items → N bullets, never N items crammed into one run-on sentence.

**Bold the 2–4 load-bearing words** in each bullet so a skim-reader catches the gist.
Don't bold full sentences.

**No inline walls of code or long paths.** A file path or URL that wraps mid-sentence
breaks mobile layout — put it on its own line or behind a Markdown link.

**Depth goes in the vault note, not the comment.** The comment is the glance; the link is
the deep-dive. If a bullet needs more than 20 words to be accurate, the extra words belong
in the linked note.

**Target size: 5–8 short lines** for a handback comment. A research summary or plan
outline that must be inline may run longer — but each *section* must still follow these
rules, not just the opening.

**Bad example** (wall-of-text, buried lede, marathon sentence):

> I went through the issue and confirmed that the configuration file located at
> `~/development/linear-agent-poller/profiles/agent-writing.md` was updated, and also
> checked the related `linear-agent-poll.md` orchestrator file to make sure both the
> comment-writing and description-writing surfaces now carry the new legibility constraint
> block that you asked for so that future handbacks are shorter and easier to read on mobile.

**Good example** (answer first, one idea per bullet, bold key words, depth behind link):

> ✅ **Legibility rules wired** — comments and descriptions, both surfaces.
> - **agent-writing.md** — new rule block at end of § 4 (Report & hand back).
> - **linear-agent-poll.md** — new rule block in B6 (applies to all tracks).
> - Full spec: [SAT-596-ticket-legibility-prompt.md](vault link) (by Claude)
