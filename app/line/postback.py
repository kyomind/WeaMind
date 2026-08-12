"""Prepare and execute typed PostBack actions without LINE SDK dependencies."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import parse_qs

from app.core.config import settings
from app.core.database import SessionLocal
from app.line.messaging import (
    LocationRequestRecipe,
    MessageChoice,
    MessageChoicesRecipe,
    ReplyRecipe,
    TextRecipe,
    UriChoice,
    UriChoicesRecipe,
)
from app.user.service import create_user_if_not_exists, get_recent_queries, get_user_by_line_id
from app.weather.workflow import query_preset

from .weather_presentation import QueryKind, build_weather_reply

logger = logging.getLogger(__name__)
_LOCK_DENIED_RECIPE = TextRecipe("操作太過頻繁，請放慢腳步 ☕️")


@dataclass(frozen=True)
class PresetWeatherAction:
    """Query weather for a user's saved location."""

    user_id: str
    location_type: str


@dataclass(frozen=True)
class CurrentWeatherAction:
    """Ask the user to share a current location."""


@dataclass(frozen=True)
class LocationSettingsAction:
    """Show the location-settings entry point."""


@dataclass(frozen=True)
class RecentQueriesAction:
    """Show a user's recent weather-query locations."""

    user_id: str


@dataclass(frozen=True)
class OtherMenuAction:
    """Show links from the other-information menu."""


@dataclass(frozen=True)
class InvalidAction:
    """Preserve the specific recipe for invalid or incomplete PostBack data."""

    recipe: ReplyRecipe


type PostbackAction = (
    PresetWeatherAction
    | CurrentWeatherAction
    | LocationSettingsAction
    | RecentQueriesAction
    | OtherMenuAction
    | InvalidAction
)


@dataclass(frozen=True)
class PostbackPlan:
    """Describe one closed PostBack action and its processing-lock policy."""

    action: PostbackAction
    requires_lock: bool
    lock_denied_recipe: ReplyRecipe


def prepare_postback(raw_data: str, user_id: str) -> PostbackPlan:
    """Parse raw query-string data into an immutable executable action plan."""
    data = _parse_data(raw_data)
    action = data.get("action")
    action_type = data.get("type")

    if action == "weather":
        if action_type in {"home", "office"}:
            return PostbackPlan(
                PresetWeatherAction(user_id, action_type), True, _LOCK_DENIED_RECIPE
            )
        if action_type == "current":
            return PostbackPlan(CurrentWeatherAction(), False, _LOCK_DENIED_RECIPE)
        return PostbackPlan(InvalidAction(TextRecipe("未知的地點類型")), False, _LOCK_DENIED_RECIPE)
    if action == "settings":
        if action_type == "location":
            logger.info("Location setting requested via PostBack")
            return PostbackPlan(LocationSettingsAction(), False, _LOCK_DENIED_RECIPE)
        logger.warning("Unknown settings PostBack type", extra={"type": action_type})
        return PostbackPlan(InvalidAction(TextRecipe("未知的設定類型")), False, _LOCK_DENIED_RECIPE)
    if action == "recent_queries":
        return PostbackPlan(RecentQueriesAction(user_id), True, _LOCK_DENIED_RECIPE)
    if action == "other":
        if action_type == "menu":
            return PostbackPlan(OtherMenuAction(), False, _LOCK_DENIED_RECIPE)
        logger.warning("Unknown other PostBack type", extra={"type": action_type})
        return PostbackPlan(InvalidAction(TextRecipe("未知的操作")), False, _LOCK_DENIED_RECIPE)
    logger.warning("Unknown PostBack action", extra={"postback_data": data})
    return PostbackPlan(InvalidAction(TextRecipe("未知的操作")), False, _LOCK_DENIED_RECIPE)


def execute_postback(plan: PostbackPlan) -> ReplyRecipe:
    """Execute a prepared action and always return exactly one reply recipe."""
    try:
        action = plan.action
        if isinstance(action, PresetWeatherAction):
            kind = (
                QueryKind.PRESET_HOME if action.location_type == "home" else QueryKind.PRESET_OFFICE
            )
            return build_weather_reply(query_preset(action.user_id, action.location_type), kind)
        if isinstance(action, CurrentWeatherAction):
            return LocationRequestRecipe(
                text="請點擊地圖上任意位置，將為您查詢該地天氣", label="開啟地圖選擇"
            )
        if isinstance(action, LocationSettingsAction):
            liff_url = f"{settings.BASE_URL}/static/liff/location/index.html"
            return TextRecipe(
                "地點設定\n\n請點擊下方連結設定您的常用地點：\n"
                f"{liff_url}\n\n設定完成後，您就可以透過快捷功能查詢住家或公司的天氣了！"
            )
        if isinstance(action, RecentQueriesAction):
            return _execute_recent_queries(action)
        if isinstance(action, OtherMenuAction):
            return UriChoicesRecipe(
                text="請選擇想了解的資訊：",
                choices=(
                    UriChoice(
                        "🔄 更新", "https://github.com/kyomind/WeaMind/blob/main/CHANGELOG.md"
                    ),
                    UriChoice(
                        "📖 使用說明", "https://github.com/kyomind/WeaMind/blob/main/README.md"
                    ),
                    UriChoice("ℹ️ 專案介紹", "https://api.kyomind.tw/static/about/index.html"),
                ),
            )
        return action.recipe  # noqa: TRY300
    except Exception:
        logger.exception(
            "Error executing PostBack action", extra={"action": type(plan.action).__name__}
        )
        if isinstance(plan.action, PresetWeatherAction):
            return TextRecipe("查詢時發生錯誤，請稍後再試。")
        return TextRecipe("系統暫時有點忙，請稍後再試一次。")


def _parse_data(raw_data: str) -> dict[str, str]:
    """Parse PostBack query-string data while containing malformed input."""
    if not raw_data:
        return {}
    try:
        parsed = parse_qs(raw_data, keep_blank_values=False)
    except Exception:
        logger.exception("Failed to parse PostBack data", extra={"raw_data": raw_data})
        return {}
    return {key: values[0] for key, values in parsed.items() if values}


def _execute_recent_queries(action: RecentQueriesAction) -> ReplyRecipe:
    """Load query history and close its database session before returning a recipe."""
    with SessionLocal() as session:
        user = get_user_by_line_id(session, action.user_id)
        if not user:
            user = create_user_if_not_exists(session, action.user_id)
        names = tuple(
            location.full_name for location in get_recent_queries(session, user.id, limit=5)
        )

    if not names:
        return TextRecipe("您還沒有查詢過其他地點的天氣\n\n試試看輸入地點名稱來查詢天氣吧！")
    return MessageChoicesRecipe(
        text="最近查過的 5 個地點：",
        choices=tuple(MessageChoice(label=name, text=name) for name in names),
    )
