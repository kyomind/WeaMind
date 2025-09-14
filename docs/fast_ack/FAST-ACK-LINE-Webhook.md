# Fast ACK for LINE Webhook

日期: 2025-09-14
狀態: 已實作並測試 (在分支 `feature/fast-webhook-ack`)
作者: WeaMind 团队

---

## 背景與目標
- 症狀：併發時段出現 `HTTP 400 {"message":"Invalid reply token"}`，且錯誤呈「短時間連發 + 約 1 分鐘後再現」的節奏，疑似 LINE redelivery。
- 根因推論：webhook 回應 `200 OK` 並非第一時間回，而是等待 handler 完整處理（包含對 LINE 的 Reply API、Redis 鎖、外部 I/O）才回，導致超時與重送風險升高。
- 目標：讓 webhook 在「最短可回覆時」立即 ACK (`200 OK`)，把慢操作移出同步路徑，降低 redelivery 與 `replyToken` 逾時/重用風險。

---

## 設計原則
1. 先驗簽、再 ACK、後處理
   - 同步只做最輕量且必要的檢查（`content-type`、簽章驗證）。
   - 立即回 `200 OK`（Fast ACK）。
   - 真正業務處理放到背景任務執行，不阻塞 ACK。
2. 安全優先
   - 簽章驗證不通過即回 `400`，避免對無效請求回 `200`。
3. 漸進增強
   - 先落地 Fast ACK，觀察 redelivery/400 是否下降。
   - 後續再補冪等防護（redelivery 去重、replyToken 一次性保護等）。

---

## 實作摘要
- 檔案: `app/line/router.py`
- 主要變更：
  - 同步驗證 `content-type` 與簽章（以 HMAC-SHA256 計算與 `compare_digest` 比對）。
  - 立即回傳 `{"message": "OK"}` 以 ACK。
  - 使用 FastAPI `BackgroundTasks` 將 `webhook_handler.handle(body, signature)` 丟到背景執行。
  - 背景例外以 log 記錄，不影響 ACK。

程式骨架：
```python
# 1) validate content-type
# 2) read body
# 3) verify signature (HMAC)
# 4) log reception (no full body)
# 5) background_tasks.add_task(webhook_handler.handle, body_as_text, x_line_signature)
# 6) return {"message": "OK"}
```

---

## 為何同步驗簽
- 官方與安全常識建議：簽章不合法應回 `400`，不能對無效請求回 `200`。
- 驗簽成本極低（HMAC-SHA256），不會顯著影響 ACK 時間。
- 若將驗簽放背景：
  - 對不合法請求也回了 `200`（LINE不重送），且還啟動不必要的背景工作，違背安全與資源節約。

---

## 觀測與驗收
- 觀測點：
  - Webhook 入口：`Received LINE webhook: length=...` 與存取日誌 `POST /line/webhook ... 200` 的時間差應顯著縮短。
  - 回覆階段：`x-line-request-id`（若可取得）應記錄於回覆 log，便於跨端追蹤。
- 驗收判準：
  - `Invalid reply token` 錯誤次數明顯下降或趨近於 0。
  - 日誌顯示背景任務正常處理；若 redelivery 存在，未再觸發第二次 `reply_message` 導致 400。

---

## 後續建議（非本次改動）
1. Redelivery 去重
   - 若 SDK 或事件包含 `deliveryContext.isRedelivery`，在事件最外層直接略過回覆並記錄 `INFO`。
2. `replyToken` 一次性保護
   - 以 Redis `SETNX` 短 TTL（~70s）保護，首個持有者才可回覆；後續相同 token 嘗試一律略過。
3. 例外處理策略
   - `except` 區塊不再用同一 `replyToken` 補回覆，只記錄錯誤上下文，避免製造第二次回覆。
4. 快速 ACK 一致化
   - 將所有 handler 的慢操作（外部 I/O/查詢）解耦至背景/佇列；需要互動的結果用 Push API（以 `userId`）發送。

---

## 風險與相容性
- 相容性：路由合約未變（`POST /line/webhook` 返回 `{"message": "OK"}`）。
- 風險：背景任務中的例外不會影響 ACK，需要透過 log/監控來及時發現與告警。
- 效能：驗簽為 O(n) HMAC 計算，但 n 很小（webhook 載荷通常數 KB），可忽略。

---

## 變更清單
- `app/line/router.py`：新增 `BackgroundTasks`、同步 HMAC 驗簽、立即 ACK、背景處理。

---

## 分支資訊
- 分支：`feature/fast-webhook-ack`
- 建議 PR 標題：`feat: fast ACK for LINE webhook (defer handling to background)`
- 建議檢查項：
  - [ ] 測試環境實際觀測 ACK 延遲顯著下降
  - [ ] `Invalid reply token` 錯誤趨勢下降
  - [ ] 背景例外是否有足夠 log 與告警
