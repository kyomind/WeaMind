# Issue tracker: GitHub

Issues and specs live in GitHub Issues for `kyomind/WeaMind`.
Use the `gh` CLI for all operations.

## Conventions

- Create: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- Read: `gh issue view <number> --json number,title,body,labels,comments`.
- List: `gh issue list --state open --json number,title,body,labels,comments`; apply label and state filters as needed.
- Sub-issues: `gh issue create --parent <parent> ...` or `gh issue edit <parent> --add-sub-issue <child>`.
- Blocking: use native dependencies with `gh issue edit <child> --add-blocked-by <blocker>`. If unavailable, put `Blocked by: #<n>` at the top of the child body.
- Count open blockers: `gh api repos/kyomind/WeaMind/issues/<n> --jq .issue_dependencies_summary.blocked_by`. A ticket is startable only when every blocker is closed.
- Comment: `gh issue comment <number> --body "..."`.
- Labels: `gh issue edit <number> --add-label "..."` or `--remove-label "..."`.
- Close: post an explanation with `gh issue comment`, then use `gh issue close`. Do not rely on `close --comment` for already-closed issues.

Before the first issue creation in a session, verify the target with
`gh repo view --json nameWithOwner`. File only into the user's repo,
never the upstream skills repo; confirm unexpected targets with the user.

## Pull requests as a triage surface

**PRs as a request surface: no.**

GitHub shares issue and PR numbers. For an ambiguous number, try
`gh pr view <number>`, then fall back to `gh issue view <number>`.

## Skill operations

- "Publish to the issue tracker": create a GitHub issue.
- "Fetch the relevant ticket": read the GitHub issue.
