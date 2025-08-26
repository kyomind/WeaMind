# Project Accomplishments

## Todo and Completed
- [x] 1.Pydantic的FastAPI config設定 2025-05-15
- [x] 2.🧃新增 pyright 作為專案的 type checker 2025-05-16
- [x] 3.db遷移工具設定檔(還沒真的第一次遷移) 2025-05-30
- [x] 4.🧃(uv)🍎專案容器化（尤其是開發用 db）2025-06-16
- [x] 5.🍎(介紹uvicorn)hello api、設定uvicorn並成功運行 FastAPI app runtime 2025-06-16
- [x] 6.設定與撰寫基本 api 測試(demo) 2025-06-16
- [x] 7.🍎建議部署和開發用的不同版的docker-compose.yml，使用繼承方式 2025-06-16
- [x] 8.🍎設定好 coverage 測試，cli、xml 等報告 2025-06-17
- [x] 9.將todo prompt和arch prompt移至docs目錄下 2025-06-17
- [x] 10.設計 user 模組的 Pydantic schema 與基本 CRUD API 2025-06-18
- [x] 11.🍎重構測試、建立 fixture 與型別註記，並補充註解說明 2025-06-18
- [x] 12.建立 line webhook API endpoint 2025-06-19
- [x] 13.🍎CI 加入 Codecov，並在 PR 時自動產出報告(bot) 2025-06-23
- [x] 14.執行 Alembic 資料庫遷移，建立 user table 2025-06-25
- [x] 15.🍎加了好幾個badge，與GitHub Actions相關的主要有sonarcloud、codeql 2025-06-26
- [x] 16.🍎新增 Dependabot 與 Codecov 設定 2025-06-28
- [x] 17.🍎雲端 VM 部署 FastAPI 並設定 Nginx 反向代理與 HTTPS 憑證 2025-07-04
- [x] 18.LINE Developers 平台建立 channel 並取得 token 2025-07-10
- [x] 19.webhook URL 設定、驗證與應聲蟲訊息測試 2025-07-11
- [x] 20.實作 LINE Bot follow/unfollow 事件處理與自動建立用戶記錄功能 2025-08-11
- [x] 21.設計並建立天氣與行政區資料庫 Schema，實作 Alembic 遷移，初始化所有鄉鎮區(location)資料 2025-08-14
- [x] 22.實作地點輸入解析功能，支援中文地名模糊查詢與智慧回應 2025-08-14
- [x] 23.實作 Quick Reply 功能，用於查詢獲得 2 或 3 個結果時 2025-08-16
- [x] 24.移除用戶 API 安全漏洞，刪除無認證的危險端點 2025-08-19
- [x] 25.實作 LINE Bot LIFF 地點設定功能（文字觸發版）2025-08-19
- [x] 26.實作 LINE Bot Rich Menu 六格配置與點擊事件處理 2025-08-23
- [x] 27.實作用戶查詢記錄與最近查詢功能 2025-08-24
- [x] 28.實作當前位置天氣查詢功能，支援地理位置分享與智慧地點識別 2025-08-26
- [ ] 29.實作 LINE Bot 公告系統與 Rich Menu 其它功能基礎架構
  - **目的**：建立 Rich Menu「其它」按鈕的核心架構，並實作完整的公告系統，讓用戶能夠透過 LINE 對話框查看系統公告與維護資訊。
  - **為何重要**：此功能是建立與用戶溝通管道的關鍵，讓開發團隊能夠有效地向用戶推送重要資訊（如系統維護、新功能發布）。同時建立的架構也為後續其他「其它」選單功能奠定基礎。
  - **可能的挑戰**：
    - 設計合適的 `announcements.json` 資料結構，需平衡可讀性與擴展性。
    - Flex Message 的動態生成邏輯需要處理字數限制與排版美觀性。
    - 靜態頁面的 JavaScript 需要適當的錯誤處理與載入狀態顯示。
    - Quick Reply 選單的 postback 事件處理需要與現有的 Rich Menu 系統整合。
  - **實作方向與細節**：
    1. 在 `app/line/service.py` 中新增 Rich Menu「其它」按鈕的事件處理邏輯，回傳 Quick Reply 選單。
    2. 設計並建立 `/static/announcements.json` 檔案結構，包含 id、title、body、level、時間等欄位。
    3. 實作 `handle_other_announcements` postback 處理函式，讀取 JSON 並動態生成 Flex Message Carousel。
    4. 建立 `/static/announcements/index.html` 靜態頁面，使用 JavaScript fetch API 讀取同一份 JSON 並渲染完整公告列表。
    5. 在 FastAPI 中設定 `/static` 路由，確保靜態檔案可以正確存取。
    6. 撰寫單元測試驗證 JSON 讀取、Flex Message 生成、postback 處理等功能。
  - **預期成果與驗收依據**：
    - 用戶點擊 Rich Menu「其它」按鈕後，會收到包含三個選項的 Quick Reply 選單。
    - 點擊「📢 公告」選項後，會收到最新 1-3 則公告的 Flex Message Carousel。
    - Flex Message 中的「查看完整內容」按鈕能正確跳轉到靜態頁面，顯示所有歷史公告。
    - 公告資料僅需維護一份 `announcements.json`，兩處（Flex + 靜態頁）會自動同步顯示。

- [ ] 30.完善 Rich Menu 其它功能選項（Changelog 與產品說明）
  - **目的**：完成「其它」功能的其餘兩個選項，讓用戶能夠查看產品更新歷史與使用說明，建立完整的客戶服務與產品資訊體系。
  - **為何重要**：提供用戶自助查詢管道，減少客服負擔，同時提升產品的專業形象與用戶體驗。Changelog 連結到 GitHub 可展現開發透明度，使用說明則能幫助新用戶快速上手。
  - **可能的挑戰**：
    - 使用說明頁面需要平衡資訊完整性與閱讀體驗，避免過於冗長或過於簡略。
    - 靜態頁面的 RWD 設計需要在手機端有良好的閱讀體驗。
    - 需要考慮未來內容更新的維護成本與更新流程。
  - **實作方向與細節**：
    1. 在前一個 Todo 建立的 Quick Reply 選單中，補齊「📄 Changelog」與「ℹ️ 介紹與說明」兩個 URI Action。
    2. 確認 GitHub CHANGELOG.md 的 URL 格式，設定正確的連結路徑。
    3. 建立 `/static/help/index.html` 使用說明頁面，包含產品介紹、主要功能說明、常見問題等內容。
    4. 設計適合手機閱讀的 CSS 樣式，確保在 LINE 內建瀏覽器中有良好體驗。
    5. 建立說明頁面的內容架構：產品簡介、功能導覽、地點設定教學、常見問題、聯絡資訊等。
    6. 進行完整的「其它」功能整合測試，確保三個選項都能正常運作。
  - **預期成果與驗收依據**：
    - Quick Reply 選單中的「📄 Changelog」按鈕能正確開啟 GitHub 上的 CHANGELOG.md 頁面。
    - 「ℹ️ 介紹與說明」按鈕能開啟設計良好的產品說明頁面，內容包含完整的使用指南。
    - 說明頁面在手機端有良好的閱讀體驗，字體大小、行距、排版都適合手機閱讀。
    - 整個「其它」功能流程順暢，用戶能夠輕鬆找到所需的資訊。

## 說明

- 日期格式為 YYYY-MM-DD，代表「已完成日期」，如果沒有日期則代表還沒完成
- 🍎代表可作為文章素材(由作者決定，預設無)
- 🧃代表已撰寫文章
- 每一個 todo 應限制可在 45-75 分鐘內完成，格式細節請參考 `docs/Example.md`

## Future Todo

- [ ] 實作完整的 LINE ID Token JWT 簽名驗證
- [x] 25.實作 LINE Bot LIFF 地點設定功能（文字觸發版）
  - [ ] 二級行政區的下拉選單出現閃爍式的重新載入問題、取消行為不當
  - [ ] LIFF SDK 的錯誤訊息問題，以及scope write是否真的必要(登入會比較讓人謹慎)
  - [ ] 設定地址時使用者不存在與 follow 時的整合！
- [ ] 單元測試的 db 應該由 SQLite 改為 PostgreSQL，因為兩者的方言可能會有差異，應以 PostgreSQL 為主，參考「最近查詢」的 TODO
- [ ] 重新調整 rich menu 位置分配
