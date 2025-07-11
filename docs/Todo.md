# Todo List for this Project

- [x] 1.Pydantic的FastAPI config設定 2025-05-15
- [x] 2.🧃新增 pyright 作為專案的 type checker 2025-05-16
- [x] 3.db遷移工具設定檔(還沒真的第一次遷移) 2025-05-30
- [x] 4.🍎🍎🍎專案容器化（尤其是開發用 db）2025-06-16
- [x] 5.設定第一個 api 並成功運行 FastAPI app runtime 2025-06-16
- [x] 6.設定與撰寫基本 api 測試(demo) 2025-06-16
- [x] 7.🍎建議部署和開發用的不同版的docker-compose.yml，使用繼承方式 2025-06-16
- [x] 8.🍎設定好 coverage 測試，cli、xml 等報告 2025-06-17
- [x] 9.將todo prompt和arch prompt移至docs目錄下 2025-06-17
- [x] 10.設計 user 模組的 Pydantic schema 與基本 CRUD API 2025-06-18
- [x] 11.🍎重構測試、建立 fixture 與型別註記，並補充註解說明 2025-06-18
- [x] 12.🍏建立 line webhook API endpoint，能正確接收與驗證來自 LINE 的 webhook 請求 2025-06-19
- [x] 13.🍎CI 加入 Codecov，並在 PR 時自動產出報告(bot) 2025-06-23
- [x] 14.🍎🍎執行 Alembic 資料庫遷移，建立 user table 2025-06-25
- [x] 15.🍎加了好幾個badge，與GitHub Actions相關的主要有sonarcloud、codeql 2025-06-26
- [x] 16.🍎新增 Dependabot 與 Codecov 設定 2025-06-28
- [x] 17.雲端 VM 部署 FastAPI 並設定 Nginx 反向代理與 HTTPS 憑證 2025-07-04
- [x] 18.LINE Developers 平台建立 channel 並取得 token 2025-07-10
  - **目的**：於 LINE Developers 平台建立 Messaging API channel，取得 channel secret 與 access token，並設定於專案環境。
  - **為何重要**：這是專案能與 LINE 平台串接的前置條件，沒有正確的 channel 資訊與 token，webhook 無法驗證、API 也無法推播訊息。
  - **可能的挑戰**：
    - LINE Developers 後台操作流程不熟悉，或 channel 權限設定錯誤。
    - channel secret、access token 需安全保存並正確配置於專案環境變數。
  - **實作方向與細節**：
    1. 於 LINE Developers 平台建立 Messaging API channel。
    2. 取得 channel secret 與 access token。
    3. 將 channel secret、access token 設定於專案環境變數。
    4. （可選）將相關設定紀錄於專案文件。
  - **預期成果與驗收依據**：
    - 成功取得 channel secret 與 access token，並正確設定於專案環境。
    - 專案可正確讀取這些變數。

- [ ] 19.webhook URL 設定、驗證與應聲蟲訊息測試
  - **目的**：將 webhook URL 設定於 LINE Developers 後台，並驗證 webhook 能正確收到事件並實現「應聲蟲」功能（收到訊息即原樣回覆）。
  - **為何重要**：這是讓 LINE 平台能將訊息事件推送到專案 API，並確保 API 能正確回應用戶訊息的關鍵步驟。
  - **可能的挑戰**：
    - webhook URL 需為 HTTPS，且 Nginx/防火牆設定需正確。
    - webhook handler 需正確驗證 X-Line-Signature 並回應 200 OK。
    - 應聲蟲功能需正確呼叫 LINE Messaging API 並處理簽名驗證。
  - **實作方向與細節**：
    1. 在 LINE Developers 後台設定 webhook URL，指向 https://<your-domain>/line/webhook，並啟用 webhook。
    2. 於 FastAPI 專案中實作 webhook handler，驗證 X-Line-Signature 並回應 200 OK。
    3. 實作應聲蟲功能：收到 LINE 訊息事件時，API 會用相同內容回覆發訊者。
    4. 測試從 LINE 傳送訊息，確認 webhook 能收到事件並正確回覆原訊息。
    5. （可選）將相關測試流程紀錄於專案文件。
  - **預期成果與驗收依據**：
    - LINE Developers 後台 webhook URL 驗證通過，能收到 200 OK。
    - 實際從 LINE 傳送訊息，FastAPI webhook 能收到事件並以「應聲蟲」方式回覆相同訊息。
    - channel access token 驗證可用，API 能成功推播訊息至 LINE 並回覆內容與收到訊息一致。

## 說明

- 日期格式為 YYYY-MM-DD，代表「已完成日期」，如果沒有日期則代表還沒完成
- 🍎代表可作為文章素材
- 🧃代表已撰寫文章
- 每一個 todo 應限制可在 45-75 分鐘內完成
