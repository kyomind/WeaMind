"""Service layer for LINE Bot operations."""

import json

import httpx

from app.core.config import settings
from app.line.schemas import LineWebhook


async def send_reply_message(reply_token: str, message: str) -> None:
    """
    Send a reply message using LINE Messaging API.

    Args:
        reply_token: The reply token from LINE webhook event
        message: The message text to send
    """
    if settings.LINE_CHANNEL_ACCESS_TOKEN == "CHANGE_ME":
        print(f"Would reply with token {reply_token}: {message}")
        return

    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
    }

    payload = {"replyToken": reply_token, "messages": [{"type": "text", "text": message}]}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"LINE API error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error sending LINE message: {e}")


async def handle_line_events(webhook_body: dict) -> None:
    """
    Handle LINE webhook events (echo bot functionality).

    Args:
        webhook_body: The parsed webhook request body
    """
    try:
        webhook = LineWebhook(**webhook_body)
    except Exception as e:
        print(f"Error parsing webhook body: {e}")
        return

    for event in webhook.events:
        # 處理訊息事件
        if event.type == "message" and event.message and event.message.type == "text":
            if event.replyToken and event.message.text:
                # 應聲蟲功能：原樣回覆收到的訊息
                await send_reply_message(event.replyToken, event.message.text)
                print(f"Echo reply sent: {event.message.text}")


async def process_webhook_body(body: bytes) -> None:
    """
    Process LINE webhook body and handle events.

    Args:
        body: The raw request body as bytes
    """
    try:
        webhook_body = json.loads(body.decode("utf-8"))
        await handle_line_events(webhook_body)
    except Exception as e:
        print(f"Error processing LINE webhook: {e}")
