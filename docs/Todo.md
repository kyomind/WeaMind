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
- [ ] 27.實作用戶查詢記錄與最近查詢功能
  - **目的**：記錄用戶的查詢歷史，提供「最近查過」快捷功能，提升多地點查詢的效率，完善 Rich Menu 的核心體驗。
  - **[FOR AI]** 已創建分支 `feature/user-query-history`，準備開始實作。關鍵決策：30天清理策略確定，SQL排除住家/公司邏輯已分析。
  - **為何重要**：解決 PRD 中提到的「多地點查詢痛點」，讓用戶可以快速重複查詢最近關心的地點，避免重複輸入。這是提升用戶黏性和使用頻率的關鍵功能。
  - **可能的挑戰**：
    - 查詢記錄的資料結構設計，需要平衡效能與功能需求。
    - 記錄清理機制，避免無限增長的歷史資料。（註：資料清理由 wea-data 模組負責，非本專案實作範圍）
    - Quick Reply 介面的動態生成和用戶體驗優化。
    - 查詢頻率統計和排序邏輯的效能考量。
    - 「最近查詢」SQL 查詢需要智慧排除用戶已設定的住家/公司地點，避免重複顯示。
  - **實作方向與細節**：
    1. 設計 `UserQuery` 資料模型，包含 `user_id`、`location_id`、`query_time` 等欄位。
    2. 執行 Alembic 遷移建立 `user_queries` 表格。
    3. 在每次成功的地點查詢後自動記錄查詢歷史。
    4. 實作 `get_recent_queries` 方法，取得用戶最近查詢的 3 個不重複地點（需排除已設定的住家/公司地點）。SQL 邏輯需要動態處理：用戶可能只設定住家/公司其中一個、兩者都設定、或都沒設定的情況。
    5. 在 Rich Menu 的「最近查過」功能中整合 Quick Reply 介面。
    6. 設計查詢記錄的清理策略（保留最近 30 天）。（註：實際清理由 wea-data 模組負責）
    7. 新增對應的 service 方法和 API 支援查詢歷史的管理。
    8. 撰寫測試案例涵蓋記錄儲存、查詢和清理邏輯。（註：清理邏輯測試僅驗證資料結構設計，實際清理由 wea-data 負責）
  - **[FOR AI]** 實作順序建議：models -> migration -> service -> tests -> line integration。注意 User 模型在 `app/user/models.py` 已有 home_location_id/work_location_id 可參考排除邏輯。
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
- [x] 25.實作 LINE Bot LIFF 地點設定功能（文字觸發版）
  - [ ] 二級行政區的下拉選單出現閃爍式的重新載入問題、取消行為不當
  - [ ] LIFF SDK 的錯誤訊息問題，以及scope write是否真的必要(登入會比較讓人謹慎)
  - [ ] 設定地址時使用者不存在與 follow 時的整合！

## Check List
