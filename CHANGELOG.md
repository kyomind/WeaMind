# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-08-22

****### 新增
- **LINE Bot 核心功能**: 完整的 LINE webhook 整合，支援 follow/unfollow 事件處理
- **智慧地點解析**: 支援中文地名模糊查詢，涵蓋全台鄉鎮區資料
- **Quick Reply 互動**: 當查詢結果為 2-3 個地點時，自動提供快速回覆選項
- **LIFF 地點設定**: 透過 LINE 前端框架實現便民的地點偏好設定
- **自動用戶管理**: LINE Bot follow 時自動建立用戶記錄
- **DDD 架構設計**: 採用領域驅動設計，模組化程式碼結構
- **PostgreSQL 整合**: 完整的資料庫設計，包含用戶、天氣、行政區資料表
- **完整測試覆蓋**: pytest 測試框架，涵蓋核心業務邏輯
- **Docker 容器化**: 支援開發與生產環境的 docker-compose 配置

### 修正
- 移除無認證的危險 API 端點，提升系統安全性
- 優化用戶管理 API，移除冗餘代碼
- 增強 LINE webhook 接收的日誌記錄，便於除錯

### 改進
- 重構 JWT token 創建邏輯，提升測試可靠性
- 新增詳細的測試規範文件，標準化開發流程
- 使用 Ruff 進行格式化和 lint 檢查

---

## 發布說明
每個版本的詳細異動請參考對應的 [GitHub Releases](https://github.com/kyomind/WeaMind/releases)。

## 回饋與建議
如有任何功能建議或問題回報，歡迎透過 [GitHub Issues](https://github.com/kyomind/WeaMind/issues) 與我們聯繫。

---
*WeaMind - 讓天氣查詢變得更簡單、更直觀* 🌤️
