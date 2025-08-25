#!/bin/zsh

echo "🌳 Git Worktree 創建工具"
echo ""
echo "📋 現有分支："
git branch -a | grep -E "(feature/|hotfix/|bugfix/)" | head -10
echo ""
echo "💡 請輸入要創建 worktree 的分支名稱："
read -r TARGET_BRANCH

if [[ -z "$TARGET_BRANCH" ]]; then
    echo "❌ 未輸入分支名稱，取消操作"
    exit 1
fi

# 檢查是否為 main 分支
if [[ "$TARGET_BRANCH" == "main" ]]; then
    echo "❌ 錯誤：不建議為 main 分支創建 worktree"
    echo "💡 main 分支應該保持為主要工作目錄"
    exit 1
fi

# 獲取當前分支
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# 構建 worktree 路徑
WORKTREE_PATH="../WeaMind-$TARGET_BRANCH"

# 檢查路徑是否已存在
if [[ -d "$WORKTREE_PATH" ]]; then
    echo "❌ 錯誤：worktree 路徑已存在: $WORKTREE_PATH"
    echo "💡 請先移除現有的 worktree 或使用不同的分支名稱"
    exit 1
fi

# 檢查分支是否存在
if git show-ref --verify --quiet refs/heads/$TARGET_BRANCH; then
    # 分支存在，檢查是否被其他 worktree 使用
    if [[ "$CURRENT_BRANCH" == "$TARGET_BRANCH" ]]; then
        echo "❌ 錯誤：目標分支 '$TARGET_BRANCH' 正在當前目錄中被使用"
        echo "💡 解決方案："
        echo "   1. 切換到其他分支: git checkout main"
        echo "   2. 然後再執行: make worktree-add"
        exit 1
    fi

    echo "🌳 為現有分支 '$TARGET_BRANCH' 創建 worktree..."
    echo "📁 路徑: $WORKTREE_PATH"

    if git worktree add "$WORKTREE_PATH" "$TARGET_BRANCH"; then
        echo "✅ 成功創建 worktree!"
        echo "📂 cd $WORKTREE_PATH"
    else
        echo "❌ 創建失敗：分支 '$TARGET_BRANCH' 可能在其他 worktree 中使用"
        exit 1
    fi
else
    # 分支不存在，創建新分支
    echo "🌱 分支 '$TARGET_BRANCH' 不存在，將創建新分支..."
    echo "📁 路徑: $WORKTREE_PATH"

    if git worktree add -b "$TARGET_BRANCH" "$WORKTREE_PATH"; then
        echo "✅ 成功創建新分支和 worktree!"
        echo "📂 cd $WORKTREE_PATH"
    else
        echo "❌ 創建失敗"
        exit 1
    fi
fi
