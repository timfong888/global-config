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

> **ENFORCEMENT:** Making **any tool call** on a directly-delegated ticket signals that work is in progress. Therefore `mcp__linear__linear_updateIssue` with `stateId` = In Progress MUST be your **first** tool call — before reading the issue, analyzing anything, or posting any comment. If you find yourself mid-task without having set In Progress, set it immediately.
> - **Already In Progress:** proceed without a second transition call (the state change is idempotent).
> - **Call fails:** retry once; if still failing, proceed with the work and note the failure in your pickup comment.
> - **Scope:** applies only to direct delegation (@blocks mention, direct comment, agent poller) — exempt for background or multi-ticket workflows that incidentally touch an issue.

## Handback Rules

- When a task is complete, summarize what changed and what is next in one or two sentences.
- Post comments on Linear issues as a human engineer would: note when starting significant work, post a brief status when completing milestones, and ask questions when blocked. Keep comments concise and substantive — skip trivial one-liners.
- Detailed reports, analyses, and research findings go in the assistant response; brief status updates and handback notes go as Linear comments.
- Updating issue state (status, description, labels) is allowed only when explicitly instructed — **except** for the workflow status transitions defined in the Linear Workflow Status Management section above, which happen automatically.

## Linear API Notes

- **`getIssueHistory` does not expose state transitions.** The MCP wrapper returns `type: "unknown"`, `from: null`, `to: null` for state-change events. To verify a state change was applied, check that `updatedAt` advanced after the `updateIssue` call — do not rely on `getIssueHistory` to confirm state transitions.

## Linear Hierarchical Context

When working on a Linear issue — via direct `@blocks` mention or poller dispatch — **fetch parent and project context before beginning work**. Critical context (which repo to use, architecture decisions, scope rules) often lives in the parent epic or project description and is invisible from the child issue alone.

### Fetch (one call, before starting work)

After identifying the issue, load its full hierarchy. Use `mcp__linear__linear_getIssueById` for the issue itself (which returns `project` and `parent` fields), then make a raw GraphQL call via the Linear MCP for the full nested parent:

```graphql
query IssueContext($id: String!) {
  issue(id: $id) {
    id identifier title description
    project { id name description }
    parent {
      id identifier title description
      parent { id identifier title description }
    }
  }
}
```

> **Direct `@blocks` mention sessions:** `formatted_context` carries the `issue_identifier` (e.g. `AUR-3`). Use `mcp__linear__linear_getIssueById` with that identifier to get the issue and its `parent`/`project`. If no `issue_identifier` is present, skip this step.

> **Poller-dispatched workers:** the orchestrator provides the issue `id` directly. The `linear-agent-poll` skill's B1 extends this fetch with agent-context block resolution and vault CLAUDE.md linking — follow B1 for the full poller fetch; this section defines the base that B1 builds on.

### Stack the context (additive — nothing is dropped)

Treat fetched descriptions as additional context, least-specific first:

| Layer | Source |
|---|---|
| Project | `project.description` |
| Parent epic | `parent.description` |
| Grandparent | `parent.parent.description` (if present) |
| Issue | `issue.description` + comments |

All layers are **co-present and additive** — a less-specific layer is never discarded because a more-specific one exists. If two layers state genuinely contradictory hard rules on the same point, the more-specific layer wins (`issue > parent > grandparent > project`). Contradiction is the exception; additive stacking is the norm.

Traverse at most **2 hops up** (parent + grandparent). Do not fetch beyond the grandparent.

## Skills

Individual skill files live in `.claude/skills/`. Each skill is loaded via the `Skill` tool using its directory name. Skills in this repo are available globally to all Blocks agent sessions.

## Constraints

- Work only within the `workspace` directory. Create subfolders per cloned repository.
- Never commit to a repository's default branch unless explicitly instructed.
- Always clone repositories using `mcp__blocks-internal-mcp__clone_repository_into_folder`.
- Always create a pull request after pushing a new branch with code changes.
- Never force push. Never skip hooks (`--no-verify`).
