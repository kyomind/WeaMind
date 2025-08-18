# LIFF Location 目錄說明

此目錄包含 WeaMind LIFF 地點設定功能的相關檔案。

## 檔案說明

### 生產環境檔案
- `index.html` - 正式的 LIFF 頁面，只能在 LINE 環境中運行
- `app.js` - LIFF 主邏輯，包含真實的 LINE SDK 整合
- `style.css` - 樣式表

### 開發工具
- `dev-preview.html` - **僅供本地開發預覽使用**
  - 不包含 LIFF SDK
  - 使用模擬數據
  - 用於檢查頁面樣式和基本交互
  - **不可用於生產環境**

## 使用方式

### 生產環境測試
```
在 LINE 中輸入「設定地點」 → 開啟真實 LIFF 頁面
```

### 本地開發預覽
```bash
# 啟動本地服務器
make dev-run

# 訪問預覽頁面 (僅供樣式檢查)
open http://localhost:8000/static/liff/location/dev-preview.html
```

## 注意事項

⚠️ **dev-preview.html 警告**:
- 僅供開發時樣式檢查使用
- 無法進行真實的功能測試
- 所有業務邏輯測試必須在真實 LINE 環境中進行
