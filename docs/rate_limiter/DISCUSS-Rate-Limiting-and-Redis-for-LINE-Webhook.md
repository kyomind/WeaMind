# 討論紀錄：LINE Webhook 的 1 秒冷卻（Rate Limiting）與 Redis 決策

本文整理我們針對 v1「1 秒冷卻」需求的討論，包含問題背景、候選方案、關鍵結論與共識、實作計畫、風險與後續方向，作為未來回顧決策依據。

## 背景與問題定義
- 目標：在 LINE Bot Webhook 情境中，針對相同行為主體（使用者、群組、聊天室）在 1 秒內只讓第一個請求被處理，其餘請求「靜默忽略」（不回覆、不呼叫 LINE API）。
- 動機：
  - LINE 平台不會替我們擋「快速連點」，所有點擊會透傳到 Webhook。
  - 降低濫用與誤觸成本，避免多餘外部 API 呼叫。
  - 與產品策略一致：V1 重基本防護，後續再做可觀測與優化。
- 現況：
  - Webhook 入口位於 `app/line/router.py` 的 `POST /line/webhook`；驗簽與事件分派由 LINE 官方 SDK（`WebhookHandler`）處理，實際事件邏輯在 `app/line/service.py`。
  - 專案目前未引入 Redis 套件或服務。

參考：`prd/Redis-and-Observability-Strategy.md`

## 需求要點（v1）
- 冷卻設計：動態窗口（處理期間鎖定）+ 5 秒超時。
- Key 維度：以來源識別子為準，優先順序 `userId > groupId > roomId`。
  - Key 命名建議：`processing:user:{id}`、`processing:group:{id}`、`processing:room:{id}`。
- 命中冷卻：簡單回應告知處理中（如：「⏳ 正在為您查詢天氣，請稍候...」），不進行天氣查詢。
- 套用事件：TextMessage、LocationMessage、Postback。
- 不套用：Follow/Unfollow（避免影響首次互動或狀態維護）。

## 候選方案與評估

### 方案 A：使用 FastAPI/Starlette 內建限流
- 結論：不可行。FastAPI 與 Starlette 均無內建 rate limiting 功能。

### 方案 B：第三方中介層限流
- 可用但不貼合需求。須大幅自訂以支援 LINE 事件的來源 ID 作為 key，且預設回 429 行為需改為靜默忽略。

### 方案 C（採用）：應用層冷卻（Handler 級）+ Redis 原子操作
- 做法：在各事件 handler 的最前面檢查處理狀態，若正在處理則回應告知等待。
- Redis 指令：`SETEX key 5 1`（設定處理中標記，5 秒超時）
  - 成功設定：代表未在處理 → 放行並執行天氣查詢，完成後刪除標記。
  - 已存在：代表處理中 → 回應「⏳ 正在為您查詢天氣，請稍候...」。
- 優點：
  - 與 LINE 驗簽與事件分派流程相容，改動面小、風險低。
  - 行為可精準定義（只針對目標事件、適當回應）。
  - 真正防止重複查詢，而非僅時間窗限制。
  - 提供良好的用戶體驗。
  - 容易擴充觀測（未來可加計數器/直方圖）。
- 注意：需 Redis 以支援多實例一致性。

### 方案 D：In-Memory 冷卻（僅單實例）
- 僅作為本地開發的 fallback，無法跨實例一致。

### 方案 E：Router 級前置冷卻（分派前）
- 可最早擋請求，但與官方 SDK 耦合較深，v1 不建議。

## 關鍵結論與共識
- FastAPI/Starlette 無「內建」 rate limit 能力。
- 為達到「以 LINE 來源 ID 為 key、跨實例一致、原子操作」的目標，Redis 在實務上是「必要」的（除非永遠單實例）。
- v1 決策：採「方案 C」——在 handler 層加入處理狀態檢查，若正在處理則回應告知等待；以 Redis `SETEX` 指令設定處理中標記（5 秒超時）。
- 套用範圍：Text/Location/Postback；Follow/Unfollow 不套用。
- 設計理念：動態窗口（處理期間鎖定）比固定時間窗更符合實際需求，簡單回應比靜默忽略提供更好的用戶體驗。

## v1 實作計畫（最小可行）
1. 設定
   - 在 `app/core/config.py` 新增：
     - `PROCESSING_LOCK_ENABLED`（預設 `true`）
     - `PROCESSING_LOCK_TIMEOUT_SECONDS`（預設 `5`）
     - `REDIS_URL`（必要；無則可選擇啟用 In-Memory fallback 僅供本地開發）
2. 模組
   - 新增 `app/core/processing_lock.py`：
     - 介面：`try_acquire_lock(key: str, timeout_seconds: int) -> bool`
     - 介面：`release_lock(key: str) -> None`
     - Redis 實作：`SETEX key timeout 1` + `DELETE key`
     - 可選 In-Memory fallback（本地/單實例）
     - `build_actor_key(source) -> str | None`：從 `event.source` 萃取 `userId/groupId/roomId`
3. 接點
   - 在 `app/line/service.py` 的三個 handler（Text/Location/Postback）：
     - 開始時嘗試取得鎖，失敗則回應「⏳ 正在為您查詢天氣，請稍候...」
     - 成功取得鎖則執行查詢，完成後釋放鎖（使用 try/finally）
   - Follow/Unfollow 不變。
4. 測試與驗收
   - 單元測試：第一次 `try_acquire_lock` 為 True；隨即第二次為 False；5 秒後為 True。
   - 基礎整合測試：模擬處理中的連續事件，第二次回應處理中訊息而非天氣結果。
5. 交付時間（人力評估）
   - 估時 2–3 小時；包含設計調整、程式實作與基本測試。

## 成功標準（驗收）
- 同一來源（`userId/groupId/roomId`）在處理期間的重複觸發：只有第一個事件被處理，其餘事件回應處理中訊息。
- 處理完成或 5 秒超時後，該來源可以正常發送新請求。
- 既有功能（地點解析、回覆、Postback 路由）不受影響。
- 測試、型別、Lint 皆通過。

## 風險與邊界
- 多事件同一 webhook：LINE 可能一次傳多個 events；以 handler 級處理鎖會出現「第一個放行、其餘回應處理中」的行為，符合預期。
- 缺少來源 ID：極少數事件若無 `userId/groupId/roomId`，則不套用處理鎖（保守放行並記錄 warn）。
- 多實例一致性：須以 Redis 確保一致；In-Memory 僅限本地單實例。
- UX 考量：處理中的回應訊息應簡潔友善，避免讓用戶感到困惑。
- 錯誤處理：需確保異常情況下能正確釋放鎖，避免永久鎖定（使用 try/finally 或超時機制）。

## 後續方向（v1.x / v2）
- v1.1：
  - 正式引入 `redis` 套件與 `docker compose` 的 Redis 服務，設定 `REDIS_URL`。
  - 加入基本健康檢查與連線錯誤降級策略（例如：Redis 故障時暫時放行或退回 In-Memory）。
- v2（可觀測性）：
  - 計量：`processing_lock_hits_total`（Counter）、`processing_duration_seconds`（Histogram）。
  - 匯出 Prometheus 指標，分析重複請求率、處理時間分布，支援後續資料驅動優化。
- 其他：
  - Router 級前置檢查（若未來要更早攔截）
  - 更細緻的鎖定策略（例如按事件類型差異化超時時間）
  - 針對特殊情況的白名單機制

## 參考與備註
- 專案內文：`prd/Redis-and-Observability-Strategy.md`
- FastAPI 官方文件：無內建限流；可使用第三方 ASGI 中介軟體。
- 第三方庫（僅備查）：`fastapi-limiter`、`starlette-limiter`、`slowapi`、`fastapi-cap`（皆偏向中介層，LINE Webhook 情境需要大幅自訂）。
