"""Service layer for LINE Bot operations using official SDK."""

import logging
import time

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import (
    FollowEvent,
    LocationMessageContent,
    MessageEvent,
    PostbackEvent,
    TextMessageContent,
    UnfollowEvent,
)

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.processing_lock import processing_lock_service
from app.line import metrics as line_metrics
from app.user.service import create_user_if_not_exists, deactivate_user
from app.weather.workflow import query_shared_location, query_text

from .messaging import (
    LineSdkReplyMessenger,
    ReplyMessenger,
    ReplyRecipe,
    TextRecipe,
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
from .sdk_dispatch import LineSdkWebhookDispatcher
from .weather_presentation import QueryKind, build_weather_reply

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
    "process_webhook_events",
    "webhook_handler",
]

logger = logging.getLogger(__name__)


# The SDK requires fixed decorated callbacks, while core handlers receive the
# messenger explicitly. Production wrappers below close over this immutable root.
production_reply_messenger = LineSdkReplyMessenger(settings.LINE_CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
webhook_dispatcher = LineSdkWebhookDispatcher(webhook_handler)


def process_webhook_events(
    body_text: str,
    signature: str,
    fallback_event_types: list[str] | None = None,
) -> None:
    """
    Parse and dispatch webhook events while recording event-level metrics.

    The router records only the received counter. This function owns the
    per-event success, error, and duration metrics by wrapping the LINE SDK's
    dispatch flow at the event boundary.

    Args:
        body_text: Raw webhook request body decoded as UTF-8 text.
        signature: Verified LINE signature header value.
        fallback_event_types: Pre-classified event_type labels from the router,
            used when parsing fails before runtime event objects exist.

    Raises:
        InvalidSignatureError: If the payload cannot be validated by the LINE
            SDK parser.
        Exception: Re-raises handler errors after recording metrics for the
            failing event.
    """
    parse_start_time = time.perf_counter()
    try:
        payload = webhook_dispatcher.parse(body_text, signature)
    except InvalidSignatureError:
        event_types = fallback_event_types or ["unknown"]
        line_metrics.record_webhook_error(event_types, "signature_error")
        line_metrics.record_webhook_duration(event_types, time.perf_counter() - parse_start_time)
        raise
    except Exception:
        event_types = fallback_event_types or ["unknown"]
        line_metrics.record_webhook_error(event_types, "handler_error")
        line_metrics.record_webhook_duration(event_types, time.perf_counter() - parse_start_time)
        raise

    for event in payload.events:
        event_type = line_metrics.normalize_runtime_event_type(event)
        start_time = time.perf_counter()
        try:
            if webhook_dispatcher.dispatch(event, payload):
                line_metrics.record_webhook_success([event_type])
            else:
                logger.info("No handler registered for LINE event")
        except InvalidSignatureError:
            line_metrics.record_webhook_error([event_type], "signature_error")
            raise
        except Exception:
            line_metrics.record_webhook_error([event_type], "handler_error")
            raise
        finally:
            line_metrics.record_webhook_duration([event_type], time.perf_counter() - start_time)


def handle_message_event(event: MessageEvent, messenger: ReplyMessenger) -> None:
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

    try:
        user_id = getattr(event.source, "user_id", None) if event.source else None
        query_result = query_text(message.text, user_id)
        recipe: ReplyRecipe = build_weather_reply(query_result, QueryKind.TEXT)
    except Exception:
        logger.exception(f"Unexpected error parsing location input: {message.text}")
        recipe = TextRecipe("系統暫時有點忙，請稍後再試一次。")

    messenger.reply(event.reply_token, recipe)


def handle_location_message_event(event: MessageEvent, messenger: ReplyMessenger) -> None:
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

    try:
        user_id = getattr(event.source, "user_id", None) if event.source else None
        query_result = query_shared_location(lat, lon, address, user_id)
        recipe: ReplyRecipe = build_weather_reply(query_result, QueryKind.SHARED_LOCATION)
        logger.info("Location query completed")
    except Exception:
        logger.exception("Error handling location message from user")
        recipe = TextRecipe("系統暫時有點忙，請稍後再試一次。")

    messenger.reply(event.reply_token, recipe)


def handle_follow_event(event: FollowEvent, messenger: ReplyMessenger) -> None:
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

        with SessionLocal() as session:
            # Create user if not exists or reactivate if inactive
            create_user_if_not_exists(session, user_id)
            logger.info("User followed - user record created/activated")

        # Release the database connection before waiting on the LINE API.
        if event.reply_token:
            messenger.reply(
                event.reply_token,
                TextRecipe("Welcome! You can now start interacting with me."),
            )

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

        with SessionLocal() as session:
            # Deactivate user
            user = deactivate_user(session, user_id)
            if user:
                logger.info("User unfollowed - user record deactivated")
            else:
                logger.warning("Unfollow event for unknown user")

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


def handle_postback_event(event: PostbackEvent, messenger: ReplyMessenger) -> None:
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
                messenger.reply(event.reply_token, TextRecipe("操作太過頻繁，請放慢腳步 ☕️"))
                return

        dispatch_postback(event, user_id, postback_data, messenger)

    except Exception:
        logger.exception("Error handling PostBack event")
        if event.reply_token:
            messenger.reply(event.reply_token, TextRecipe("系統暫時有點忙，請稍後再試一次。"))


@webhook_handler.add(MessageEvent, message=TextMessageContent)
def _handle_message_event_callback(event: MessageEvent) -> None:
    """Compose the production messenger with the decorated text handler."""
    handle_message_event(event, production_reply_messenger)


@webhook_handler.add(MessageEvent, message=LocationMessageContent)
def _handle_location_message_event_callback(event: MessageEvent) -> None:
    """Compose the production messenger with the decorated location handler."""
    handle_location_message_event(event, production_reply_messenger)


@webhook_handler.add(FollowEvent)
def _handle_follow_event_callback(event: FollowEvent) -> None:
    """Compose the production messenger with the decorated follow handler."""
    handle_follow_event(event, production_reply_messenger)


@webhook_handler.add(PostbackEvent)
def _handle_postback_event_callback(event: PostbackEvent) -> None:
    """Compose the production messenger with the decorated PostBack handler."""
    handle_postback_event(event, production_reply_messenger)
