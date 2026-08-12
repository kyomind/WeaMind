"""Handle LINE rich-menu PostBack actions through the reply messenger seam."""

from __future__ import annotations

import logging
from urllib.parse import parse_qs

from linebot.v3.webhooks import PostbackEvent

from app.core.config import settings
from app.core.database import SessionLocal
from app.line.messaging import (
    LocationRequestRecipe,
    MessageChoice,
    MessageChoicesRecipe,
    ReplyMessenger,
    TextRecipe,
    UriChoice,
    UriChoicesRecipe,
)
from app.user.service import (
    create_user_if_not_exists,
    get_recent_queries,
    get_user_by_line_id,
)
from app.weather.workflow import query_preset

from .weather_presentation import QueryKind, build_weather_reply

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


def dispatch_postback(
    event: PostbackEvent,
    user_id: str,
    postback_data: dict[str, str],
    messenger: ReplyMessenger,
) -> None:
    """Route a PostBack event to the appropriate handler."""
    action = postback_data.get("action")

    if action == "weather":
        handle_weather_postback(event, user_id, postback_data, messenger)
        return

    if action == "settings":
        handle_settings_postback(event, postback_data, messenger)
        return

    if action == "recent_queries":
        handle_recent_queries_postback(event, messenger)
        return

    if action == "other":
        handle_other_postback(event, postback_data, messenger)
        return

    logger.warning("Unknown PostBack action", extra={"postback_data": postback_data})
    messenger.reply(event.reply_token, TextRecipe("未知的操作"))


def handle_weather_postback(
    event: PostbackEvent,
    user_id: str,
    data: dict[str, str],
    messenger: ReplyMessenger,
) -> None:
    """Handle weather-related PostBack operations for home, office, or current."""
    location_type = data.get("type")

    if location_type in {"home", "office"}:
        handle_user_location_weather(event, user_id, location_type, messenger)
        return

    if location_type == "current":
        handle_current_location_weather(event, messenger)
        return

    messenger.reply(event.reply_token, TextRecipe("未知的地點類型"))


def handle_user_location_weather(
    event: PostbackEvent,
    user_id: str,
    location_type: str,
    messenger: ReplyMessenger,
) -> None:
    """Reply with preset location weather information for home or office."""
    try:
        kind = QueryKind.PRESET_HOME if location_type == "home" else QueryKind.PRESET_OFFICE
        query_result = query_preset(user_id, location_type)
        messenger.reply(event.reply_token, build_weather_reply(query_result, kind))
    except Exception:
        logger.exception("Error handling preset location weather", extra={"type": location_type})
        messenger.reply(event.reply_token, TextRecipe("查詢時發生錯誤，請稍後再試。"))


def handle_settings_postback(
    event: PostbackEvent,
    data: dict[str, str],
    messenger: ReplyMessenger,
) -> None:
    """Handle settings-related PostBack operations."""
    settings_type = data.get("type")

    if settings_type == "location":
        logger.info("Location setting requested via PostBack")
        liff_url = f"{settings.BASE_URL}/static/liff/location/index.html"
        response_message = (
            "地點設定\n\n"
            "請點擊下方連結設定您的常用地點：\n"
            f"{liff_url}\n\n"
            "設定完成後，您就可以透過快捷功能查詢住家或公司的天氣了！"
        )
        messenger.reply(event.reply_token, TextRecipe(response_message))
        return

    logger.warning("Unknown settings PostBack type", extra={"type": settings_type})
    messenger.reply(event.reply_token, TextRecipe("未知的設定類型"))


def handle_recent_queries_postback(
    event: PostbackEvent,
    messenger: ReplyMessenger,
) -> None:
    """Handle PostBack events requesting recent query history."""
    try:
        user_id = getattr(event.source, "user_id", None) if event.source else None
        if not user_id:
            logger.warning("Recent queries PostBack event without user_id")
            messenger.reply(event.reply_token, TextRecipe("用戶識別錯誤"))
            return

        with SessionLocal() as session:
            user = get_user_by_line_id(session, user_id)
            if not user:
                user = create_user_if_not_exists(session, user_id)

            recent_locations = get_recent_queries(session, user.id, limit=5)
            recent_location_names = tuple(location.full_name for location in recent_locations)

        # Build and send only after releasing the database connection.
        if not recent_location_names:
            messenger.reply(
                event.reply_token,
                TextRecipe("您還沒有查詢過其他地點的天氣\n\n試試看輸入地點名稱來查詢天氣吧！"),
            )
            return

        recipe = MessageChoicesRecipe(
            text="最近查過的 5 個地點：",
            choices=tuple(
                MessageChoice(label=location_name, text=location_name)
                for location_name in recent_location_names
            ),
        )
        send_result = messenger.reply(event.reply_token, recipe)
        if send_result.success:
            logger.info("Recent queries response sent", extra={"options": len(recipe.choices)})
        # Never spend a single-use reply token on a fallback after a failed send.
    except Exception:
        logger.exception("Error handling recent queries PostBack")
        messenger.reply(event.reply_token, TextRecipe("系統暫時有點忙，請稍後再試一次。"))


def handle_current_location_weather(
    event: PostbackEvent,
    messenger: ReplyMessenger,
) -> None:
    """Prompt the user to share their current location for weather lookup."""
    messenger.reply(
        event.reply_token,
        LocationRequestRecipe(
            text="請點擊地圖上任意位置，將為您查詢該地天氣",
            label="開啟地圖選擇",
        ),
    )


def handle_other_postback(
    event: PostbackEvent,
    data: dict[str, str],
    messenger: ReplyMessenger,
) -> None:
    """Handle PostBack events triggered from the other menu."""
    postback_type = data.get("type")

    if postback_type == "menu":
        messenger.reply(
            event.reply_token,
            UriChoicesRecipe(
                text="請選擇想了解的資訊：",
                choices=(
                    UriChoice(
                        label="🔄 更新",
                        uri="https://github.com/kyomind/WeaMind/blob/main/CHANGELOG.md",
                    ),
                    UriChoice(
                        label="📖 使用說明",
                        uri="https://github.com/kyomind/WeaMind/blob/main/README.md",
                    ),
                    UriChoice(
                        label="ℹ️ 專案介紹",
                        uri="https://api.kyomind.tw/static/about/index.html",
                    ),
                ),
            ),
        )
        return

    logger.warning("Unknown other PostBack type", extra={"type": postback_type})
    messenger.reply(event.reply_token, TextRecipe("未知的操作"))
