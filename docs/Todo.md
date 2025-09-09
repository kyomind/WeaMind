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
- [x] 29.實作 LINE Bot 公告系統與 Rich Menu 其它功能基礎架構 2025-08-27
- [x] 30.完善 Rich Menu 其它功能選項（Changelog 與產品說明） 2025-08-27
- [x] 31.Rich Menu 變動：將「其它」改為「更多資訊」 2025-08-28
- [x] 32.🍎LIFF 地點設定頁面錯誤處理與穩定性改善，包含 SDK 載入失敗、權限 scope、自動重新登入資料遺失、UI/UX 優化 2025-09-10

## 說明

- 日期格式為 YYYY-MM-DD，代表「已完成日期」，如果沒有日期則代表還沒完成
- 🍎代表可作為文章素材(由作者決定，預設無)
- 🧃代表已撰寫文章
- 每一個 todo 應限制可在 45-75 分鐘內完成，格式細節請參考 `docs/Example.md`

## Future Todo

- [ ] 實作完整的 LINE ID Token JWT 簽名驗證
- [ ] 實作 LIFF SDK integrity 自動化檢查與更新機制，在 CI 中定期檢查 LINE SDK 版本並自動更新 integrity hash
- [x] 25.實作 LINE Bot LIFF 地點設定功能（文字觸發版）
  - [x] 二級行政區的下拉選單出現閃爍式的重新載入問題、取消行為不當
  - [x] LIFF SDK 的錯誤訊息問題，以及scope write是否真的必要(登入會比較讓人謹慎) 2025-09-10
- [ ] 單元測試的 db 應該由 SQLite 改為 PostgreSQL，因為兩者的方言可能會有差異，應以 PostgreSQL 為主，參考「最近查詢」的 TODO
- [ ] 使用說明考慮用 MkDocs 生成靜態網站或 GitHub 倉庫首頁的 README.md
