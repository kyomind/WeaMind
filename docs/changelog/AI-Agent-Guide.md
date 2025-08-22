# WeaMind CHANGELOG 自動化維護指南

> **AI Agent 專用文件** - 本文件提供完整的自動化流程，AI agent 可直接執行所有操作

## 🎯 目標
為 WeaMind 專案建立專業的版本歷史記錄，支援產品行銷和用戶溝通，並通過 GitHub Actions 實現完全自動化發布。

## 📋 超簡化的3步驟流程

### Step 1: 檢查狀態
```bash
make changelog-status
```

### Step 2: 準備 AI 資料
```bash
# 自動收集 commits 並提供 AI 提示詞
make changelog-prepare [VERSION=0.2.0]
```

### Step 3: 一鍵發布（含 GitHub Release）
```bash
# 更新版本、提交、標籤、推送，觸發 GitHub Actions
make changelog-release VERSION=0.2.0
```

## 🤖 GitHub Actions 自動發布

**重要**: 當執行 `make changelog-release` 時，系統會自動：

1. ✅ 更新 `pyproject.toml` 版本號
2. ✅ 提交變更並創建 git 標籤
3. ✅ 推送標籤到 GitHub
4. 🚀 **觸發 GitHub Actions**，自動建立 Release 頁面
5. 📝 GitHub 自動生成 Release Notes

**不再需要手動操作 GitHub Release 頁面！**
- 如果是安全性相關，特別標註
```

#### 2.2 驗證和優化內容
```
請檢查並優化以下 CHANGELOG 內容：

[貼上生成的內容]

優化重點：
1. 確保語調一致且專業親和
2. 突出對使用者的實際價值
3. 技術亮點是否完整
4. emoji 使用是否恰當
5. 分類是否正確
```

### Phase 3: 文件更新與版本管理

#### 3.1 更新 CHANGELOG.md
1. 打開 `/Users/kyo/Code/WeaMind/CHANGELOG.md`
2. 在現有版本之前插入新版本內容
3. 更新「即將推出 (Coming Soon)」部分（如需要）

#### 3.2 版本號更新與驗證
```bash
# 使用自動化工具更新版本號
make version-update VERSION=[NEW_VERSION]

# 檢查更新結果
git diff HEAD -- pyproject.toml CHANGELOG.md
```

### Phase 4: 提交與發布

#### 4.1 提交變更
```bash
# 檢查變更狀態
git status

# 添加相關文件
git add CHANGELOG.md pyproject.toml

# 提交變更
git commit -m "chore: bump version to v[NEW_VERSION]

- 更新 CHANGELOG.md 新增 v[NEW_VERSION] 版本記錄
- 更新 pyproject.toml 版本號
- [簡要描述主要變更]"
```

#### 4.2 創建標籤並推送
```bash
# 創建版本標籤
git tag v[NEW_VERSION]

# 推送到遠端
git push origin [CURRENT_BRANCH] --tags

# 如果在 main 分支，額外推送標籤
git push origin main --tags
```

#### 4.3 使用快捷指令（可選）
```bash
# 一鍵發布（需先確保 CHANGELOG.md 已更新）
make release VERSION=[NEW_VERSION]
```

## 🛠️ AI Agent 執行腳本範例

```bash
#!/bin/bash
# WeaMind CHANGELOG 自動化腳本
# 使用方法: ./auto-changelog.sh [NEW_VERSION]

set -e

NEW_VERSION=$1
CURRENT_DATE=$(date +%Y-%m-%d)

if [ -z "$NEW_VERSION" ]; then
    echo "❌ 請提供版本號"
    echo "使用方法: $0 0.2.0"
    exit 1
fi

echo "🚀 開始 WeaMind v$NEW_VERSION 版本更新流程"

# Phase 1: 檢查環境
echo "📋 檢查當前狀態..."
make version-check

# 收集 commit 資訊
echo "📝 收集變更資訊..."
COMMITS=$(git log --oneline -10)
echo "$COMMITS"

# Phase 2: 提示 AI 生成內容
echo "💡 請在 VS Code Copilot Chat 中使用以下提示詞："
echo "=================================================="
echo "@workspace 根據以下 git commits 為 WeaMind 產生 CHANGELOG 內容："
echo ""
echo "$COMMITS"
echo ""
echo "要求：繁體中文、Keep a Changelog 格式、版本號設為 $NEW_VERSION、日期設為 $CURRENT_DATE"
echo "=================================================="
echo ""
echo "⏸️  請手動編輯 CHANGELOG.md 後按 Enter 繼續..."
read -p ""

# Phase 3: 更新版本號
echo "🔧 更新版本號..."
make version-update VERSION=$NEW_VERSION

# Phase 4: 提交與發布
echo "📦 提交變更並創建標籤..."
git add CHANGELOG.md pyproject.toml
git commit -m "chore: bump version to v$NEW_VERSION"
git tag v$NEW_VERSION

echo "✅ 版本 v$NEW_VERSION 準備完成！"
echo "🚀 執行以下命令完成發布："
echo "   git push origin $(git branch --show-current) --tags"
```

## 📚 參考資料

### 必讀文件
- `.github/instructions/changelog-maintenance.instructions.md` - 詳細維護指南
- `.github/copilot-instructions.md` - 專案開發規範
- `docs/Todo.md` - 了解專案功能進展

### 工具指令
- `make version-check` - 檢查版本狀態
- `make version-update VERSION=x.y.z` - 更新版本號
- `make release VERSION=x.y.z` - 一鍵發布
- `make changelog-help` - 快速參考

### Emoji 參考指南
- 🚀 新功能發布
- 🌍 地理/位置相關
- ⚡ 效能改進
- 🎯 精準功能
- 👤 用戶相關
- 🏗️ 架構改進
- 🗄️ 資料庫相關
- 🧪 測試相關
- 🐳 Docker/部署
- 📊 監控/分析
- 🔒 安全性
- 🧹 代碼清理
- 📝 文件相關
- 🔧 工具改進
- 🎨 UI/UX 改進
- 🌦️ 天氣相關功能

## ⚠️ 重要注意事項

1. **版本號規範**：遵循 [Semantic Versioning](https://semver.org/)
   - MAJOR.MINOR.PATCH (例：1.0.0)
   - 新功能 = MINOR++
   - 修復 = PATCH++
   - 破壞性變更 = MAJOR++

2. **語言一致性**：所有面向用戶的內容使用繁體中文

3. **行銷角度**：CHANGELOG 是產品展示工具，強調用戶價值

4. **技術準確性**：雖然要親和，但技術細節必須準確

5. **自動觸發**：當編輯 `CHANGELOG.md` 或 `pyproject.toml` 時，相關指導文件會自動載入

## 🎯 成功指標

一個優秀的 CHANGELOG 版本應該：
- ✅ 用戶能快速理解新功能價值
- ✅ 開發者能了解技術改進
- ✅ 語調專業但親和
- ✅ 格式一致且美觀
- ✅ 突出產品競爭優勢
- ✅ 展現持續改進的專業形象
