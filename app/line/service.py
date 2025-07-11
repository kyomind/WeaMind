"""Service layer for LINE Bot operations."""

import json
import logging

import httpx

from app.core.config import settings
from app.line.schemas import LineWebhook

logger = logging.getLogger(__name__)


async def send_reply_message(reply_token: str, message: str) -> None:
    """
    Send a reply message using LINE Messaging API.

    Args:
        reply_token: The reply token from LINE webhook event
            Example: "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA"
        message: The message text to send
            Example: "Hello, World!"
    """
    if settings.LINE_CHANNEL_ACCESS_TOKEN == "CHANGE_ME":
        logger.info(f"Would reply with token {reply_token}: {message}")
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
                logger.error(f"LINE API error: {response.status_code} - {response.text}")
        except Exception:
            logger.exception("Error sending LINE message")


async def handle_line_events(webhook_body: dict) -> None:
    """
    Handle LINE webhook events (echo bot functionality).

    Args:
        webhook_body: The parsed webhook request body
            Example: {
                "events": [
                    {
                        "type": "message",
                        "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
                        "source": {
                            "userId": "U4af4980629...",
                            "type": "user"
                        },
                        "timestamp": 1462629479859,
                        "message": {
                            "type": "text",
                            "id": "444573844083572737",
                            "text": "Hello, world"
                        }
                    }
                ]
            }
    """
    try:
        webhook = LineWebhook(**webhook_body)
    except Exception:
        logger.exception("Error parsing webhook body")
        return

    for event in webhook.events:
        # 處理訊息事件
        if event.type == "message" and event.message and event.message.type == "text":
            if event.replyToken and event.message.text:
                # 應聲蟲功能：原樣回覆收到的訊息
                await send_reply_message(event.replyToken, event.message.text)
                logger.info(f"Echo reply sent: {event.message.text}")


async def process_webhook_body(body: bytes) -> None:
    """
    Process LINE webhook body and handle events.

    Args:
        body: The raw request body as bytes
            Example: b'{"events":[{"type":"message","replyToken":"nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
                       "source":{"userId":"U4af4980629...","type":"user"},"timestamp":1462629479859,
                       "message":{"type":"text","id":"444573844083572737","text":"Hello, world"}}]}'
    """
    try:
        webhook_body: dict = json.loads(body.decode("utf-8"))
        await handle_line_events(webhook_body)
    except Exception:
        logger.exception("Error processing LINE webhook")
