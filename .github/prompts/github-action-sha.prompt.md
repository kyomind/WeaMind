# GitHub Action SHA 值查詢指南

## 背景
SonarQube 等安全工具建議使用 commit SHA 而非標籤來引用 GitHub Actions，以確保版本固定性和安全性。

## 快速查詢流程

### 1. 查詢最新版本信息
```bash
curl -s https://api.github.com/repos/{owner}/{repo}/releases/latest | grep -E '"tag_name"|"target_commitish"'
```

### 2. 查詢特定標籤的 SHA 值
```bash
curl -s https://api.github.com/repos/{owner}/{repo}/git/refs/tags/{tag} | grep '"sha"'
```

## 常用 Actions 示例

### softprops/action-gh-release
```bash
# 查詢最新版本
curl -s https://api.github.com/repos/softprops/action-gh-release/releases/latest | grep -E '"tag_name"|"target_commitish"'

# 查詢 v2 標籤的 SHA
curl -s https://api.github.com/repos/softprops/action-gh-release/git/refs/tags/v2 | grep '"sha"'
```

### actions/checkout
```bash
# 查詢 v4 標籤的 SHA
curl -s https://api.github.com/repos/actions/checkout/git/refs/tags/v4 | grep '"sha"'
```

## 使用格式
獲取 SHA 後，在 workflow 中使用：
```yaml
uses: owner/repo@{sha} # {original_tag}
```

例如：
```yaml
uses: softprops/action-gh-release@72f2c25fcb47643c292f7107632f7a47c1df5cd8 # v2
```

## 注意事項
1. SHA 值通常是完整的 40 字符
2. 保留註釋 `# {tag}` 便於識別對應版本
3. 官方 Actions（如 actions/*）可以保持標籤格式，因為它們由 GitHub 官方維護
4. 第三方 Actions 建議使用 SHA 值以提高安全性

## 自動化腳本
可以創建腳本來批量更新：
```bash
#!/bin/bash
# get-action-sha.sh
OWNER=$1
REPO=$2
TAG=$3

if [ -z "$OWNER" ] || [ -z "$REPO" ] || [ -z "$TAG" ]; then
    echo "Usage: $0 <owner> <repo> <tag>"
    exit 1
fi

SHA=$(curl -s "https://api.github.com/repos/$OWNER/$REPO/git/refs/tags/$TAG" | grep '"sha"' | cut -d'"' -f4)
echo "uses: $OWNER/$REPO@$SHA # $TAG"
```

使用方式：
```bash
./get-action-sha.sh softprops action-gh-release v2
```
