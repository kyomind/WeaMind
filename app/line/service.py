"""Service layer for LINE Bot operations using official SDK."""

import logging

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessageAction,
    MessagingApi,
    QuickReply,
    QuickReplyItem,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import FollowEvent, MessageEvent, TextMessageContent, UnfollowEvent

from app.core.config import settings
from app.core.database import get_session
from app.user.service import create_user_if_not_exists, deactivate_user
from app.weather.service import LocationParseError, LocationService

logger = logging.getLogger(__name__)

# Configure LINE Bot SDK
configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)


@webhook_handler.add(MessageEvent, message=TextMessageContent)
def handle_message_event(event: MessageEvent) -> None:
    """
    Handle text message events with location parsing functionality.

    Args:
        event: The LINE message event
        attributes: (partial)
            - reply_token: Token to reply to the message
            - message: The message content, expected to be TextMessageContent
            - type: The type of the message, expected to be 'text'
    """
    # Ensure reply_token is not empty
    if not event.reply_token:
        logger.warning("Reply token is empty")
        return

    # Type assertion since webhook_handler decorator ensures this is TextMessageContent
    message = event.message
    if not isinstance(message, TextMessageContent):
        logger.warning(f"Unexpected message type: {type(message)}")
        return

    # Get database session
    session = next(get_session())

    # Check for special commands first
    if message.text.strip() == "設定地點":
        session.close()
        send_liff_location_setting_response(event.reply_token)
        return

    # Initialize variables to ensure they're always defined
    needs_quick_reply = False

    try:
        # Parse as location input
        locations, response_message = LocationService.parse_location_input(session, message.text)

        # Check if Quick Reply is needed (2-3 locations found)
        needs_quick_reply = 2 <= len(locations) <= 3

        # Log the parsing result
        logger.info(
            f"Location parsing result: {len(locations)} locations found for '{message.text}'"
        )

    except LocationParseError as e:
        # Handle location parsing errors with user-friendly messages
        response_message = e.message
        logger.info(f"Location parsing error for '{e.input_text}': {e.message}")

    except Exception:
        # For unexpected errors, provide generic error message
        logger.exception(f"Unexpected error parsing location input: {message.text}")
        response_message = "😅 系統暫時有點忙，請稍後再試一次。"

    finally:
        session.close()

    # Send response to user
    with ApiClient(configuration) as api_client:
        messaging_api_client = MessagingApi(api_client)
        try:
            # Create Quick Reply items if needed
            quick_reply = None
            if needs_quick_reply:
                quick_reply_items = [
                    QuickReplyItem(
                        type="action",
                        imageUrl=None,  # Optional for text-only quick reply
                        action=MessageAction(
                            type="message",
                            label=location.full_name,
                            text=location.full_name,
                        ),
                    )
                    for location in locations
                ]
                quick_reply = QuickReply(items=quick_reply_items)

            messaging_api_client.reply_message(
                # NOTE: Pyright doesn't fully support Pydantic field aliases yet.
                # Snake_case params work at runtime but static analysis only sees camelCase.
                ReplyMessageRequest(
                    reply_token=event.reply_token,  # type: ignore[call-arg]
                    messages=[
                        TextMessage(
                            text=response_message,
                            quick_reply=quick_reply,  # type: ignore[call-arg]
                        )
                    ],  # type: ignore
                    notification_disabled=False,  # type: ignore[call-arg]
                )
            )
            logger.info(f"Response sent: {response_message}")
        except Exception:
            logger.exception("Error sending LINE message")


@webhook_handler.add(FollowEvent)
def handle_follow_event(event: FollowEvent) -> None:
    """
    Handle follow events - create or reactivate user record.

    Args:
        event: The LINE follow event
    """
    try:
        user_id = getattr(event.source, "user_id", None) if event.source else None
        if not user_id:
            logger.warning("Follow event without user_id")
            return

        # Get database session
        session = next(get_session())  # Corrected call
        try:
            # Create user if not exists or reactivate if inactive
            user = create_user_if_not_exists(session, user_id)
            logger.info(f"User {user_id} followed - user record created/activated (ID: {user.id})")

            # Send welcome message if reply token exists
            if event.reply_token:
                with ApiClient(configuration) as api_client:
                    messaging_api_client = MessagingApi(api_client)
                    try:
                        messaging_api_client.reply_message(
                            ReplyMessageRequest(
                                reply_token=event.reply_token,  # type: ignore[call-arg]
                                messages=[
                                    TextMessage(
                                        text="Welcome! You can now start interacting with me.",
                                        quick_reply=None,  # type: ignore[call-arg]
                                        quote_token=None,  # type: ignore[call-arg]
                                    )
                                ],  # type: ignore
                                notification_disabled=False,  # type: ignore[call-arg]
                            )
                        )
                        logger.info(f"Welcome message sent to user {user_id}")
                    except Exception:
                        logger.exception(f"Error sending welcome message to user {user_id}")
        finally:
            session.close()

    except Exception:
        logger.exception("Error handling follow event")


@webhook_handler.add(UnfollowEvent)
def handle_unfollow_event(event: UnfollowEvent) -> None:
    """
    Handle unfollow events - deactivate user record.

    Args:
        event: The LINE unfollow event
    """
    try:
        user_id = getattr(event.source, "user_id", None) if event.source else None
        if not user_id:
            logger.warning("Unfollow event without user_id")
            return

        # Get database session
        session = next(get_session())  # Corrected call
        try:
            # Deactivate user
            user = deactivate_user(session, user_id)
            if user:
                logger.info(f"User {user_id} unfollowed - user record deactivated (ID: {user.id})")
            else:
                logger.warning(f"Unfollow event for unknown user {user_id}")
        finally:
            session.close()

    except Exception:
        logger.exception("Error handling unfollow event")


@webhook_handler.default()
def handle_default_event(event: object) -> None:
    """
    Handle events that don't have specific handlers.

    Args:
        event: The LINE event
    """
    logger.info(f"Received unhandled event: {event}")


def send_liff_location_setting_response(reply_token: str) -> None:
    """
    Send LIFF location setting response to user.

    Args:
        reply_token: Reply token from LINE message event
    """
    liff_url = f"{settings.BASE_URL}/static/liff/location/"
    response_message = (
        "🏠 地點設定\n\n"
        "請點擊下方連結設定您的常用地點：\n"
        f"{liff_url}\n\n"
        "設定完成後，您就可以透過快捷功能查詢住家或公司的天氣了！"
    )

    with ApiClient(configuration) as api_client:
        messaging_api_client = MessagingApi(api_client)
        try:
            messaging_api_client.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,  # type: ignore[call-arg]
                    messages=[TextMessage(text=response_message)],  # type: ignore
                    notification_disabled=False,  # type: ignore[call-arg]
                )
            )
            logger.info(f"LIFF location setting response sent: {liff_url}")
        except Exception:
            logger.exception("Failed to send LIFF location setting response")
