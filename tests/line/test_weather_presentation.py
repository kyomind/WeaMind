"""Test LINE presentation for structured Weather Query results."""

from datetime import datetime

import pytest

from app.line.weather_presentation import format_weather_query
from app.weather.location_resolution import InvalidInputReason
from app.weather.workflow import (
    ForecastData,
    LocationData,
    QueryOutcome,
    WeatherQueryResult,
)


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        (WeatherQueryResult(QueryOutcome.INVALID_INPUT), "輸入格式不正確"),
        (
            WeatherQueryResult(QueryOutcome.INVALID_INPUT, invalid_reason=InvalidInputReason.EMPTY),
            "輸入不能為空",
        ),
        (
            WeatherQueryResult(
                QueryOutcome.INVALID_INPUT, invalid_reason=InvalidInputReason.INVALID_LENGTH
            ),
            "🤔 輸入的字數不對喔！請輸入 2 到 7 個字的地名",
        ),
        (
            WeatherQueryResult(
                QueryOutcome.INVALID_INPUT, invalid_reason=InvalidInputReason.NON_CHINESE
            ),
            "請輸入中文地名",
        ),
        (
            WeatherQueryResult(QueryOutcome.MULTIPLE_LOCATIONS),
            "找到多個符合的地點，請選擇：",
        ),
        (
            WeatherQueryResult(QueryOutcome.TOO_MANY_LOCATIONS),
            "🤔 找到太多符合的地點了！請輸入更具體的地名",
        ),
        (
            WeatherQueryResult(QueryOutcome.LOCATION_NOT_FOUND, query_text="臺北路"),
            "找不到「臺北路」這個地點耶🙈，建議輸入二級行政區名稱，"
            "比如「中壢」、「水上」或「信義區、魚池鄉」",
        ),
        (
            WeatherQueryResult(QueryOutcome.OUTSIDE_TAIWAN),
            "抱歉，目前僅支援台灣地區的天氣查詢 🌏",
        ),
        (WeatherQueryResult(QueryOutcome.PRESET_NOT_SET), "尚未設定地點"),
        (
            WeatherQueryResult(
                QueryOutcome.NO_WEATHER,
                locations=(LocationData(1, "臺北市松山區"),),
            ),
            "抱歉，目前無法取得 臺北市松山區 的天氣資料，請稍後再試。",
        ),
    ],
)
def test_format_non_forecast_outcomes(result: WeatherQueryResult, expected: str) -> None:
    """Translate every non-forecast outcome into stable LINE text."""
    assert format_weather_query(result) == expected


def test_format_forecast() -> None:
    """Format immutable forecast data without ORM or Session access."""
    forecast = ForecastData(
        start_time=datetime(2026, 8, 12, 0),
        end_time=datetime(2026, 8, 12, 3),
        fetched_at=datetime(2026, 8, 12, 0),
        weather_emoji="☀️",
        precipitation_probability=10,
        max_temperature=30,
    )
    result = WeatherQueryResult(
        QueryOutcome.FORECAST,
        locations=(LocationData(1, "臺北市松山區"),),
        forecast=(forecast,),
    )

    assert format_weather_query(result) == (
        "🗺️ 臺北市松山區\n\n☀️ 08-11 🌡️30°💧10%\n\n08/12 08:00 更新"
    )
