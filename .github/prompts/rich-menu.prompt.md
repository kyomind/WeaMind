---
mode: 'agent'
description: 'Rich Menu 管理和上傳指南'
---

# Rich Menu 管理和上傳指南

## 概述

WeaMind 專案提供完整的 Rich Menu 自動化管理工具，包含圖片上傳、配置設定、以及 PostBack 事件處理。本指南說明如何使用專案內建的 Rich Menu 管理功能。

## 工具架構

### 核心檔案
- **管理腳本**: `scripts/rich_menu_manager.py`
- **Makefile 指令**: `upload`, `upload-list`, `upload-delete`
- **設計文檔**: `docs/rich_menu/README.md`
- **實作計畫**: `docs/rich_menu/implementation-plan.md`

### 技術依賴
- **HTTP 客戶端**: httpx (已安裝)
- **LINE API**: LINE Bot SDK
- **環境變數**: `LINE_CHANNEL_ACCESS_TOKEN`

## Rich Menu 上傳流程

### 準備階段

#### 1. 圖片規格確認
```
尺寸: 2500 x 1686 像素
格式: PNG 或 JPEG  
大小: < 1MB
配置: 六格 (2x3) 佈局
```

#### 2. 按鈕配置 (已預設)
```
上排左 (查住家): x=0, y=0, width=833, height=843
上排中 (查公司): x=833, y=0, width=833, height=843  
上排右 (最近查過): x=1666, y=0, width=834, height=843
下排左 (目前位置): x=0, y=843, width=833, height=843
下排中 (設定地點): x=833, y=843, width=833, height=843
下排右 (其它): x=1666, y=843, width=834, height=843
```

### 上傳操作

#### 建立新的 Rich Menu
```bash
# 基本上傳 (會自動設定為預設)
make upload IMAGE=path/to/rich_menu.png

# 範例: 上傳設計檔案
make upload IMAGE=docs/rich_menu/rich_menu.png
```

#### 管理現有 Rich Menu
```bash
# 列出所有 Rich Menu
make upload-list

# 刪除指定 Rich Menu  
make upload-delete ID=richmenu-xxx-xxx-xxx
```

### PostBack 資料格式 (已預設)

每個按鈕的 PostBack 配置：

```json
{
  "查住家": {
    "data": "action=weather&type=home",
    "displayText": "查住家"
  },
  "查公司": {
    "data": "action=weather&type=office", 
    "displayText": "查公司"
  },
  "最近查過": {
    "data": "action=recent_queries",
    "displayText": "最近查過"
  },
  "目前位置": {
    "data": "action=weather&type=current",
    "displayText": "目前位置"
  },
  "設定地點": {
    "data": "action=settings&type=location",
    "displayText": "設定地點"
  },
  "其它": {
    "data": "action=menu&type=more",
    "displayText": "其它"
  }
}
```

## 程式實作指南

### PostBack 事件處理

Rich Menu 點擊會觸發 PostbackEvent，需要在 `app/line/service.py` 中實作：

```python
from linebot.v3.webhooks import PostbackEvent

@webhook_handler.add(PostbackEvent)
def handle_postback_event(event: PostbackEvent) -> None:
    """處理 Rich Menu PostBack 事件"""
    # 解析 PostBack 資料
    data = parse_postback_data(event.postback.data)
    
    # 路由到對應處理器
    if data.get("action") == "weather":
        handle_weather_postback(event, user_id, data)
    elif data.get("action") == "settings":
        handle_settings_postback(event, data)
    # ... 其他處理邏輯
```

### 功能實作優先順序

1. **立即實作**: 查住家、查公司、設定地點
2. **佔位回應**: 最近查過、目前位置、其它
3. **後續擴充**: 完整功能實作

## 常見問題與解決方案

### 上傳失敗
```bash
# 檢查環境變數
echo $LINE_CHANNEL_ACCESS_TOKEN

# 檢查圖片規格
file path/to/image.png
identify path/to/image.png  # 需要 ImageMagick
```

### Rich Menu 不顯示
- 確認已設定為預設 Rich Menu
- 檢查用戶是否已加入好友
- 重新加入 Bot 或清除聊天記錄

### PostBack 事件未觸發
- 確認 webhook URL 設定正確
- 檢查 PostbackEvent handler 是否註冊
- 查看伺服器 log 中的錯誤訊息

## 測試流程

### 1. 上傳驗證
```bash
# 上傳 Rich Menu
make upload IMAGE=test_menu.png

# 確認上傳成功
make upload-list
```

### 2. 功能測試
- 點擊 Rich Menu 按鈕
- 檢查聊天室回應
- 確認 PostBack 資料正確

### 3. 清理測試
```bash
# 刪除測試用 Rich Menu
make upload-delete ID=test_menu_id
```

## 最佳實務

### 開發階段
1. **先手動上傳**測試圖片和座標
2. **實作 PostBack 處理**邏輯
3. **用腳本自動化**正式部署

### 生產環境
1. **版本控制**Rich Menu 圖片和配置
2. **備份現有**Rich Menu ID
3. **分階段部署**避免影響用戶

### 維護管理
1. **定期清理**未使用的 Rich Menu
2. **監控 API**使用量和錯誤率
3. **追蹤用戶**點擊行為數據

## 進階功能

### 條件式 Rich Menu
```python
# 根據用戶狀態設定不同 Rich Menu
if user.has_home_location:
    set_rich_menu(user_id, "full_menu_id")
else:
    set_rich_menu(user_id, "setup_menu_id")
```

### A/B 測試
```python
# 隨機分配不同 Rich Menu 進行測試
import random
menu_id = random.choice(["menu_a_id", "menu_b_id"])
set_rich_menu(user_id, menu_id)
```

---

**注意**: 所有座標、PostBack 資料、和 API 調用邏輯都已在 `scripts/rich_menu_manager.py` 中預先配置，AI 助手可以直接使用而無需手動計算或輸入。
