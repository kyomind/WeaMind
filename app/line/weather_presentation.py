"""Translate structured Weather Query results into LINE-facing Chinese text."""

from datetime import UTC, timedelta, timezone

from app.weather.workflow import QueryOutcome, WeatherQueryResult


def format_weather_query(result: WeatherQueryResult) -> str:
    """Format a structured Weather Query result for LINE."""
    location = result.selected_location
    if result.outcome == QueryOutcome.INVALID_INPUT:
        return result.invalid_input_message or "輸入格式不正確"
    if result.outcome == QueryOutcome.MULTIPLE_LOCATIONS:
        return "找到多個符合的地點，請選擇："
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
        return "尚未設定地點"
    if location is None:
        return "系統暫時有點忙，請稍後再試一次。"
    forecast = result.forecast
    if result.outcome == QueryOutcome.NO_WEATHER or len(forecast) == 0:
        return f"抱歉，目前無法取得 {location.full_name} 的天氣資料，請稍後再試。"

    taiwan_tz = timezone(timedelta(hours=8))
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
    updated = forecast[0].fetched_at.replace(tzinfo=UTC).astimezone(taiwan_tz)
    lines.extend(["", f"{updated:%m/%d %H:%M} 更新"])
    return "\n".join(lines)
