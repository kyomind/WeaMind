"""Service layer for LINE Bot operations using official SDK."""

import logging
from urllib.parse import parse_qs

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    LocationAction,
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
from app.user.service import (
    create_user_if_not_exists,
    deactivate_user,
    get_recent_queries,
    get_user_by_line_id,
    record_user_query,
)
from app.weather.service import LocationParseError, LocationService, WeatherService

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

    # Initialize variables to ensure they're always defined
    needs_quick_reply = False

    try:
        # Parse as location input
        locations, response_message = LocationService.parse_location_input(session, message.text)

        # Check if Quick Reply is needed (2-3 locations found)
        needs_quick_reply = 2 <= len(locations) <= 3

        # Record successful location queries for history
        # This includes both direct single matches and Quick Reply selections
        if len(locations) == 1:
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
            # Try GPS location first
            location = LocationService.find_nearest_location(session, lat, lon)
            # If no GPS result but we have address, try address location
            if not location and address:
                location = LocationService.extract_location_from_address(session, address)

            if location:
                user = get_user_by_line_id(session, user_id)
                if user:
                    record_user_query(session, user.id, location.id)
                    logger.info("Recorded location query for user")

        logger.info("Location query completed")

    except Exception:
        logger.exception("Error handling location message from user")
        response_message = "😅 系統暫時有點忙，請稍後再試一次。"

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


def send_liff_location_setting_response(reply_token: str | None) -> None:
    """
    Send LIFF location setting response to user.

    Args:
        reply_token: Reply token from LINE message event
    """
    if not reply_token:
        logger.warning("Cannot send LIFF response: reply_token is None")
        return

    liff_url = f"{settings.BASE_URL}/static/liff/location/index.html"
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
                    replyToken=reply_token,  # type: ignore[call-arg]
                    messages=[
                        TextMessage(
                            text=response_message,
                            quoteToken=None,  # type: ignore[call-arg]
                            quickReply=None,  # type: ignore[call-arg]
                        )
                    ],  # type: ignore
                    notificationDisabled=False,  # type: ignore[call-arg]
                )
            )
            logger.info(f"LIFF location setting response sent: {liff_url}")
        except Exception:
            logger.exception("Failed to send LIFF location setting response")


# PostBack Event Handlers


def parse_postback_data(data: str) -> dict[str, str]:
    """
    Parse PostBack data string into dictionary.

    Args:
        data: PostBack data string (e.g., "action=weather&type=home")

    Returns:
        Dictionary of parsed data
    """
    try:
        # Parse query string format
        parsed = parse_qs(data)
        # Convert list values to single strings
        return {key: values[0] for key, values in parsed.items() if values}
    except Exception:
        logger.warning(f"Failed to parse PostBack data: {data}")
        return {}


@webhook_handler.add(PostbackEvent)
def handle_postback_event(event: PostbackEvent) -> None:
    """
    Handle PostBack events from Rich Menu clicks.

    Args:
        event: The LINE PostBack event
    """
    try:
        # Check reply token
        if not event.reply_token:
            logger.warning("PostBack event without reply_token")
            return

        # Parse PostBack data
        postback_data = parse_postback_data(event.postback.data)

        # Get user ID
        user_id = getattr(event.source, "user_id", None) if event.source else None
        if not user_id:
            logger.warning("PostBack event without user_id")
            return

        # Route to appropriate handler
        if postback_data.get("action") == "weather":
            handle_weather_postback(event, user_id, postback_data)
        elif postback_data.get("action") == "settings":
            handle_settings_postback(event, postback_data)
        elif postback_data.get("action") == "recent_queries":
            handle_recent_queries_postback(event)
        elif postback_data.get("action") == "menu":
            handle_menu_postback(event, postback_data)
        else:
            logger.warning(f"Unknown PostBack action: {postback_data}")
            send_error_response(event.reply_token, "未知的操作")

    except Exception:
        logger.exception("Error handling PostBack event")
        if event.reply_token:
            send_error_response(event.reply_token, "😅 系統暫時有點忙，請稍後再試一次。")


def handle_weather_postback(event: PostbackEvent, user_id: str, data: dict[str, str]) -> None:
    """
    Handle weather-related PostBack events.

    Args:
        event: PostBack event
        user_id: LINE user ID
        data: Parsed PostBack data
    """
    location_type = data.get("type")

    if location_type in ["home", "office"]:
        handle_user_location_weather(event, user_id, location_type)
    elif location_type == "current":
        handle_current_location_weather(event)
    else:
        send_error_response(event.reply_token, "未知的地點類型")


def handle_user_location_weather(event: PostbackEvent, user_id: str, location_type: str) -> None:
    """
    Handle home/office weather queries.

    Args:
        event: PostBack event
        user_id: LINE user ID
        location_type: "home" or "office"
    """
    session = next(get_session())

    try:
        # Get or create user from database
        user = get_user_by_line_id(session, user_id)
        if not user:
            # Auto-create user for authenticated LINE users
            user = create_user_if_not_exists(session, user_id, display_name=None)

        # Get user's location
        if location_type == "home":
            location = user.home_location
            location_name = "住家"
        else:  # office
            location = user.work_location
            location_name = "公司"

        if not location:
            send_location_not_set_response(event.reply_token, location_name)
            return

        # Query weather using existing logic
        location_text = location.full_name
        _, response_message = LocationService.parse_location_input(session, location_text)

        # Record query for home/office weather lookups (but don't duplicate in history)
        # Note: These are not recorded as they are the user's preset locations

        # Send response
        send_text_response(event.reply_token, response_message)

    except Exception:
        logger.exception(f"Error handling {location_type} weather query")
        send_error_response(event.reply_token, "😅 查詢時發生錯誤，請稍後再試。")
    finally:
        session.close()


def handle_settings_postback(event: PostbackEvent, data: dict[str, str]) -> None:
    """
    Handle settings-related PostBack events.

    Note: 「設定地點」按鈕已改為 URI Action，直接開啟 LIFF 頁面，
    所以這個函數可能不會被 location 類型的事件觸發。

    Args:
        event: PostBack event
        data: Parsed PostBack data
    """
    settings_type = data.get("type")

    if settings_type == "location":
        # This should not be reached if using URI action
        logger.warning("Location setting via PostBack - should use URI action instead")
        send_liff_location_setting_response(event.reply_token)
    else:
        send_error_response(event.reply_token, "未知的設定類型")


def handle_recent_queries_postback(event: PostbackEvent) -> None:
    """Handle recent queries PostBack events."""
    try:
        # Get user ID
        user_id = getattr(event.source, "user_id", None) if event.source else None
        if not user_id:
            logger.warning("Recent queries PostBack event without user_id")
            send_error_response(event.reply_token, "用戶識別錯誤")
            return

        session = next(get_session())

        try:
            # Get or create user from database
            user = get_user_by_line_id(session, user_id)
            if not user:
                # Auto-create user for authenticated LINE users
                user = create_user_if_not_exists(session, user_id, display_name=None)

            # Get recent queries
            recent_locations = get_recent_queries(session, user.id, limit=5)

            if not recent_locations:
                send_text_response(
                    event.reply_token,
                    "📜 您還沒有查詢過其他地點的天氣\n\n試試看輸入地點名稱來查詢天氣吧！",
                )
                return

            # Create Quick Reply items for recent locations
            quick_reply_items = [
                QuickReplyItem(
                    type="action",
                    imageUrl=None,
                    action=MessageAction(
                        type="message",
                        label=location.full_name,
                        text=location.full_name,
                    ),
                )
                for location in recent_locations
            ]

            quick_reply = QuickReply(items=quick_reply_items)

            # Send response with Quick Reply
            response_message = "📜 最近查過的地點："

            with ApiClient(configuration) as api_client:
                messaging_api_client = MessagingApi(api_client)
                try:
                    messaging_api_client.reply_message(
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
                    logger.info(
                        f"Recent queries response sent with {len(recent_locations)} options"
                    )
                except Exception:
                    logger.exception("Error sending recent queries response")
                    send_error_response(event.reply_token, "😅 查詢時發生錯誤，請稍後再試。")
        finally:
            session.close()

    except Exception:
        logger.exception("Error handling recent queries PostBack")
        send_error_response(event.reply_token, "😅 系統暫時有點忙，請稍後再試一次。")


def handle_current_location_weather(event: PostbackEvent) -> None:
    """Handle current location weather PostBack - request user to share location."""
    if not event.reply_token:
        logger.warning("Cannot request location: reply_token is None")
        return

    # Create location request message with Quick Reply
    message_text = "請分享您的位置，我將為您查詢當地的天氣資訊 🌤️"

    # Create Quick Reply with location sharing button
    quick_reply_items = [
        QuickReplyItem(
            type="action",
            imageUrl=None,
            action=LocationAction(
                type="location",
                label="分享我的位置",
            ),
        )
    ]
    quick_reply = QuickReply(items=quick_reply_items)

    with ApiClient(configuration) as api_client:
        messaging_api_client = MessagingApi(api_client)
        try:
            messaging_api_client.reply_message(
                ReplyMessageRequest(
                    replyToken=event.reply_token,
                    messages=[
                        TextMessage(
                            text=message_text,
                            quoteToken=None,
                            quickReply=quick_reply,
                        )
                    ],
                    notificationDisabled=False,
                )
            )
            logger.info("Location request sent successfully")
        except Exception:
            logger.exception("Error sending location request")


def handle_menu_postback(event: PostbackEvent, data: dict[str, str]) -> None:
    """Handle menu PostBack (placeholder)."""
    _ = data  # Acknowledge unused parameter
    send_text_response(event.reply_token, "📢 更多功能即將推出，敬請期待！")


def send_text_response(reply_token: str | None, text: str) -> None:
    """Send simple text response."""
    if not reply_token:
        logger.warning("Cannot send text response: reply_token is None")
        return

    with ApiClient(configuration) as api_client:
        messaging_api_client = MessagingApi(api_client)
        try:
            messaging_api_client.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,  # type: ignore[call-arg]
                    messages=[
                        TextMessage(
                            text=text,
                            quoteToken=None,  # type: ignore[call-arg]
                            quickReply=None,  # type: ignore[call-arg]
                        )
                    ],  # type: ignore
                    notificationDisabled=False,  # type: ignore[call-arg]
                )
            )
        except Exception:
            logger.exception("Error sending text response")


def send_location_not_set_response(reply_token: str | None, location_name: str) -> None:
    """Send response when user location is not set."""
    message = f"請先設定{location_name}地址，點擊下方「設定地點」按鈕即可設定。"
    send_text_response(reply_token, message)


def send_error_response(reply_token: str | None, message: str) -> None:
    """Send error response."""
    send_text_response(reply_token, message)
