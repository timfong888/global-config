# Global Blocks Agent Instructions

This file contains global instructions that apply to every Blocks agent session launched from this repository.

## Tone and Communication

- Be concise and direct. Avoid unnecessary preamble or filler.
- Use plain Markdown in responses — assume it renders correctly.
- Do not ask follow-up questions unless absolutely necessary or explicitly instructed.
- Attempt task completion before asking for help.

## Signing Convention

When committing code associated with a Linear ticket, include the ticket identifier in the commit message:

```
SAT-123: Brief description of the change
```

## Linear Workflow Status Management

When Blocks is directly delegated a Linear issue (via @blocks mention, direct comment, or the agent poller), it **automatically manages workflow status** — no explicit instruction needed:

| Event | Status | Additional actions |
|---|---|---|
| Picks up the issue | → **In Progress** | Set state **before** posting the pickup comment |
| Work complete, needs review | → **In Review** | — |
| Blocked on external dependency or real-world action only the user can take | → **Blocked** | Set priority Urgent |
| Needs inline input (a question the user can answer by replying) | → **In Review** | Set priority Urgent; include a `🔴 Needs input` marker in the comment body |

Rules:
- **State first, comment second.** Always set the Linear state transition before posting any comment — the state change is the immediately visible signal; the comment follows.
- **Never self-certify Done.** Every completion lands in **In Review**; the user promotes to Done after reviewing.
- Use **Blocked** only when the work truly stopped on something a typed reply alone cannot fix (external dependency, purchase, access grant). Use **Needs input** (In Review + Urgent) for a question the user can answer inline.
- Resolve workflow state IDs by introspecting the team's configured states via the Linear API (`team { states { nodes { id name type } } }`) — never hard-code an id; state ids differ per workspace.

> **CRITICAL — pickup ordering (SAT-833):** Your **very first tool call** upon receiving a direct delegation (via `@blocks` mention or the agent poller) **MUST** be `mcp__linear__linear_updateIssue` with `stateId` set to the team's In Progress state. Do not read the issue, do not analyze anything, do not post any comment first. The state transition is the pickup signal. Sequence: (1) update state → In Progress, (2) post pickup comment, (3) begin work.
>
> To verify a state change was applied when `getIssueHistory` returns `type: "unknown"`: confirm that the issue's `updatedAt` timestamp advanced after the `updateIssue` call. The MCP history tool does not expose state-change details — `updatedAt` advancement is the reliable confirmation.

## Handback Rules

- When a task is complete, summarize what changed and what is next in one or two sentences.
- Post comments on Linear issues as a human engineer would: note when starting significant work, post a brief status when completing milestones, and ask questions when blocked. Keep comments concise and substantive — skip trivial one-liners.
- Detailed reports, analyses, and research findings go in the assistant response; brief status updates and handback notes go as Linear comments.
- Updating issue state (status, description, labels) is allowed only when explicitly instructed — **except** for the workflow status transitions defined in the Linear Workflow Status Management section above, which happen automatically.

## Skills

Individual skill files live in `.claude/skills/`. Each skill is loaded via the `Skill` tool using its directory name. Skills in this repo are available globally to all Blocks agent sessions.

## Constraints

- Work only within the `workspace` directory. Create subfolders per cloned repository.
- Never commit to a repository's default branch unless explicitly instructed.
- Always clone repositories using `mcp__blocks-internal-mcp__clone_repository_into_folder`.
- Always create a pull request after pushing a new branch with code changes.
- Never force push. Never skip hooks (`--no-verify`).
