# Skills Inventory — what was kept, merged, and dropped

Decision record for the consolidation of Tim's local Claude Code skills (the `02-AI-Tools/skills/`
tree in his Obsidian vault) into this repo for Blocks. Linear: SAT-685.

**Result: the 42 skills worth porting — 14,513 lines — became 23 skills / 1,833 lines (-87%).**
Nothing was deleted from the vault; it remains the source of truth. This is an export.

## How the counts add up

The vault tree holds **70 directories that contain their own `SKILL.md`** (55 at the top level,
15 more that live only under `skills/user/`). Every one is accounted for below:

| | Count |
|---|---|
| Ported — merged into 9 consolidated skills | 28 |
| Ported — condensed 1:1 | 14 |
| **Ported subtotal** | **42** |
| Not ported — local GUI / personal account | 15 |
| Not ported — vault-filing only | 6 |
| Not ported — superseded or stale | 5 |
| Not ported — byte-identical duplicate (`prompt-runner`) | 1 |
| Not ported — already in this repo (`canvas`) | 1 |
| **Not-ported subtotal** | **28** |
| **Total** | **70** |

Two further groups sit outside that 70 because they have no `SKILL.md` of their own: three empty
directories, and five plugin-managed symlinks. Both are described under "Not ported".

## Why anything was cut at all

Blocks merges this repo's skills into *every* session — sandbox, Slack, GitHub, and Linear. Two
properties of that make a straight copy of 70 skills the wrong answer:

1. **Every skill's description is resident context in every session.** Seventy descriptions is a
   standing tax on unrelated work.
2. **Names are a global namespace.** Blocks silently appends a number on collision
   (`review-security2`), so near-duplicate skills don't just waste space — they make the losing
   one unreachable by the name people type.

The skills were also written for weaker models and narrate procedure a current model already
knows. The editorial rule applied throughout: **keep what the model cannot infer** — exact IDs,
endpoints, credential locations, file paths, API quirks, house rules, named taxonomies — and cut
what it can. That is where most of the 87% went; very little actual capability was lost.

## Merged

Nine consolidations account for 28 of the source skills.

| Skill | Merged from | Lines |
|---|---|---|
| `spec-review` | `dev-spec-clarity`, `dev-spec-completeness`, `dev-spec-dx-review`, `dev-spec-implementation-readiness`, `dev-spec-technical-accuracy-v2` | 3,091 → 128 |
| `prd-review` | `pm-orchestrator` + its 5 sub-agents (`pm-strategy-agent`, `pm-jtbd-agent`, `pm-research-agent`, `pm-validation-agent`, `pm-writing-agent`) | 2,227 → 91 |
| `frontend-performance-audit` | `nextjs-performance-audit`, `nextjs-bundle-check`, `react-rerender-audit` | 950 → 161 |
| `google-sheets` | `google-sheets`, `google-sheets-sdk`, `perplexity-sheets` | 1,135 → 102 |
| `prd-intake` | `pm-intake`, `intake-to-prd-weave` | 808 → 70 |
| `excalidraw` | `excalidraw-generator`, `excalidraw-export` | 525 → 69 |
| `content-review` | `pm-blog-announcement-reviewer`, `content-positioning-os` | 512 → 80 |
| `run-prompts` | `prompt-in-line`, `prompt-runner` | 419 → 67 |
| `gdoc-review` | `editorial-review`, `gdocs-review-and-comment`, `google-docs-review` | 418 → 107 |

Each merge was verified by reading the sources, not inferred from similar names. The notable ones:

- **`spec-review`** — five separate ~500-line rubrics, each repeating the same output template,
  "review process," and "quality standards" boilerplate. The five *lenses* are genuinely
  distinct; the five *files* were not. Each lens's native scoring scale was preserved rather than
  unified, because they measure different things and averaging them would be meaningless.
- **`prd-review`** — the orchestrator dispatched five subagents that are byte-equivalent to five
  skills of the same name. Blocks has no vault subagents to dispatch to, so the rubrics are now
  inline. The 85-point threshold, "writing always re-runs," 5-round cap, and plateau detection are
  house conventions and were kept exactly.
- **`frontend-performance-audit`** — `nextjs-bundle-check` is an elaboration of the audit's
  category 2 and `react-rerender-audit` of its category 5, with the same libraries, grep patterns,
  and fix code. Genuine duplication.
- **`gdoc-review`** — the three sources actively *contradicted* each other on whether the Drive
  API can anchor a comment. Resolved in favour of the two that say it cannot; see Corrections.

## Condensed 1:1

Fourteen skills kept their identity and were rewritten for density.

| Skill | Lines | Skill | Lines |
|---|---|---|---|
| `add-mcp-server` | 909 → 80 | `research-synthesizer` | 233 → 57 |
| `linear-sanitize` | 488 → 106 | `pm-1-1-prep` | 233 → 45 |
| `skills-diagnostic` | 466 → 38 | `public-writing` | 226 → 42 |
| `github-ticket` | 325 → 111 | `vercel-comments-deployment` | 180 → 84 |
| `prompt-engineer` | 326 → 55 | `linear-ticket` | 134 → 77 |
| `filecoin-pay-subgraph` | 307 → 118 | `mem0` | 52 → 31 |
| `slack-thread-writer` | 305 → 66 | `skills-creator` | 246 → 48 |

`linear-sanitize` and `public-writing` were routing stubs whose real content lived in sibling
`references/*.md` files (~545 lines). Blocks reads one `SKILL.md` per skill, so that content was
inlined — those two gained substance while shrinking.

`skills-creator` and `skills-diagnostic` were retargeted from "manage `~/.claude/skills` symlinks
on this Mac" to "author and validate skills in a repo," which is what they mean under Blocks.

## Not ported

None of this was deleted from the vault. It is listed so the omissions are deliberate and
reviewable rather than silent.

### Depends on a local GUI app, local session, or personal account (15)

Blocks runs in a cloud sandbox where none of these exist, and a skill that cannot execute is
pure context cost.

`things` (Things 3), `open-in-obsidian`, `move-to-obsidian`, `logseq-todo-process`,
`logseq-weekly-sync`, `logseq-log-artifacts`, `telegram-check-filecoin`, `schedule-calendly`,
`expensify-automation`, `playwright-cli` (needs a locally installed binary), `photo-compositing`,
`time-block`, `sync-gdoc`, `career-coach`, `wab-statements`.

The last one deserves its own note: `wab-statements` drives a browser into a mortgage servicer's
portal, which conflicts with Tim's standing rule that agents never drive browsers into bank or
brokerage portals. It should not be in a globally-loaded skill set on that ground alone.

### Vault-filing only (6)

Their entire job is writing into the Obsidian PARA structure. There is no non-inferable API quirk
or house rule inside worth extracting.

`mcp-inventory-updater`, `organize-mcp-to-vault`, `sync-project-skills`, `master-list-migrator`,
`add-shared-link`, `substack-intake-agent`.

### Byte-identical duplicate (1)

`prompt-runner` exists twice in the vault — once at the top level and once under `skills/user/`,
with identical contents. Only the live copy was used as a merge source for `run-prompts`.

### Superseded, stale, or empty (5 skills + 3 empty directories)

- `dev-spec-technical-accuracy` (v1) — no YAML frontmatter at all, so Claude Code never loaded it;
  already unlinked from `~/.claude/skills`. Superseded by v2 **except** for its
  auth-documentation checks (header format, OAuth flow, per-endpoint scopes, webhook signature
  verification), which no other lens covered. Those were folded into `spec-review`'s completeness
  lens rather than lost.
- `pm-setup` — symlinks PM slash commands from a hardcoded local vault path. Obsolete under Blocks.
- `pipedream-mcp-enhancer` — builds on the pipedream MCP servers, which are retired.
- `filoz-google-sheets` — already in the vault's `retired-skills/`. Its only content was a catalog
  of FilOz spreadsheet IDs; see Corrections for why it was not carried forward.
- `test-skill` — a discovery-system test fixture.
- `project/`, `project-archives/`, `retirement-advisor/` — empty directories, no `SKILL.md`.

### Not Tim's to vendor (5)

`autofix`, `basecamp`, `code-review`, `composio-cli`, `find-skills` are symlinks into
`.agents/skills/`, installed and updated by `npx skills add`. Copying them here would fork them
and guarantee a name collision with the plugin-managed originals.

### Already present (1)

`canvas` already exists in this repo from SAT-636. The vault's copy is older, longer, and pins an
`mcpServers` command to an absolute path under the user's home directory. Left untouched.

## Corrections made along the way

These are changes of substance, not compression — flagged because they alter behavior.

1. **`filecoin-pay-subgraph` — the documented endpoint is dead.** The source skill pointed at
   `project_cmdvcyb5ffuzh01z06x0t0vt8/subgraphs/pay/1.0.1`, which does not match anything else in
   the vault. The endpoint the vault cites 37 times
   (`project_cmb9tuo8r1xdw01ykb8uidk7h/.../filecoin-pay-mainnet/1.0.6`) was tested directly on
   2026-07-31 and returns `404 Subgraph not found` — as does every other subgraph under that
   project, which points at a project-level rotation rather than one bad deploy. The skill now
   says to resolve the current endpoint from the Goldsky dashboard and smoke-test it, instead of
   asserting a URL that fails. **This is a live data-pipeline issue beyond the scope of SAT-685
   and needs its own ticket.**
2. **`gdoc-review` — resolved a contradiction between sources.** `gdocs-review-and-comment`
   presented `GOOGLEDRIVE_CREATE_COMMENT` + `quoted_file_content_value` as if it anchors normally;
   the other two sources state it renders as "Original content deleted" and that only Playwright
   produces a true `kix.*` anchor. The merged skill documents the API limitation and keeps
   Playwright as the fallback for genuine highlights.
3. **`slack-thread-writer` — fixed a latent formatting bug.** The source template used
   `**bold**`, which does not render in Slack. Slack mrkdwn rules (`*bold*`, `<url|label>`) are now
   stated explicitly. The "never auto-send, draft only" house rule was also added.
4. **`frontend-performance-audit` — the "51 rules" claim is unsupported.** The source asserts
   "Vercel's 51 performance rules across 8 categories" but only ever names 17 of them (categories 1
   and 2 carry three rules each, the other six carry two). All 8 categories and all 17 named rules
   are preserved, and the skill now advertises 17 rather than 51; it states plainly that the rest are not
   specified, so nobody invents them to reach 51.
5. **`google-sheets` — FilOz spreadsheet IDs dropped.** They are real-format IDs, but they came
   from a skill Tim had already retired, belong to another org's Drive, carry no capture date, and
   depend on `tim@filoz.org` OAuth this skill no longer documents. A stale ID in a globally-loaded
   skill sends the agent to the wrong document *silently*. The skill now points back at the vault
   copy instead.
6. **Retired infrastructure removed throughout.** References to Rube MCP / `rube-personal`
   (sunset 2026-05-15), `composio-personal` (never existed), the pipedream MCP servers, and
   Greptile (retired 2026-05-27, replaced by CodeRabbit) were replaced with the Composio CLI, with
   direct GraphQL via `$LINEAR_API_KEY` as the documented Linear fallback.
   `scripts/validate_skills.py` fails the build if any of them reappear.

## Open items for Tim

- **Goldsky endpoint (correction 1)** — needs a real fix and its own ticket. Until then
  `filecoin-pay-subgraph` can describe the schema but cannot query.
- **Composio tool slugs** in `pm-1-1-prep` and `linear-ticket` were written from the documented
  naming convention and not executed live (the CLI logs out frequently). Both skills instruct the
  agent to resolve the live slug with `composio search <app>` first rather than trusting a
  hardcoded one, so a wrong guess degrades to a lookup instead of a failure.
- **Proposed vault cleanups** — not performed, since the vault stays source of truth:
  delete the empty `project/`, `project-archives/`, `retirement-advisor/` directories; delete
  `test-skill`; remove `skills/prompt-runner/`, which is a byte-identical orphan of
  `skills/user/prompt-runner/`; and either delete `dev-spec-technical-accuracy` (v1) or give it
  frontmatter, since without it Claude Code has never loaded it.
