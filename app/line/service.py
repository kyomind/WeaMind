"""Service layer for LINE Bot operations using official SDK."""

import logging

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    ApiClient,
    MessageAction,
    MessagingApi,
    QuickReply,
    QuickReplyItem,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    FollowEvent,
    LocationMessageContent,
    MessageEvent,
    PostbackEvent,
    TextMessageContent,
    UnfollowEvent,
)

from app.core.config import settings
from app.core.database import get_session
from app.core.processing_lock import processing_lock_service
from app.user.service import (
    create_user_if_not_exists,
    deactivate_user,
    get_user_by_line_id,
    record_user_query,
)
from app.weather.service import LocationParseError, LocationService, WeatherService

from .messaging import (
    configuration,
    send_error_response,
    send_liff_location_setting_response,
    send_location_not_set_response,
    send_other_menu_quick_reply,
    send_text_response,
)
from .postback import (
    dispatch_postback,
    handle_current_location_weather,
    handle_other_postback,
    handle_recent_queries_postback,
    handle_settings_postback,
    handle_user_location_weather,
    handle_weather_postback,
    parse_postback_data,
    should_use_processing_lock,
)

__all__ = [
    "handle_message_event",
    "handle_location_message_event",
    "handle_follow_event",
    "handle_unfollow_event",
    "handle_default_event",
    "handle_postback_event",
    "handle_weather_postback",
    "handle_user_location_weather",
    "handle_settings_postback",
    "handle_recent_queries_postback",
    "handle_current_location_weather",
    "handle_other_postback",
    "parse_postback_data",
    "should_use_processing_lock",
    "send_text_response",
    "send_error_response",
    "send_liff_location_setting_response",
    "send_location_not_set_response",
    "send_other_menu_quick_reply",
    "webhook_handler",
]

logger = logging.getLogger(__name__)

# Configure LINE Bot SDK
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

    # Initialize variables to ensure they're always defined
    needs_quick_reply = False

    try:
        # Parse as location input
        locations, response_message = LocationService.parse_location_input(session, message.text)

        # Check if Quick Reply is needed (2-3 locations found)
        needs_quick_reply = 2 <= len(locations) <= 3

        # For single location match, get actual weather data
        if len(locations) == 1:
            response_message = WeatherService.handle_text_weather_query(session, message.text)

            # Get user for recording query history
            user_id = getattr(event.source, "user_id", None) if event.source else None
            if user_id:
                user = get_user_by_line_id(session, user_id)
                if user:
                    record_user_query(session, user.id, locations[0].id)
                    logger.info("Recorded query history for user")

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
        response_message = "系統暫時有點忙，請稍後再試一次。"

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
            logger.info("Response sent to user")
        except Exception:
            logger.exception("Error sending LINE message")


@webhook_handler.add(MessageEvent, message=LocationMessageContent)
def handle_location_message_event(event: MessageEvent) -> None:
    """
    Handle location message events from user location sharing.

    Args:
        event: The LINE message event containing location data
    """
    # Ensure reply_token is not empty
    if not event.reply_token:
        logger.warning("Reply token is empty for location message")
        return

    # Type assertion since webhook_handler decorator ensures this is LocationMessageContent
    message = event.message
    if not isinstance(message, LocationMessageContent):
        logger.warning(f"Unexpected message type: {type(message)}")
        return

    # Extract GPS coordinates and address information
    lat = message.latitude
    lon = message.longitude
    address = getattr(message, "address", None)

    logger.info("Received location message from user")
    if address:
        logger.info("Location message includes address information")

    # Get database session
    session = next(get_session())

    try:
        # Use WeatherService to handle location-based weather query with address verification
        response_message = WeatherService.handle_location_weather_query(session, lat, lon, address)

        # Record query for user history if location was found in Taiwan
        user_id = getattr(event.source, "user_id", None) if event.source else None
        if user_id:
            # Use same logic as WeatherService.handle_location_weather_query
            # Step 1: Address-first strategy (if available)
            location = None
            if address:
                location = LocationService.extract_location_from_address(session, address)

            # Step 2: GPS fallback (if address failed or not available)
            if not location:
                location = LocationService.find_nearest_location(session, lat, lon)

            if location:
                user = get_user_by_line_id(session, user_id)
                if user:
                    record_user_query(session, user.id, location.id)
                    logger.info("Recorded location query for user")

        logger.info("Location query completed")

    except Exception:
        logger.exception("Error handling location message from user")
        response_message = "系統暫時有點忙，請稍後再試一次。"

    finally:
        session.close()

    # Send response to user
    send_text_response(event.reply_token, response_message)


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
            create_user_if_not_exists(session, user_id)
            logger.info("User followed - user record created/activated")

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
                        logger.info("Welcome message sent to user")
                    except Exception:
                        logger.exception("Error sending welcome message to user")
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
                logger.info("User unfollowed - user record deactivated")
            else:
                logger.warning("Unfollow event for unknown user")
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
    logger.info("Received unhandled event type")


@webhook_handler.add(PostbackEvent)
def handle_postback_event(event: PostbackEvent) -> None:
    """
    Handle PostBack events triggered from the LINE rich menu.

    Args:
        event: The LINE PostBack event payload
    """
    try:
        if not event.reply_token:
            logger.warning("PostBack event without reply_token")
            return

        postback_data = parse_postback_data(event.postback.data)

        user_id = getattr(event.source, "user_id", None) if event.source else None
        if not user_id:
            logger.warning("PostBack event without user_id")
            return

        needs_lock = should_use_processing_lock(postback_data)
        lock_key = None

        if needs_lock and hasattr(event, "source") and event.source:
            lock_key = processing_lock_service.build_lock_key(event.source)

        if lock_key and settings.PROCESSING_LOCK_ENABLED:
            if not processing_lock_service.try_acquire_lock(lock_key):
                send_text_response(event.reply_token, "操作太過頻繁，請放慢腳步 ☕️")
                return

        dispatch_postback(event, user_id, postback_data)

    except Exception:
        logger.exception("Error handling PostBack event")
        if event.reply_token:
            send_error_response(event.reply_token, "系統暫時有點忙，請稍後再試一次。")
