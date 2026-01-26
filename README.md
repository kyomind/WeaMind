[![WeaMind CI](https://github.com/kyomind/WeaMind/actions/workflows/ci.yml/badge.svg)](https://github.com/kyomind/WeaMind/actions/workflows/ci.yml)
[![CodeQL](https://github.com/kyomind/WeaMind/actions/workflows/codeql.yml/badge.svg)](https://github.com/kyomind/WeaMind/security/code-scanning)
[![codecov](https://codecov.io/gh/kyomind/WeaMind/branch/main/graph/badge.svg)](https://codecov.io/gh/kyomind/WeaMind)
[![SonarCloud](https://sonarcloud.io/api/project_badges/measure?project=kyomind_WeaMind&metric=sqale_rating)](https://sonarcloud.io/summary/overall?id=kyomind_WeaMind)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/kyomind/WeaMind)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

A smart LINE bot for Taiwan weather updates. See [DeepWiki](https://deepwiki.com/kyomind/WeaMind) for details.

WeaMind 是一個智慧天氣 LINE Bot，透過簡單的操作或文字查詢，提供即時台灣天氣資訊。

本服務完全**免費**，如果對你有幫助，歡迎[贊助我一杯咖啡](https://portaly.cc/kyomind/support)，或點擊右上角的 ⭐️ 支持我。

## 快速導覽

- [使用說明](#使用說明)
  - [智慧文字搜尋](#1-智慧文字搜尋)
  - [設定住家、公司](#2-設定住家公司一鍵查詢天氣)
  - [快速重複查詢](#3-快速重複查詢)
  - [地圖查詢](#4-地圖查詢)
  - [加入好友](#加入好友開始使用)
- [開發者技術亮點](#開發者技術亮點)
  - [Fast ACK Webhook 架構](#-fast-ack-webhook-架構)
  - [Redis 分散式鎖](#-redis-分散式鎖)
  - [Domain-Driven Design 架構](#-domain-driven-design-架構)
  - [pytest 單元測試體系](#-pytest-單元測試體系)
  - [現代化開發工具鏈](#-現代化開發工具鏈)
  - [完整 CI Pipeline](#-完整-ci-pipeline)
  - [容器化與部署](#-容器化與部署)
## 使用說明

加入 WeaMind 為好友後，點擊聊天視窗下方的「功能選單」即可開始使用。

![WeaMind](https://img.kyomind.tw/2352352we-min-20250929-222126.png)

### 1. 智慧文字搜尋
- 直接輸入「二級行政區」名稱，比如「`大安區`」、「`水上`」、「`中壢`」等，將進行地名的模糊比對。
- 系統會自動識別並回傳該地區的天氣資訊。

### 2. 設定住家、公司，一鍵查詢天氣
- 透過「`設定地點`」功能，預先設定常用地址。
- 點擊「`查住家`」或「`查公司`」立即取得該地區的完整天氣資訊。

### 3. 快速重複查詢
- 「`最近查過`」會記錄您最近查詢過的 **5 個地點**（不含住家與公司）。
- 點擊後重新查詢，無需重複輸入地址。

### 4. 地圖查詢
- 點擊「`地圖查詢`」會開啟 LINE 地圖介面。
- 直接在地圖上選擇位置，系統會自動取得該地點資訊並查詢當地天氣。
- 不限於目前所在位置，你可以查詢**任意地點**的天氣。

## 加入好友，開始使用

1. 掃描下方 QR Code（推薦）或搜尋 LINE ID `@370ndhmf` 加入 WeaMind。
2. 使用功能選單開始查詢天氣資訊。

立即體驗智慧天氣查詢，讓天氣資訊隨手可得！

![WeaMind QR Code](https://img.kyomind.tw/wea-qrcode-min-20250929-223022.png)

---

## 開發者技術亮點

```mermaid
graph TB
    LINE[LINE Platform]
    REDIS[(Redis<br/>分散式鎖)]
    DB[(PostgreSQL<br/>主資料庫)]
    DATA[weamind-data<br/>微服務]

    subgraph FASTAPI["FastAPI LINE Bot App"]
        WEB[Webhook Handler]
        BG[Background Tasks]
    end

    LINE -->|Webhook| WEB
    WEB -->|Fast ACK<br/>數十毫秒| LINE
    WEB -->|非阻塞| BG
    BG -->|選擇性鎖定| REDIS
    BG <-->|資料讀寫| DB
        BG -->|回應用戶<br/>< 2 秒| LINE
    DATA -->|每 6 小時<br/>ETL 更新| DB
```

### 🚀 Fast ACK Webhook 架構
- **數十毫秒 ACK**：Webhook Handler 收到請求後立即驗證並回應 LINE Platform，避免平台重送
- **2 秒內回應用戶**：採用「快速 ACK→背景處理→回應用戶」的非同步流程
- **背景任務處理**：使用 FastAPI BackgroundTasks，避免業務邏輯阻塞 ACK

### 🔒 Redis 分散式鎖
- **防重複點擊保護**：2 秒鎖定機制，避免用戶快速連點造成重複處理
- **服務優先策略**：Redis 異常時自動降級，確保核心服務不中斷
- **精準鎖定範圍**：僅對按鈕操作加鎖，一般文字查詢保持快速回應

### 🏗️ Domain-Driven Design 架構
- **清晰領域邊界**：`core`（基礎設施）、`user`（使用者管理）、`line`（LINE Bot）、`weather`（天氣服務）
- **分層模組化設計**：按業務領域劃分模組，架構清晰易擴展，適合團隊協作開發
- **100% Type Hints 覆蓋**：以 Pyright basic 標準，達成完整型別安全

### 🧪 pytest 單元測試體系
- **94% 測試覆蓋率**：高覆蓋率確保程式碼品質與穩定性
- **32+ 測試檔案**：涵蓋 core、line、weather、user 各領域模組的完整測試
- **測試環境隔離**：SQLite 記憶體資料庫 + fixtures 設計，確保測試獨立性
- **自動化覆蓋率**：pytest-cov 整合，自動生成覆蓋率報告並上傳 Codecov

### 🛠️ 現代化開發工具鏈
- **統一環境管理**：uv 套件管理，統一 `uv run` 指令執行，消除環境差異
- **完整程式碼品質檢查**：Ruff 靜態檢查與格式化，確保程式碼一致性
- **自動化程式碼檢查**：pre-commit hooks 於 commit 前自動執行品質檢查
- **多重安全掃描**：Bandit（靜態安全）、pip-audit（CVE 檢查）、detect-secrets（敏感資料防護）

### 🔄 完整 CI Pipeline
- **多層級程式碼品質檢查**：Ruff → Pyright → Bandit → pip-audit → pytest 依序執行
- **容器化驗證**：每次 PR 自動驗證 Docker image 完整性
- **三軌安全分析**：主 CI 流程 + CodeQL + SonarCloud 多維度安全與品質監控
- **自動化發布**：Git tag 觸發自動版本發布與 release notes 生成

### 📦 容器化與部署
- **多層快取 Docker 設計**：分層快取機制（依賴層 + 應用層），大幅加速重建時間
- **自動化部署流程**：Makefile 整合資料庫健康檢查、自動遷移、錯誤處理的完整部署機制
- **多環境配置繼承**：dev/prod 環境透過 Docker Compose 組合實現環境隔離與配置複用

---

詳細技術架構請參考：
- [專案架構](docs/Architecture-Code.md) - 完整程式碼架構說明
- [DeepWiki 技術文件](https://deepwiki.com/kyomind/WeaMind) - 互動式技術探索
