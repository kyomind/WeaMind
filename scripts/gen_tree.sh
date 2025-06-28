#!/bin/zsh
# Generate a three-level project tree and write it to docs/Tree.md

echo "# Project Directory Tree (3 Levels)" > docs/Tree.md
echo "" >> docs/Tree.md
tree -L 3 -a -I '.*|__pycache__' >> docs/Tree.md
