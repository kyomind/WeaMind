# Rich Menu 實作計畫文件

## 🎯 設計確認

**採用方案：PostBack Action + Display Text**
- ✅ 用戶點擊按鈕後會看到固定的顯示文字
- ✅ 伺服器收到動態的 PostBack 資料進行個人化處理
- ✅ 確保良好的用戶體驗和程式彈性

## 📱 Rich Menu 配置

### 按鈕配置表

| 位置   | 功能     | Display Text | Action Type | Action Data                   | 狀態   |
| ------ | -------- | ------------ | ----------- | ----------------------------- | ------ |
| 上排左 | 查住家   | `查住家`     | PostBack    | `action=weather&type=home`    | ✅ 實作 |
| 上排中 | 查公司   | `查公司`     | PostBack    | `action=weather&type=office`  | ✅ 實作 |
| 上排右 | 最近查過 | `最近查過`   | PostBack    | `action=recent_queries`       | 🚧 佔位 |
| 下排左 | 目前位置 | `目前位置`   | PostBack    | `action=weather&type=current` | 🚧 佔位 |
| 下排中 | 設定地點 | -            | URI         | LIFF 地點設定頁面 URL         | ✅ 實作 |
| 下排右 | 其它     | `其它`       | PostBack    | `action=menu&type=more`       | 🚧 佔位 |

### Rich Menu JSON 設定

```json
{
  "size": {
    "width": 2500,
    "height": 1686
  },
  "selected": false,
  "name": "WeaMind Main Menu",
  "chatBarText": "選單",
  "areas": [
    {
      "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
      "action": {
        "type": "postback",
        "data": "action=weather&type=home",
        "displayText": "查住家"
      }
    },
    {
      "bounds": {"x": 833, "y": 0, "width": 833, "height": 843},
      "action": {
        "type": "postback", 
        "data": "action=weather&type=office",
        "displayText": "查公司"
      }
    },
    {
      "bounds": {"x": 1666, "y": 0, "width": 834, "height": 843},
      "action": {
        "type": "postback",
        "data": "action=recent_queries", 
        "displayText": "最近查過"
      }
    },
    {
      "bounds": {"x": 0, "y": 843, "width": 833, "height": 843},
      "action": {
        "type": "postback",
        "data": "action=weather&type=current",
        "displayText": "目前位置"
      }
    },
    {
      "bounds": {"x": 833, "y": 843, "width": 833, "height": 843},
      "action": {
        "type": "uri",
        "uri": "https://api.kyomind.tw/static/liff/location/index.html"
      }
    },
    {
      "bounds": {"x": 1666, "y": 843, "width": 834, "height": 843},
      "action": {
        "type": "postback",
        "data": "action=menu&type=more",
        "displayText": "其它"
      }
    }
  ]
}
```

## 🔧 程式實作

### 1. PostBack 事件處理器

```python
# app/line/service.py 新增 import
from linebot.v3.webhooks import PostbackEvent
from urllib.parse import parse_qs

@webhook_handler.add(PostbackEvent)
def handle_postback_event(event: PostbackEvent) -> None:
    """
    Handle PostBack events from Rich Menu clicks.
    
    Args:
        event: The LINE PostBack event
    """
    try:
        # Parse PostBack data
        postback_data = parse_postback_data(event.postback.data)
        
        # Get user ID
        user_id = getattr(event.source, "user_id", None) if event.source else None
        if not user_id:
            logger.warning("PostBack event without user_id")
            return
            
        # Route to appropriate handler
        if postback_data.get("action") == "weather":
            handle_weather_postback(event, user_id, postback_data)
        elif postback_data.get("action") == "settings":
            handle_settings_postback(event, postback_data)
        elif postback_data.get("action") == "recent_queries":
            handle_recent_queries_postback(event)
        elif postback_data.get("action") == "menu":
            handle_menu_postback(event, postback_data)
        else:
            logger.warning(f"Unknown PostBack action: {postback_data}")
            send_error_response(event.reply_token, "未知的操作")
            
    except Exception:
        logger.exception("Error handling PostBack event")
        send_error_response(event.reply_token, "😅 系統暫時有點忙，請稍後再試一次。")
```

### 2. PostBack 資料解析函數

```python
def parse_postback_data(data: str) -> dict[str, str]:
    """
    Parse PostBack data string into dictionary.
    
    Args:
        data: PostBack data string (e.g., "action=weather&type=home")
        
    Returns:
        Dictionary of parsed data
    """
    try:
        # Parse query string format
        parsed = parse_qs(data)
        # Convert list values to single strings
        return {key: values[0] for key, values in parsed.items() if values}
    except Exception:
        logger.warning(f"Failed to parse PostBack data: {data}")
        return {}
```

### 3. 天氣查詢處理器

```python
def handle_weather_postback(event: PostbackEvent, user_id: str, data: dict[str, str]) -> None:
    """
    Handle weather-related PostBack events.
    
    Args:
        event: PostBack event
        user_id: LINE user ID
        data: Parsed PostBack data
    """
    location_type = data.get("type")
    
    if location_type in ["home", "office"]:
        handle_user_location_weather(event, user_id, location_type)
    elif location_type == "current":
        handle_current_location_weather(event)
    else:
        send_error_response(event.reply_token, "未知的地點類型")

def handle_user_location_weather(event: PostbackEvent, user_id: str, location_type: str) -> None:
    """
    Handle home/office weather queries.
    
    Args:
        event: PostBack event
        user_id: LINE user ID  
        location_type: "home" or "office"
    """
    session = next(get_session())
    
    try:
        # Get user from database
        user = get_user_by_line_id(session, user_id)
        if not user:
            send_error_response(event.reply_token, "用戶不存在，請重新加入好友")
            return
            
        # Get user's location
        if location_type == "home":
            location = user.home_location
            location_name = "住家"
        else:  # office
            location = user.work_location  
            location_name = "公司"
            
        if not location:
            send_location_not_set_response(event.reply_token, location_name)
            return
            
        # Query weather using existing logic
        location_text = location.full_name
        locations, response_message = LocationService.parse_location_input(session, location_text)
        
        # Send response
        send_text_response(event.reply_token, response_message)
        
    except Exception:
        logger.exception(f"Error handling {location_type} weather query")
        send_error_response(event.reply_token, "😅 查詢時發生錯誤，請稍後再試。")
    finally:
        session.close()
```

### 4. 設定功能處理器

```python
def handle_settings_postback(event: PostbackEvent, data: dict[str, str]) -> None:
    """
    Handle settings-related PostBack events.
    
    Note: 「設定地點」按鈕已改為 URI Action，直接開啟 LIFF 頁面，
    所以這個函數可能不會被 location 類型的事件觸發。
    
    Args:
        event: PostBack event
        data: Parsed PostBack data
    """
    settings_type = data.get("type")
    
    if settings_type == "location":
        # This should not be reached if using URI action
        logger.warning("Location setting via PostBack - should use URI action instead")
        send_liff_location_setting_response(event.reply_token)
    else:
        send_error_response(event.reply_token, "未知的設定類型")
```

### 5. 佔位功能處理器

```python
def handle_recent_queries_postback(event: PostbackEvent) -> None:
    """Handle recent queries PostBack (placeholder)."""
    send_text_response(event.reply_token, "📜 最近查過功能即將推出，敬請期待！")

def handle_current_location_weather(event: PostbackEvent) -> None:
    """Handle current location weather PostBack (placeholder).""" 
    send_text_response(event.reply_token, "📍 目前位置功能即將推出，敬請期待！")

def handle_menu_postback(event: PostbackEvent, data: dict[str, str]) -> None:
    """Handle menu PostBack (placeholder)."""
    send_text_response(event.reply_token, "📢 更多功能即將推出，敬請期待！")
```

### 6. 回應函數

```python
def send_text_response(reply_token: str, text: str) -> None:
    """Send simple text response."""
    with ApiClient(configuration) as api_client:
        messaging_api_client = MessagingApi(api_client)
        try:
            messaging_api_client.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=text)],
                    notification_disabled=False,
                )
            )
        except Exception:
            logger.exception("Error sending text response")

def send_location_not_set_response(reply_token: str, location_name: str) -> None:
    """Send response when user location is not set."""
    message = f"請先設定{location_name}地址，點擊下方「設定地點」按鈕即可設定。"
    send_text_response(reply_token, message)

def send_error_response(reply_token: str, message: str) -> None:
    """Send error response."""
    send_text_response(reply_token, message)
```

## 🧪 測試計畫

### 單元測試

```python
# tests/line/test_postback.py
def test_parse_postback_data():
    """Test PostBack data parsing."""
    assert parse_postback_data("action=weather&type=home") == {
        "action": "weather", "type": "home"
    }

def test_handle_home_weather_success():
    """Test successful home weather query."""
    # Mock user with home location set
    # Assert correct response

def test_handle_home_weather_not_set():
    """Test home weather query when location not set.""" 
    # Mock user without home location
    # Assert "please set location" response
```

### 整合測試

1. **PostBack 事件處理流程**
2. **與現有 LocationService 整合**
3. **LIFF 功能整合**

### 手動測試

1. **Rich Menu 上傳**
2. **各按鈕點擊測試**
3. **錯誤情況測試**

## 📋 實作檢查清單

### Phase 0: Rich Menu 上傳 ✅ 完成
- [x] 修正 Rich Menu 管理腳本的 API 端點問題
- [x] 圖片上傳 API 改用 `https://api-data.line.me` 端點  
- [x] Rich Menu 配置改為從 JSON 檔案載入
- [x] 成功上傳 Rich Menu 並設定為預設選單
- [x] **Rich Menu ID**: `richmenu-4dd9eb07d74940972085df45d6e0406c`

### Phase 1: 核心功能
- [ ] 新增 PostbackEvent import 和處理器
- [ ] 實作 parse_postback_data 函數
- [ ] 實作 handle_postback_event 主函數
- [ ] 實作 handle_weather_postback 功能
- [ ] 實作查住家/查公司邏輯
- [x] ~~整合現有 LIFF 設定功能~~ 改為 URI Action 直接開啟

### Phase 2: 完善功能  
- [ ] 新增佔位回應函數
- [ ] 新增錯誤處理函數
- [ ] 撰寫單元測試
- [ ] 執行整合測試

### Phase 3: 部署
- [x] Rich Menu 圖片上傳
- [x] Rich Menu JSON 設定
- [ ] 實機測試驗證

## 📝 已解決的技術問題

### 1. LINE API 端點修正
**問題**: 圖片上傳時出現 404 錯誤
**解決方案**: 
- Rich Menu 建立/管理: `https://api.line.me/v2/bot/richmenu`
- 圖片上傳: `https://api-data.line.me/v2/bot/richmenu/{richMenuId}/content`

### 2. 配置檔案優化
**修正內容**:
```python
# 修正前 - 硬編碼配置
RICH_MENU_CONFIG = {...}

# 修正後 - 從 JSON 檔案載入
def load_rich_menu_config() -> dict:
    with open(RICH_MENU_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)
```

### 3. 上傳成功記錄
- 使用壓縮版圖片: `rich_menu_template-min.png` (122K)
- Rich Menu ID: `richmenu-4dd9eb07d74940972085df45d6e0406c`
- 已設定為所有用戶的預設選單

## 🎉 預期成果

完成後用戶體驗：

```
用戶點擊「查住家」
聊天室顯示：查住家天氣
機器人回覆：正在查詢台北市中正區...（基於用戶設定）

用戶點擊「設定地點」  
→ 直接開啟 LIFF 地點設定網頁（無聊天室訊息，一鍵直達）
```

## 🚀 下一步行動

Rich Menu 已成功部署！接下來需要：

1. **實作 PostBack 事件處理** - 在 `app/line/service.py` 添加處理器
2. **整合現有功能** - 連接天氣查詢和 LIFF 設定功能  
3. **測試驗證** - 確保所有按鈕功能正常運作

**建議開新對話進行程式實作，以獲得更好的開發體驗！** 🎯

---

**準備開始實作了嗎？建議按照 Phase 順序進行！** 🚀
