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
│  目前位置   │  設定地點   │    其它     │
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
- 📍 目前位置：定位圖示
- ⚙️ 設定地點：齒輪或設定圖示
- 📢 其它：資訊或更多選項圖示

### 文字規範
- 字體：建議使用無襯線字體 (如 Noto Sans TC)
- 主標題：24-28px
- 副標題：18-22px
- 行距：適中，確保清晰易讀

## PostBack 資料格式

每個格子對應的 postback data：
- 查住家：`action=weather&type=home`
- 查公司：`action=weather&type=office`
- 最近查過：`action=recent_queries`
- 目前位置：`action=weather&type=current`
- 設定地點：`action=settings&type=location`
- 其它：`action=other&type=menu`

## 檔案命名
- 設計檔案：`rich_menu_design.psd` 或 `rich_menu_design.sketch`
- 最終圖片：`rich_menu.png`
- 備用圖片：`rich_menu_alt.png`
