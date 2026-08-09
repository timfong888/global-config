#!/usr/bin/env python3
"""Post an @blocks mention comment to a Linear issue when an AI review bot submits a PR review.

Reads all inputs from environment variables (set by the GitHub Actions workflow).

Required environment variables:
    LINEAR_API_KEY         — Linear personal API key (comment:create scope)
    LINEAR_ID              — Linear issue identifier, e.g. SAT-660
    PR_NUMBER              — GitHub PR number
    PR_URL                 — Full URL to the GitHub PR
    PR_TITLE               — PR title
    REVIEW_URL             — URL to the specific review
    REVIEW_STATE           — GitHub review state (approved/changes_requested/commented)
    REVIEW_BODY            — Review body text (may be empty)
    REVIEWER_LOGIN         — GitHub login of the reviewing bot
    REPO                   — GitHub repository in owner/name format
    BLOCKS_LINEAR_USER_ID  — Linear user ID for the Blocks agent (@blocks mention target).
                             Set as a GitHub repository variable (vars.BLOCKS_LINEAR_USER_ID).
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import urllib.error
import urllib.request

BOT_NAMES: dict[str, str] = {
    "coderabbitai[bot]": "CodeRabbit",
    "sourcery-ai[bot]": "Sourcery",
}

STATE_LABELS: dict[str, str] = {
    "approved": "✅ Approved",
    "changes_requested": "🔴 Changes Requested",
    "commented": "💬 Commented",
}

MAX_BODY = 2000
LINEAR_API_URL = "https://api.linear.app/graphql"

COMMENT_MUTATION = """
mutation PostComment($issueId: String!, $body: String!, $mentionedUserIds: [String!]) {
  commentCreate(input: { issueId: $issueId, body: $body, mentionedUserIds: $mentionedUserIds }) {
    success
    comment { id url }
  }
}
"""


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        print(f"❌ Required environment variable {name} is missing or empty", file=sys.stderr)
        sys.exit(1)
    return value


def build_comment_body(
    reviewer_name: str,
    pr_number: str,
    pr_title: str,
    pr_url: str,
    repo: str,
    review_state: str,
    review_url: str,
    review_body: str,
) -> str:
    state_label = STATE_LABELS.get(
        review_state.lower(),
        review_state.replace("_", " ").title(),
    )

    if len(review_body) > MAX_BODY:
        review_body = (
            review_body[:MAX_BODY].rstrip()
            + "\n\n*(review summary truncated — see full review at the link above)*"
        )

    summary_section = (
        f"\n\n---\n\n**{reviewer_name} summary:**\n\n{review_body}"
        if review_body
        else ""
    )

    return textwrap.dedent(f"""\
        @blocks {reviewer_name} has completed its review on \
[PR #{pr_number}: {pr_title}]({pr_url}) in `{repo}`.

        **Review state:** {state_label}
        **Review:** {review_url}{summary_section}

        Please review the {reviewer_name} feedback and address any blocking comments \
before this branch is ready to merge.""")


def post_comment(api_key: str, issue_id: str, body: str, blocks_user_id: str) -> None:
    payload = json.dumps(
        {
            "query": COMMENT_MUTATION,
            "variables": {
                "issueId": issue_id,
                "body": body,
                "mentionedUserIds": [blocks_user_id],
            },
        }
    ).encode()

    req = urllib.request.Request(
        LINEAR_API_URL,
        data=payload,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
    except urllib.error.URLError as exc:
        print(f"❌ Network error posting to Linear: {exc.reason}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))

    comment_data = result.get("data", {}).get("commentCreate", {})
    if comment_data.get("success"):
        comment_url = comment_data.get("comment", {}).get("url", "")
        print(f"✅ Posted @blocks comment to Linear issue {issue_id}: {comment_url}")
    else:
        errors = result.get("errors", result)
        print(f"❌ Failed to post comment to Linear: {errors}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    api_key = _require("LINEAR_API_KEY")
    linear_id = _require("LINEAR_ID")
    pr_number = _require("PR_NUMBER")
    pr_url = _require("PR_URL")
    pr_title = _require("PR_TITLE")
    review_url = _require("REVIEW_URL")
    review_state = _require("REVIEW_STATE")
    review_body = os.environ.get("REVIEW_BODY", "").strip()
    reviewer_login = os.environ.get("REVIEWER_LOGIN", "AI reviewer")
    repo = _require("REPO")
    blocks_user_id = _require("BLOCKS_LINEAR_USER_ID")

    reviewer_name = BOT_NAMES.get(reviewer_login, reviewer_login)

    body = build_comment_body(
        reviewer_name=reviewer_name,
        pr_number=pr_number,
        pr_title=pr_title,
        pr_url=pr_url,
        repo=repo,
        review_state=review_state,
        review_url=review_url,
        review_body=review_body,
    )

    post_comment(api_key, linear_id, body, blocks_user_id)


if __name__ == "__main__":
    main()
