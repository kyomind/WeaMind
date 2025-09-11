# 📍 Rich Menu 地圖查詢功能UI文字優化實作紀錄

## 📋 功能概述

**開發分支**: `feature/map-query-ui-text-updates`
**開發時間**: 2025年9月11日
**完成狀態**: ✅ 已完成並部署新的Rich Menu

針對WeaMind LINE Bot的「目前位置」功能進行UI文字優化，解決用戶對功能理解的誤區，並更準確地反映實際的使用體驗。

## 🎯 問題分析與技術決策

### 核心問題識別

**原始問題**:
- Rich Menu按鈕標籤「目前位置」暗示自動GPS定位
- 實際功能是LINE地圖手動選點
- 用戶期待與實際體驗存在落差
- 「目前位置」帶有隱私壓力感

**技術分析**:
```
用戶期待: 自動GPS → 當前真實位置
實際功能: 地圖選點 → 用戶指定任意位置
```

### 設計原則制定

**訊息流設計原則**: 「細節從少到多」
1. **Rich Menu按鈕**: 最簡潔，吸引點擊
2. **PostBack顯示文字**: 適中詳細，確認操作
3. **操作提示訊息**: 最詳細，指導操作

**文字策略**:
- 去除隱私感暗示
- 突出功能賣點（台灣任意位置，無需輸入文字）
- 準確描述操作流程

## 🔧 技術實作方案

### 核心架構

```
LINE Bot Rich Menu → PostBack Event → Location Request → Map Selection
     ↓                    ↓                 ↓               ↓
  地圖查詢         依地圖查詢天氣    開啟地圖選擇    點選任意位置
```

### 關鍵檔案修改

#### 1. Rich Menu配置 (`docs/rich_menu/rich_menu_config.json`)

**修改前**:
```json
{
    "action": {
        "type": "postback",
        "data": "action=weather&type=current",
        "displayText": "查目前位置天氣"
    }
}
```

**修改後**:
```json
{
    "action": {
        "type": "postback",
        "data": "action=weather&type=current",
        "displayText": "依地圖查詢天氣"
    }
}
```

**技術決策**: 保持PostBack data不變，確保後端邏輯相容性

#### 2. LINE服務邏輯 (`app/line/service.py`)

**核心函式**: `handle_current_location_weather()`

**修改前**:
```python
message_text = "請分享您的位置，我將為您查詢當地天氣"
action=LocationAction(
    type="location",
    label="分享我的位置"
)
```

**修改後**:
```python
message_text = "請點點地圖上任意位置，我將為您查詢該地天氣"
action=LocationAction(
    type="location",
    label="開啟地圖選擇"
)
```

**技術決策**: 維持LocationAction架構，僅調整用戶介面文字

#### 3. Rich Menu視覺設計 (`docs/rich_menu/rich_menu_template.svg`)

**修改內容**:
- 按鈕文字: `目前位置` → `地圖查詢`
- 註解更新: 統一術語使用

### 完整修改清單

| 檔案類型      | 檔案路徑                                | 修改內容                  |
| ------------- | --------------------------------------- | ------------------------- |
| Rich Menu配置 | `docs/rich_menu/rich_menu_config.json`  | PostBack顯示文字          |
| 後端服務      | `app/line/service.py`                   | 提示訊息、Quick Reply標籤 |
| 視覺設計      | `docs/rich_menu/rich_menu_template.svg` | 按鈕文字、註解            |
| 幫助文檔      | `static/help/index.html`                | 功能說明、使用提示        |
| 設計文檔      | `docs/rich_menu/README.md`              | 格子分割說明、圖示建議    |
| 預覽頁面      | `docs/rich_menu/archive/preview.html`   | 按鈕標題                  |
| 測試檔案      | `tests/line/test_postback.py`           | 斷言內容                  |
| 公告內容      | `static/announcements.json`             | 功能介紹                  |

## 🚀 部署流程

### 1. 分支管理
```bash
git checkout -b feature/map-query-ui-text-updates
```

### 2. 文字內容更新
- 使用VS Code的replace_string_in_file工具
- 確保上下文匹配，避免誤修改
- 同步更新所有相關檔案

### 3. Rich Menu部署
```bash
make upload IMAGE=docs/rich_menu/rich_menu.png
```

**部署結果**:
- 新Rich Menu ID: `richmenu-133053dd2e7375a8ab18ced0deb51708`
- 自動設定為預設選單
- 即時生效於所有用戶

## 🧪 測試驗證

### 功能測試
1. **Rich Menu顯示**: ✅ 按鈕文字正確顯示「地圖查詢」
2. **PostBack事件**: ✅ 點擊後顯示「依地圖查詢天氣」
3. **位置請求**: ✅ 提示訊息準確描述操作
4. **Quick Reply**: ✅ 按鈕標籤為「開啟地圖選擇」

### 自動化測試更新
```python
# 更新測試斷言
assert message.text == "請點點地圖上任意位置，我將為您查詢該地天氣"
assert message.quick_reply.items[0].action.label == "開啟地圖選擇"
```

## 💡 重要技術決策

### 1. 向後相容性維持
**決策**: 保持PostBack data格式不變
**原因**:
- 避免影響現有後端邏輯
- 降低部署風險
- 僅調整用戶介面層

### 2. 訊息層級設計
**決策**: 採用「細節從少到多」原則
**原因**:
- 符合用戶認知習慣
- 避免資訊過載
- 提供漸進式引導

### 3. 術語統一標準化
**決策**: 全面使用「地圖查詢」術語
**原因**:
- 消除功能理解歧義
- 突出核心賣點
- 降低隱私顧慮

## 🔍 核心程式碼邏輯

### PostBack事件路由
```python
@webhook_handler.add(PostbackEvent)
def handle_postback_event(event: PostbackEvent) -> None:
    postback_data = parse_postback_data(event.postback.data)

    if postback_data.get("action") == "weather":
        if postback_data.get("type") == "current":
            handle_current_location_weather(event)  # 地圖查詢流程
```

### 位置請求處理
```python
def handle_current_location_weather(event: PostbackEvent) -> None:
    """處理地圖查詢PostBack - 請求用戶選擇位置"""
    message_text = "請點點地圖上任意位置，我將為您查詢該地天氣"

    quick_reply_items = [
        QuickReplyItem(
            action=LocationAction(
                type="location",
                label="開啟地圖選擇"
            )
        )
    ]
```

### 位置資訊處理
```python
@webhook_handler.add(MessageEvent, message=LocationMessageContent)
def handle_location_message_event(event: MessageEvent) -> None:
    """處理用戶地圖選擇的位置資訊"""
    lat = message.latitude
    lon = message.longitude
    address = getattr(message, "address", None)

    # 使用地址優先 + GPS備援策略
    response_message = WeatherService.handle_location_weather_query(
        session, lat, lon, address
    )
```

## 📊 效果評估

### 用戶體驗改進
- ✅ 消除「目前位置」隱私顧慮
- ✅ 準確描述實際操作流程
- ✅ 突出無需輸入文字的便利性
- ✅ 降低功能理解門檻

### 技術品質提升
- ✅ 統一術語使用
- ✅ 完善測試覆蓋
- ✅ 文檔同步更新
- ✅ 向後相容性維持

## 🔮 後續優化建議

### 短期優化
1. **用戶行為監控**: 追蹤地圖查詢使用率變化
2. **錯誤處理強化**: 地圖選擇失敗的fallback機制
3. **使用者回饋收集**: 新文字是否更清楚易懂

### 長期規劃
1. **地圖功能擴展**: 考慮整合更多地圖相關功能
2. **個人化體驗**: 根據用戶習慣調整介面文字
3. **多語言支援**: 為不同語言用戶優化表達方式

## 📚 相關文檔

- **Rich Menu管理指南**: `.github/prompts/rich-menu.prompt.md`
- **設計規格**: `docs/rich_menu/README.md`
- **架構說明**: `docs/Architecture.md`
- **測試指南**: `.github/instructions/testing-guidelines.instructions.md`

---

**開發者**: GitHub Copilot (AI Assistant)
**審核者**: kyomind
**部署時間**: 2025年9月11日
**Rich Menu ID**: `richmenu-133053dd2e7375a8ab18ced0deb51708`
