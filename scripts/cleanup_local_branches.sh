#!/bin/zsh
# 刪除所有本地無遠端對應的分支

# 同步並清理遠端刪除的分支
git fetch --prune

current=$(git rev-parse --abbrev-ref HEAD)
echo "開始刪除本地無遠端分支："
for branch in $(git branch --format='%(refname:short)'); do
  if [ "$branch" = "$current" ]; then
    echo "  $branch (當前分支，跳過)"
    continue
  fi
  if ! git show-ref --verify --quiet "refs/remotes/origin/$branch"; then
    echo "  刪除分支 $branch"
    git branch -D "$branch"
  fi
done
