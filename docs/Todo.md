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

- [ ] 17.雲端 VM 上 Git 複製專案並啟動 FastAPI（含 Docker Compose）
  - **目的**：將本地開發完成的 FastAPI 專案部署到雲端 VM，並以 Docker Compose 啟動服務，確保專案能在雲端環境正常執行。
  - **為何重要**：這是專案從本地開發邁向線上服務的第一步，確保 API 能在雲端環境穩定執行，是後續對外服務、整合 Nginx 及 LINE webhook 的基礎。
  - **可能的挑戰**：
    - VM 防火牆/安全群組需開放 8000 port。
    - Docker、Docker Compose 安裝過程可能遇到權限或相依性問題。
    - FastAPI 服務啟動時若有環境變數、資料庫連線等設定錯誤需即時修正。
  - **實作方向與細節**：
    1. 於雲端 VM 上安裝 Git、Docker、Docker Compose。
    2. Git 複製專案程式碼到 VM。
    3. 使用 `docker-compose up -d` 啟動 FastAPI 服務。
    4. 使用 `curl http://localhost:8000/docs` 或瀏覽器驗證服務啟動。
    5. （可選）將安裝與啟動步驟寫入專案文件。
  - **預期成果與驗收依據**：
    - 專案程式碼已成功複製到雲端 VM。
    - 執行 `docker-compose up -d` 後，FastAPI 服務可於 VM 的 8000 port 正常啟動。
    - 使用 `curl` 或瀏覽器連線 VM 的 8000 port（如 http://<vm-ip>:8000/docs）能看到 FastAPI Swagger UI。

- [ ] 18.安裝與設定 Nginx 反向代理＋申請 HTTPS 憑證
  - **目的**：於雲端 VM 上安裝 Nginx，設定反向代理將外部 HTTPS 請求導向 FastAPI webhook 端點，並申請 Let's Encrypt 憑證，確保 webhook 能被 LINE 平台安全存取。
  - **為何重要**：這是讓 LINE webhook 能安全、穩定對接專案 API 的關鍵步驟，沒有 HTTPS 與正確反向代理，LINE webhook 將無法串接，專案也無法對外服務。
  - **可能的挑戰**：
    - VM 防火牆/安全群組需開放 443/80 連接埠。
    - Nginx 設定需正確處理路徑、Header 轉發與 HTTPS 憑證。
    - 憑證申請過程可能遇到 DNS 或 port 佔用問題。
    - Docker Compose 與 Nginx 共用 port 時的設定協調。
  - **實作方向與細節**：
    1. 於雲端 VM 上安裝 Nginx。
    2. 設定 Nginx 反向代理，將 /line/webhook 導向 127.0.0.1:8000。
    3. 使用 Certbot 申請 Let's Encrypt 憑證，設定 Nginx 支援 HTTPS。
    4. 測試 https://<your-domain>/line/webhook 能正確回應。
    5. 在 LINE Developers 後台測試 webhook URL，確認能收到 200 OK。
    6. （可選）將 Nginx、憑證等設定寫入專案文件。
  - **預期成果與驗收依據**：
    - Nginx 已安裝並設定為反向代理，能將 https://<your-domain>/line/webhook 導向本地 8000 port。
    - 成功申請並安裝 Let's Encrypt 憑證，Nginx 能正確處理 HTTPS 連線。
    - 使用 `curl -k https://<your-domain>/line/webhook` 能收到 200 OK 回應。
    - 在 LINE Developers 後台測試 webhook URL，能收到 200 OK 回應。

## 說明

- 日期格式為 YYYY-MM-DD，代表「已完成日期」，如果沒有日期則代表還沒完成
- 🍎代表可作為文章素材
- 🧃代表已撰寫文章
- 每一個 todo 應限制可在 45-75 分鐘內完成
