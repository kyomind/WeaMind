---
description: "查證 GitHub Actions 的版本與 commit SHA，更新 workflow 的固定版本引用"
---

# Pin GitHub Actions

## Goal

Resolve the requested action version to a verified commit and update only the intended workflow references. Use `gh` for GitHub operations.

## Workflow

1. Read the target workflow and the action repository's release information. Preserve this repo's convention: official GitHub actions may use version tags; third-party actions use full commit SHAs with version comments. Do not upgrade an action merely because it needs pinning.
2. If the user requests the latest release, query it with `gh api repos/OWNER/REPO/releases/latest --jq .tag_name`. Otherwise use the requested or currently configured tag. Check release notes before a major-version upgrade.
3. Resolve the tag with `gh api repos/OWNER/REPO/git/ref/tags/TAG`. Encode the tag as a URL path component when necessary.
4. Inspect `object.type`. If it is `tag`, query `gh api repos/OWNER/REPO/git/tags/SHA` and follow the returned object until its type is `commit`. A tag-object SHA is not the commit SHA. Stop if the object cannot be resolved to a commit.
5. Verify the commit with `gh api repos/OWNER/REPO/commits/SHA`. Use the full 40-character commit SHA, not a short SHA or an unverified value from an example.
6. Update the intended `uses:` entries and retain the resolved version in a comment:

   ```yaml
   uses: owner/repo@FULL_COMMIT_SHA # vX.Y.Z
   ```

7. Review the diff and run the available workflow checks. If the task is only a lookup, report the result without editing files. Do not merge PRs or trigger workflows unless authorized.

## Output

Report the action repository, resolved tag, commit SHA, changed workflow files, and validation performed. Explain any references intentionally left as tags.
