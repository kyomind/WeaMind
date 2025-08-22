# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-08-22

### 新增 (Added)
- 🚀 **LINE Bot 核心功能** - 完整的 LINE webhook 整合，支援 follow/unfollow 事件處理
- 🌍 **智慧地點解析** - 支援中文地名模糊查詢，涵蓋全台鄉鎮區資料
- ⚡ **Quick Reply 互動** - 當查詢結果為 2-3 個地點時，自動提供快速回覆選項
- 🎯 **LIFF 地點設定** - 透過 LINE 前端框架實現便民的地點偏好設定
- 👤 **自動用戶管理** - LINE Bot follow 時自動建立用戶記錄
- 🏗️ **DDD 架構設計** - 採用領域驅動設計，模組化程式碼結構
- 🗄️ **PostgreSQL 整合** - 完整的資料庫設計，包含用戶、天氣、行政區資料表
- 🧪 **完整測試覆蓋** - pytest 測試框架，涵蓋核心業務邏輯
- 🐳 **Docker 容器化** - 支援開發與生產環境的 docker-compose 配置
- 📊 **代碼品質監控** - 整合 Ruff、Pyright、Codecov 等工具

### 修正 (Fixed)
- 🔒 **安全性強化** - 移除無認證的危險 API 端點，提升系統安全性
- 🧹 **代碼重構** - 優化用戶管理 API，移除冗餘代碼
- 📝 **日誌改進** - 增強 LINE webhook 接收的日誌記錄，便於除錯

### 改進 (Changed)
- 🔧 **JWT 測試優化** - 重構 JWT token 創建邏輯，提升測試可靠性
- 📋 **測試指南完善** - 新增詳細的測試規範文件，標準化開發流程
- 🎨 **代碼風格統一** - 使用 Ruff 進行格式化和 lint 檢查

### 技術亮點 (Technical Highlights)
- **架構**: FastAPI + SQLAlchemy 2.0 + PostgreSQL
- **開發工具**: uv 包管理、Alembic 資料庫遷移、pre-commit hooks
- **CI/CD**: GitHub Actions、Codecov、SonarCloud 整合
- **部署**: 雲端 VM + Nginx 反向代理 + HTTPS 憑證
- **LINE 整合**: webhook 驗證、事件處理、LIFF 前端框架

---

## 即將推出 (Coming Soon)

### [0.2.0] - 計劃中
- 🎨 **Rich Menu 六格配置** - 點擊優先的互動模型，提供「查住家」、「查公司」等快捷功能
- 📜 **查詢記錄功能** - 用戶查詢歷史與「最近查過」快捷選項
- 🏠 **個人地點管理** - 住家、公司地點設定與快速查詢
- 🌦️ **天氣 API 整合** - 接入氣象資料，提供實時天氣查詢服務

---

## 發布說明 (Release Notes)
每個版本的詳細異動請參考對應的 [GitHub Releases](https://github.com/kyomind/WeaMind/releases)。

## 回饋與建議 (Feedback)
如有任何功能建議或問題回報，歡迎透過 [GitHub Issues](https://github.com/kyomind/WeaMind/issues) 與我們聯繫。

---
*WeaMind - 讓天氣查詢變得更簡單、更直觀* 🌤️
