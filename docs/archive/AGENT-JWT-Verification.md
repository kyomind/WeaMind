# AGENT Spec: LINE ID Token 簽名與 Audience 驗證

狀態: 設計通過，已建立功能分支 `feature/jwt-verification`

## 1) Why — 為什麼要做
- 目前 `verify_line_id_token` 僅做基本檢查（`alg`/`iss`/`exp`/`sub`），未驗證 JWT 簽名與 `aud`，存在被偽造 ID Token 的高風險。
- 生產安全需求：必須確認 ID Token 由 LINE 簽發（簽名驗證）且是簽發給我們的應用（audience 驗證）。
- 文件中「aud 驗證 LIFF ID」需更正：正確做法是驗證 LINE Login「Channel ID」。

成功標準：
- ID Token 在生產環境必須通過：簽名驗證（`RS256/ES256`）、`iss=https://access.line.me`、有效 `exp`、`aud` 等於/包含我們的 Channel ID。
- 善用 JWKS（`https://api.line.me/oauth2/v2.1/certs`），正確處理 `kid`、網路失敗與快取。

## 2) What — 要做什麼
- 實作完整的 LINE ID Token 驗證功能（簽名 + audience）。
- 新增設定項：`LINE_CHANNEL_ID`（用於 `aud` 驗證），`ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION`（控制是否啟用 ID Token 簽名驗證，生產必須啟用）。
- 對 `verify_line_id_token` 完整化：
  - 解析 `header.kid`/`alg`，
  - 取得並快取 LINE JWKS，
  - 驗簽並解碼，
  - 驗證 `iss`、`exp`、`aud`，
  - 回傳 `sub` 作為 `line_user_id`。
- 覆蓋測試：成功、過期、錯誤簽名、`aud` 不符、`iss` 不符、不支援的 `alg`、`kid` 找不到（含刷新 JWKS）。
- 修正文檔：`aud` 應驗證 Channel ID（非 LIFF ID），新增環境變數說明。

不在本次範疇（Non-goals）:
- 更動現有 `verify_line_access_token` 流程（保留現狀）。
- CORS/用戶建立邏輯（已有處理）。

## 3) How — 技術方案與實作

### 3.1 依賴與設定
- 新增依賴（`pyproject.toml`）：
  - `PyJWT>=2.x`(已安裝了)
  - `cryptography`（PyJWT 驗簽所需）
- 新增設定（`app/core/config.py`）：
  - `LINE_CHANNEL_ID: str | None = None`
  - `ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION: bool = True`
- 生產規則：`ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION=True` 且 `LINE_CHANNEL_ID` 必須設定；否則啟動時或第一個驗證請求時給出明確錯誤。

### 3.2 驗證流程（`verify_line_id_token`）
- 前置快速檢查：格式、`alg` ∈ {`RS256`,`ES256`}（與現有一致）。
- 取得 `header.kid`；若沒有 `kid` → 401。
- 取得 JWKS：
  - 來源：`https://api.line.me/oauth2/v2.1/certs`
  - `timeout=5s`、記憶體快取（TTL 建議 24h）。
  - 先查快取 → 未命中或 `kid` 不在快取 → 刷新一次 → 仍無對應 `kid` 則 401。
- 使用對應 JWK 建立金鑰並 `jwt.decode(...)`：
  - `algorithms=["RS256","ES256"]`
  - `issuer="https://access.line.me"`
  - `audience=settings.LINE_CHANNEL_ID`（若存在）
- 額外邏輯：
  - clock skew buffer：保留現有 5 分鐘容忍。
  - `aud` 支援字串或陣列（PyJWT 自帶 `audience` 檢查即可；必要時在解碼後自查）。
  - 成功後取 `payload["sub"]` 作為 `line_user_id`。

### 3.3 錯誤處理與觀測
- 對下列情境給出明確錯誤訊息並記錄警告：
  - 簽名驗證失敗、過期、`iss`/`aud` 不符、`alg` 不支援、`kid` 缺失或未匹配、JWKS 取得失敗。
- 網路失敗策略：
  - 有快取 → 使用快取（stale-if-error）
  - 無快取 → 回 503（或 401，預設 503 更貼近「外部依賴失效」）
- 異常 user ID 監控：`len(sub) != 33` 記錄告警。

### 3.4 測試策略
- 單元測試（`tests/core`）：
  - 使用 `unittest.mock` 模擬 `httpx.AsyncClient.get` 回傳 JWKS。
  - 測試案例：
    - 驗證成功（RS256 與 ES256 各一）
    - 過期 token
    - 簽名錯誤（金鑰不符）
    - `aud` 不符（含字串與陣列兩類）
    - `iss` 不符
    - 不支援 `alg`
    - `kid` 缺失或未命中（含二次刷新仍無）
    - JWKS 取得失敗：有快取使用快取、無快取回 503
- 注意：現有測試的無簽名 token 方式將不再適用「簽名開啟」場景；
  - 可新增情境化測試在「簽名驗證關閉」時沿用原行為（短期過渡），
  - 或全面切換為「真簽名」測試（建議長期）。

### 3.5 CI/品質
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Type check: `uv run pyright .`
- Test: `uv run pytest`

## 4) 變更點一覽（預計檔案）
- `app/core/config.py`：新增 `LINE_CHANNEL_ID`、`ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION`。
- `app/core/auth.py`：重構/擴充 `verify_line_id_token`（JWKS 快取、驗簽、aud 驗證、錯誤處理）。
- `pyproject.toml`：新增依賴 `PyJWT`、`cryptography`。
- `tests/core/test_auth.py` 或新檔：新增/調整測試，覆蓋成功與錯誤情境。
- `docs/seed/Security-Assessment-and-Checklist.md`：更新「aud 驗證」為 Channel ID 並標記完成狀態（完成後）。

## 5) 限制與考量
- 外部依賴可用性：LINE JWKS 端點必須可存取；需實作快取與失敗策略。
- 金鑰輪替：必須正確處理 `kid` 輪替（未命中時刷新 JWKS，一次機會）。
- 環境變數與行為：
  - 生產：必須設定 `LINE_CHANNEL_ID` 且強制啟用簽名驗證。
  - 開發/測試：可暫時關閉簽名驗證，或透過 mock 完整驗證流程。
- `aud` 值：為 LINE Login Channel ID（數字）；不是 LIFF ID。

## 6) 共識與決策
- 「aud 驗證對象」為 Channel ID（非 LIFF ID）— 此點已校正且是必要條件。
- 優先導入完整簽名與 `aud` 驗證；`verify_line_access_token` 路徑保持不變。
- 生產環境必須強制簽名驗證與 `aud` 驗證；開發可用開關過渡。
- JWKS 以記憶體快取，TTL 預設 24 小時；`kid` 不命中時允許刷新一次。
- 網路故障時優先用快取；無快取則回 503 較貼近服務相依失效（可配置）。

## 7) 實作步驟（代理可直接執行）
1. 分支：確認在 `feature/jwt-verification`。
2. 調整設定：新增 `LINE_CHANNEL_ID`、`ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION`。
3. 加依賴：於 `pyproject.toml` 新增 `PyJWT`、`cryptography`，執行安裝。
4. 實作 JWKS 客戶端：拉取/快取/刷新；提供以 `kid` 查公鑰的介面。
5. 重構 `verify_line_id_token`：導入 `jwt.decode` 與嚴格檢查，回傳 `sub`。
6. 加查 `aud`：比對 `settings.LINE_CHANNEL_ID`（字串或陣列）。
7. 單元測試：mock JWKS 與金鑰，覆蓋成功/錯誤情境。
8. 品質檢查：ruff/pyright/pytest 需綠。
9. 文件：修正 `aud` 說明與 checklist 狀態。

## 8) Memory Hooks（Memento 風格核心提醒）
- 「aud ≠ LIFF ID」：請用 LINE Login Channel ID（數字）；別驗錯對象。
- 生產不能關簽名驗證：`ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION=True` 且必須有 `LINE_CHANNEL_ID`。
- `kid` 找不到？先刷新 JWKS 一次，再決定回錯；不要盲目失敗。
- JWKS 取用加快取：`timeout=5s`、TTL=24h；網路失敗時使用快取（stale-if-error）。
- 觀測：每個驗證錯誤要有明確原因，`sub` 長度不等於 33 要告警。
- 測試不要依賴真網路：mock `httpx.AsyncClient.get`，自建 RSA/EC 金鑰簽 token。
- 若要退路，`verify_line_access_token` 還在；但 ID Token 要達生產級安全標準。

## 9) 執行與驗證（參考指令）
- 安裝/檢查
  - `uv run ruff check .`
  - `uv run ruff format .`
  - `uv run pyright .`
  - `uv run pytest`

---
本文件面向 AI 開發代理，僅在必要處提供輕量程式碼/流程提示，避免過度綁死實作細節；若遇未預期情境，請優先遵循 Memory Hooks 與共識決策。
