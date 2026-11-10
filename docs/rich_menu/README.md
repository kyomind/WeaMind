# WeaMind Rich Menu 設計規格

## LINE Rich Menu 規範
- 圖片尺寸：2500x1686 像素
- 檔案格式：JPEG 或 PNG
- 檔案大小：最大 1MB
- 版面配置：六格 (2x3)

## WeaMind Rich Menu 配置

### 格子分割 (每格約 833x843 像素)
```
┌─────────────┬─────────────┬─────────────┐
│   查住家    │   查公司    │  最近查過   │
│ (1st grid)  │ (2nd grid)  │ (3rd grid)  │
│  🏠 住家    │  🏢 公司    │  📜 最近    │
├─────────────┼─────────────┼─────────────┤
│  地圖查詢   │  設定地點   │    其它     │
│ (4th grid)  │ (5th grid)  │ (6th grid)  │
│  📍 現在    │  ⚙️ 設定     │  📢 更多    │
└─────────────┴─────────────┴─────────────┘
```

## 設計建議

### 配色方案
- 主色調：天藍色系 (#4A90E2, #87CEEB)
- 背景：淺藍漸層或白色
- 文字：深藍色 (#2C3E50) 或黑色
- 分隔線：淺灰色 (#E8E8E8)

### 圖示建議
- 🏠 住家：房屋圖示
- 🏢 公司：辦公大樓圖示
- 📜 最近查過：時鐘或歷史圖示
- 📍 地圖查詢：定位圖示
- ⚙️ 設定地點：齒輪或設定圖示
- 📢 其它：資訊或更多選項圖示

### 文字規範
- 字體：建議使用無襯線字體 (如 Noto Sans TC)
- 主標題：24-28px
- 副標題：18-22px
- 行距：適中，確保清晰易讀

## 按鈕動作

各格子的 Postback data 或 URI：
- 查住家：`action=weather&type=home`
- 查公司：`action=weather&type=office`
- 最近查過：`action=recent_queries`
- 地圖查詢（URI）：`https://line.me/R/nv/location/`
- 設定地點（URI）：`https://api.kyomind.tw/static/liff/location/index.html`
- 其它：`action=other&type=menu`

「地圖查詢」直接開啟 LINE 原生位置畫面，不再先回覆提示與 Quick Reply。使用者選點或送出目前位置後，沿用現有位置訊息的天氣查詢流程；六宮格圖片、名稱與點擊區域不變。舊選單的 `action=weather&type=current` Postback 處理保留相容。

此 URI 僅支援手機 LINE 中使用者與官方帳號的一對一聊天室，不支援電腦版、群組或 LIFF。參考 [LINE 官方 URL scheme 文件](https://developers.line.biz/en/docs/messaging-api/using-line-url-scheme/#sending-the-location-screen)。

修改 JSON 不會更新既有線上選單；正式啟用時需另行建立選單、上傳既有圖片並設為預設。本次不執行正式更新。

## 檔案命名
- 設計檔案：`rich_menu_design.psd` 或 `rich_menu_design.sketch`
- 最終圖片：`rich_menu.png`
- 備用圖片：`rich_menu_alt.png`
