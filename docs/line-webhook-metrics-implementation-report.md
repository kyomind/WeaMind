# LINE Webhook Metrics 實作報告

## 文件目的

這份文件是給後續維護者與外部協作 AI 的工程交接說明。

它要回答的不是「這次改了哪些檔案」而已，而是更重要的兩件事：

1. 為什麼原本的實作雖然能 demo，但語意上不夠合理
2. 為什麼最後採用的做法，是在 WeaMind 現有架構下最小、但合理的修正

這份文件特別適合帶回 weamind-infra repo，讓那邊的 AI 知道：
這次改動不是否定原本 W7 MVP 的方向，而是把原本「可跑通的 demo」修正成「仍然是 MVP，但 metric 語意正確」的版本。

## 背景

本次實作對應的是 LINE webhook 路徑的 App 4 metrics：

- `line_webhook_events_total`
- `line_webhook_events_success_total`
- `line_webhook_events_error_total`
- `line_webhook_event_duration_seconds`

W7 observability spec 的核心要求是：

- 可以觀察 LINE webhook 是否進來
- 可以區分成功與失敗
- 可以看到 latency
- event_type 至少能做最小分類

在 WeaMind 的上下文裡，這四個指標的第一版重點不是做到 production-grade observability，而是做出一條「可被 Prometheus / Grafana 觀察」且語意合理的最小鏈路。

## 原本做法

原本的做法是：

1. 在 router 驗簽後，先從 webhook body 抽出 event_types
2. 立刻記錄 `line_webhook_events_total`
3. 把整個 webhook request 丟進 background task
4. 在 background task 中呼叫 LINE SDK 的 `webhook_handler.handle(...)`
5. 如果整體呼叫成功，就把整包 request 中的所有 event_types 都記成 success
6. 如果整體呼叫失敗，就把整包 request 中的所有 event_types 都記成 error
7. 最後把同一個 duration 套到整包 request 中的所有 event_types

也就是說，原本 success / error / duration 的記帳粒度其實是「整個 request」，不是「單一 event」。

## 原本做法的問題

這個做法最大的問題不是不能跑，而是 metric 名稱與實際語意不一致。

### 1. event 名稱，request 粒度實作

這四個 metrics 的命名都在講 webhook event：

- events total
- events success
- events error
- event duration

但原做法裡，success / error / duration 其實是以整包 request 為單位記錄。

如果同一個 request 中包含多個 events，例如：

- event A 成功
- event B 失敗

那原本的 router 包法只會得到「整包 request 失敗」，最後 event A 和 event B 都被記成 error，這會直接扭曲統計結果。

### 2. duration 不是 event latency，而是 batch latency

原本 `line_webhook_event_duration_seconds` 實際上量到的是整個 background task 的處理時間，然後把同一筆 duration 重複 observe 到所有 event_type 上。

這會造成兩個問題：

1. 名稱叫 event duration，但實際是 batch duration
2. 同一個 request 裡若有多個 events，histogram 會被重複餵入同一筆值，產生偏斜

### 3. 測試有驗證 helper 被呼叫，但沒有驗證粒度正確

原本測試主要確認：

- 收到 webhook 時有沒有呼叫 metrics helper
- 成功或失敗時有沒有記錄 metrics

但沒有驗證在「一個 request 含多個 events」時，記帳是否仍然正確。

因此原本的測試能過，並不代表 metric 語意正確。

## 最終採用的做法

最後採用的修正策略是：

### 原則一：保留 router 的同步邊界責任

router 仍然負責：

- content type 驗證
- LINE signature 驗證
- request body decode
- received metric
- fast ACK

這部分沒有被推翻，因為它本來就合理。

### 原則二：把 success / error / duration 下沉到 event dispatch 邊界

真正的修正點在 service 層。

新增了一個 `process_webhook_events(...)`，它不再把 metrics 包在整包 `webhook_handler.handle(...)` 外圍，而是重用 LINE SDK 本來的 dispatch 邏輯，逐筆 event 做：

1. 解析 payload
2. 逐筆取出 event
3. 找出對應 handler
4. 呼叫 handler
5. 對這一筆 event 記 success / error / duration

這樣做之後：

- 一個 event 成功，只記那一個 success
- 一個 event 失敗，只記那一個 error
- duration 也只對應那一筆 event

### 原則三：不要把 metrics 邏輯散進每個 business handler

沒有把 metrics 直接塞進：

- `handle_message_event`
- `handle_location_message_event`
- `handle_follow_event`
- `handle_unfollow_event`
- `handle_postback_event`

原因很實務：

1. 這會讓 metrics concern 滲進各個業務函式
2. 每新增一個 handler 都要記得再補 metrics
3. 之後要統一調整 error / duration 邏輯會很痛

因此最後是選擇在「event dispatch 邊界」集中處理，讓 metrics 成為 cross-cutting concern，而不是散落的業務程式碼。

## 變更摘要

### 1. `app/line/metrics.py`

新增並整理：

- 4 個 Prometheus metrics 定義
- `metrics_response()`
- `extract_event_types_from_body()`
- `normalize_event_type()`
- `normalize_runtime_event_type()`
- `record_webhook_received()`
- `record_webhook_success()`
- `record_webhook_error()`
- `record_webhook_duration()`

其中最重要的是把分類邏輯拆成兩種：

- raw payload 分類：給 router 在背景任務前用
- runtime object 分類：給 service 在逐筆 dispatch 時用

這樣可以避免 service 為了知道 event_type 又回頭重新 parse raw JSON。

### 2. `app/line/router.py`

router 現在的責任變得更清楚：

- 驗證 request
- 抽 event_types
- 記 received
- 把 background task 委派給 `process_webhook_events(...)`

它不再直接記 success / error / duration。

### 3. `app/line/service.py`

新增：

- `_ParsedWebhookPayload`
- `_resolve_event_handler()`
- `process_webhook_events()`

`_resolve_event_handler()` 的角色是重用 LINE SDK 原本的 handler lookup 規則，避免手動重寫一套新的 event routing。

`process_webhook_events()` 的角色是把 metrics 包在真正逐筆 dispatch 的邊界上。

### 4. `app/main.py`

新增 `/metrics` endpoint，暴露 Prometheus text format 給抓取端使用。

### 5. 測試

新增或補強：

- `tests/line/test_metrics.py`
- `tests/line/test_webhook.py`
- `tests/test_main.py`

測試重點分工如下：

- `test_webhook.py` 驗證 router 邊界責任
- `test_metrics.py` 驗證分類與 helper 邏輯
- `test_main.py` 驗證 `/metrics` 端點存在

後續又進一步補了 metrics.py 的最小高回報測試，讓它的覆蓋率從偏低拉升到幾乎完整。

## 為什麼這樣做更合理

這次改動的核心判斷是：

> 不需要推翻原本 MVP 的方向，只需要把 metric 記帳的邊界放到正確的位置。

這個做法比較合理，原因有四個。

### 1. metric 名稱終於和資料語意一致

這是最大的理由。

改完之後，event success / error / duration 真的是針對單一 event，而不是整包 request 的推估值。

### 2. 改動小，但修正的是根本問題

這次沒有大改架構，也沒有去碰核心業務流程。

保留了：

- Fast ACK 模式
- 既有 router 結構
- 既有 handler 註冊方式
- 既有 event_type 最小分類策略

真正改的只有 metrics 記帳邊界。這是最小投入、最大修正。

### 3. 維持 cross-cutting concern 的集中管理

把 metrics 集中在 dispatch 邊界，而不是塞進每個 handler，之後要擴充新的 event types、error labels、latency 邏輯時，修改點仍然集中。

### 4. 符合 demo MVP 的收斂原則

這次沒有追求：

- 完整 alerting
- tracing
- dependency latency
- queue/backlog metrics
- multiprocess registry

因為這些都不是 W7 demo MVP 的最小必要條件。

這次修正聚焦在「既然要有這 4 個 metrics，就至少讓它們的語意是對的」。

## Trade-offs 與已知限制

### 1. 使用了 LINE SDK 的私有內部方法

`_resolve_event_handler()` 與 `process_webhook_events()` 目前重用了 LINE SDK 的私有機制：

- `_WebhookHandler__get_handler_key`
- `_WebhookHandler__invoke_func`
- `_handlers`
- `_default`

這在封裝純度上不漂亮，但在目前專案脈絡下是合理取捨。

原因是：

1. 它能最小成本重用既有 handler registry
2. 不需要手動重寫整套路由分派
3. 不會把 metrics concern 散進每個 handler

代價是未來若 LINE SDK 內部實作改動，這裡要一起檢查。

### 2. parser 失敗時仍然只能用 fallback event types

如果 payload 在 runtime parse 前就失敗，系統無法拿到真正的 runtime event object，因此只能退回 router 預先抽出的 event_types，或使用 `unknown`。

這是合理降級，不是設計缺陷。

### 3. service.py 的覆蓋率仍低於 metrics.py

這不是這次工作的重點。`process_webhook_events()` 的主要關鍵路徑已經有測，但 service.py 仍有大量既有 handler 分支未完全覆蓋。

本次工作優先級是把新加的 metrics 模組與其邊界補到足夠合理，而不是順手把整個 service layer 全面補測。

## 驗證結果

最終完整測試結果：

- `uv run pytest`
- `236 passed`

最終 coverage 結果：

- total: 94%
- `app/line/metrics.py`: 98%
- `app/line/router.py`: 98%
- `app/line/service.py`: 88%
- `app/main.py`: 100%

這表示本次改動至少達成了兩件事：

1. 沒有破壞原本功能
2. 新增的 metrics 模組不是只靠手感實作，而是有相對扎實的驗證

## 對 weamind-infra / W7 spec 的回應

如果要用一句話總結這次對原始 W7 做法的調整，可以這樣說：

> 原本的做法已經成功把 observability 鏈路跑通，但 success / error / duration 實際上仍停留在 request 粒度。這次改動不是推翻那個 MVP，而是把這三個 metrics 下沉到 event dispatch 邊界，讓指標語意與命名一致，同時保留 Fast ACK 與最小分類策略不變。

也就是說，這次不是否定原本做法，而是把它從：

- 「可 demo 的 webhook metrics」

修正為：

- 「仍然是 MVP，但 event-level 語意正確的 webhook metrics」

## 建議後續工作

如果未來要再往前走，建議順序如下：

1. 補 `app/line/service.py` 中 `process_webhook_events()` 的更多異常分支測試
2. 視需求決定是否要把 LINE SDK 私有方法包成更穩定的 project-local adapter
3. 再往 Grafana query 與 dashboard 整理推進
4. 若部署模式改為多 worker，再評估 Prometheus multiprocess registry

不建議的順序是先去做更多 dashboard 或更多 metrics，再回頭修正 event/request 語意。因為那樣只會把錯的資料模型往下游放大。

## 結論

這次最重要的工程決策不是「新增了 4 個 metrics」，而是：

> 決定把 success / error / duration 的記帳邊界，從 router 的整包 request 外圍，移到 LINE event 的逐筆 dispatch 邊界。

這個改動很小，但它修正的是資料語意的根本問題。

對於 W7 observability MVP 來說，這就是最小但合理的做法。
