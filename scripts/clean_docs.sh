#!/bin/zsh

set -e  # 遇到錯誤立即退出

# 設定變數
DOCS_DIR="docs"

# 保留的檔案列表
KEEP_FILES=(
    "Example.md"
    "Todo.md"
    "Tree.md"
)

# 檢查 docs 目錄是否存在
if [ ! -d "$DOCS_DIR" ]; then
    echo "錯誤: docs 目錄不存在"
    exit 1
fi

echo "正在清理 docs 目錄..."
echo "保留的檔案: ${KEEP_FILES[*]}"

# 進入 docs 目錄
cd "$DOCS_DIR"

# 找出所有檔案和目錄
ALL_ITEMS=(*)

# 如果目錄為空，直接退出
if [ ${#ALL_ITEMS[@]} -eq 1 ] && [ "${ALL_ITEMS[1]}" = "*" ]; then
    echo "docs 目錄已經是空的"
    exit 0
fi

# 建立要刪除的項目列表
TO_DELETE=()

for item in "${ALL_ITEMS[@]}"; do
    # 檢查是否在保留列表中
    keep=false
    for keep_file in "${KEEP_FILES[@]}"; do
        if [ "$item" = "$keep_file" ]; then
            keep=true
            break
        fi
    done

    # 如果不在保留列表中，加入刪除列表
    if [ "$keep" = false ]; then
        TO_DELETE+=("$item")
    fi
done

# 顯示要刪除的項目
if [ ${#TO_DELETE[@]} -eq 0 ]; then
    echo "沒有需要刪除的檔案"
    exit 0
fi

echo ""
echo "將要刪除的項目："
for item in "${TO_DELETE[@]}"; do
    echo "  - $item"
done

echo ""
read -q "REPLY?確認刪除以上項目？(y/n): "
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 執行刪除
    for item in "${TO_DELETE[@]}"; do
        if [ -f "$item" ]; then
            rm "$item"
            echo "已刪除檔案: $item"
        elif [ -d "$item" ]; then
            rm -rf "$item"
            echo "已刪除目錄: $item"
        fi
    done

    echo ""
    echo "✅ 清理完成！"
    echo "保留的檔案："
    ls -la
else
    echo "取消刪除操作"
    exit 1
fi
