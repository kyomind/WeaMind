"""Own every normal LINE reply decision for structured Weather Query results."""

from __future__ import annotations

from datetime import UTC, timedelta, timezone
from enum import StrEnum

from app.weather.location_resolution import InvalidInputReason, QueryOutcome, ResolvedLocation
from app.weather.workflow import ForecastData, WeatherQueryResult

from .messaging import MessageChoice, MessageChoicesRecipe, ReplyRecipe, TextRecipe

# LINE Quick Reply is only a helpful shortcut for a handful of candidates; more
# choices than this read worse than asking the user for a more specific name.
_MAX_LOCATION_CHOICES = 3

_BUSY_TEXT = "系統暫時有點忙，請稍後再試一次。"

_INVALID_INPUT_TEXT = {
    InvalidInputReason.EMPTY: "輸入不能為空",
    InvalidInputReason.INVALID_LENGTH: "🤔 輸入的字數不對喔！請輸入 2 到 7 個字的地名",
    InvalidInputReason.NON_CHINESE: "請輸入中文地名",
}


class QueryKind(StrEnum):
    """Name the closed set of Weather Query entry points a reply can answer."""

    TEXT = "text"
    SHARED_LOCATION = "shared_location"
    PRESET_HOME = "preset_home"
    PRESET_OFFICE = "preset_office"


# The preset wording is derived here so no caller passes display text inward.
_PRESET_NAME = {
    QueryKind.PRESET_HOME: "住家",
    QueryKind.PRESET_OFFICE: "公司",
}


def build_weather_reply(result: WeatherQueryResult, kind: QueryKind) -> ReplyRecipe:
    """
    Decide the single reply recipe for one normal Weather Query result.

    Args:
        result: Structured, ORM-free workflow output.
        kind: The entry point the user came from, which the workflow result
            cannot express on its own.

    Returns:
        Exactly one recipe, including for incomplete or unknown data.
    """
    if result.outcome == QueryOutcome.MULTIPLE_LOCATIONS:
        return _multiple_locations_recipe(result)

    return TextRecipe(_reply_text(result, kind))


def _multiple_locations_recipe(result: WeatherQueryResult) -> ReplyRecipe:
    """Offer Quick Reply choices when the candidate list is short enough."""
    locations = result.locations
    prompt = "找到多個符合的地點，請選擇："
    if not 2 <= len(locations) <= _MAX_LOCATION_CHOICES:
        return TextRecipe(prompt)
    return MessageChoicesRecipe(
        text=prompt,
        choices=tuple(
            MessageChoice(label=location.full_name, text=location.full_name)
            for location in locations
        ),
    )


def _reply_text(result: WeatherQueryResult, kind: QueryKind) -> str:
    """Choose the reply wording for every outcome without Quick Reply choices."""
    if result.outcome == QueryOutcome.INVALID_INPUT:
        if result.invalid_reason is None:
            return "輸入格式不正確"
        return _INVALID_INPUT_TEXT[result.invalid_reason]
    if result.outcome == QueryOutcome.TOO_MANY_LOCATIONS:
        return "🤔 找到太多符合的地點了！請輸入更具體的地名"
    if result.outcome == QueryOutcome.LOCATION_NOT_FOUND:
        query_text = result.query_text or "輸入的地名"
        return (
            f"找不到「{query_text}」這個地點耶🙈，建議輸入二級行政區名稱，"
            "比如「中壢」、「水上」或「信義區、魚池鄉」"
        )
    if result.outcome == QueryOutcome.OUTSIDE_TAIWAN:
        return "抱歉，目前僅支援台灣地區的天氣查詢 🌏"
    if result.outcome == QueryOutcome.PRESET_NOT_SET:
        preset_name = _PRESET_NAME.get(kind)
        if preset_name is None:
            return "尚未設定地點"
        return f"請先設定{preset_name}地址，點擊下方「設定地點」按鈕即可設定。"

    location = result.selected_location
    if location is None:
        # A forecast outcome without exactly one location is incomplete data.
        return _BUSY_TEXT
    if result.outcome == QueryOutcome.NO_WEATHER or len(result.forecast) == 0:
        return f"抱歉，目前無法取得 {location.full_name} 的天氣資料，請稍後再試。"
    return _format_forecast(location, result.forecast)


def _format_forecast(location: ResolvedLocation, forecast: tuple[ForecastData, ...]) -> str:
    """Render a non-empty forecast for one resolved location in Taiwan time."""
    taiwan_tz = timezone(timedelta(hours=8))
    updated = forecast[0].fetched_at.replace(tzinfo=UTC).astimezone(taiwan_tz)
    lines = [f"🗺️ {location.full_name}", ""]
    for index, weather in enumerate(forecast[:8], start=1):
        start = weather.start_time.replace(tzinfo=UTC).astimezone(taiwan_tz)
        end = weather.end_time.replace(tzinfo=UTC).astimezone(taiwan_tz)
        precipitation = weather.precipitation_probability or 0
        lines.append(
            f"{weather.weather_emoji or '⛅'} {start:%H}-{end:%H} "
            f"🌡️{weather.max_temperature}°💧{precipitation}%"
        )
        if index == 4 and len(forecast) > 4:
            lines.append("")
    lines.extend(["", f"{updated:%m/%d %H:%M} 更新"])
    return "\n".join(lines)
