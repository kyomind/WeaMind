# AGENT 規格：LINE Webhook「處理中鎖」（鎖定上限 5 秒）

## 快速摘要（給 AI agent）
- 目標：同一使用者同時間只處理一次，其餘回覆「處理中」。
- 鎖鍵：`processing:user:{userId}`；TTL 固定 5s。
- 流程：handler 開頭嘗試鎖 → 鎖已存在就回覆提示，不進入查詢 → 成功則執行查詢，`finally` 主動釋放；若異常最多等 TTL 自解。
- 邊界：Redis 失敗放行；不使用 In-Memory fallback；不採 nonce+Lua；不做 i18n。
- 隱私：log 不得記錄個資（含 ID）；可觀測性以不含個資的計數器/直方圖為主（後續實作）。

本文件提供給 AI agent（如 Claude Code、Copilot）作為本次功能的實作依據：聚焦 Why / What / How、限制與關鍵決策，僅在必要處附上介面與偽碼。

## Why（要解決的問題）
- LINE Bot Webhook 在極短時間內可能收到同一使用者的多次觸發：
  - 造成重複外部 API 呼叫（成本/延遲）
  - 導致重複回覆（壞體驗）
  - 多實例部署下，若無共享狀態，就無法一致地避免重複處理
- 目標：同一使用者在「處理期間」只放行第一個事件；其餘事件回覆簡短的「處理中」訊息，不進行實際查詢。

## What（要實作的功能）
- 套用於三種事件：`TextMessage`、`LocationMessage`、`Postback`。
- Handler 開頭嘗試取得「處理中鎖」：
  - 取得失敗：立即回覆 `"⏳ 正在為您查詢天氣，請稍候..."`，不進入查詢流程。
  - 取得成功：執行原有查詢流程；處理完成後釋放鎖（以 finally 保證），或由 TTL 自動到期。
- `Follow/Unfollow` 不套用此機制。
- 鎖 key 以使用者為單位（僅 `userId`）。
- 鎖控策略：動態視處理狀態鎖定，TTL 上限 5 秒（本次固定）。

## How（技術方案與實作方式）

### 採用方案
- 應用層（Handler 級）鎖控 + Redis 原子操作，以確保跨實例一致性與低耦合。
- 關鍵指令：`SET key value EX <seconds> NX`（僅在 key 不存在時設定並帶 TTL）。

### 鎖鍵與 TTL
- Key 命名：
  - `processing:user:{userId}`
- 預設 TTL：`5` 秒（本次固定使用）。

### 設定項（新增於 `app/core/config.py`）
- `PROCESSING_LOCK_ENABLED: bool = true`
- `PROCESSING_LOCK_TIMEOUT_SECONDS: int = 5`
- `REDIS_URL: str | None`（固定使用 `redis://redis:6379/0`；可視環境覆寫）

### 模組（新增 `app/core/processing_lock.py`）
- 介面合約（僅示意型別）：
  - `def try_acquire_lock(key: str, timeout_seconds: int) -> bool`
  - `def release_lock(key: str) -> None`
  - `def build_actor_key(source: Any) -> str | None`（由 LINE 事件 `source` 萃取 `userId`，找不到則回 `None`）
- Redis 實作：
  - 取得鎖：`SET key 1 EX <timeout> NX` → True/False
  - 釋放鎖：`DEL key`（best-effort；finally 釋放）
- 失敗策略：Redis 連線/操作失敗時「放行」（不鎖），不啟用 In-Memory fallback（本次 v1 不納入）。

### Handler 接入點（`app/line/service.py`）
- 在 Text/Location/Postback 的 handler 開頭加入：
  1) `key = build_actor_key(event.source)`；若 `None` → 不套鎖（保守放行，記錄 warn）。
  2) `try_acquire_lock(key, PROCESSING_LOCK_TIMEOUT_SECONDS)`；若失敗 → 回覆「處理中」，return。
  3) 若成功 → `try: <原查詢流程> finally: release_lock(key)`（處理完成需主動釋放；如異常則依 TTL 最多 5s）。

### 偽碼（必要即可）
```python
key = build_actor_key(event.source)
if key and PROCESSING_LOCK_ENABLED:
    if not try_acquire_lock(key, PROCESSING_LOCK_TIMEOUT_SECONDS):
        reply_text("⏳ 正在為您查詢天氣，請稍候...")
        return
    try:
        handle_weather_query(event)
    finally:
        release_lock(key)
else:
    handle_weather_query(event)
```

### 訊息策略
- 鎖命中時僅回覆：`"⏳ 正在為您查詢天氣，請稍候..."`。
- 不呼叫外部 API、不進入查詢流程，避免重複成本。

## 限制與考量
- 多事件同一 webhook：LINE 可能一次傳多個 events；以 handler 級鎖控會呈現「第一個放行，其餘回覆處理中」，符合需求。
 - 缺失使用者 ID：未取得 `userId` 時，不套用鎖（保守放行），同時記錄 `warn` 日誌（不得包含個資）。
 - 例外狀況：`finally` 確保釋放鎖；TTL 作為最後保險避免永久鎖定（最多 5s）。
 - 多實例一致性：需 Redis；v1 不採用 In-Memory fallback。
 - Redis 故障：放行（不鎖）；後續可加健康檢查與告警（不在本次範圍）。
 - 安全性與隱私：鍵名以固定前綴 + `userId` 組合；log 不得記錄個資（含 ID）。
- 效能：鎖操作 O(1)；建議安裝 `redis[hiredis]` 以優化解析。

### 隱私與可觀測性建議（不含個資）
- 日誌：
  - 僅記錄動作結果（如 acquired/missed/released）、事件類型與流程狀態，不記錄 `userId` 或任何個資。
  - 可加入請求內部 correlation id（隨機、短期、不可回溯到個人）。
- 指標（v1 建檔，v1.1 實作）：
  - `processing_lock_acquire_total`（Counter）
  - `processing_lock_miss_total`（Counter）
  - `processing_lock_release_total`（Counter）
  - `processing_duration_seconds`（Histogram）
  - 不以 `userId` 當 label，僅以事件類型或結果分類。

## 重要共識與決策（自討論彙整）
- 採 Handler 級鎖控，與 LINE SDK 分派流程相容，改動小、風險低。
- 鎖 key 維度以使用者識別（僅 `userId`）。
- 套用事件：Text/Location/Postback；不套用：Follow/Unfollow。
- 鎖控策略：動態視處理狀態鎖定，上限 5 秒；命中鎖回簡短「處理中」訊息。
- 原子性：使用 `SET ... EX <ttl> NX`（較 `SETEX` 更能保證「僅於不存在時設定」）。
- 可觀測性（後續）：加入計數器與直方圖、Prometheus 匯出。
- Redis 故障：放行（不鎖）。
- 安全刪鎖（nonce + Lua）：本次不採用。
- 不需要 E2E 批次投遞情境測試（本次省略）。

## 開發檢核清單（務必逐項確認）
- 鎖鍵與 TTL：
  - [ ] 只使用 `userId` 作為鍵：`processing:user:{userId}`
  - [ ] TTL 固定 5 秒（設定 `PROCESSING_LOCK_TIMEOUT_SECONDS=5`）
- 介面與指令：
  - [ ] 取得鎖使用 `SET key 1 EX <ttl> NX`，不可覆蓋既有鎖
  - [ ] 釋放鎖於 `finally` 使用 `DEL key`（以處理完成為準）
- 套用範圍：
  - [ ] 僅 Text/Location/Postback 套用鎖
  - [ ] Follow/Unfollow 不套用
- 失敗與降級：
  - [ ] Redis 連線/操作失敗時「放行」（不鎖）
  - [ ] 不使用 In-Memory fallback（v1 不納入）
- 文案與國際化：
  - [ ] 命中鎖回覆文案固定：`⏳ 正在為您查詢天氣，請稍候...`
  - [ ] 不進行 i18n
- 隱私與日誌：
  - [ ] log 不得記錄個資（含 `userId`）；僅記錄 acquired/missed/released 狀態
  - [ ] 可選加入非個資的 correlation id（隨機、短期）
- 可觀測性（規劃，非本次落地）：
  - [ ] `processing_lock_acquire_total`、`processing_lock_miss_total`、`processing_lock_release_total`、`processing_duration_seconds`
  - [ ] 監控指標不以 `userId` 作為 label

## 測試與驗收標準
- 單元測試：
  - 同一 key：首次 `try_acquire_lock` → True；隨後立即再呼叫 → False；等待 TTL 後 → True。
  - `build_actor_key` 對不同 `source` 類型產生正確鍵名；缺失 ID → `None`。
- 整合測試：
  - 連續事件：第一個事件進入實際處理；第二個事件回覆「處理中」。
  - `Follow/Unfollow` 流程不受影響。
- 成功標準：
  - 處理期間重複觸發，僅第一個被處理，其餘回覆處理中。
  - 完成或超時後，來源可正常發送新請求。
  - 既有功能（地點解析、回覆、Postback 路由）不受影響。
  - `uv run pytest`、`uv run ruff check .`、`uv run pyright .` 均通過。

## 實作路徑與檔案
- `app/core/config.py`：新增三個設定項與預設值。
- `app/core/processing_lock.py`：鎖實作（Redis + 可選 In-Memory fallback）。
- `app/line/service.py`：在 Text/Location/Postback 的 handler 入口導入鎖邏輯。

## 部署與環境
- 依專案慣例使用 `uv`。
- 依賴：`redis[hiredis]` 已安裝。
- 環境變數：
  - `REDIS_URL`（固定：`redis://redis:6379/0`，必要時可依環境覆寫）
  - `PROCESSING_LOCK_ENABLED=true`
  - `PROCESSING_LOCK_TIMEOUT_SECONDS=5`
- Docker Compose：
  - 若 dev/prod 設定無差異，建議加入「共用」`docker-compose.yml`。
  - 如 dev/prod 需不同設定，則分別在 `docker-compose.dev.yml` 與 `docker-compose.prod.yml` 加入 `redis` 服務。

## Memory Hooks（給未來的 AI agent）
- 一定用 `SET key 1 EX <ttl> NX` 取得鎖，避免覆蓋既有鎖。
- `try/finally` 釋放鎖；TTL 是最後保險。
- 鍵名只使用 `userId`：`processing:user:{userId}`。
- Follow/Unfollow 不走鎖；Text/Location/Postback 要鎖。
- 命中鎖時只回「處理中」，不要呼叫外部 API。
- 保持型別標註與 docstring；用 `uv run` 跑測試與 Lint。
- Redis 失敗放行（不鎖）；不採用 In-Memory fallback；不採用 nonce + Lua 安全刪鎖（本次）。

---

如需擴充（觀測性、降級策略、Router 級前置攔截），請建立後續 `v1.x / v2` 任務。
