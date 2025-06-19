# LINE Bot 架構討論筆記

## 1. LINE Bot 基本架構與登入機制

### 1.0 基本架構圖

```text
LINE Platform ─→ Webhook
Webhook ─┬─→ 立即回應 OK ─→ LINE Platform
         └─→ 背景任務開始處理
               ├─→ 查詢天氣資料
               └─→ 使用 Message API 回覆用戶
```

### 1.1 使用者驗證機制

- LINE Bot 不需要獨立的登入頁面
- 使用者透過 LINE App 加入 Bot 好友時即完成驗證
- LINE 會在 webhook 事件中提供使用者的 LINE User ID

### 1.2 使用者資料流程

1. 使用者加入 Bot 時，LINE 發送 `follow` 事件到 webhook
2. 系統可以：
   - 取得使用者的 LINE User ID
   - 在資料庫建立使用者記錄
   - 發送歡迎訊息

### 1.3 必要的 API Endpoints

現階段主要需要：

- Webhook API (`/line/webhook`)：接收所有 LINE 事件
- User CRUD API：主要用於後台管理，非一般用戶使用

## 2. 使用者建立流程

### 2.1 建議的實作方式

```python
from fastapi import FastAPI, Header, Request
from app.user.crud import create_user

app = FastAPI()

@app.post("/line/webhook")
async def line_webhook(request: Request, x_line_signature: str = Header(...)):
    body = await request.body()
    # ... 驗證簽名 ...

    events = parse_webhook_body(body)

    for event in events:
        if event.type == "follow":
            # 直接在此建立使用者
            user = await create_user(
                line_user_id=event.source.user_id,
                name=event.source.display_name
            )
            # ... 發送歡迎訊息 ...
```

### 2.2 內部處理的優點

1. **效能考量**
   - 減少不必要的網路往返
   - 降低系統複雜度
   - 減少潛在的錯誤點

2. **安全性考量**
   - 核心邏輯在內部處理
   - 避免暴露不必要的 API endpoint

## 3. 訊息處理流程

### 3.1 非同步處理架構

```python
from fastapi import FastAPI, Header, Request, BackgroundTasks
from app.weather.service import process_weather_request

app = FastAPI()

@app.post("/line/webhook")
async def line_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_line_signature: str = Header(...)
):
    body = await request.body()
    events = parse_webhook_body(body)

    # 將事件處理加入背景任務
    for event in events:
        background_tasks.add_task(process_weather_request, event)

    # 立即回應 LINE Platform
    return {"message": "OK"}
```

### 3.2 背景處理函式

```python
async def process_weather_request(event):
    """在背景處理天氣查詢請求"""
    try:
        if event.type == "message" and event.message.type == "text":
            user_input = event.message.text

            # 耗時的天氣查詢處理
            weather_info = await get_weather_info(user_input)

            # 使用 LINE Message API 回覆用戶
            await send_text_message(
                to=event.source.user_id,
                text=weather_info
            )
    except Exception as e:
        # 錯誤處理...
        logger.error(f"處理天氣請求時發生錯誤: {str(e)}")
```

### 3.3 非同步處理的重要性

1. **符合 LINE 平台要求**
   - LINE Platform 期望在 1 秒內收到回應
   - 超時可能導致重試機制啟動

2. **處理流程**

   ```text
   LINE Platform ─→ Webhook
   Webhook ─┬─→ 立即回應 OK ─→ LINE Platform
           └─→ 背景任務開始處理
                  ├─→ 查詢天氣資料
                  └─→ 使用 Message API 回覆用戶
   ```

3. **系統優勢**
   - 快速回應 webhook 請求
   - 複雜邏輯在背景處理
   - 更好的錯誤處理機制
   - 更有效的資源利用

## 4. 實作注意事項

1. 使用 FastAPI 的 `BackgroundTasks` 處理耗時操作
2. 確保 webhook 快速回應
3. 實作適當的錯誤處理機制
4. 考慮加入日誌記錄
5. 視需要實作重試機制

## 5. 後續可能的擴展

1. 後台管理介面
2. 系統監控
3. LIFF 網頁功能（如果需要）
4. 第三方服務整合

---

- [ ] 12.建立 line webhook API endpoint，能正確接收與驗證來自 LINE 的 webhook 請求
  - **目的**：建立一個可接收 LINE webhook 請求的 API endpoint，並驗證請求的合法性。由於本專案現階段唯一且最重要的 API 即為此 webhook，應直接設置於 `app/main.py`，作為專案的中心 API 入口。
  - **預期成果**：能夠於 FastAPI app 的主程式中正確接收來自 LINE 的 webhook 請求，並驗證簽名，確保安全性。
  - **可能的挑戰**：
    - 需正確解析 LINE 傳來的 JSON 結構。
    - 驗證 X-Line-Signature 標頭，確保請求來自 LINE 官方。
    - 處理 webhook event 的異常情境（如重複、格式錯誤等）。
    - 需考慮未來若有多個 webhook 或 API 時的結構擴充性。
  - **實作方向與細節**：
    1. 於 `app/main.py` 直接建立 `/line/webhook` POST endpoint，作為專案主要 API 入口。
    2. 解析 request body，並驗證 X-Line-Signature。
    3. 驗證方式可參考 LINE 官方文件，需用 channel secret 計算 HMAC-SHA256。
    4. 撰寫單元測試，模擬 webhook 請求與驗證。
    5. 撰寫文件，說明如何設定 channel secret 及測試 webhook。
    6. 若未來 API 增加，可再考慮將 webhook 拆分至專屬模組。
  - **為何重要**：此功能是與 LINE 平台串接的基礎，且現階段為專案唯一且最核心的 API，確保訊息來源安全，並可進行後續 event 處理。
