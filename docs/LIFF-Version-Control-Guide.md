# LIFF 版本控制 - AI 自動更新指南

## 概述
WeaMind 的 LIFF 地點設定功能使用版本控制來破除瀏覽器快取。當 AI 修改前端檔案時，應該自動更新版本號。

## 自動更新規則

### 1. HTML 檔案版本更新
檔案：`static/liff/location/index.html`

尋找包含 `AUTO_UPDATE_VERSION` 註解的行：
```html
<!-- AUTO_UPDATE_VERSION: Cache busting version for CSS -->
<link rel="stylesheet" href="style.css?v=YYYYMMDD-HHMM">

<!-- AUTO_UPDATE_VERSION: Cache busting version for JavaScript -->
<script src="app.js?v=YYYYMMDD-HHMM"></script>
```

**AI 操作指引：**
- 當修改任何 HTML/CSS/JS 檔案時，自動更新 `?v=` 後的時間戳記
- 格式：`YYYYMMDD-HHMM`（年月日-時分）
- 範例：`20250817-1430`

### 2. JavaScript 檔案版本更新
檔案：`static/liff/location/app.js`

尋找檔案開頭的版本註解：
```javascript
// AUTO_UPDATE_VERSION: YYYYMMDD-HHMM (AI can update this timestamp when making changes)
```

**AI 操作指引：**
- 修改 app.js 時，更新此註解中的時間戳記
- 與 HTML 中的版本保持一致

### 3. 版本更新時機
AI 應該在以下情況自動更新版本：
- 修改 `static/liff/location/` 目錄下任何檔案
- 修改 HTML 結構或樣式
- 修改 JavaScript 邏輯
- 修改 CSS 樣式

### 4. 手動更新方式
開發者也可以手動執行：
```bash
make update-liff-version
```

## 範例

### 修改前：
```html
<!-- AUTO_UPDATE_VERSION: Cache busting version for CSS -->
<link rel="stylesheet" href="style.css?v=20250817-1325">
```

### 修改後（AI 自動更新）：
```html
<!-- AUTO_UPDATE_VERSION: Cache busting version for CSS -->
<link rel="stylesheet" href="style.css?v=20250817-1435">
```

## 注意事項
- 版本號必須在 HTML 和 JS 檔案中保持一致
- 每次修改都應該生成新的時間戳記
- 時間戳記應該反映實際的修改時間
- AI 在回應用戶時，應該提到已更新版本號用於破除快取

## 好處
1. **自動化**：AI 修改檔案時自動處理版本控制
2. **一致性**：確保每次修改都更新版本
3. **無需人工介入**：開發者專注於功能，不需記得更新版本
4. **立即生效**：避免瀏覽器快取問題
