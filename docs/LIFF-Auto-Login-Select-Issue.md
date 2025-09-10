# LIFF 自動登入後下拉選單（縣市資料）失效問題 - 已解決

> **狀態：✅ 已實作完成** - 本文件記錄問題分析與實際解決方案。

---
## 問題現象
隔一段時間（約 12 小時）再開啟 LIFF 地點設定頁：
1. LINE 顯示登入成功對話框（Overlay Flow），未整頁刷新。
2. 回到頁面後，縣市下拉選單只有預設的「請選擇縣市」，無實際資料。
3. 行政區選單也維持停用狀態。
4. 使用者誤以為功能故障。

## 根因分析
**核心問題：** `liff.login()` 的 Overlay 模式不會重新載入頁面，導致原本假設會完整執行的初始化流程中斷。

```mermaid
graph TD
A[init()] --> B{liff.isLoggedIn()?}
B -- false --> C[liff.login(); return ❌]
B -- true --> D{accessToken 存在?}
D -- false --> C
D -- true --> E[loadAdminData() ✅]
E --> F[setupEventListeners() ✅]
F --> G[populateCounties() ✅]
```

**失敗路徑：** 登入檢查失敗 → `return` 提早結束 → 後續步驟永不執行 → 事件未綁定 → 資料未載入

## 已實作解決方案

### 核心策略：架構解耦 + 自動恢復
採用**事件綁定前移 + 登入資料解耦 + 自動續接輪詢**的組合方案：

1. **事件綁定前移** - 在 constructor 中立即綁定，確保使用者操作永不失效
2. **登入檢查分離** - `ensureAuth()` 可獨立重入，失敗時強制 redirectUri 登入
3. **資料載入分離** - `ensureData()` 冪等設計，可安全多次呼叫
4. **自動續接機制** - overlay 後自動輪詢恢復，無需使用者操作
5. **狀態可視化** - 下拉選單顯示載入狀態，失敗時提供重試選項
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
## 實作細節

### 1. 架構重構 (Constructor)
```javascript
constructor() {
    this.adminData = {};
    this.isInitialized = false;
    this.isLoadingAdminData = false;  // 防重複載入鎖
    this.retryCount = 0;             // 重試計數
    this.maxRetries = 2;             // 最大重試次數

    // 事件綁定前移：無論登入狀態如何都先綁定事件
    this.setupEventListeners();
    this.init();
}
```

### 2. 分離式登入檢查 (ensureAuth)
```javascript
async ensureAuth() {
    if (!liff.isLoggedIn()) {
        // 強制使用 redirectUri 確保完整刷新
        liff.login({ redirectUri: window.location.href });
        return;
    }

    try {
        const accessToken = liff.getAccessToken();
        if (!accessToken) {
            liff.login({ redirectUri: window.location.href });
            return;
        }
    } catch (error) {
        liff.login({ redirectUri: window.location.href });
        return;
    }
}
```

### 3. 冪等資料載入 (ensureData)
```javascript
async ensureData() {
    // 冪等設計：如果已有資料則快速返回
    if (Object.keys(this.adminData).length > 0) {
        return;
    }
    await this.loadAdminData();
}
```

### 4. 自動續接輪詢機制
```javascript
async tryResumeFlowWithPolling(maxMs = 5000, stepMs = 300) {
    const startTime = Date.now();
    this.showCountyPlaceholder('(載入中...)');

    while (Date.now() - startTime < maxMs) {
        try {
            if (liff.isLoggedIn() && liff.getAccessToken()) {
                await this.ensureData();
                this.populateCounties();
                return true;
            }
        } catch (error) {
            // 忽略錯誤，繼續輪詢
        }
        await new Promise(resolve => setTimeout(resolve, stepMs));
    }

    this.showCountyPlaceholder('(載入逾時，點擊重試)', true);
    return false;
}
```

### 5. 下拉狀態管理
```javascript
showCountyPlaceholder(text, clickable = false) {
    const countySelect = document.getElementById('county');

    // 移除舊 placeholder，加入新狀態
    const placeholderOption = document.createElement('option');
    placeholderOption.textContent = text;
    placeholderOption.disabled = !clickable;
    placeholderOption.className = 'placeholder-option';

    if (clickable) {
        placeholderOption.addEventListener('click', () => {
            this.forceRecover();
        });
    }

    countySelect.insertBefore(placeholderOption, countySelect.firstChild);
}
```

## 使用者體驗流程對比

### 🔴 修復前（糟糕體驗）
```
開啟頁面 → 登入成功彈窗 → 點「繼續」→
下拉選單空白 → 使用者以為壞了 → 關閉頁面 😞
```

### 🟢 修復後（順暢體驗）
```
開啟頁面 → 登入成功彈窗 → 點「繼續」→
下拉顯示「載入中...」→ 1-3秒後自動填入縣市 → 正常使用 😊
```

### 🟡 失敗時（優雅降級）
```
載入失敗 → 顯示「載入逾時，點擊重試」→
使用者點擊 → 重新嘗試 → 成功或建議重開
```

## 關鍵特性

| 特性     | 說明                      | 正常情況   | 問題情況     |
| -------- | ------------------------- | ---------- | ------------ |
| 事件綁定 | 在 constructor 中立即綁定 | ✅ 正常運作 | ✅ 仍可互動   |
| 資料載入 | 冪等設計，可安全重複呼叫  | ✅ 一次成功 | 🔄 自動重試   |
| 自動續接 | 500ms 後檢查，失敗才輪詢  | ✅ 不執行   | 🔄 自動恢復   |
| 狀態提示 | 下拉內顯示載入/重試狀態   | ✅ 正常資料 | 💬 狀態提示   |
| 重試機制 | 最多 2 次，超過建議重開   | ✅ 不需要   | 🔄 使用者可控 |

## 完成驗收 ✅

以下條件已在程式碼中實現：

- ✅ **事件綁定前移**：`setupEventListeners()` 在 constructor 中執行
- ✅ **登入檢查分離**：`ensureAuth()` 可獨立重入，失敗時強制 redirectUri
- ✅ **資料載入解耦**：`ensureData()` 冪等設計，可安全多次呼叫
- ✅ **自動續接機制**：`tryResumeFlowWithPolling()` 在 overlay 後自動輪詢
- ✅ **狀態可視化**：`showCountyPlaceholder()` 管理載入/重試狀態
- ✅ **防重複載入**：`isLoadingAdminData` 鎖機制
- ✅ **重試限制**：`retryCount` 與 `maxRetries` 控制
- ✅ **優雅降級**：失敗時提供清楚的重試選項

## 測試場景

### 主要測試情境
1. **正常使用**：已登入使用者開啟頁面 → 縣市資料正常載入
2. **Overlay 登入**：12小時後重開 → 登入彈窗 → 自動恢復資料 → 正常使用
3. **網路失敗**：載入失敗 → 顯示重試選項 → 使用者可手動恢復
4. **重複操作**：多次點擊不會造成重複載入

### 預期結果
- **無感使用**：正常情況下沒有額外開銷，只有 500ms 後的輕量檢查
- **自動恢復**：Overlay 登入後 1-3 秒內自動填充縣市資料
- **清楚提示**：失敗時使用者知道可以重試，不會誤以為功能故障伪代碼骨架（僅結構示意）：
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

## 未來進階優化（選擇性）

- **狀態機化**：明確的 `AUTH_CHECK` / `AUTH_RECOVERING` / `DATA_LOADING` / `READY` 狀態管理
- **可觀測性**：記錄登入恢復耗時、資料載入成功率，供後續優化參考
- **本地緩存**：行政區資料改用 LocalStorage + 版本號，減少重載頻率
- **更細緻的錯誤分類**：區分網路錯誤、權限錯誤、伺服器錯誤等，提供更精準的使用者指引

---
## AI Memory Hooks 🤖

**核心記憶點：**
- ✅ **已解決**：Overlay 登入導致初始化中斷問題
- 🔧 **解法**：事件前移 + 分離式登入檢查 + 自動續接輪詢
- 🎯 **關鍵**：`setupEventListeners()` 在 constructor，`tryResumeFlowWithPolling()` 自動恢復
- 🔒 **防護**：`isLoadingAdminData` 鎖 + `retryCount` 限制 + 優雅降級
- 📱 **UX**：下拉內狀態提示，不干擾正常流程，失敗可重試

**測試重點：** 12小時後開啟 → Overlay登入 → 1-3秒自動恢復 → 正常使用

---
## TL;DR
**問題：** Overlay 登入不刷新頁面 → 初始化中斷 → 下拉空白
**解法：** 架構解耦 + 自動恢復 → 使用者無感體驗 ✅
