---
name: gdoc-review
description: Review a Google Doc and post inline comments. Editorial mode applies Tim's voice + AI-slop rubric; role mode reviews from a stated perspective (CPO, investor, engineer). Activate with "/gdoc-review <url>", "review this doc", "editorial review", "copyedit this Google Doc", "review this from a CPO's perspective", "add comments to this Google Doc".
---

# Google Doc Review

Read a Google Doc, analyze it, present a numbered approval table, wait for explicit go-ahead, then post comments. Never post before approval — the user edits the table; you post what they approve.

## Modes

- **`editorial`** — act as Tim's editor/copyeditor/proofreader. Apply the AI-slop + editorial rubric below. Default when the request is "review this doc", "edit this doc", "proofread", or unqualified.
- **`role`** — review from a stated role/perspective (e.g. "review this as a CPO would"). Ask: what does someone in this role need to know or decide? Prioritize gaps, contradictions, missing decisions over generic observations. No fixed rubric — the role itself is the lens.

Both modes: `Resolve identity → Read doc → Analyze → Numbered approval table → Wait → Post → Verify`.

## Identity / connection resolution

Default: Composio project `timfong888_org`, the `timfong888`-prefixed connection (not `aurora`). If the invoking project's CLAUDE.md names a different Composio project/connection (e.g. an Aurora doc), use that instead — read the project CLAUDE.md first. If ambiguous, ask; the wrong connection returns empty output, not an error.

## Rubric (editorial mode)

Starter rubric seeded from Tim's writing memory/CLAUDE.md (public-writing, pm-writing-agent conventions). Tim edits this list over time. Critique the prose itself — never accuse the author of using AI; name the specific problem in the sentence.

**Flag these patterns:**

- Throat-clearing/filler: "It's important to note that", "In today's fast-paced world", "In conclusion", restating the heading before saying anything.
- Corporate jargon: leverage, synergy, seamless, robust, cutting-edge, game-changing, best-in-class, holistic, empower, unlock, streamline, "at scale" (when vague).
- Generic filler vocabulary: delve, tapestry, landscape, realm, navigate (figurative), underscore, testament, beacon, "plays a vital/crucial role".
- Empty intensifiers/hedges: very, really, quite, incredibly, arguably, somewhat, "some", "various", "a number of" — when substituting for a concrete number or claim.
- Tricolon padding: reflexive "fast, reliable, and scalable" rule-of-three lists that add cadence but no content.
- "Not only X but also Y" / "It's not just X, it's Y" and other rhythmic scaffolding.
- Uniform sentence rhythm; em-dashes as a default connector.
- Assertion without evidence: "significantly improves", "users love", "industry-leading" with no number/source/example.
- Sycophancy or false balance: "Great question", both-sides mush that dodges a decision.
- Passive voice hiding the actor: "mistakes were made", "it was decided" — who?
- Abstraction with no concrete instance: a paragraph that never touches a real example, name, or figure.

**Check the doc for these (Tim's editorial framework):**

- Directness — leads with the point/decision; flag a buried lede.
- Evidence over assertion — every strong claim earns a number or source.
- Scannable & actionable — structure a reader can skim.
- Contextual accuracy — matches what's actually known/decided; flag claims contradicting established project context.
- Voice — plain, confident, no jargon or AI cadence.

Prioritize substance (unsupported claims, missing decisions, contradictions, buried lede) over nits. Don't manufacture comments on clean passages.

## Approval table — wait before posting

| # | Anchor text (exact, quoted from doc) | Issue | Suggested comment |
|---|---|---|---|
| 1 | "exact phrase from doc" | AI-slop: buzzword | "'leverage' → 'use'. Say what it does." |
| 2 | "exact phrase from doc" | Unsupported claim | "Needs a number — what's the actual lift?" |

Anchor text must appear **only once** in the doc (lengthen the substring if it repeats). Ask the user to approve, edit rows, or skip numbers. Do not proceed without explicit go-ahead.

## Posting comments

**Primary — Composio CLI.** Read the doc, then post:

```bash
composio execute GOOGLEDOCS_GET_DOCUMENT_PLAINTEXT -d '{"document_id": "<DOC_ID>"}'

composio execute GOOGLEDRIVE_CREATE_COMMENT -d '{
  "file_id": "<DOC_ID>",
  "content": "N. <comment text> (by Claude)",
  "quoted_file_content_value": "<exact anchor phrase, appears only once>"
}'

composio execute GOOGLEDRIVE_LIST_COMMENTS -d '{"file_id": "<DOC_ID>"}'
composio execute GOOGLEDRIVE_DELETE_COMMENT -d '{"file_id": "<DOC_ID>", "comment_id": "<ID>"}'
```

Prefix every comment with its table number and sign `(by Claude)`. Capture returned comment `id`s in case deletion is needed.

**Known constraint — inline-anchored (highlighted) comments cannot be created via the API.** The Drive/Docs API accepts anchor data but Google Workspace editors only honor internal `kix.PARAGRAPH_ID` values, which no public API exposes (open since 2016: issuetracker.google.com/issues/36763384). A `GOOGLEDRIVE_CREATE_COMMENT` call with `quoted_file_content_value` often lands but renders as "Original content deleted" instead of a real highlight.

**Fallback — Playwright, for a real inline-highlighted comment.** Use when the doc must show a genuine highlighted anchor (this is the default expectation in `editorial` mode). Drives the actual Docs UI. The approval table was built from an earlier read — re-check each anchor against the live doc as you go, not from memory:

```javascript
// Cmd+F → type → confirm exactly one match → Enter → Escape (selection persists) → Cmd+Opt+M → type comment → Post
async function addComment(page, searchText, commentText) {
  await page.keyboard.press('Meta+f');
  await page.waitForTimeout(600);
  await page.getByRole('searchbox', { name: 'Find in document' }).fill(searchText);
  await page.waitForTimeout(400);

  // Google Docs' find bar renders "n of m" (or "No results") next to the box —
  // read it before touching anything else. Abort this anchor, don't guess,
  // unless it reads exactly "1 of 1".
  const matchLabel = await page.getByText(/^(\d+ of \d+|No results)$/).textContent().catch(() => null);
  if (matchLabel !== '1 of 1') {
    await page.keyboard.press('Escape');
    return { posted: false, searchText, reason: matchLabel ? `matched "${matchLabel}", not exactly one` : 'not found' };
  }

  await page.keyboard.press('Enter');
  await page.waitForTimeout(600);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  // Docs renders the selection on a canvas — no DOM API can confirm it stuck.
  // Screenshot here and visually confirm searchText is highlighted before
  // continuing; if it isn't, skip this anchor rather than comment blind.
  await page.keyboard.press('Meta+Alt+m');
  await page.waitForTimeout(800);
  await page.getByRole('textbox', { name: 'Comment draft' }).fill(commentText);
  await page.waitForTimeout(300);
  await page.getByRole('button', { name: 'Post Comment' }).click();
  await page.waitForTimeout(1000);
  return { posted: true, searchText };
}
```

Two abort conditions, checked in order: (1) the match-count label isn't exactly `1 of 1` — anchor missing or duplicated; (2) after Enter+Escape, the screenshot doesn't show `searchText` visibly highlighted — selection didn't survive. Either one means skip that row, don't post, and carry it into the skipped list for the Verify report below. Navigate with `?tab=<TAB_ID>` for multi-tab docs and confirm the correct tab in the snapshot before starting. If Playwright lands on a Google sign-in page, stop and ask the user to log in — do not fall back to guessing or to API-based posting. Post in batches of 3–5, snapshotting between batches. Pass `commentText` to `.fill()` unchanged — apostrophes don't need escaping there. Only escape apostrophes/quotes where the transport actually requires it: inside a JS string literal, a shell command, or a JSON payload (e.g. the Composio CLI calls above).

## Verify

```bash
composio execute GOOGLEDRIVE_LIST_COMMENTS -d '{"file_id": "<DOC_ID>"}'
```

Confirm each posted comment has a real `kix.*` anchor, not "Original content deleted". Report: N posted, anything skipped, anything that failed to anchor.
