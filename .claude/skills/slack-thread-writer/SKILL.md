---
name: slack-thread-writer
description: Transform meeting notes, updates, proposals, or findings into a scannable Slack thread (TLDR first, owners and due dates, open questions) using Slack mrkdwn formatting. Use for "write a Slack thread", "turn this into a Slack update", "draft a Slack message about X". Draft only — never auto-send.
---

# Slack Thread Writer

Transform content into a scannable, action-oriented Slack thread.

## House rule

Never auto-send to Slack — a tool-driven post is still an outbound send. Default output is a paste-ready draft. Only post via a tool after the user explicitly confirms the draft (approves the text or says "send it"); even then, reply with the thread link plus the paste-ready text so the user can verify what went out.

## Slack formatting (mrkdwn, not markdown)

- Bold: `*bold*` (single asterisk), not `**bold**`
- Italic: `_italic_`; strikethrough: `~strike~`
- Bullets: `•` or `-` — flatten nested/numbered lists, including action items, to bullets; mrkdwn doesn't render numbered lists reliably
- Links: `<https://url|label>`, not `[label](url)`
- Backtick code spans/blocks work as in markdown

**Thread vs. broadcast**: default to replying in-thread. Only use "also send to channel" (broadcast) for something the whole channel needs immediately — don't broadcast routine updates.

## Thread shape

1. **TLDR** — one sentence, contains the outcome, no jargon, stands alone.
2. **Stakeholders** — `@mention` owners; `cc:` for FYI audience/channels.
3. **Context** — max 3 bullets: why this matters now, what changed, key constraint/opportunity.
4. **Outcome wanted** — specific, measurable, timeline included.
5. **Success criteria** — 2-3 measurable outcomes.
6. **Action items** — grouped by urgency (This week / Next steps), 2-3 each; every action has an owner and a due date.
7. **Tracking** — how progress will be measured; link to dashboard/doc.
8. **Open questions / blockers**.
9. **Links** — supporting docs/issues/PRs.

Keep the whole thread under ~500 words, scannable in 30 seconds. Never hide the outcome in the middle; never use vague actions like "explore" or "consider" without an owner and date.

## Example

Input: "We need to integrate the payments API with third-party billing providers... coordinate with BD and identify which providers to target first."

Output:

```text
*Enable 3 major billing providers to integrate with the payments API by Dec 1*

@tim @bd-team @eng-payments
cc: #partnerships

*CONTEXT*
• Current billing integrations are manual and don't scale
• Customers need a seamless checkout → billing → reconciliation flow

*OUTCOME*
Customers can route payments through major billing providers without engineering support

*ACTIONS — This week*
• [@tim] Draft integration requirements doc — Due Nov 8
• [@bd-team] Identify top 3 target providers + intro calls — Due Nov 8

*OPEN QUESTIONS*
• Which providers have existing API partnerships?
```

## Quality checks

TLDR is one sentence with the outcome. Every action has an owner and a due date. Context is ≤3 bullets. Open questions are surfaced. Under 500 words. Draft only — never sent automatically.
