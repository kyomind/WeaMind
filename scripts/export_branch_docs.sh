#!/bin/zsh

set -e  # 遇到錯誤立即退出

# 設定變數
BASE_TARGET_DIR="/Users/kyo/Library/CloudStorage/OneDrive-個人/WeaMind/branch-docs"
DOCS_SOURCE_DIR="docs"
CURRENT_DATE=$(date +%Y-%m-%d)

# 檢查目標基礎路徑是否存在
if [ ! -d "$BASE_TARGET_DIR" ]; then
    echo "錯誤: 目標路徑不存在: $BASE_TARGET_DIR"
    echo "請確保在 macOS 環境下執行此腳本"
    exit 1
fi

# 檢查 docs 目錄是否存在
if [ ! -d "$DOCS_SOURCE_DIR" ]; then
    echo "錯誤: docs 目錄不存在"
    exit 1
fi

# 取得當前分支名稱
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)

# 移除 feature/ 前綴（如果存在）
CLEAN_BRANCH_NAME=${BRANCH_NAME#feature/}

# 建立子目錄名稱
SUBDIR_NAME="${CURRENT_DATE}-${CLEAN_BRANCH_NAME}"
TARGET_DIR="${BASE_TARGET_DIR}/${SUBDIR_NAME}"

echo "當前分支: $BRANCH_NAME"
echo "清理後分支名: $CLEAN_BRANCH_NAME"
echo "目標目錄: $TARGET_DIR"

# 檢查子目錄是否已存在
if [ -d "$TARGET_DIR" ]; then
    echo "錯誤: 目標目錄已存在: $TARGET_DIR"
    echo "請先刪除該目錄後再執行此腳本"
    exit 1
fi

# 建立目標目錄
echo "建立目錄: $TARGET_DIR"
mkdir -p "$TARGET_DIR"

# 複製 docs 目錄內容（省略 docs 父目錄，保留子目錄結構）
echo "正在複製 docs 目錄內容..."
cp -r "$DOCS_SOURCE_DIR"/* "$TARGET_DIR/"

# 複製 prd 目錄內容（省略 prd 父目錄，保留子目錄結構）
echo "正在複製 prd 目錄內容..."
cp -r "prd"/* "$TARGET_DIR/"

echo "✅ 成功完成！"
echo "已將 docs 和 prd 目錄內容複製到: $TARGET_DIR"

# 顯示複製的內容結構
echo ""
echo "複製的內容："
ls -la "$TARGET_DIR"
