"""Service layer for LINE Bot operations using official SDK."""

import logging

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure LINE Bot SDK
configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)


@webhook_handler.add(MessageEvent, message=TextMessageContent)
def handle_message_event(event: MessageEvent) -> None:
    """
    Handle text message events with echo bot functionality.

    Args:
        event: The LINE message event
    """
    # 確保消息內容是文本類型
    if not isinstance(event.message, TextMessageContent):
        logger.warning(f"Received non-text message: {type(event.message)}")
        return

    # 確保 reply_token 不為空
    if not event.reply_token:
        logger.warning("Reply token is empty")
        return

    if settings.LINE_CHANNEL_ACCESS_TOKEN == "CHANGE_ME":
        logger.info(f"Would reply with token {event.reply_token}: {event.message.text}")
        return

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        try:
            line_bot_api.reply_message(
                # NOTE: Pyright doesn't fully support Pydantic field aliases yet.
                # Snake_case params work at runtime but static analysis only sees camelCase.
                ReplyMessageRequest(
                    reply_token=event.reply_token,  # type: ignore[call-arg]
                    messages=[TextMessage(text=event.message.text)],  # type: ignore
                    notification_disabled=False,  # type: ignore[call-arg]
                )
            )
            logger.info(f"Echo reply sent: {event.message.text}")
        except Exception:
            logger.exception("Error sending LINE message")


@webhook_handler.default()
def handle_default_event(event: object) -> None:
    """
    Handle events that don't have specific handlers.

    Args:
        event: The LINE event
    """
    logger.info(f"Received unhandled event: {event}")


# Legacy function for backward compatibility (optional)
async def send_reply_message(reply_token: str, message: str) -> None:
    """
    Send a reply message using LINE Messaging API (legacy function).

    Args:
        reply_token: The reply token from LINE webhook event
        message: The message text to send
    """
    if settings.LINE_CHANNEL_ACCESS_TOKEN == "CHANGE_ME":
        logger.info(f"Would reply with token {reply_token}: {message}")
        return

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        try:
            line_bot_api.reply_message(
                # NOTE: Pyright doesn't fully support Pydantic field aliases yet.
                # Snake_case params (reply_token) work at runtime via allow_population_by_field_name
                # but static analysis only sees camelCase params (replyToken) in __signature__.
                ReplyMessageRequest(
                    reply_token=reply_token,  # pyright: ignore
                    messages=[TextMessage(text=message)],  # pyright: ignore
                    notification_disabled=False,  # pyright: ignore
                )
            )
            logger.info(f"Reply sent: {message}")
        except Exception:
            logger.exception("Error sending LINE message")


# 保留舊的函數用於向後兼容（可選）
async def process_webhook_body(body: bytes) -> None:
    """
    Process LINE webhook body (legacy function).

    Args:
        body: The raw request body as bytes
            Example: b'{"events":[{"type":"message","replyToken":"nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
                       "source":{"userId":"U4af4980629...","type":"user"},"timestamp":1462629479859,
                       "message":{"type":"text","id":"444573844083572737","text":"Hello, world"}}]}'
    """
    try:
        webhook_handler.handle(body.decode("utf-8"), "")
    except Exception:
        logger.exception("Error processing LINE webhook")
        raise
