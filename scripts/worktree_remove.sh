#!/bin/zsh

# 獲取所有 worktree 信息
WORKTREES=($(git worktree list --porcelain | grep "^worktree" | cut -d' ' -f2-))

# 檢查是否有 worktree
if [[ ${#WORKTREES[@]} -eq 0 ]]; then
    echo "❌ 沒有找到任何 worktree"
    exit 1
fi

# 過濾掉主目錄（通常是第一個，也是當前目錄）
REMOVABLE_WORKTREES=()
CURRENT_DIR=$(pwd)

for worktree in "${WORKTREES[@]}"; do
    # 跳過當前目錄
    if [[ "$worktree" != "$CURRENT_DIR" ]]; then
        REMOVABLE_WORKTREES+=("$worktree")
    fi
done

# 檢查是否有可移除的 worktree
if [[ ${#REMOVABLE_WORKTREES[@]} -eq 0 ]]; then
    echo "❌ 沒有可移除的 worktree（除了當前目錄）"
    exit 1
fi

# 顯示可移除的 worktrees 列表
echo "♻️ 可移除的 worktrees："
for i in {1..${#REMOVABLE_WORKTREES[@]}}; do
    echo "  $i) ${REMOVABLE_WORKTREES[$i]}"
done
echo ""

# 提示用戶選擇
echo "🗑️  請選擇要移除的 worktree 編號 (1-${#REMOVABLE_WORKTREES[@]})："
read -r CHOICE

# 驗證選擇
if [[ ! "$CHOICE" =~ ^[0-9]+$ ]] || [[ "$CHOICE" -lt 1 ]] || [[ "$CHOICE" -gt ${#REMOVABLE_WORKTREES[@]} ]]; then
    echo "❌ 無效的選擇，請輸入 1 到 ${#REMOVABLE_WORKTREES[@]} 之間的數字"
    exit 1
fi

# 獲取選中的 worktree 路徑
SELECTED_WORKTREE="${REMOVABLE_WORKTREES[$CHOICE]}"

# 確認移除
echo "⚠️  確定要移除 worktree: $SELECTED_WORKTREE？ (Y/n)"
read -r CONFIRM

if [[ "$CONFIRM" =~ ^[Nn]$ ]]; then
    echo "ℹ️  取消操作"
else
    if git worktree remove "$SELECTED_WORKTREE"; then
        echo "✅ 成功移除 worktree: $SELECTED_WORKTREE"
    else
        echo "❌ 移除失敗"
        exit 1
    fi
fi
