# DONE — LINE ID Token 簽名與 Audience 驗證：實作紀錄

狀態：已完成（分支 `feature/jwt-verification` 已綠，含測試/型別/靜態檢查）

本文件整理本次導入「LINE ID Token 簽名驗證與 audience 驗證」的完整實作脈絡，包含採用的技術方案、關鍵決策、遇到的問題與解法、核心架構與測試策略，供後續開發者理解與維護。

---

## 背景與目標
- 既有 `verify_line_id_token` 僅做解碼與基本欄位檢查（`alg`/`iss`/`exp`/`sub`），缺少「簽名驗證」與「audience 驗證」。
- 風險：惡意者可偽造 ID Token（無法確認 token 確實由 LINE 簽發，且是否簽發給我方應用）。
- 目標：
  - 使用 LINE JWKS 完成 RS256/ES256 的數位簽名驗證。
  - 驗證 `iss=https://access.line.me`。
  - 驗證 `aud` 等於我方 LINE Login Channel ID（注意：不是 LIFF ID）。
  - 加入生產環境護欄與健全的錯誤處理/快取策略。

對應規格文件：`docs/AGENT-JWT-Verification.md`

---

## 變更總覽
- 設定（`app/core/config.py`）
  - 新增 `LINE_CHANNEL_ID: str | None = None`
  - 新增 `ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION: bool = True`
- 驗證實作（`app/core/auth.py`）
  - 完整簽名驗證（PyJWT + cryptography），僅接受 `RS256`/`ES256`。
  - JWKS 取得與記憶體快取（TTL 24h），支援 `kid` 輪替：未命中會刷新一次。
  - audience/issuer/過期（含 5 分鐘 leeway）檢查；`sub` 長度異常告警。
  - 生產護欄：`ENV=production` 時，強制需要 `LINE_CHANNEL_ID` 且簽名驗證必須啟用。
  - 網路失敗策略：有快取走 stale，無快取回 503。
- 相依套件（`pyproject.toml`）
  - 新增 `cryptography>=43.0.3`（PyJWT 驗簽所需）。
- 測試（`tests/`）
  - 保留既有測試：在 `tests/conftest.py` 設定 `ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION=false`，確保舊有「無簽名 token」測試仍可運行（過渡期）。
  - 新增 `tests/core/test_auth_id_token_signature.py`：
    - RSA/EC 真簽名成功路徑。
    - aud 不符、`kid` 缺失等失敗路徑。
    - 測試使用記憶體直灌 JWKS，避免網路依賴；若缺 `cryptography` 會自動 skip。
- 文件更新（`docs/seed/Security-Assessment-and-Checklist.md`）
  - 將 JWT 簽名與 audience 驗證標記為「已完成」，並補充生產環境變數說明。

---

## 技術方案與核心設計

### 1) `verify_line_id_token` 核心流程
- 解析 JWT header，拒絕非 `RS256`/`ES256`。
- 讀取 `kid`，透過 JWKS 快取取得對應公鑰：
  - 若快取未命中或 `kid` 找不到：刷新 JWKS 一次；仍找不到則 401。
- 呼叫 `jwt.decode(...)` 完成簽名與欄位驗證：
  - `algorithms=["RS256","ES256"]`
  - `issuer="https://access.line.me"`
  - `audience=settings.LINE_CHANNEL_ID`（若有設定）
  - `leeway=300`（允許 5 分鐘 clock skew）
  - 若未設定 `LINE_CHANNEL_ID`，以 `options={"verify_aud": False}` 關閉 `aud` 驗證。
- 成功後回傳 `payload["sub"]` 作為 `line_user_id`，並對異常長度（非 33）記錄告警。

當 `settings.ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION=False` 時（僅限開發/測試）：
- 降級為「輕量檢查」：格式/alg、`exp`（+5 分鐘容忍）、`iss`、（若存在）`aud`、`sub`。
- 不做簽名驗證，便於保留既有無簽名測試與本地開發。

### 2) JWKS 快取
- 來源：`https://api.line.me/oauth2/v2.1/certs`。
- 快取：
  - 全域記憶體 `_JWKS_CACHE: tuple[dict[str, dict], float] | None`。
  - TTL 24 小時；逾期或 `force_refresh=True` 時會刷新。
- 失敗策略：
  - 取得失敗且有舊快取 → 回傳 stale（記錄警告）。
  - 取得失敗且無快取 → 503（外部依賴失效）。

### 3) 生產環境護欄
- 若 `ENV=production`：
  - `ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION` 必須為 `True`。
  - `LINE_CHANNEL_ID` 必須設定。
  - 否則直接回 500，避免不安全設定誤上線。

### 4) 錯誤對應
- 401：格式錯誤、演算法不支援、簽名無效、過期、issuer/audience 不符、`kid` 缺失或未知。
- 503：JWKS 取得失敗且無可用快取。

---

## 關鍵決策與理由
- 使用 PyJWT + cryptography：
  - 社群採用度高，支援 RS/EC 演算法與 JWK 解析，整合成本低。
- JWKS 記憶體快取 + stale-if-error：
  - 降低對外部端點的依賴與延遲；短暫故障時維持服務能力。
- `kid` 未命中時刷新一次：
  - 因應金鑰輪替；避免過度刷新造成不必要的外呼。
- `verify_aud` 依設定決定：
  - 若 `LINE_CHANNEL_ID` 未設定則不驗 `aud`（開發/測試彈性）。
- 生產環境強制簽名驗證與 `LINE_CHANNEL_ID`：
  - 安全底線，不允許部署錯誤配置。
- 測試環境暫時關閉簽名驗證：
  - 兼容既有無簽名測試；另增真簽名測試，以漸進式過渡。

---

## 遇到問題與解法
1) jwt.algorithms 型別/存取問題
- 症狀：靜態分析在直接 `import jwt.algorithms` 或全域匯入時會有解析/型別提示問題。
- 作法：在 `_public_key_from_jwk` 內部以「區域匯入」方式 `from jwt import algorithms as jwt_algorithms`，避免匯入期依賴問題，也使得單元測試載入更健壯。

2) `cryptography` 相依與測試環境
- 症狀：測試主機若缺 `cryptography` 會造成匯入錯誤。
- 作法：
  - `pyproject.toml` 正式加入 `cryptography` 依賴。
  - 新增簽名測試時，使用 `importlib.util.find_spec("cryptography")` 檢測，不存在則整個檔案 `pytest.skip`，避免在 CI 或極端環境下中斷。

3) 風格規則（Ruff D213、行長）
- 症狀：多行 docstring 摘要行位置、過長行報警。
- 作法：調整 docstring 標準位置、拆行。

4) 型別檢查（Pyright）
- 症狀：測試 helper 的 `key` 參數型別過窄或過寬導致錯誤。
- 作法：使用 `Any` 並以 `# noqa: ANN401` 註解，符合測試彈性與型別檢查。

5) 舊測試相容
- 症狀：既有測試使用「無簽名 token」策略。
- 作法：測試環境設 `ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION=false`，保留原行為；另新增含真簽名的測試檔逐步涵蓋安全路徑。

---

## 程式碼核心架構與關鍵邏輯
- `app/core/auth.py`
  - `verify_line_id_token(token: str) -> str`
    - 契約：回傳 `sub`（LINE user id）。
    - 行為：
      - 生產環境強制簽名與 `aud` 驗證；開發/測試可關閉簽名改走輕量檢查。
      - 錯誤分類：401（驗證不通過）、503（外部依賴失效）。
  - `_load_jwks_from_network() -> dict[str, dict]`
    - 以 5 秒 timeout 讀取 JWKS，並轉為以 `kid` 為 key 的 map。
  - `_get_cached_jwks(force_refresh: bool=False, allow_stale_on_error: bool=True)`
    - 記憶體快取（TTL 24h），支援 stale-if-error。
  - `_public_key_from_jwk(jwk: dict) -> Any`
    - 解析 RSA/EC JWK 為可供 PyJWT 使用的 public key。
  - `_get_signing_key_for_kid(kid: str) -> Any`
    - 先查快取，`kid` 未命中則刷新一次；失敗回 401；JWK 解析失敗回 503。

資料形狀：
- `_JWKS_CACHE: tuple[dict[str, dict], float] | None`
  - 第 1 元素：`{kid: jwk}`
  - 第 2 元素：`fetched_at`（UNIX timestamp）

邊界情境：
- `kid` 缺失或完全未知。
- JWKS 端點短暫不可用（使用舊快取）。
- `aud` 為字串或陣列（都可驗）。
- 時間偏移（允許 300 秒）。

---

## 測試策略與覆蓋
- 既有測試（不驗簽名）：
  - `tests/core/test_auth.py`（格式、alg、過期、issuer、sub 缺失、等）
- 新增測試（驗簽）：
  - `tests/core/test_auth_id_token_signature.py`
    - 成功：RSA 與 EC 各一（含 `aud` 驗證）。
    - 失敗：`aud` 不符、`kid` 缺失。
    - 技巧：以記憶體直灌 `_JWKS_CACHE` 模擬 JWKS；必要時自動跳過（無 `cryptography`）。

品質門檻（本次執行紀錄）：
- Lint：`uv run ruff check .` → PASS
- Type：`uv run pyright .` → PASS
- Test：`uv run pytest -q` → 190 passed
- Coverage（重點）：總體約 90%；`app/core/auth.py` 約 63%（主要未覆蓋：JWKS 網路失敗/刷新分支，可後續增補 mock 測試）

---

## 環境變數與執行方式
- 生產環境必要變數：
  ```bash
  export ENV=production
  export LINE_CHANNEL_ID=<你的 LINE Login Channel ID>  # 純數字
  export ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION=true
  ```
- 開發/測試（可暫時關閉簽名驗證，便於沿用舊測試或本地除錯）：
  ```bash
  export ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION=false
  # （未設定 LINE_CHANNEL_ID 時將自動略過 aud 驗證）
  ```
- 常用指令：
  ```bash
  uv sync
  uv run ruff check .
  uv run ruff format .
  uv run pyright .
  uv run pytest -q
  ```

---

## 風險與後續工作
- 風險：
  - JWKS 端點長時間不可用時，stale 快取可能過舊（預設 24h）。
  - `app/core/auth.py` 的網路/快取分支覆蓋率仍可提升。
- 後續建議：
  - 增補測試：
    - JWKS 取得失敗有舊快取（stale-if-error）。
    - `kid` 未命中 → 刷新仍未命中。
  - 加入度量：對 401 類型細分（簽名、aud、issuer、過期、kid），便於營運監控。
  - 視需求調整 JWKS TTL 或引入持久化快取（例如 Redis），以兼顧可用性與新鮮度。

---

## 變更檔案清單
- `app/core/config.py`：新增 `LINE_CHANNEL_ID`、`ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION`。
- `app/core/auth.py`：`verify_line_id_token` 全面升級；新增 JWKS 快取與相關 helper。
- `pyproject.toml`：新增 `cryptography` 依賴。
- `tests/conftest.py`：測試環境關閉簽名驗證。
- `tests/core/test_auth_id_token_signature.py`：新增 RSA/EC 驗簽與異常案例測試。
- `docs/seed/Security-Assessment-and-Checklist.md`：更新狀態與設定。

---

## 附：`verify_line_id_token` 契約摘要
- 輸入：`token: str`
- 成功：`sub: str`（LINE user id）
- 驗證：`alg∈{RS256,ES256}`、`iss`、`exp`（leeway 300s）、`aud`（若設定）、簽名（啟用時）
- 錯誤：401（驗證不通過）、503（JWKS 端點失效且無快取）

> 備註：本功能已與現有 `verify_line_access_token` 相互獨立，未更動其流程。

---

以上。
