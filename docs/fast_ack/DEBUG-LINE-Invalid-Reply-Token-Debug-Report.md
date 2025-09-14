# DEBUG 報告：`Invalid reply token` 週期性錯誤（調查與推論）

- 日期：2025-09-14
- 狀態：調查中（不改碼觀察優先）
- 相關：`docs/DEBUG-LINE-Invalid-Reply-Token-and-Processing-Lock.md`

---

## 1) 問題摘要
- 錯誤集中於 LINE 回覆階段 `reply_message`（函式：`send_text_response`），HTTP 400：`{"message":"Invalid reply token"}`。
- 日誌呈現「短時間連續數次」+「約 1 分鐘後再出現一次」之節奏，且同時段伴隨多筆 `POST /line/webhook 200`。
- 使用者已停止操作，但仍定期出現新錯誤。
- 部署背景：vm 主機位於德國，與台灣平均延遲約 800ms(和LINE server的延遲不確定)，這可能增加了 webhook 快速回 `200` 的難度，進而提高 redelivery 與 `replyToken` 逾時/重用風險。

結論（暫擬）：高度懷疑是 LINE 的「重送（Redelivery）」被我們再次回覆所致（同一 `replyToken` 第二次使用 → 400）。

---

## 2) 最可能根因（依優先序）
1. LINE 重送事件未去重（最可能）
   - LINE 採 at-least-once 投遞；在先前處理超時/傳輸失敗時，會以退避策略重送相同事件。
   - 目前流程未針對 `deliveryContext.isRedelivery`（若 SDK 可取）做去重；重送抵達時仍嘗試 `reply_message` → `replyToken` 第二次使用 → 400。

2. 同一處理序列內存在「二次回覆」備援邏輯
   - 某些 `except` 內再次用同一 `replyToken` 呼叫 `send_error_response` → 仍是 400。
   - 造成同一時刻附近多條相同堆疊（形成「連發」）。

3. 回覆延遲導致 `replyToken` 到期
   - `replyToken` 有短時效（約 1 分鐘）；若流程偏慢，呼叫回覆時已過期 → 400。
   - 也可能進一步觸發 LINE 重送，與 1) 疊加。

4. 多 worker 下的重入競態（UI-only 路徑）
   - 若 `action=other` 未加用戶鎖，連點/重送容易讓多個 worker 爭用同一 `replyToken`。
   - 若近期已將 `other` 納入鎖，該因子會下降但仍需觀察。

---

## 3) 現象與佐證
- 「短時間連發 + 約一分鐘後再現」非常貼近重送退避模式。
- 同時段多筆 `POST /line/webhook 200`，顯示 LINE 確實再次送入事件（非本服務自行重試）。
- 錯誤堆疊集中於回覆階段（`send_text_response`），符合「同一 `replyToken` 被第二次使用」的典型症狀。
- 高延遲環境（平均 ~800ms）使 webhook 處理時間更接近 redelivery 觸發的臨界，若回覆路徑包含外部 I/O 或等待，將更易命中重送/逾時情境。

---

## 4) 不改碼的驗證計畫（觀察優先）
為快速鎖定主因，先加觀測點（只增 log，不改行為）：

- Webhook 入口（每個事件）
  - 記錄：`event.type`、`event.timestamp`、`source.userId`
  - 記錄：`deliveryContext.isRedelivery`（若 SDK 版本提供）
  - 記錄：`postback.data`（若有，注意隱私）

- 每次回覆前（呼叫 `reply_message` 前）
  - 記錄：「處理延遲」= `now - event.timestamp`（毫秒）
  - 記錄：「回覆路徑/handler 名稱」

- 觀察判準
- 重要事實：在 redelivery 中，LINE 使用「相同」的 `replyToken`，且該 token 單次可用、有效時間極短（約 1 分鐘）。


## 5) 最小修正方向（供後續選擇，暫不實作）
- 非根因：`400 Invalid reply token` 的直接原因是「同一個 `replyToken` 被第二次使用」──通常由 redelivery 或同事件路徑內的二次回覆造成，與「鎖是否存在」沒有直接因果。
- 鎖的價值是「降併發風險」：在多 worker 或重送與點擊重入疊加下，鎖能減少「同時」處理導致的雙回覆，但對「先後兩次（第一次已用掉 token，第二次 redelivery 再來）」無能為力。
- 週期性症狀更像 redelivery/backoff：若鎖 TTL 過短、fail-open 或未覆蓋 UI-only 路徑，確實可能偶發雙回覆，但不會造成「規律的週期性」，因此鎖不是本案關鍵因素。
- UI-only 路徑策略：對 `action=other` 等純 UI 回覆，若搶不到鎖應「不回覆、只記 info」以避免重入下的第二次回覆。
- 結論：治本在於「對 redelivery 與回覆行為做 idempotency 保護」，鎖僅作為輔助降低併發競態。
- 重送去重（建議優先）

- 移除同事件內的二次回覆
優先序（建議）：
1. 重送去重（最重要）
  - 在最外層事件處理判斷 `deliveryContext.isRedelivery == true` 時「直接略過回覆並快速回 `200 OK`」，僅記 `INFO`：`skip replying due to redelivery`（可加上 `eventId`/`userId`）。
2. `replyToken` 一次性保護（短 TTL 去重鍵）
  - 以 Redis `SETNX` 建立 `reply_token:{token}`，TTL 約 70 秒（略短於 LINE token 壽命），首個持有者才可進入回覆；後續同 token 嘗試一律略過回覆並記 `INFO`。
3. 移除同事件內的二次回覆
  - `except` 區塊不再用同一 `replyToken` 嘗試補救回覆，只記錄錯誤與關鍵上下文，避免在 redelivery 場景造成第二次回覆。
4. UI-only 納入用戶鎖且「鎖搶不到不回覆」
  - 確保 `action=other` 等純 UI 路徑在用戶鎖範圍內；鎖搶不到則略過回覆（只記 `INFO`），降低併發重入下的雙回覆風險。
5. 快速 ACK 原則與解耦慢工
  - 縮短 webhook 回應路徑，優先快速 `200 OK`；將慢操作改為背景任務 + Push API（以 `userId`）而非 Reply API（依賴短時效 token），以降低 redelivery 機率。
  - `except` 不再用同一 `replyToken` 呼叫 `send_error_response`，僅記錄錯誤。

- UI-only 納入用戶鎖
  - 確保 `action=other` 等純 UI 路徑在用戶鎖範圍；鎖搶不到則略過回覆（只記 `info`）。

- 若仍有 token 到期
  - 縮短回覆路徑，快速 `200 OK`；慢操作改為 Push（以 `userId`）非 Reply（依賴短時效 token）。
---

## 6) 驗收標準
- 觀察期內 `Invalid reply token` 次數趨近 0。
- 日誌顯示 `isRedelivery=True` 的事件已被略過回覆（包含 `skip replying due to redelivery`）。
- 若導入 `replyToken` 一次性保護：重複 token 嘗試不再觸發 `reply_message`，而是記錄 `token-guard miss` 類型的 `INFO`。
- 日誌顯示 `isRedelivery=True` 的事件已被略過回覆。
---

## 7) 後續可選改善

---

## 9) 一句話總結
核心不是鎖，而是冪等（idempotency）：對 redelivery 與二次回覆設防（略過回覆、一次性 token 保護、例外不補回覆、快速 ACK），鎖只在併發時提供輔助降風險。
- 加入 `replyToken` 一次性保護（短 TTL 去重鍵）作為最後保險。
- 對外部 I/O 加超時與降載策略，避免阻塞回覆。
- 強化觀測：對每次 `reply_message` 記錄 `x-line-request-id`，便於跨端對照排查。

---

## 8) 附註
- 本報告不涉及任何行為改動；建議先按第 4 節新增觀察用 log，定位主因後再選擇第 5 節的最小修正。
