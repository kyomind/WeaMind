# LIFF Location 目錄說明

此目錄包含 WeaMind LIFF 地點設定功能的相關檔案。

## 檔案說明

### 生產環境檔案
- `index.html` - 正式的 LIFF 頁面，只能在 LINE 環境中運行
- `app.js` - LIFF 主邏輯，包含真實的 LINE SDK 整合
- `style.css` - 樣式表

## 使用方式

### 生產環境測試
```
在 LINE 中輸入「設定地點」 → 開啟真實 LIFF 頁面
```

### 本地開發
```bash
# 啟動本地服務器
make dev-run
```

## 注意事項

⚠️ **重要提醒**:
- 此頁面只能在真實 LINE 環境中正常運作
- 所有功能測試必須在真實 LINE 環境中進行
