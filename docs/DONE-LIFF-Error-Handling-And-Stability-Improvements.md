# DONE-LIFF-Error-Handling-And-Stability-Improvements

## 專案概述

此次實作主要解決 WeaMind LIFF 地點設定頁面的錯誤處理問題和穩定性改善，包括：
1. LIFF SDK 載入失敗導致的初始化錯誤
2. LINE 自動重新登入導致的資料遺失問題
3. 權限 scope 相關的錯誤訊息
4. 用戶體驗優化（按鈕行為、錯誤提示等）

## 主要問題與解決方案

### 1. LIFF SDK 載入失敗問題

**問題描述**：
- 控制台出現 `ReferenceError: liff is not defined`
- 資源完整性檢查失敗：`Failed to find a valid digest in the 'integrity' attribute`
- 第三方 Cloudflare beacon 被阻擋

**根本原因**：
LIFF SDK 的 `integrity` 屬性使用過期的 SHA-384 雜湊值，當 LINE 更新 SDK 時，雜湊值不符導致瀏覽器阻擋載入。

**解決方案**：
```html
<!-- 移除過期的 integrity 屬性 -->
<script charset="utf-8" src="https://static.line-scdn.net/liff/edge/2/sdk.js"
        crossorigin="anonymous"></script>
```

**技術決策與原因**：
- **移除 integrity 而非更新**：LINE 隨時可能更新 SDK，維護正確的 integrity 值會成為運維負擔
- **保留 crossorigin="anonymous"**：維持基本的安全性
- **HTTPS + 官方 CDN**：LINE 官方 CDN 本身就具備足夠的安全性

### 2. LIFF SDK 載入等待機制

**實作核心**：
```javascript
function waitForLIFF() {
    return new Promise((resolve, reject) => {
        let attempts = 0;
        const maxAttempts = 50; // 5 seconds max wait

        const checkLIFF = () => {
            attempts++;
            if (typeof liff !== 'undefined') {
                resolve();
            } else if (attempts >= maxAttempts) {
                reject(new Error('LIFF SDK loading timeout'));
            } else {
                setTimeout(checkLIFF, 100);
            }
        };

        checkLIFF();
    });
}
```

**設計考量**：
- **輪詢間隔**：100ms 平衡響應速度與性能
- **超時設定**：5秒超時避免無限等待
- **錯誤處理**：載入失敗時顯示明確錯誤訊息

### 3. 權限 Scope 錯誤解決

**問題**：
提交表單後出現 `"The permission is not in LIFF app scope."`

**原因分析**：
`liff.sendMessages()` 需要 `chat_message.write` 權限，但 LIFF 應用程式只設定了 `openid` 和 `profile` scope。

**解決方案**：
```javascript
// 移除需要額外權限的功能
// await this.sendConfirmationMessage(locationType, county, district);

// 改為只顯示成功訊息
this.showMessage(`${locationType === 'home' ? '住家' : '公司'}地點設定成功！`, 'success');
```

**技術決策**：
- **最小權限原則**：不增加不必要的 scope 權限
- **簡化用戶體驗**：成功訊息已足夠，無需額外發送 LINE 訊息

### 4. LINE 自動重新登入資料遺失問題

**問題場景**：
用戶第 N 次進入 LIFF 頁面時，遇到 LINE 自動登出/登入過程，導致已載入的縣市資料被清空。

**解決架構**：
```javascript
// 按需檢查機制
countySelect.addEventListener('focus', async () => {
    await this.ensureDataLoaded();
});

async ensureDataLoaded() {
    if (Object.keys(this.adminData).length === 0) {
        // 只在資料遺失時重新載入
        this.showMessage('正在載入地區資料...', 'info');
        await this.loadAdminData();
        this.populateCounties();
    }
}
```

**設計原則**：
- **按需觸發**：在用戶操作時檢查，而非定期輪詢
- **性能優化**：避免不必要的網路請求
- **用戶友善**：異常情況下提供載入提示，正常情況下靜默載入

### 5. 用戶體驗優化

#### 5.1 按鈕行為改善

**原始問題**：
- 「取消」按鈕試圖關閉視窗，但在 LIFF 環境中通常無效
- 成功後自動關閉視窗，阻止用戶設定多個地點

**改善方案**：
```javascript
// 取消按鈕改為重置表單
cancelBtn.addEventListener('click', () => {
    this.resetForm();
});

resetForm() {
    // 重設所有表單狀態
    document.querySelector('input[name="locationType"][value="home"]').checked = true;
    document.getElementById('county').value = '';
    // ... 其他重置邏輯
}
```

**按鈕文字更正**：
```html
<!-- 更準確地反映功能 -->
<button type="button" id="cancelBtn" class="btn btn-secondary">重置</button>
```

#### 5.2 錯誤訊息改善

**分層錯誤處理**：
```javascript
let errorMessage = '初始化失敗，請重新整理頁面';
if (error.message && error.message.includes('LIFF SDK not loaded')) {
    errorMessage = 'LIFF SDK 載入失敗，請檢查網路連線或重新整理頁面';
} else if (error.message && error.message.includes('permission')) {
    errorMessage = '權限設定有誤，請聯繫客服';
}
```

**自動隱藏機制**：
```javascript
// 錯誤訊息 5 秒後自動隱藏，其他訊息 3 秒
const hideDelay = type === 'error' ? 5000 : 3000;
```

## 核心架構設計

### 初始化流程
```
DOM Ready → waitForLIFF() → init() → loadAdminData() → populateCounties()
    ↓
setupEventListeners() → 監聽用戶操作
```

### 資料載入策略
```
正常進入：靜默載入，無用戶提示
異常恢復：ensureDataLoaded() → 顯示載入提示 → 恢復資料
```

### 錯誤處理層級
1. **SDK 載入層**：waitForLIFF() 處理 SDK 載入失敗
2. **初始化層**：init() 處理 LIFF 初始化錯誤
3. **資料載入層**：loadAdminData() 處理 API 請求錯誤
4. **用戶操作層**：ensureDataLoaded() 處理資料恢復

## 關鍵技術決策

### 1. 不使用定期檢查
**原因**：定期檢查會消耗資源且不符合用戶操作流程，改用事件驅動的按需檢查。

### 2. 移除視窗關閉功能
**原因**：LIFF 環境中 `liff.closeWindow()` 通常無效，且會阻止用戶設定多個地點。

### 3. 保持最小 Scope 權限
**原因**：避免用戶對隱私的疑慮，遵循最小權限原則。

### 4. 漸進式錯誤處理
**原因**：不同層級的錯誤需要不同的處理策略，提供更精確的錯誤訊息。

## 監控與維護

### 健康檢查腳本
```bash
# scripts/check_liff_health.sh
# 檢查 LIFF 頁面和 SDK 的可用性
curl -f -s -o /dev/null "$LIFF_URL"
curl -f -s -o /dev/null "$LIFF_SDK_URL"
```

### 建議監控項目
1. LIFF SDK 可用性
2. 地區資料 API 回應時間
3. 用戶設定成功率
4. 錯誤訊息出現頻率

## 後續改進方向

1. **錯誤追蹤**：整合如 Sentry 等錯誤追蹤服務
2. **性能監控**：監控資料載入時間和用戶操作流程
3. **A/B測試**：測試不同的錯誤提示文案效果
4. **離線支援**：考慮在網路不穩定時的降級方案

## 測試驗證

### 手動測試場景
1. 正常進入頁面載入
2. 模擬 SDK 載入失敗
3. 模擬 LINE 自動重新登入
4. 設定多個地點的用戶流程
5. 重置按鈕功能驗證

### 預期改善效果
- ✅ 消除 LIFF SDK 載入錯誤
- ✅ 解決權限 scope 相關錯誤
- ✅ 提升在 LINE 自動重新登入情況下的穩定性
- ✅ 改善用戶操作流程和按鈕行為
- ✅ 提供更友善的錯誤提示和載入反饋
