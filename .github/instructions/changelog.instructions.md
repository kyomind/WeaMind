---
applyTo: "CHANGELOG.md,pyproject.toml"
---

# WeaMind CHANGELOG 維護指南

## 如何使用 GitHub Copilot 協助維護 CHANGELOG

### 1. 版本發布前的準備工作

#### 收集變更資訊
```bash
# 查看自上次發布以來的 commits
git log --oneline v0.1.0..HEAD

# 查看 PR 合併記錄
git log --oneline --merges v0.1.0..HEAD

# 查看檔案變更統計
git diff --stat v0.1.0..HEAD
```

#### 使用 Copilot Chat 產生 CHANGELOG 內容
在 VS Code 中的 Copilot Chat：

```
@workspace 請根據以下 git log 產生 CHANGELOG.md 的新版本內容：

[貼上 git log 輸出]

要求：
1. 使用繁體中文
2. 遵循 Keep a Changelog 格式
3. 分類為：新增(Added)/修正(Fixed)/改進(Changed)/移除(Removed)
4. 重點描述使用者可見的功能變更
5. 加入適當的 emoji 圖標
6. 保持專業但親和的語調
7. 突出技術亮點和產品價值
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
4. **移除 (Removed)** - 棄用功能移除

#### 內容撰寫原則
- 每項變更以動詞開頭（如：實作、新增、修正、改進）
- 使用使用者語言，避免過度技術性描述
- 重要功能用 **粗體** 標示
- 加入相關 emoji 增加可讀性
- 提及對使用者的實際價值

### 3. 版本號管理

#### 更新版本號（手動）
```bash
# 更新 pyproject.toml 中的版本號
# version = "0.2.0"
```

#### 創建 Git 標籤
```bash
git add CHANGELOG.md pyproject.toml
git commit -m "chore: bump version to v0.2.0"
git tag v0.2.0
git push origin main --tags
```

### 4. Copilot 快速指令範本

#### 生成新版本 CHANGELOG
```
根據最近的開發進度，為 WeaMind v0.2.0 產生 CHANGELOG 內容。重點關注：
- LINE Bot Rich Menu 功能
- 用戶查詢記錄系統
- 天氣 API 整合
- 任何安全性改進

請使用專業但親和的語調，突出產品價值。
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

- [ ] 確認版本號在 `pyproject.toml` 中已更新
- [ ] CHANGELOG.md 包含所有重要變更
- [ ] 內容使用繁體中文且語調一致
- [ ] 新增項目突出使用者價值
- [ ] 技術亮點部分準確完整
- [ ] 「即將推出」部分已更新
- [ ] Git 標籤已建立並推送

### 6. 行銷重點提示

記住 WeaMind 是一個**產品**，CHANGELOG 也是行銷材料：
- 強調使用者體驗改進
- 突出技術創新亮點
- 展示開發團隊的專業度
- 營造持續進步的形象
- 與使用者建立連結感

### 7. 常用 Emoji 參考

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
