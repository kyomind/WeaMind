#!/bin/bash

# WeaMind Instructions Sync Script
# Copies .github/copilot-instructions.md to other AI tool configuration files

set -e

# 定義來源檔案和目標檔案
SOURCE_FILE=".github/copilot-instructions.md"
TARGET_FILES=("AGENTS.md" "GEMINI.md" "CLAUDE.md")

# 檢查來源檔案是否存在
if [[ ! -f "$SOURCE_FILE" ]]; then
    echo "錯誤: 來源檔案 $SOURCE_FILE 不存在"
    exit 1
fi

echo "同步 GitHub Copilot 指令到其他 AI 工具配置檔案..."
echo "來源檔案: $SOURCE_FILE"

# 複製到每個目標檔案
for target in "${TARGET_FILES[@]}"; do
    echo "複製到: $target"
    cp "$SOURCE_FILE" "$target"
    echo "✅ $target 已更新"
done

echo ""
echo "🎉 所有檔案同步完成!"
echo "已同步的檔案:"
for target in "${TARGET_FILES[@]}"; do
    echo "  - $target"
done
