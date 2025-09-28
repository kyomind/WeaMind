"""PostBack handling utilities for the LINE rich menu actions."""

from __future__ import annotations

import logging
from urllib.parse import parse_qs

from linebot.v3.messaging import (
    ApiClient,
    LocationAction,
    MessageAction,
    MessagingApi,
    QuickReply,
    QuickReplyItem,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import PostbackEvent

from app.core.database import get_session
from app.line.messaging import (
    configuration,
    send_error_response,
    send_liff_location_setting_response,
    send_location_not_set_response,
    send_other_menu_quick_reply,
    send_text_response,
)
from app.user.service import (
    create_user_if_not_exists,
    get_recent_queries,
    get_user_by_line_id,
)
from app.weather.service import WeatherService

logger = logging.getLogger(__name__)


def parse_postback_data(data: str) -> dict[str, str]:
    """Parse raw postback query string data into a dictionary."""
    if not data:
        return {}

    try:
        parsed = parse_qs(data, keep_blank_values=False)
    except Exception:
        logger.exception("Failed to parse PostBack data", extra={"raw_data": data})
        return {}

    return {key: values[0] for key, values in parsed.items() if values}


def should_use_processing_lock(postback_data: dict[str, str]) -> bool:
    """Determine whether a PostBack action should use the processing lock."""
    action = postback_data.get("action")
    action_type = postback_data.get("type")

    if action == "weather":
        return action_type in {"home", "office"}

    if action == "recent_queries":
        return True

    return False


def dispatch_postback(event: PostbackEvent, user_id: str, postback_data: dict[str, str]) -> None:
    """Route a PostBack event to the appropriate handler."""
    action = postback_data.get("action")

    if action == "weather":
        handle_weather_postback(event, user_id, postback_data)
        return

    if action == "settings":
        handle_settings_postback(event, postback_data)
        return

    if action == "recent_queries":
        handle_recent_queries_postback(event)
        return

    if action == "other":
        handle_other_postback(event, postback_data)
        return

    logger.warning("Unknown PostBack action", extra={"postback_data": postback_data})
    send_error_response(event.reply_token, "未知的操作")


def handle_weather_postback(event: PostbackEvent, user_id: str, data: dict[str, str]) -> None:
    """Handle weather-related PostBack operations (home, office, or current)."""
    location_type = data.get("type")

    if location_type in {"home", "office"}:
        handle_user_location_weather(event, user_id, location_type)
        return

    if location_type == "current":
        handle_current_location_weather(event)
        return

    send_error_response(event.reply_token, "未知的地點類型")


def handle_user_location_weather(event: PostbackEvent, user_id: str, location_type: str) -> None:
    """Reply with preset location weather information for home or office."""
    session = next(get_session())

    try:
        user = get_user_by_line_id(session, user_id)
        if not user:
            user = create_user_if_not_exists(session, user_id, display_name=None)

        location_name = "住家" if location_type == "home" else "公司"
        location = user.home_location if location_type == "home" else user.work_location

        if not location:
            send_location_not_set_response(event.reply_token, location_name)
            return

        response_message = WeatherService.handle_text_weather_query(session, location.full_name)
        send_text_response(event.reply_token, response_message)
    except Exception:
        logger.exception("Error handling preset location weather", extra={"type": location_type})
        send_error_response(event.reply_token, "查詢時發生錯誤，請稍後再試。")
    finally:
        session.close()


def handle_settings_postback(event: PostbackEvent, data: dict[str, str]) -> None:
    """Handle settings-related PostBack operations."""
    settings_type = data.get("type")

    if settings_type == "location":
        logger.info("Location setting requested via PostBack")
        send_liff_location_setting_response(event.reply_token)
        return

    logger.warning("Unknown settings PostBack type", extra={"type": settings_type})
    send_error_response(event.reply_token, "未知的設定類型")


def handle_recent_queries_postback(event: PostbackEvent) -> None:
    """Handle PostBack events requesting recent query history."""
    try:
        user_id = getattr(event.source, "user_id", None) if event.source else None
        if not user_id:
            logger.warning("Recent queries PostBack event without user_id")
            send_error_response(event.reply_token, "用戶識別錯誤")
            return

        session = next(get_session())
        try:
            user = get_user_by_line_id(session, user_id)
            if not user:
                user = create_user_if_not_exists(session, user_id, display_name=None)

            recent_locations = get_recent_queries(session, user.id, limit=5)
            if not recent_locations:
                send_text_response(
                    event.reply_token,
                    "您還沒有查詢過其他地點的天氣\n\n試試看輸入地點名稱來查詢天氣吧！",
                )
                return

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
            response_message = "最近查過的 5 個地點："

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
                            ],
                            notification_disabled=False,  # type: ignore[call-arg]
                        )
                    )
                    logger.info(
                        "Recent queries response sent",
                        extra={"options": len(recent_locations)},
                    )
                except Exception:
                    logger.exception("Error sending recent queries response")
                    send_error_response(event.reply_token, "查詢時發生錯誤，請稍後再試。")
        finally:
            session.close()

    except Exception:
        logger.exception("Error handling recent queries PostBack")
        send_error_response(event.reply_token, "系統暫時有點忙，請稍後再試一次。")


def handle_current_location_weather(event: PostbackEvent) -> None:
    """Prompt the user to share their current location for weather lookup."""
    if not event.reply_token:
        logger.warning("Cannot request location: reply_token is None")
        return

    message_text = "請點擊地圖上任意位置，將為您查詢該地天氣"

    quick_reply_items = [
        QuickReplyItem(
            type="action",
            imageUrl=None,
            action=LocationAction(
                type="location",
                label="開啟地圖選擇",
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


def handle_other_postback(event: PostbackEvent, data: dict[str, str]) -> None:
    """Handle PostBack events triggered from the 'other' menu."""
    postback_type = data.get("type")

    if postback_type == "menu":
        send_other_menu_quick_reply(event.reply_token)
        return

    logger.warning("Unknown other PostBack type", extra={"type": postback_type})
    send_error_response(event.reply_token, "未知的操作")
