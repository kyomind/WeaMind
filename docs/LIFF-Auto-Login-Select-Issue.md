# LIFF 自動登入後下拉選單（縣市資料）失效問題說明

> 本文件聚焦於「自動登入導致縣市下拉選單無資料」之根因分析與解法策略。其他 UX / 成功訊息優化不在此文件範圍。

---
## 問題現象
隔一段時間（約 12 小時）再開啟 LIFF 地點設定頁：
1. LINE 顯示登入成功對話框（Overlay Flow），未整頁刷新。
2. 回到頁面後，縣市下拉選單只有預設的「請選擇縣市」，無實際資料。
3. 行政區選單也維持停用狀態。
4. 無錯誤訊息彈出。

## 表面症狀 vs 真正狀態
| 項目     | 表面感受       | 真實狀態                          |
| -------- | -------------- | --------------------------------- |
| 下拉內容 | 資料『被清空』 | 初始化流程未完成 → 根本沒載入資料 |
| 事件監聽 | 似乎失效       | `setupEventListeners()` 尚未執行  |
| 登入狀態 | 看似已登入     | 登入後流程未恢復後半段初始化      |

## 根因（Root Cause）
`init()` 中流程：
```mermaid
graph TD
A[init()] --> B{liff.isLoggedIn()?}
B -- false --> C[liff.login(); return]
B -- true --> D{accessToken 存在?}
D -- false --> C[liff.login(); return]
D -- true --> E[loadAdminData()]
E --> F[setupEventListeners()]
F --> G[populateCounties()]
```
登入過期時：
- `liff.login()` 採 Overlay 模式（非整頁 redirect）。
- JS 執行序因 `return` 結束，後半段 (`loadAdminData()` / `setupEventListeners()` / `populateCounties()`) **永遠沒執行**。
- 頁面保持原 HTML 靜態狀態 → 下拉列表空。

## 為何 `ensureDataLoaded()` 沒救回？
`ensureDataLoaded()` 只會在 `countySelect` 綁定的 `focus` 事件觸發；但事件綁定是在 `setupEventListeners()` 裏面，而初始化因提早 return 根本沒跑到，所以事件沒綁 → 無法觸發補救。

## 風險點總結
| 風險                 | 說明                                                     |
| -------------------- | -------------------------------------------------------- |
| 初始化步驟耦合       | 資料載入、事件綁定、UI 填充綁在同一條成功線路上。        |
| 登入流程假設錯誤     | 假設 `liff.login()` 一定會 reload；實際有 overlay 模式。 |
| 無『登入後續接』機制 | 沒有針對 overlay flow 的重啟/續接邏輯。                  |
| 無冪等設計           | `init()` 無法安全多次呼叫或分段恢復。                    |

## 解法選項評估
| 方案 | 描述                                                              | 優點                         | 缺點                | 適合階段 |
| ---- | ----------------------------------------------------------------- | ---------------------------- | ------------------- | -------- |
| A    | `liff.login({ redirectUri: window.location.href })` 強制 redirect | 最小變動，確保重新跑完整流程 | 體驗跳頁、載入成本  | 短期止血 |
| B    | 事件綁定前移（建構時就綁），資料載入解耦                          | 不怕 init 中斷，可懸掛恢復   | 需調整結構          | 中期穩定 |
| C    | 登入後輪詢/回調續接（poll `isLoggedIn()` + token）                | 無需 reload，用戶體驗流暢    | 輪詢需 timeout 控制 | 中期增強 |
| D    | 狀態機化（明確 PHASE_*）                                          | 長期可維護、清晰             | 工程量較大          | 長期演進 |
| E    | Promise 化 ensureAuth()/ensureData()                              | 可重入、簡化錯誤處理         | 仍需重新分層        | 中期可行 |

## 建議策略（採用）
採『B + A(備援)』：
1. 先前移事件綁定，讓互動永不失效（即使資料未載入）。
2. 若偵測登入缺失或 token 為空 → 使用 `liff.login({ redirectUri })` 強制完整刷新（備援）。
3. 使用者操作下拉時 → `ensureDataLoaded()` 再次嘗試載入（資料層懸掛恢復）。

## 待實作具體調整（Checklist）
- [ ] 將 `setupEventListeners()` 從 `init()` 移到 constructor（或 DOMContentLoaded 早期階段）。
- [ ] 調整事件邏輯：`focus` 時若 `!adminData` → 觸發 `ensureAuthThenData()`。
- [ ] 新增 `ensureAuth()`：
  - 若 `!liff.isLoggedIn()` 或 `!token` → `liff.login({ redirectUri: location.href })`。
  - 已登入但 token 取不到 → 視為過期 → 同上。
- [ ] 新增 `ensureData()`：冪等；若已有 `adminData` 則快速返回。
- [ ] `init()` 僅負責：`await ensureAuth(); await ensureData(); populateCounties();`。
- [ ] UI 提示：登入後補流程進行時顯示『正在恢復資料…』。
- [ ] 錯誤（資料載入失敗）→ 允許使用者再次點擊下拉重試。
- [ ] 加入防抖/鎖：同時多次點擊不會觸發重複載入。

## 風險控管
| 風險                 | 緩解策略                                                      |
| -------------------- | ------------------------------------------------------------- |
| 多次併發載入         | 使用旗標 `isLoadingAdminData`                                 |
| 登入循環（連續失敗） | 設定最大嘗試次數 / 顯示『登入失敗，請重開 LIFF』              |
| Token race           | 取得 token 後立即用於後續 API，超時則重登                     |
| 使用者誤判功能故障   | 自動續接 polling + 下拉 placeholder 狀態提示 + 逾時可點擊重試 |

## 完成驗收條件（Acceptance Criteria）
- [ ] 登入過期 → 重新開啟頁面 → 完成 overlay 登入 → 不需要手動刷新即可看到縣市列表。
- [ ] 下拉第一次 focus 時若資料尚未載入：顯示『正在載入』，完成後自動填充。
- [ ] 連點下拉不會造成重複 fetch。
- [ ] 模擬 `adminData = {}` 再次點擊 → 自動恢復並填充。
- [ ] Overlay 登入後即使使用者無任何互動：自動 polling 續接流程（≤ 3 秒內）→ 成功填充或出現重試文案。
- [ ] 續接逾時顯示『載入逾時，點擊重試』；點擊後在不刷新頁面情況下可恢復並填充。
- [ ] 失敗（離線）→ 顯示『載入失敗，點擊重試』；再次 focus 可重試。

## 使用者誤判風險與最小 UX 緩解
> 不擴張本文件 UX 範疇；僅加入防止「看起來壞掉」的極薄保護層。

目標：避免 overlay 自動登入後，頁面靜止於空白下拉使使用者誤以為系統壞掉。

最小解：
1. 自動續接輪詢（Polling Resume）
  - Overlay 關閉即啟動 `tryResumeFlowWithPolling(interval=300ms, timeout=5000ms)`。
  - 條件達成：`liff.isLoggedIn() && accessToken` → 立即 `ensureData()` → 填充。
2. 下拉 placeholder 狀態
  - 初始插入第一個 disabled option：`(載入中…)`。
  - 成功後移除；若 timeout → 改成 `(載入逾時，點擊重試)` 並綁 `click` 觸發 `forceRecover()`。
3. 重試/鎖定
  - `forceRecover()` 內部鎖：避免多重並行。
  - 最多兩次失敗 → 將 placeholder 改為 `(請關閉後重新開啟或稍後再試)`。
4. 非侵入式提示
  - 不使用 modal；所有資訊留在下拉內，避免干擾操作流程。
5. 基礎觀測打點
  - `OVERLAY_RESUME_START`, `OVERLAY_RESUME_SUCCESS`, `OVERLAY_RESUME_TIMEOUT`, `OVERLAY_RESUME_RETRY`, `OVERLAY_RESUME_GIVEUP`。

伪代碼骨架（僅結構示意）：
```js
async function tryResumeFlowWithPolling(maxMs = 5000, step = 300) {
  const start = Date.now();
  showPlaceholder('(載入中…)');
  while (Date.now() - start < maxMs) {
   if (liff.isLoggedIn() && liff.getAccessToken()) {
    try {
      await ensureData();
      populateCounties();
      clearPlaceholder();
      return true;
    } catch { /* swallow → 下一輪或逾時處理 */ }
   }
   await delay(step);
  }
  showPlaceholder('(載入逾時，點擊重試)', { clickable: true, onClick: forceRecover });
  return false;
}
```

成功標準：大多數 overlay 登入場景中，使用者無需任何操作即可在 3 秒內看到縣市資料；失敗時提供清晰單步重試而非讓下拉保持空白。

## 未來進階（選擇性）
- 加入狀態機：`AUTH_CHECK` / `AUTH_RECOVERING` / `DATA_LOADING` / `READY`。
- 加入可觀測性：記錄登入恢復耗時、資料載入成功率。
- 將行政區資料改為本地緩存（LocalStorage + 版本號）減少重載頻率。

---
## for AI Memory Hooks（請未來的 AI 助手閱讀）
- HOOK_AUTH_FLOW: 原因是 `liff.login()` overlay 不 reload，init 提早 return 導致後續未執行。
- HOOK_PRIMARY_PLAN: 採方案 B 事件前移 + 方案 A redirectUri 做 fallback。
- HOOK_DO_NOT_FORGET: 事件一定要在資料載入前就綁；`ensureDataLoaded()` 要可被多次安全呼叫。
- HOOK_RACE_CONDITION: 防止多次點擊同時觸發 fetch，需加 `isLoadingAdminData`。
- HOOK_ACCEPTANCE: 測試情境列在『完成驗收條件』，實作後逐條勾。
- HOOK_IF_STUCK: 若 overlay 仍不觸發任何流程 → 加 300ms 輪詢登入狀態上限 5 秒作續接。
- HOOK_SCOPE_LIMIT: 本文件只處理『自動登入後資料未載入』，不要混入 UX 訊息相關調整。
- HOOK_USER_RISK: 已加入自動續接 + placeholder + 逾時重試以降低使用者誤判功能故障。

---
## TL;DR
登入過期後的 overlay 流程沒有刷新頁面 → 原本假設 reload 的初始化邏輯失效 → 事件與資料都沒載入 → 下拉顯示空。解法：將事件綁定提早、登入與資料載入解耦、必要時強制 redirectUri 登入，並加入可重試與冪等保護。
