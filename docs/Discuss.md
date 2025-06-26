# 討論紀錄：LINE Webhook 雲端部署與應聲蟲功能

## 主要邏輯鏈條

1. 本地開發完成 webhook 端點（已完成）
2. 準備雲端 VM（已具備）
3. 雲端 VM 上 Git 複製專案
4. 設定 Nginx 反向代理，讓 webhook 能被外部存取（含 HTTPS 憑證）
5. 在 LINE Developers 後台設定 webhook URL，指向雲端公開網址
6. 測試 LINE 傳訊息，API 能收到並正確回應（如應聲蟲回覆）
7. （可選）將 webhook 收到的 userId/訊息等資料存入資料庫

## Todo 拆解建議

- 每個 todo 控制在 45-75 分鐘內，避免過大或過小
- 建議優先順序：
  1. 雲端 VM 部署 FastAPI 專案（Git 複製、Docker compose up）
  2. 設定 Nginx 反向代理（含 HTTPS 憑證）
  3. LINE Developers 後台設定 webhook URL 並驗證
  4. 實作 webhook 應聲蟲功能（收到訊息原樣回覆）
  5. （可選）資料入庫

## 討論重點

- Nginx 設定與 HTTPS 憑證是部署 webhook 到雲端時最容易卡住的地方
- 每個任務都要明確、可驗收，且能快速 deliver value
- 完成前三步後，webhook 才能真正上線，後續再做訊息回覆與資料入庫

## 範例程式碼：應聲蟲 webhook handler

```python
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/line/webhook")
async def line_webhook(request: Request):
    body = await request.json()
    events = body.get("events", [])
    for event in events:
        if event.get("type") == "message":
            reply_token = event["replyToken"]
            user_message = event["message"]["text"]
            # 呼叫 LINE Messaging API 回覆訊息
            # 這裡僅示意，實際需補上 channel access token 與 requests.post
            # requests.post(
            #     "https://api.line.me/v2/bot/message/reply",
            #     headers={"Authorization": "Bearer <token>"},
            #     json={
            #         "replyToken": reply_token,
            #         "messages": [{"type": "text", "text": user_message}]
            #     }
            # )
    return JSONResponse({"status": "ok"})
```

---

如需調整 todo 拆解或有其他需求，請再補充！