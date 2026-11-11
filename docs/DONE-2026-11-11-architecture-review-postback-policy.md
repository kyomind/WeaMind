# 架構探索結案：保留目前的 PostBack Action 失敗政策配置

整理日期：2026-11-11

## MEMOS：新 Session 先讀這裡

- **已完成的是架構探索與決策，不是產品重構。** 使用者已同意：目前不值得為 PostBack Action 的特殊失敗文案單獨開工，維持現狀。
- 本次分析基準為 `main` 的 `70a81ad`。未修改產品程式、測試或設定；本文件是探索結案紀錄。
- 唯一保留到最後的候選：`app/line/service.py` 的事件 adapter 必須辨識 `PresetWeatherAction`，才能選擇專屬錯誤文案。確有 locality 摩擦，但只有一個 caller、一種特殊情況，改善收益有限。
- **不要把初版 HTML 的 `Worth exploring` 誤讀成已核准實作。** 後續檢視 Git 歷史後，最終決策是「現在不改，不另開重構任務」。
- 重新評估的觸發條件：第二種 action 也需要特殊失敗政策、出現第二個 caller，或實際修改已反覆要求跨檔同步。觸發條件不是預先承諾的待辦。
- 最重要的不變量：**業務失敗後，錯誤提示即使成功送出，仍須是 `handler_error`，不能變成 success。** 先讀 [Webhook outcome 修正紀錄](FIX-2026-11-07-webhook-event-outcomes.md)。
- 本次相關測試 **87 passed**；沒有全套測試、真實 LINE／Redis／PostgreSQL 或部署驗證。
- **待處理 issue／事項：沒有。** 沒有因本次探索建立 GitHub Issue，也沒有待實作的 interface 設計。

## 任務與探索方法

使用者要求執行 `improve-codebase-architecture`：找出值得深化的 module，重點是 testability 與 AI 導覽，而不是湊出重構清單。產物須為暫存 HTML，使用 before／after 圖呈現候選，尚不設計 interface；只有使用者選擇繼續時，才進入 grilling。

本次依序：

1. 讀取專案規範、`GLOSSARY.md`、`codebase-design` 詞彙與 HTML 報告規格。
2. 先看 Git 歷史再決定範圍，將注意力放在近期變動的 LINE 事件處理、PostBack Action，以及先前已深化的 Weather Query 與 Location resolution。
3. 主 agent 檢查 event orchestration、outcome 傳遞、PostBack 與限流責任，另派 fresh-context 子代理獨立探索。
4. 對照原始碼、測試與既有修正紀錄，套用 deletion test，區分「真正減少 caller 知識」和「只是把程式搬到另一個 helper」。
5. 產生一項候選的 HTML 報告；使用者要求進一步判斷是否真的值得改，再檢查引入該分支的 commit 與 action 演變，收斂為不改。

### 歷史範圍注意事項

這兩種命令的意義不同：

```bash
# 全 repo 最近 100 commits 中，哪些產品／測試路徑反覆出現
# 這是歷史範圍統計，不代表每筆都是獨立需求。
git log -100 --format= --name-only | rg '^(app|tests)/' | sort | uniq -c | sort -nr

# 最近 100 筆「有修改指定路徑」的歷史，可能追溯得更久
# 不可將此結果稱為全 repo 最近 100 commits。
git log -100 --format= --name-only -- app tests
```

本次兩者都有查看，並以個別功能 commit 的內容判斷熱點，不以次數直接認定架構缺陷。近期真正相關的產品變動是 `f075318` 的 webhook outcome 修正；先前多次深化集中在 2026-08-12。

### 協作

- 模式：唯讀 delegation，不是兩位 reviewer 的正式 review。
- 子代理：`architecture-codex`，Herdr 註冊 kind 為 `codex`，啟動 profile 為 `codex:gpt-6.1-sol:medium`。
- 主 agent 與子代理獨立找到相同的 PostBack 失敗政策摩擦，主 agent 再核對原始碼、歷史與測試。
- 子代理沒有修改 repo 或執行測試；87 個測試由主 agent 執行。協作 tab 已關閉。

## 唯一候選：PostBack Action 失敗回覆政策

### 現況與證據

以下行號以 `70a81ad` 為準，後續請用符號與文字搜尋重新定位。

| 位置 | 責任／證據 |
| --- | --- |
| `app/line/postback.py:76–113` | `PostbackPlan` 與 `prepare_postback` 集中 action、是否限流及限流拒絕文案 |
| `app/line/postback.py:116–143` | `execute_postback` 決定正常 recipe，非預期例外向 caller 傳遞 |
| `app/line/service.py:267–280` | caller 先選通用錯誤文案，再辨識 `PresetWeatherAction` 改選專屬文案 |
| `app/line/service.py:281–294` | caller 執行限流政策、呼叫 action、回覆並決定 `EventOutcome` |
| `tests/line/test_postback.py` | typed plan、動作執行、例外傳遞、限流拒絕與 preparation failure |
| `tests/line/test_event_outcomes.py` | 真實 router、SDK parser、callback、dispatch 路徑上的 outcome 與 preset 錯誤文案 |

現在的責任流程：

```text
SDK event adapter 提取欄位
  → PostBack Action module 準備 plan
  → caller 辨識具體 action，選擇錯誤文案
  → caller 套用 lock policy
  → action module 回傳正常 recipe，或拋出例外
  → caller 回覆並回傳 EventOutcome
  → dispatcher／metrics
```

探索過的方向是讓 action-specific 失敗回覆政策與其他 action policy 保持 locality，使事件 adapter 不再需要認識具體 action。**沒有決定新的 interface、結果型別或例外模型，也沒有核准實作。**

### 為何這段知識出現在 caller

`git show f075318 -- app/line/postback.py app/line/service.py` 顯示：

- 舊 `execute_postback` 會攔下執行例外並回傳普通錯誤 recipe，外部因此無法只從正常返回辨識業務失敗。
- outcome 修正移除這個例外吞噬，改由事件 adapter 明確回傳 `HANDLER_ERROR`。
- 為維持 Preset Location 原有「查詢時發生錯誤，請稍後再試。」文案，caller 加入兩行 action 型別判斷；其他情況仍用「系統暫時有點忙，請稍後再試一次。」。

因此這不是無理由的任意分散，而是修復真實計數問題時，保留既有行為的一個小取捨。不能為了集中政策而還原成「吞例外、回傳普通 recipe」。

### 最終判斷：目前不值得專門改

1. **摩擦存在，但很小。** 只有一個 caller、一種特殊情況，未見多處重複擴散。
2. **現有 module 仍有 depth。** 刪掉 PostBack module 會把解析、action dispatch、限流政策與 Query History session lifecycle 散回 caller；它不是 shallow pass-through。
3. **可預期收益主要是 locality，不是新功能或已知可靠性缺陷的修復。** 現有分支容易理解，也有回歸測試保護。
4. **不要為兩行判斷新增更大的 interface 成本。** 新結果型別、泛用 executor 或 action framework 可能抵銷原本有限的 leverage。

初版報告評為 `Worth exploring`，指的是可以討論的候選，不代表應立即開工。進一步判斷後，使用者同意維持現狀。

## 明確不做的事

- 不把限流、整段事件 orchestration 或所有錯誤處理一併重構。
- 不新增只有一個 adapter 的抽象 seam。
- 不加入 queue、去重、重試、持久化排程或改變批次中止語意。
- 不為消除少量相似程式，重寫 Weather Query workflow。
- 不把短 module 自動視為 shallow：SDK dispatch 隱藏私有 SDK 相容知識；reply messaging 已有 production／in-memory adapter 的真實 seam。
- 不拆回已有 locality 的 Location resolution、Weather Query 呈現與 Query History best-effort 寫入。

此結論不是宣稱全 repo 沒有改善空間，而是本次範圍內沒有值得立即實作的架構候選。

## 驗證與產物

主 agent 執行：

```bash
uv run pytest tests/line/test_event_outcomes.py tests/line/test_postback.py tests/line/test_sdk_dispatch.py tests/line/test_service_basic.py tests/core/test_processing_lock.py -q --tb=short
```

結果：**87 passed in 0.25s**。這是當次本機的新鮮測試結果，不是引用舊報告。

- 測試預設產生 coverage 輸出並更新本機 coverage artifacts；這只是選定測試集，不能把其 coverage 數字當作完整測試覆蓋率。
- 分析與報告完成後、建立本文件前，`git status --short` 為空。
- 暫存 HTML 已產生，做過基本結構／必要區塊檢查，並以 macOS `open` 開啟；沒有以瀏覽器自動化確認 Mermaid 實際渲染。
- HTML 使用 Tailwind 與 Mermaid CDN，需要網路才能完整呈現。暫存檔可被系統清除；**本 Markdown 才是持久交接依據**。

當次 HTML 絕對路徑：

```text
/var/folders/6g/2zrv1ccn7rdg385sdm6_c9100000gn/T/architecture-review-20261111-091516.html
```

未做：全套 pytest、lint／type check、真實 LINE／Redis／PostgreSQL、負載測試、外部監控或部署檢查。沒有藉本次測試結果宣稱正式環境已驗證。

## 下一次如何接續或如法炮製

### 如果只是接手理解

先讀 MEMOS、最終判斷，以及 [Webhook outcome 修正紀錄](FIX-2026-11-07-webhook-event-outcomes.md)。沒有待辦，不需要為「完成 handoff」而開始重構，也不需要把暫時不值得改的理由另外立成永久禁止重構的 ADR。

### 如果新的需求觸發重新評估

1. 先核對最新程式與 Git 歷史，確認是否真的新增 caller 或 action-specific 失敗政策；不要只重複引用本文件的行號。
2. 搜尋 `PresetWeatherAction`、`error_recipe`、`prepare_postback`、`execute_postback`，畫出誰必須知道哪些政策。
3. 再套 deletion test：修改是否確實減少 caller 知識，還是只新增轉呼叫 helper？一個 module 的深度不以檔案長短判斷。
4. 先向使用者確認值得開工，再討論 interface。不要把本次責任示意圖視為已選定的設計。
5. 若進入實作，必須保留業務失敗身分、preset 文案、preparation failure 通用提示、限流拒絕語意、TTL／fail-open 行為，以及 DB session 在 transport 前關閉。
6. 測試以承擔責任的 module interface 為主；保留少量真實 webhook 路徑驗證 outcome 傳遞。可考慮補上「業務失敗且錯誤提示傳送也失敗」案例，不得宣稱本次已新增此測試。

可重用的查證命令：

```bash
git log -18 --oneline -- app
git log -10 --format='%h %ad %s' --date=short -- app/line/postback.py
git show f075318 -- app/line/postback.py app/line/service.py
rg -n 'PresetWeatherAction|error_recipe|prepare_postback|execute_postback' app tests/line
```

### 如果要重新做一次整體架構探索

重新讀取可用的 `improve-codebase-architecture` 與 `codebase-design` skill，從當時的近期變動決定範圍，再看 `GLOSSARY.md` 與相關決策紀錄。獨立探索、交叉驗證、用證據排除不值得改的候選；**零個值得立即實作的候選，也是有效成果。**

## 待處理事項

沒有。本次探索與不改的決策已完成；重新評估條件僅供未來需求出現時參考，不構成未完成工作。
