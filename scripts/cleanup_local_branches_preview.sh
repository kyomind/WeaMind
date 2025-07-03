#!/bin/zsh
# 列出所有本地無遠端對應的分支

git fetch --prune
current=$(git rev-parse --abbrev-ref HEAD)
echo "以下本地分支在遠端不存在，將被刪除："
for branch in $(git branch --format='%(refname:short)'); do
  if [ "$branch" = "$current" ]; then
    echo "  $branch (當前分支，跳過)"
    continue
  fi
  if ! git show-ref --verify --quiet "refs/remotes/origin/$branch"; then
    echo "  $branch"
  fi
done
