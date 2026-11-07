# Webhook 隱式狀態機試行

基準：`6e2263899087520c5b4f43e31fe0573b80b65690`。日期：2026-11-07。

後續更新：成功／失敗計數已在工作分支修正，見 `FIX-2026-11-07-webhook-event-outcomes.md`。以下保留修正前分析；探針已改為驗證修正後結果。

證據更正：初版 Follow 探針缺少 `follow.isUnblocked`，SDK 將它當成 unknown event，並未進入 Follow handler，因此當時的 Follow 動態重現描述不成立。後續已補正資料，將正式回歸測試放回上述基準版，確認 Follow DB failure 確實仍被計為成功。修正版同一案例通過，應以後續回歸測試作為動態證據。

依據使用者提供的〈Prompt 效用評估〉，實驗「從實作反推狀態與不變量，再驗證無效狀態是否可達」。匯出檔不含原始 prompt 圖片，因此本次依其方法說明執行。範圍限定 webhook 接收、事件 dispatch、回覆結果、Redis TTL 限流與 Follow 狀態；不是全 repo 稽核。

## 結果

找到 **1 組已重現的可觀測性缺陷（兩條觸發路徑）**，另記錄 3 個設計／容錯限制。沒有把 TTL 到期或 fail-open 當成互斥鎖缺陷。此次只新增報告及重現腳本，未修改產品程式、提交或部署。

## 狀態與不變量

以下將「現行轉換」與「應滿足的語意」分開，避免把推導出的需求冒充既有規格。

| 子系統 | 現行狀態／轉換 | 檢查的不變量與結果 |
|---|---|---|
| 接收 | 未驗證 → 拒絕，或已驗證 → 排入記憶體背景工作 → HTTP 200 | 無效簽章不可進業務處理；既有測試通過。200 只代表接收，不代表工作完成 |
| 事件 | 待處理 → dispatch → 正常返回／拋錯 | 正常返回不一定等於業務成功；這是本次確認的缺口 |
| 回覆 | 未嘗試 → `SendResult.sent()`／`SendResult.failed(...)` | 若 success 指標表示事件成功，明確 failed 不應被算成 success；目前違反 |
| Follow | 無使用者／停用 → 建立／啟用；DB 例外 → 記錄 log 並返回 | DB 失敗不得被誤認為啟用成功；目前外層計數違反，未宣稱資料庫資料已被錯誤寫入 |
| 限流 | key 不存在 → SET NX EX 成功 → key 存在 → TTL 到期 | Redis 正常且 key 尚存時拒絕新請求；不保證整段工作互斥，也不保證事件只處理一次 |
| 降級 | Redis 不可用／停用 → 直接放行 | 可用性優先是明確設計；不視為缺陷 |
| 重送 | 相同 webhookEventId → 再次 parse／dispatch | 現行沒有事件去重，不具有 exactly-once 保證；沒有找到此保證的既有承諾 |

## 已確認：失敗事件仍增加成功計數

優先級：P2，影響監控可信度與故障定位。

來源：`app/line/service.py:97` 以 dispatcher 正常返回作為成功依據；`app/line/sdk_dispatch.py:35` 只確認 callback 已返回，不收集業務結果。`app/line/service.py:141` 忽略 `messenger.reply()` 的 `SendResult`；Follow 的 `app/line/service.py:208` 則將資料庫例外記錄後吞掉。`app/line/messaging.py` 的 `SendResult.failed()` 是正式介面，並非假設。

兩個確定性重現：

1. 真實 router、簽章驗證、SDK parse 和註冊 handler，替換外部回覆邊界，使其回傳 `SendResult.failed(INVALID_REQUEST)`。結果：success +1，error +0。
2. 相同真實路徑，Follow 在開啟 DB session 時注入例外。結果：HTTP 200，success +1，error +0。

`docs/line-webhook-metrics-implementation-report.md` 描述的是事件成功／失敗計數，而不只是 callback 是否返回，因此這是可確認的指標語意缺陷。Unfollow 有相同攔截結構，但本次動態重現只涵蓋 Follow。天氣查詢失敗後成功送出錯誤提示是否算成功，另有產品語意選擇，不併入已確認項目。

建議修復分組：先讓 handler 回傳明確處理結果，讓 SDK 適配層把結果交給 metrics 邊界；保留外部錯誤的正常封裝，不為了計數而把所有失敗改為拋例外。至少新增「回覆 failed 不計 success」與「Follow DB failure 計 error」兩個回歸測試。若決定 success 只表示 callback 返回，則需改名並另設業務結果指標。

## 設計與容錯限制

### 批次中止：注入未攔截例外可重現

`app/line/service.py:102-106` 在逐事件迴圈內重新拋錯，使剩餘事件不被處理；router 背景工作攔下例外，HTTP 仍為 200。兩筆文字事件中，第一筆回覆被注入 `RuntimeError`，只進入一次查詢，第二筆未執行。

這個轉換也被既有 `test_process_webhook_events_stops_after_failing_event` 明確固定。正式 messenger 會將常見 API／網路錯誤封裝為 SendResult，所以本例證明的是「未攔截例外的影響範圍」，不是常見 API 錯誤一定會丟失後續事件。若要改善，應先決定批次內事件是否獨立，再改成每筆隔離並更新原測試；不列為新發現的正常路徑缺陷。

### 事件重送：沒有持久化去重

用相同 webhookEventId 送入兩次，第二次標記 `isRedelivery=true`。觀察到 query 呼叫兩次、reply 嘗試兩次。此結果證明重入業務流程，**不代表 LINE 接受兩次回覆，也不代表實際 DB 寫入兩次**：這兩個外部邊界在實驗中被替換。

`app/weather/workflow.py` 另顯示查詢包含 history 寫入；若要保證重送不增加副作用，需要一起設計事件 claim、完成狀態與失敗恢復。單加一個短 TTL key 無法提供該保證。現階段列為交付語意限制，不直接引入 queue 或去重資料表。

### Fast ACK 與 TTL 限流的保證範圍

背景工作沒有持久化排程或應用層重試。ACK 後程序中止可能遺失未完成工作；本次沒有殺程序或做真實平台重送測試，這是原始碼所呈現的架構限制。

TTL 的可行交錯：A 在 t=0 取得 key，工作尚未結束；TTL 到期後 B 取得 key，A、B 可重疊。這符合 `docs/rate_limiter/DONE-Redis-Lock-1sec-Timeout-Implementation.md` 刻意移除手動釋放、改成時間窗限流的決策。**本次沒有使用真實 Redis 或執行多程序並發測試**，只確認實作與該設計一致；不將推導交錯宣稱為 runtime 證明。

## 重現與驗證

從 repo 根目錄執行：

```sh
UV_CACHE_DIR=/tmp/weamind-uv-cache uv run --offline python docs/experiments/webhook_state_probe.py
UV_CACHE_DIR=/tmp/weamind-uv-cache uv run --offline pytest tests/core/test_processing_lock.py tests/line/test_metrics.py tests/line/test_webhook.py -q --tb=short
```

實測：重現腳本 exit 0；既有測試 **37 passed**。腳本使用 SQLite 記憶體設定、假憑證及 mock 業務邊界，不連正式 Redis、DB 或 LINE。注入例外時預期會印出 error log。

```text
reply_rejected: success_events=1, error_events=0
batch_failure: HTTP=200, query_calls=1/2, error_events=1
follow_db_failure: HTTP=200, success_events=1, error_events=0
same_event_replay: query_calls=2, reply_attempts=2
```

腳本斷言的是目前觀察到的缺陷／限制，並非期望行為的 regression suite；未放入正式 tests。修復後應調整或移除此腳本的舊觀察斷言。TestClient 會等待背景工作，不使用本次結果證明實際網路 ACK 延遲。

這輪方法的效用是把「收到、正常返回、業務成功、回覆成功」四種狀態分開，找出既有全綠測試未涵蓋的結果傳遞缺口；不是製造大量並發 bug 清單。
