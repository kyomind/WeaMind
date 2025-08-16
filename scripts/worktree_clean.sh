#!/bin/zsh

echo "🧹 清理過期的 worktree 引用..."
if git worktree prune; then
    echo "✅ 清理完成"
else
    echo "❌ 清理失敗"
    exit 1
fi
