#!/usr/bin/env bash

set -euo pipefail

TARGET_REPO="kyomind/weamind-infra"
DEFAULT_BRANCH="main"
MANIFEST_PATH="manifests/deployment.yaml"
IMAGE_REPO="ghcr.io/kyomind/weamind"
RELEASE_VERSION="${1:-}"

if [[ -z "$RELEASE_VERSION" ]]; then
  echo "Usage: $0 <release-version>" >&2
  exit 1
fi

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "GH_TOKEN is required." >&2
  exit 1
fi

for command_name in gh git sed grep mktemp; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Required command not found: $command_name" >&2
    exit 1
  fi
done

branch_name="bump-weamind-${RELEASE_VERSION}"
commit_message="Bump weamind image to ${RELEASE_VERSION}"
pr_title="$commit_message"
release_url="https://github.com/kyomind/WeaMind/releases/tag/v${RELEASE_VERSION}"
target_image="${IMAGE_REPO}:${RELEASE_VERSION}"
temp_dir="$(mktemp -d)"

cleanup() {
  rm -rf "$temp_dir"
}

trap cleanup EXIT

gh repo clone "$TARGET_REPO" "$temp_dir/weamind-infra" -- --branch "$DEFAULT_BRANCH"

cd "$temp_dir/weamind-infra"

gh auth setup-git

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

git switch -C "$branch_name"

current_image="$(grep -E '^[[:space:]]*image:' "$MANIFEST_PATH" | head -n 1 | awk '{print $2}')"

sed -i.bak "s|${IMAGE_REPO}:[^[:space:]]*|${target_image}|" "$MANIFEST_PATH"
rm -f "${MANIFEST_PATH}.bak"

if git diff --quiet -- "$MANIFEST_PATH"; then
  echo "No manifest change detected. Skipping PR creation."
  exit 0
fi

git add "$MANIFEST_PATH"
git commit -m "$commit_message"
git push --force-with-lease origin "$branch_name"

pr_body=$(cat <<EOF
Update deployment image in ${MANIFEST_PATH}

- from: ${current_image}
- to: ${target_image}
- release: ${release_url}
EOF
)

existing_pr_number="$(gh pr list --repo "$TARGET_REPO" --head "$branch_name" --json number --jq '.[0].number // empty')"

if [[ -n "$existing_pr_number" ]]; then
  gh pr edit "$existing_pr_number" --repo "$TARGET_REPO" --title "$pr_title" --body "$pr_body"
  echo "Updated existing PR #${existing_pr_number}."
else
  gh pr create \
    --repo "$TARGET_REPO" \
    --base "$DEFAULT_BRANCH" \
    --head "$branch_name" \
    --title "$pr_title" \
    --body "$pr_body"
fi
