# FIX-LIFF-Location-Settings-Authentication-Cache-Issues.md

## 問題概述
**日期：** 2025年8月17日  
**功能：** LIFF 地點設定 ("設定地點" 指令)  
**主要問題：** Token 過期、無限登入循環、瀏覽器快取問題  

## 發現的錯誤

### 1. LIFF URL 路徑錯誤
**錯誤現象：**
- 初始 LIFF URL 缺少 `index.html`
- 用戶點擊 "設定地點" 後無法正常載入頁面

**錯誤原因：**
- LIFF 設定中的端點 URL 不完整
- 缺少具體的 HTML 檔案路徑

**解決方案：**
- 修正 LIFF 端點 URL 為完整路徑包含 `index.html`

### 2. 錯誤使用 ID Token 進行 API 驗證
**錯誤現象：**
```
Invalid LINE ID Token: ID token has expired
```
- 10小時前產生的 ID Token 已過期
- 使用者陷入無限重定向循環
- OAuth 參數不斷累加到 URL

**錯誤原因：**
- **根本問題：ID Token 不應該用於 API 驗證**
- ID Token 設計用途是身份驗證 (Authentication)，不是授權驗證 (Authorization)
- Access Token 才是用於 API 呼叫的正確 Token 類型
- 誤用 ID Token 導致後續的過期和循環問題

**解決方案：**
- 從 ID Token 認證切換至 Access Token 認證
- 使用 Access Token 進行後端 API 驗證
- 實作 `verify_line_access_token()` 函數
- 改善 OAuth 重定向處理邏輯

### 3. 瀏覽器快取問題
**錯誤現象：**
- 程式碼更新後，瀏覽器仍載入舊版本
- 強制重整（Ctrl+F5）無效
- LIFF 環境的強烈快取行為

**錯誤原因：**
- LIFF 瀏覽器環境對靜態資源有極強的快取策略
- 缺乏版本控制機制
- HTTP 快取標頭不足以破除快取

**解決方案：**
- 實作版本控制參數 `?v=YYYYMMDD-HHMM`
- 在 HTML 和 JS 檔案中加入 `AUTO_UPDATE_VERSION` 註解
- 創建自動化版本更新腳本

### 4. LIFF Scope 權限問題
**錯誤現象：**
- 缺少 `chat_message.write` 權限警告
- 無法傳送確認訊息到 LINE 聊天室

**錯誤原因：**
- LIFF 應用程式 scope 設定不完整
- 僅有 `profile` 和 `openid` 權限

**解決方案：**
- 在 LINE Developers Console 中新增 `chat_message.write` scope
- 更新 LIFF 權限設定

## 修正過程

### 階段 1: 基礎功能實作
1. **建立 LIFF 頁面結構**
   - 創建 `static/liff/location/index.html`
   - 實作雙層地區選擇（縣市/行政區）
   - 設定表單驗證邏輯

2. **後端 API 整合**
   - 建立 `/users/locations` API 端點
   - 實作地點資料儲存邏輯
   - 整合使用者認證機制

### 階段 2: 認證問題排查
1. **發現 ID Token 過期問題**
   ```javascript
   // 錯誤的認證方式
   const idToken = liff.getIDToken();
   // Token 已過期 10 小時
   ```

2. **實作正確的 Access Token 認證**
   ```python
   # app/core/auth.py
   async def verify_line_access_token(access_token: str) -> dict:
       async with httpx.AsyncClient() as client:
           response = await client.get(
               "https://api.line.me/oauth2/v2.1/verify",
               params={"access_token": access_token}
           )
   ```

3. **前端切換到正確的 Token 類型**
   ```javascript
   // 錯誤：使用 ID Token 進行 API 驗證
   const idToken = liff.getIDToken();
   
   // 正確：使用 Access Token 進行 API 驗證
   const accessToken = liff.getAccessToken();
   ```

### 階段 3: 快取問題解決
1. **發現快取問題**
   - 移除版本參數後，瀏覽器載入最舊的程式碼版本
   - 強制重整無效

2. **實作版本控制系統**
   ```html
   <!-- AUTO_UPDATE_VERSION: Cache busting version for CSS -->
   <link rel="stylesheet" href="style.css?v=20250817-1330">
   
   <!-- AUTO_UPDATE_VERSION: Cache busting version for JavaScript -->
   <script src="app.js?v=20250817-1330"></script>
   ```

3. **建立自動化工具**
   ```bash
   # scripts/update_liff_version.sh
   make update-liff-version  # 一鍵更新版本號
   ```

### 階段 4: 程式碼清理與優化
1. **移除除錯程式碼**
   - 清理 `console.log` 除錯訊息
   - 移除測試用的重定向邏輯
   - 保留功能性錯誤處理

2. **建立 AI 自動更新機制**
   - 在程式碼中加入 `AUTO_UPDATE_VERSION` 註解標記
   - 讓 AI 能自動識別並更新版本號
   - 確保每次修改都破除快取

## 最終解決方案

### 認證機制
```javascript
// 使用 Access Token 替代 ID Token
const accessToken = liff.getAccessToken();
fetch('/users/locations', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`
    }
});
```

### 版本控制
```html
<!-- 明確的版本標記供 AI 識別 -->
<!-- AUTO_UPDATE_VERSION: Cache busting version for CSS -->
<link rel="stylesheet" href="style.css?v=20250817-1330">
```

### 後端驗證
```python
# 使用 LINE API 驗證 Access Token
async def get_current_line_user_id_from_access_token(
    access_token: str = Depends(oauth2_scheme)
) -> str:
    token_info = await verify_line_access_token(access_token)
    return token_info["client_id"]
```

## 關鍵學習點

### 1. LIFF Token 使用原則
- **ID Token**：用於身份驗證 (Authentication)，確認使用者身份
- **Access Token**：用於授權驗證 (Authorization)，進行 API 呼叫
- **關鍵錯誤**：不應該使用 ID Token 進行後端 API 驗證
- LIFF 環境的 Token 快取行為非常強烈

### 2. LIFF 快取特性
- LIFF 瀏覽器對靜態資源有極強的快取策略
- 標準的 HTTP 快取標頭（`no-cache`, `no-store`）不足以破除快取
- 必須使用版本參數 (`?v=timestamp`) 強制載入新版本

### 3. 開發工作流程
- LIFF 應用程式無法本地測試，必須遠端部署
- 每次修改都需要更新版本號
- 自動化版本控制是必要的

### 4. Scope 權限管理
- LIFF scope 變更需要重新授權
- `chat_message.write` 權限是傳送訊息的必要條件

## 測試驗證

### 功能測試
✅ 地點設定表單正常運作  
✅ 縣市/行政區雙層選擇功能  
✅ API 資料儲存成功  
✅ 確認訊息傳送到 LINE 聊天室  

### 認證測試
✅ Access Token 認證機制正常  
✅ Token 過期處理邏輯正確  
✅ 無限登入循環問題已解決  

### 快取測試
✅ 版本控制破除瀏覽器快取  
✅ 程式碼修改立即生效  
✅ 自動化版本更新工具正常  

## 維護指南

### 日常開發流程
1. 修改 LIFF 相關檔案
2. 執行 `make update-liff-version` 更新版本
3. 執行 `make dev-up` 重啟 Docker
4. 測試功能是否正常

### AI 修改程式碼時
- AI 會自動識別 `AUTO_UPDATE_VERSION` 註解
- 自動生成新的時間戳記版本號
- 同步更新 HTML 和 JS 檔案中的版本參數

### 故障排查
1. **認證問題**：檢查 Access Token 是否有效
2. **快取問題**：確認版本號是否已更新
3. **Scope 問題**：檢查 LIFF Console 中的權限設定

## 相關檔案

### 核心檔案
- `static/liff/location/index.html` - LIFF 頁面
- `static/liff/location/app.js` - 前端邏輯
- `app/core/auth.py` - Access Token 驗證
- `app/user/router.py` - 地點設定 API

### 工具檔案
- `scripts/update_liff_version.sh` - 版本更新腳本
- `docs/LIFF-Version-Control-Guide.md` - AI 自動更新指南
- `Makefile` - 開發指令集

### 設定檔案
- LINE Developers Console LIFF 設定
- Docker 部署設定

## 後續改進建議

1. **監控機制**：加入 Token 過期監控和自動重新整理
2. **錯誤回報**：實作更詳細的錯誤日誌記錄
3. **測試環境**：考慮建立 LIFF 測試環境減少部署頻率
4. **版本管理**：考慮語意化版本控制 (semantic versioning)

---

**建立者：** GitHub Copilot  
**最後更新：** 2025年8月17日  
**狀態：** 已解決並正常運作
