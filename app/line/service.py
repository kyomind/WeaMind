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
    response_text = message.text  # Default to echo

    try:
        # Try to parse as location input
        locations, response_message = LocationService.parse_location_input(session, message.text)
        response_text = response_message

        # Log the parsing result
        logger.info(
            f"Location parsing result: {len(locations)} locations found for '{message.text}'"
        )

    except LocationParseError as e:
        # Handle location parsing errors with user-friendly messages
        response_text = e.message
        logger.info(f"Location parsing error for '{e.input_text}': {e.message}")

    except Exception:
        # For unexpected errors, fall back to echo behavior
        logger.exception(f"Unexpected error parsing location input: {message.text}")
        response_text = message.text

    finally:
        session.close()

    # Send response to user
    with ApiClient(configuration) as api_client:
        messaging_api_client = MessagingApi(api_client)
        try:
            messaging_api_client.reply_message(
                # NOTE: Pyright doesn't fully support Pydantic field aliases yet.
                # Snake_case params work at runtime but static analysis only sees camelCase.
                ReplyMessageRequest(
                    reply_token=event.reply_token,  # type: ignore[call-arg]
                    messages=[TextMessage(text=response_text)],  # type: ignore
                    notification_disabled=False,  # type: ignore[call-arg]
                )
            )
            logger.info(f"Response sent: {response_text}")
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
