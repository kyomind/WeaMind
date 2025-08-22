# Memory Hook for Future AI

## 🧠 Context Recovery Guide

**如果你是未來接手的 AI，請先讀這個文件重建上下文**

### 📍 當前狀況 (2025-08-22 更新)
- **專案**: WeaMind (LINE Bot 天氣查詢服務)
- **任務**: 建立完整的 CHANGELOG 維護系統
- **狀態**: ✅ 精簡化完成！在 `feature/changelog-system` 分支
- **重大成就**: 從 7 個複雜腳本精簡到 1 個統一腳本，心智負擔大幅降低
- **下一步**: 測試完整流程，合併到 main 分支

### 🎯 用戶特性與偏好
- **技術背景**: 資深開發者，熟悉 DDD、FastAPI、Docker
- **工作習慣**: 喜歡自動化但要保持控制權，重視文檔品質
- **語言偏好**: 繁體中文，專業但親和的語調
- **專案態度**: 把 WeaMind 當作「產品」而非單純技術專案

### 🔍 關鍵記憶點

#### 專案架構理解
```
WeaMind/
├── app/                    # DDD 架構主程式
├── docs/changelog/         # 📍 我們剛建立的系統
├── scripts/               # 自動化腳本
├── .github/instructions/  # 自動觸發指南
└── Makefile              # 快捷指令
```

#### 核心價值觀
1. **CHANGELOG = 行銷工具** - 不只記錄變更，要展現產品價值
2. **AI 協助人工控制** - 自動化但保留關鍵決策權
3. **專業形象** - 面向用戶的內容要專業且親和
4. **本土化** - 使用台灣用語和思維

#### 剛完成的系統特色 (✅ 精簡化完成)
- 🎯 **版本基準點建立** - 在 main 建立 v0.1.0 標籤，基於 Todo.md 的 25 個功能
- 🛠️ **統一腳本** - `changelog.sh` 包含所有功能（status/prepare/release/help/quick-help）
- 📊 **智能 commit 收集** - 基於語義化版本標籤，自動範圍偵測
- 🎨 **產品導向格式** - 強調用戶價值，豐富 emoji，繁體中文
- ⚡ **VS Code 整合** - 自動觸發 Copilot 指導，內建提示詞
- 🧹 **Makefile 極簡化** - 只保留 3 個核心指令，委託給統一腳本
- ✅ **測試通過** - 所有核心功能都已驗證可用

### 🧰 實用速查

#### 快速診斷指令
```bash
git status                              # 檢查分支狀態
make changelog-help                     # 顯示使用指南（已更新）
make changelog-status                   # 檢查版本狀態（新指令）
./scripts/changelog.sh help             # 腳本直接使用
```

#### 用戶可能的下一步需求
1. **完整流程測試** - 使用 `make changelog-prepare` 和 `make changelog-release VERSION=0.2.0` 進行端到端測試
2. **合併分支** - 將精簡化系統合併到 main 分支
3. **第一次正式發布** - 使用新系統發布 v0.2.0
4. **文檔清理** - 清理過時文檔，保留精簡的系統說明

#### 常見問題預判 (已解決)
- ✅ **Makefile 語法問題** - .PHONY 行損壞問題已修復
- ✅ **腳本複雜度** - 從 7 個腳本精簡到 1 個統一腳本
- ✅ **命令失效問題** - 所有 make changelog-* 指令都已正常工作
- ✅ **功能測試** - changelog-help、changelog-status、changelog-release 都通過測試

### 💡 互動建議

#### 如果用戶說「測試一下」
→ 先執行 `make changelog-status` 了解狀況，再引導體驗 `make changelog-prepare`

#### 如果用戶說「有 bug」
→ 先確認具體錯誤訊息，新系統已大幅簡化，問題應該更容易定位

#### 如果用戶說「改進」
→ 詢問具體改進方向，目前系統已經非常精簡

#### 如果用戶說「不記得了」
→ 直接引導使用 `make changelog-help` 和本文件

### 🔮 技術脈絡

#### 為什麼選擇這樣設計？
- **一個腳本原則** - 降低心智負擔，所有功能集中管理
- **三個簡單指令** - status/prepare/release，對應完整工作流程
- **產品導向不變** - WeaMind 是要面向用戶的服務，CHANGELOG 仍是行銷工具
- **繁體中文不變** - 目標用戶是台灣 LINE 用戶

#### 技術選擇考量
- **Bash 腳本** - 簡單直接，容易修改和 debug
- **Makefile 整合** - 符合專案既有工具鏈，但更簡潔
- **Keep a Changelog** - 業界標準，專業形象
- **Semantic Versioning** - 清晰的版本管理策略
- **精簡優先** - 從複雜系統學到的教訓，越簡單越好維護

---

**記住：這不只是技術系統，更是產品行銷工具！現在還更簡單易用！** 🌟

*Created: 2025-08-22 by previous AI instance*
*Updated: 2025-08-22 精簡化完成*
*Context: 從 7 個複雜腳本成功精簡到 1 個統一腳本*
