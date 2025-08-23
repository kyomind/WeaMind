# WeaMind CHANGELOG 維護指南

## 🤖 AI 助理重要指示

**當用戶要求更新 CHANGELOG 或版本時，AI 助理必須：**

1. **優先使用 Makefile 指令**，避免手動操作：
   ```bash
   make changelog-status                    # 檢查狀態
   make changelog-prepare [VERSION=x.y.z]   # 準備資料
   make changelog-release VERSION=x.y.z     # 完整發布
   ```

2. **嚴格遵循後面的「標準發布流程」**，確保不遺漏任何步驟

---

## 📋 標準發布流程

### 步驟 1：檢查狀態
```bash
make changelog-status
```
- 查看當前版本和分支
- 統計待發布的 commits 數量
- 顯示自上次版本以來的變更

### 步驟 2：準備資料
```bash
make changelog-prepare VERSION=0.2.0
```
- 自動收集 commits 資料
- 提供完整的 Copilot Chat 提示詞
- 輸出格式化的變更清單

### 步驟 3：生成內容
使用 Copilot Chat（提示詞由步驟 2 自動提供）：
```
根據以下 git commits 為 WeaMind 產生 CHANGELOG 內容：
[系統自動提供的 commits]

要求：繁體中文、Keep a Changelog 格式、面向一般用戶、突出產品價值
```

### 步驟 4：發布版本
```bash
make changelog-release VERSION=0.2.0
```
- 自動更新 `pyproject.toml` 版本號
- 執行 `uv lock` 更新 lock 檔案
- 提交所有變更（CHANGELOG.md + pyproject.toml + uv.lock）
- 建立 git tag
- 推送到遠端倉庫
- 觸發 GitHub Actions 建立 Release

---

## 📝 CHANGELOG 內容規範

### 版本格式
```markdown
## [版本號] - YYYY-MM-DD
```

### 變更分類（優先順序）
1. **新增 (Added)** - 新功能、新特性
2. **修正 (Fixed)** - 錯誤修復、安全性修正
3. **改進 (Changed)** - 既有功能改進、效能優化

### 撰寫原則
- **面向用戶**：使用一般用戶能理解的語言
- **突出價值**：說明功能對用戶的實際好處
- **簡潔明瞭**：每項變更一行描述，重點功能用 **粗體**
- **產品導向**：強調使用者體驗而非技術細節

### 內容範例
```markdown
## [0.2.0] - 2025-08-25

### 新增
- **智慧推薦功能**: 根據用戶查詢習慣，主動推薦相關天氣資訊
- 支援語音查詢，讓天氣查詢更便利

### 修正
- 修復地點搜尋偶爾無回應的問題，提升查詢穩定性
- 改善 LIFF 頁面在不同裝置上的顯示效果

### 改進
- 優化查詢速度，回應時間縮短 30%
- 更新天氣圖示設計，視覺效果更直觀
```

---

## 🛠️ 進階用法與工具

### 直接使用腳本
```bash
./scripts/changelog.sh status           # 查看狀態
./scripts/changelog.sh prepare [ver]    # 準備資料
./scripts/changelog.sh release <ver>    # 發布版本
./scripts/changelog.sh help             # 顯示幫助
```

### 手動 Git 操作（僅供參考）
```bash
# 收集變更資訊
git log --oneline v0.1.0..HEAD
git log --oneline --merges v0.1.0..HEAD  # PR 合併記錄
git diff --stat v0.1.0..HEAD             # 檔案變更統計

# 手動版本管理（不建議）
# 更新 pyproject.toml，提交，建立標籤，推送
```

### Copilot Chat 範本

#### 生成特定功能版本
```
為 WeaMind v0.2.0 產生 CHANGELOG，重點關注：
- LINE Bot Rich Menu 功能
- 用戶查詢記錄系統
- 天氣 API 整合
- 安全性改進

要求：簡潔明瞭，面向一般用戶，突出產品價值。
```

#### 優化既有內容
```
優化這段 CHANGELOG 內容，讓它更吸引使用者：
[貼上現有內容]

優化方向：突出產品價值、生動描述、加入使用情境、保持技術準確性
```

---

## ✅ 發布檢查清單

### 自動化流程檢查
- [ ] 執行 `make changelog-status` 確認有新變更
- [ ] 執行 `make changelog-prepare` 獲得 commits 資料
- [ ] 使用 Copilot Chat 生成內容並完善 CHANGELOG.md
- [ ] 執行 `make changelog-release VERSION=x.y.z` 完成發布
- [ ] 確認 GitHub Actions 成功建立 Release

### 內容品質檢查
- [ ] 使用繁體中文且語調一致
- [ ] 重要功能用粗體突出
- [ ] 避免過多技術術語
- [ ] 強調用戶價值和體驗改進
- [ ] 版本號格式正確 (x.y.z)

---

## 🎯 產品行銷要點

記住 WeaMind 是一個**產品**，CHANGELOG 也是行銷材料：

### 語調原則
- 專業親和，避免過於技術性
- 強調使用者體驗改進
- 突出功能的實際價值
- 簡潔明瞭，易於理解

### 常用 Emoji
- 🚀 新功能發布
- 🌤️ 天氣相關功能
- 🎯 精準功能
- 👤 用戶相關
- 🔒 安全性
- 🔧 工具改進
- 🎨 UI/UX 改進

---

## 📚 快速參考

### 基本指令
```bash
make changelog-status                    # 查看狀態
make changelog-prepare [VERSION=x.y.z]   # 準備資料
make changelog-release VERSION=x.y.z     # 發布版本
make changelog-help                      # 顯示指南
```

### 重要提醒
- 🎯 **AI 助理必須優先使用 Makefile 指令**
- 📋 **遵循四步驟標準流程**
- 🚫 **避免手動 git 操作**
- ✨ **內容面向用戶，突出產品價值**
