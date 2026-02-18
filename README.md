[![WeaMind CI](https://github.com/kyomind/WeaMind/actions/workflows/ci.yml/badge.svg)](https://github.com/kyomind/WeaMind/actions/workflows/ci.yml)
[![CodeQL](https://github.com/kyomind/WeaMind/actions/workflows/codeql.yml/badge.svg)](https://github.com/kyomind/WeaMind/security/code-scanning)
[![codecov](https://codecov.io/gh/kyomind/WeaMind/branch/main/graph/badge.svg)](https://codecov.io/gh/kyomind/WeaMind)
[![SonarCloud](https://sonarcloud.io/api/project_badges/measure?project=kyomind_WeaMind&metric=sqale_rating)](https://sonarcloud.io/summary/overall?id=kyomind_WeaMind)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/kyomind/WeaMind)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

A smart LINE Bot for Taiwan weather updates.

> **WeaMind on Kubernetes**：[weamind-infra](https://github.com/kyomind/weamind-infra) - WeaMind 的 Kubernetes (K3s) 部署與架構

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
  - [Fast ACK Webhook 架構](#fast-ack-webhook-架構)
  - [Redis 分散式鎖](#redis-分散式鎖)
  - [Domain-Driven Design 架構](#domain-driven-design-架構)
  - [pytest 單元測試體系](#pytest-單元測試體系)
  - [現代化開發工具](#現代化開發工具)
  - [CI Pipeline](#ci-pipeline)

## 使用說明

加入 WeaMind 為好友後，點擊聊天視窗下方的「功能選單」即可開始使用。

![WeaMind](https://img.kyomind.tw/2352352we-min-20250929-222126.png)

### 1. 智慧文字搜尋
- 直接輸入「二級行政區」名稱，例如「`大安區`」、「`水上`」、「`中壢`」，就能快速查詢。
- 系統會自動識別地點並回傳天氣資訊。

### 2. 設定住家、公司，一鍵查詢天氣
- 透過「`設定地點`」功能，預先設定常用地址。
- 點擊「`查住家`」或「`查公司`」即可立即查詢天氣。

### 3. 快速重複查詢
- 「`最近查過`」會記錄您最近查詢的 **5 個地點**（不含住家與公司）。
- 點擊即可重新查詢，無需重複輸入。

### 4. 地圖查詢
- 點擊「`地圖查詢`」開啟 LINE 地圖介面。
- 在地圖上選擇任意位置，系統會自動查詢該地點的天氣。
- 不限於目前所在位置，可查詢**任何地點**的天氣。

## 加入好友，開始使用

1. 掃描下方 QR Code（推薦）或搜尋 LINE ID `@370ndhmf` 加入 WeaMind。
2. 點擊功能選單即可開始查詢。

立即體驗智慧天氣查詢！

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

### Fast ACK Webhook 架構
- **數十毫秒 ACK**：Webhook Handler 收到請求後立即驗證並回應 LINE Platform，避免平台重送
- **2 秒內回應**：快速 ACK → 背景處理 → 回應用戶
- **非阻塞設計**：使用 FastAPI `BackgroundTasks` 處理業務邏輯，不阻塞 webhook 回應

### Redis 分散式鎖
- **2 秒鎖定機制**：避免用戶快速連點造成重複處理
- **異常降級策略**：Redis 異常時核心服務繼續運作
- **選擇性加鎖**：僅對按鈕操作加鎖，文字查詢不受影響

### Domain-Driven Design 架構
- **領域模組劃分**：`core`（基礎設施）、`user`（使用者管理）、`line`（LINE Bot）、`weather`（天氣服務）
- **分層架構實踐**：每個領域模組包含 `router.py`、`service.py`、`models.py` 實現三層分離

### pytest 單元測試體系
- **94% 測試覆蓋率**：32+ 測試檔案涵蓋 core、line、weather、user 各模組
- **獨立測試環境**：SQLite 記憶體資料庫 + fixtures，每個測試獨立運行不互相干擾
- **Codecov 監控**：每次 PR 自動檢查覆蓋率變化，防止新功能降低測試覆蓋率

### 現代化開發工具
- **uv 套件管理**：統一的 Python 套件與虛擬環境管理，所有指令使用 `uv run` 執行
- **Ruff 檢查與格式化**：取代 Pylint、Black、isort 的全方位工具
- **Pyright 型別檢查**：100% Type Hints 覆蓋，確保型別安全
- **pre-commit 自動化**：Git commit 前自動執行格式化與檢查
- **安全掃描工具**：Bandit（靜態安全分析）、pip-audit（CVE 檢查）、detect-secrets（敏感資料防護）

### CI Pipeline
- **自動化品質檢查**：每次 push 執行 Ruff → Pyright → Bandit → pip-audit → pytest + Codecov 完整流程
- **Image 建置與推送**：CI 成功後自動推送 image 到 GHCR（支援 amd64/arm64）
- **三重安全掃描**：主 CI 流程 + CodeQL（程式碼安全掃描）+ SonarCloud（技術債與品質監控）
- **自動發布機制**：Git tag 觸發版本發布與 release notes 生成

---

進一步了解：
- [WeaMind 專案介紹：技術選型與架構](https://blog.kyomind.tw/weamind)（撰寫中）
- [DeepWiki 技術文件](https://deepwiki.com/kyomind/WeaMind) - 互動式技術探索
