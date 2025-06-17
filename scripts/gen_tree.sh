#!/bin/zsh
# 產生專案三層樹狀圖並寫入 docs/Tree.md

echo "# Project Directory Tree (3 Levels)" > docs/Tree.md
echo "" >> docs/Tree.md
tree -L 3 -a -I '.*' >> docs/Tree.md
