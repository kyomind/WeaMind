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
- [ ] 24.實作 LINE Bot LIFF 地點設定功能（文字觸發版）
- [ ] 25.實作 LINE Bot Rich Menu 六格配置與點擊事件處理
  - **目的**：實現 PRD 中「點擊優先」互動模型的核心功能，讓 80% 的用戶互動透過 Rich Menu 完成，提供查住家、查公司、最近查過等快捷功能。
  - **為何重要**：這是產品 UX 策略的核心實作，將大幅降低用戶輸入成本，從繁瑣的文字輸入轉為一鍵點擊查詢。Rich Menu 是 LINE Bot 的主要互動介面，直接影響用戶留存和使用頻率。
  - **可能的挑戰**：
    - Rich Menu 圖片設計需要符合 LINE 規範（2500x1686 像素）且視覺清晰易懂。
    - postback 事件與 message 事件的混合處理邏輯。
    - 模擬天氣回應的設計需要符合 PRD 格式規範。
    - 測試 Rich Menu 需要實際部署到 LINE 平台驗證。
  - **實作方向與細節**：
    1. 設計 Rich Menu 六格配置圖片：查住家、查公司、最近查過、我的地點、使用教學、其他。
    2. 在 `app/line/service.py` 中新增 `handle_postback_event` 函數處理 Rich Menu 點擊事件。
    3. 實作各個功能的 postback data 解析與路由邏輯。
    4. 為尚未實作的功能（住家/公司查詢）建立模擬回應，格式符合 PRD 規範。
    5. 透過 LINE Bot API 設定 Rich Menu 並上傳圖片資源。
    6. 建立對應的測試案例驗證 postback 事件處理邏輯。
  - **預期成果與驗收依據**：
    - LINE Bot 成功顯示六格 Rich Menu，用戶可正常點擊各功能。
    - 點擊「查住家」、「查公司」時顯示相應的模擬天氣回應或設定提示。
    - 點擊「最近查過」時能處理相應邏輯（即使暫無資料）。
    - 所有 postback 事件都有對應的處理函數且不會發生錯誤。
- [ ] 26.實作用戶查詢記錄與最近查詢功能
  - **目的**：記錄用戶的查詢歷史，提供「最近查過」快捷功能，提升多地點查詢的效率，完善 Rich Menu 的核心體驗。
  - **為何重要**：解決 PRD 中提到的「多地點查詢痛點」，讓用戶可以快速重複查詢最近關心的地點，避免重複輸入。這是提升用戶黏性和使用頻率的關鍵功能。
  - **可能的挑戰**：
    - 查詢記錄的資料結構設計，需要平衡效能與功能需求。
    - 記錄清理機制，避免無限增長的歷史資料。
    - Quick Reply 介面的動態生成和用戶體驗優化。
    - 查詢頻率統計和排序邏輯的效能考量。
  - **實作方向與細節**：
    1. 設計 `UserQuery` 資料模型，包含 `user_id`、`location_id`、`query_time` 等欄位。
    2. 執行 Alembic 遷移建立 `user_queries` 表格。
    3. 在每次成功的地點查詢後自動記錄查詢歷史。
    4. 實作 `get_recent_queries` 方法，取得用戶最近查詢的 3 個不重複地點。
    5. 在 Rich Menu 的「最近查過」功能中整合 Quick Reply 介面。
    6. 設計查詢記錄的清理策略（如保留最近 30 天或最多 100 筆記錄）。
    7. 新增對應的 service 方法和 API 支援查詢歷史的管理。
    8. 撰寫測試案例涵蓋記錄儲存、查詢和清理邏輯。
  - **預期成果與驗收依據**：
    - 用戶每次成功查詢地點後，系統自動記錄查詢歷史。
    - 「最近查過」功能能正確顯示最近 3 個查詢地點的 Quick Reply 選項。
    - 點擊 Quick Reply 中的地點能立即觸發天氣查詢（或模擬回應）。
    - 查詢記錄具備適當的清理機制，不會無限累積資料。

## 說明

- 日期格式為 YYYY-MM-DD，代表「已完成日期」，如果沒有日期則代表還沒完成
- 🍎代表可作為文章素材(由作者決定，預設無)
- 🧃代表已撰寫文章
- 每一個 todo 應限制可在 45-75 分鐘內完成，格式細節請參考 `docs/Example.md`

## Future Todo

- [ ] 實作完整的 LINE ID Token JWT 簽名驗證

## Check List
- [ ] 二級行政區的下拉選單出現閃爍式的重新載入問題
- [ ] LIFF SDK 的錯誤訊息問題，以及scope write是否真的必要(登入會比較讓人謹慎)
- [ ] 設定地址時使用者不存在與 follow 時的整合！
