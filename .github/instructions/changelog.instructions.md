---
applyTo: "CHANGELOG.md,pyproject.toml"
---

# WeaMind CHANGELOG 維護指南

## 如何使用 GitHub Copilot 協助維護 CHANGELOG

### 1. 版本發布前的準備工作

#### 使用簡化的 changelog.sh 腳本

**最簡單的方式：**
```bash
# 1. 查看目前狀態和待發布的變更
make changelog-status

# 2. 準備 CHANGELOG 資料（自動提供 AI 提示詞）
make changelog-prepare [VERSION=0.2.0]
```

#### 手動收集變更資訊（進階用法）
```bash
# 查看自上次發布以來的 commits
git log --oneline v0.1.0..HEAD

# 查看 PR 合併記錄
git log --oneline --merges v0.1.0..HEAD

# 查看檔案變更統計
git diff --stat v0.1.0..HEAD
```

#### 使用 Copilot Chat 產生 CHANGELOG 內容
在 VS Code 中的 Copilot Chat（提示詞已內建在 `make changelog-prepare` 中）：

```
根據以下 git commits 為 WeaMind 產生 CHANGELOG 內容：

[貼上 git log 輸出]

要求：
- 繁體中文，Keep a Changelog 格式
- 簡潔明瞭，面向一般用戶而非開發者
- 突出產品價值和用戶體驗
- 避免過多技術細節
- 不要包含「即將推出」或「技術亮點」區塊
- 每項功能一行描述，重點功能可用粗體

格式範例：
## [版本號] - 日期

### 新增
- **核心功能名稱**: 簡潔的功能描述，說明對用戶的價值
- 次要功能描述

### 修正
- 修復具體問題，說明影響和改善

### 改進
- 現有功能的優化說明
```

### 2. CHANGELOG 格式規範

#### 版本標題格式
```markdown
## [版本號] - YYYY-MM-DD
```

#### 變更分類優先順序
1. **新增 (Added)** - 新功能、新特性
2. **修正 (Fixed)** - 錯誤修復、安全性修正
3. **改進 (Changed)** - 既有功能改進、效能優化

#### 內容撰寫原則
- 每項變更簡潔明瞭，一行為主
- 使用一般用戶能理解的語言，避免技術術語
- 重要功能用 **粗體** 標示
- 說明功能對用戶的實際價值
- 避免過度技術性的描述

### 3. 版本號管理與發布

#### 使用簡化腳本發布（推薦）
```bash
# 一鍵發布新版本（包含版本號更新、提交、標籤、推送）
make changelog-release VERSION=0.2.0
```

#### 手動版本管理（進階）
```bash
# 更新 pyproject.toml 中的版本號
# version = "0.2.0"

# 創建 Git 標籤
git add CHANGELOG.md pyproject.toml
git commit -m "chore: bump version to v0.2.0"
git tag v0.2.0
git push origin main --tags
```

#### 完整發布流程
```bash
# 1. 檢查狀態
make changelog-status

# 2. 準備資料（獲得 AI 提示詞）
make changelog-prepare VERSION=0.2.0

# 3. 使用 Copilot Chat 生成內容並手動編輯 CHANGELOG.md

# 4. 發布版本
make changelog-release VERSION=0.2.0
```

### 4. Copilot 快速指令範本

#### 生成新版本 CHANGELOG
```
根據最近的開發進度，為 WeaMind v0.2.0 產生 CHANGELOG 內容。重點關注：
- LINE Bot Rich Menu 功能
- 用戶查詢記錄系統
- 天氣 API 整合
- 任何安全性改進

要求：簡潔明瞭，面向一般用戶，突出產品價值。
```

#### 優化既有 CHANGELOG 內容
```
請優化這段 CHANGELOG 內容，讓它更吸引使用者：
[貼上現有內容]

優化方向：
1. 更突出產品價值
2. 使用更生動的描述
3. 加入使用者情境
4. 保持技術準確性
```

### 5. 發布檢查清單

#### 使用簡化流程
- [ ] 執行 `make changelog-status` 確認有新變更
- [ ] 執行 `make changelog-prepare` 獲得 commits 資料
- [ ] 使用 Copilot Chat 生成 CHANGELOG 內容
- [ ] 手動編輯 CHANGELOG.md 完善內容
- [ ] 執行 `make changelog-release VERSION=x.y.z` 完成發布

#### 傳統手動檢查
- [ ] 確認版本號在 `pyproject.toml` 中已更新
- [ ] CHANGELOG.md 包含所有重要變更
- [ ] 內容使用繁體中文且語調一致
- [ ] 新增項目突出使用者價值
- [ ] 技術亮點部分準確完整
- [ ] 「即將推出」部分已更新
- [ ] Git 標籤已建立並推送

### 6. 快速參考指令

#### 新的簡化指令
```bash
make changelog-status                    # 查看目前狀態
make changelog-prepare [VERSION=x.y.z]   # 準備 commits 資料
make changelog-release VERSION=x.y.z     # 發布新版本
make changelog-help                      # 顯示使用指南
```

#### 腳本直接使用
```bash
./scripts/changelog.sh status           # 查看狀態
./scripts/changelog.sh prepare [ver]    # 準備資料
./scripts/changelog.sh update <version> # 發布版本
./scripts/changelog.sh help             # 顯示幫助
```

### 7. 行銷重點提示

記住 WeaMind 是一個**產品**，CHANGELOG 也是行銷材料：
- 強調使用者體驗改進
- 突出功能對用戶的實際價值
- 使用簡潔明瞭的語言
- 避免過多技術細節
- 重點功能用粗體突出

### 8. 常用 Emoji 參考

- 🚀 新功能發布
- �️ 天氣相關功能
- 🎯 精準功能
- 👤 用戶相關
-  安全性
- 🔧 工具改進
- 🎨 UI/UX 改進
