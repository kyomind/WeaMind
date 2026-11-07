# 修正 Webhook 事件結果計數

日期：2026-11-07。分支：`fix/webhook-event-outcomes`。

## 問題與修正

原先 dispatcher 只確認 callback 正常返回，便增加 success。回覆介面回傳 `SendResult.failed()`，或 handler 攔下 DB／查詢例外後返回，都會被誤認為成功。

新增 `EventOutcome`，將業務結果沿著 handler → callback → dispatcher → metrics 傳遞。SDK 的私有 `__invoke_func` 不回傳 callback 結果，所以適配層仍沿用 SDK 註冊解析，改為直接呼叫本專案單參數 callback，並驗證其回傳型別。

| 情境 | 結果 |
|---|---|
| 文字、位置或 PostBack 正常完成且回覆成功 | success +1 |
| 回覆介面回傳失敗 | error +1，error_type=`reply_error` |
| 查詢／DB／業務例外，即使錯誤提示送出成功 | error +1，error_type=`handler_error` |
| 缺少必要來源／reply token、非預期 message 型別 | handler_error |
| Follow DB 成功，有 token 時歡迎訊息亦須成功 | success；回覆失敗則 reply_error |
| Follow 無 reply token，但 DB 操作成功 | success，保留歡迎訊息可選的既有行為 |
| Unfollow 成功；或使用者本來就不存在 | success，視為已達成無啟用使用者的狀態 |
| 限流拒絕，但成功送出操作過頻提示 | success，視為成功處理限流政策 |
| 未支援／沒有 handler 的事件 | skipped，不增加 success 或 error；仍記 duration |

PostBack 執行層原本會吞掉查詢例外並回傳普通 recipe；現在由事件層統一轉成失敗結果並發送原有提示。預設地點的錯誤訊息仍為「查詢時發生錯誤，請稍後再試。」。

正常的無資料、未設地點、無效查詢等可預期業務回覆，在回覆成功時仍視為成功。Query History 的 best-effort savepoint 行為維持原狀。未攔截例外仍遵循既有批次中止行為；這次沒有加入批次隔離、去重、重試或持久化排程。

## 驗證

- 正式回歸測試：`tests/line/test_event_outcomes.py`，15 個案例，使用真實 router、簽章驗證、SDK parse、註冊 callback 與 dispatch；外部查詢／DB／回覆由測試替身隔離。
- 將其中 14 個成功／失敗案例放回基準 `6e2263899087520c5b4f43e31fe0573b80b65690` 的暫存 checkout：**9 failed、5 passed**。修正版 15 個案例全部通過，新增的一個案例確認未處理事件為 skipped。
- 完整測試：**313 passed**，coverage 96%。這是本機結果，並非真實 LINE、PostgreSQL、Redis 或部署驗證。
- `uv run --offline ruff check .`、`uv run --offline ruff format --check .`、`uv run --offline pyright .`、`git diff --check` 全部通過；執行時使用 `UV_CACHE_DIR=/tmp/weamind-uv-cache`。
- 更新診斷腳本後 exit 0：回覆失敗與 Follow DB failure 都是 success=0、error=1；重送仍執行兩次、未攔截例外仍中止批次。

初版稽核的 Follow 探針缺少 `follow.isUnblocked`，實際被 SDK 當成 unknown event；已在原報告補上證據更正，並用有效事件在修正前後重新驗證。舊版確實存在 Follow DB failure 誤計成功，但初版探針不足以證明它。

## 相容性與工作狀態

Prometheus metric 名稱不變，新增低基數 error_type `reply_error`。如果外部 dashboard／告警只篩選 `handler_error`，需確認是否應納入此分類；本次沒有讀寫外部監控設定。既有指標是累積值，修正不會回填歷史計數。default handler 由誤計 success 改成 skipped，因此 received 不應直接等同 success + error。

本次修正與本機檢查已完成；本紀錄隨修正、測試與稽核證據一併提交，尚未 push、建立 PR 或部署。後續可獨立處理批次隔離，並在需要時檢查監控查詢；不屬於本次修正的未完成實作。
