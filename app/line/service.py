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
    # Ensure the message content is text type
    if not isinstance(event.message, TextMessageContent):
        logger.warning(f"Received non-text message: {type(event.message)}")
        return

    # Ensure reply_token is not empty
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
