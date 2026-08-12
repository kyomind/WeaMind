"""Test the complete LINE reply decision for structured Weather Query results."""

from datetime import datetime, timedelta

import pytest

from app.line.messaging import (
    MessageChoice,
    MessageChoicesRecipe,
    ReplyRecipe,
    TextRecipe,
)
from app.line.weather_presentation import QueryKind, build_weather_reply
from app.weather.location_resolution import InvalidInputReason
from app.weather.workflow import (
    ForecastData,
    QueryOutcome,
    ResolvedLocation,
    WeatherQueryResult,
)


def _forecast(hour: int, emoji: str | None = "☀️") -> ForecastData:
    """Create one forecast period starting at the given UTC hour."""
    return ForecastData(
        start_time=datetime(2026, 8, 12, hour),
        end_time=datetime(2026, 8, 12, hour) + timedelta(hours=3),
        fetched_at=datetime(2026, 8, 12, 0),
        weather_emoji=emoji,
        precipitation_probability=10,
        max_temperature=30,
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
            WeatherQueryResult(QueryOutcome.TOO_MANY_LOCATIONS),
            "🤔 找到太多符合的地點了！請輸入更具體的地名",
        ),
        (
            WeatherQueryResult(QueryOutcome.LOCATION_NOT_FOUND, query_text="臺北路"),
            "找不到「臺北路」這個地點耶🙈，建議輸入二級行政區名稱，"
            "比如「中壢」、「水上」或「信義區、魚池鄉」",
        ),
        (
            WeatherQueryResult(QueryOutcome.LOCATION_NOT_FOUND),
            "找不到「輸入的地名」這個地點耶🙈，建議輸入二級行政區名稱，"
            "比如「中壢」、「水上」或「信義區、魚池鄉」",
        ),
        (
            WeatherQueryResult(QueryOutcome.OUTSIDE_TAIWAN),
            "抱歉，目前僅支援台灣地區的天氣查詢 🌏",
        ),
        (
            WeatherQueryResult(
                QueryOutcome.NO_WEATHER,
                locations=(ResolvedLocation(1, "臺北市松山區"),),
            ),
            "抱歉，目前無法取得 臺北市松山區 的天氣資料，請稍後再試。",
        ),
        (
            WeatherQueryResult(
                QueryOutcome.FORECAST,
                locations=(ResolvedLocation(1, "臺北市松山區"),),
            ),
            "抱歉，目前無法取得 臺北市松山區 的天氣資料，請稍後再試。",
        ),
        (WeatherQueryResult(QueryOutcome.FORECAST), "系統暫時有點忙，請稍後再試一次。"),
        (WeatherQueryResult(QueryOutcome.NO_WEATHER), "系統暫時有點忙，請稍後再試一次。"),
    ],
)
@pytest.mark.parametrize("kind", list(QueryKind))
def test_build_text_reply_outcomes(
    result: WeatherQueryResult, expected: str, kind: QueryKind
) -> None:
    """Translate every text-only outcome into one stable text recipe."""
    assert build_weather_reply(result, kind) == TextRecipe(expected)


def test_multiple_locations_build_message_choices() -> None:
    """Offer Quick Reply choices for a short list of candidate locations."""
    result = WeatherQueryResult(
        QueryOutcome.MULTIPLE_LOCATIONS,
        locations=(ResolvedLocation(1, "新北市永和區"), ResolvedLocation(2, "臺南市永和區")),
    )

    assert build_weather_reply(result, QueryKind.TEXT) == MessageChoicesRecipe(
        text="找到多個符合的地點，請選擇：",
        choices=(
            MessageChoice(label="新北市永和區", text="新北市永和區"),
            MessageChoice(label="臺南市永和區", text="臺南市永和區"),
        ),
    )


@pytest.mark.parametrize("count", [0, 1, 4])
def test_multiple_locations_outside_choice_range_fall_back_to_text(count: int) -> None:
    """Fall back to the prompt text when the candidate list cannot become choices."""
    result = WeatherQueryResult(
        QueryOutcome.MULTIPLE_LOCATIONS,
        locations=tuple(ResolvedLocation(index, f"地點{index}") for index in range(count)),
    )

    recipe = build_weather_reply(result, QueryKind.TEXT)

    assert recipe == TextRecipe("找到多個符合的地點，請選擇：")


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        (QueryKind.PRESET_HOME, "請先設定住家地址，點擊下方「設定地點」按鈕即可設定。"),
        (QueryKind.PRESET_OFFICE, "請先設定公司地址，點擊下方「設定地點」按鈕即可設定。"),
        (QueryKind.TEXT, "尚未設定地點"),
        (QueryKind.SHARED_LOCATION, "尚未設定地點"),
    ],
)
def test_preset_not_set_wording_derives_from_query_kind(kind: QueryKind, expected: str) -> None:
    """Derive the preset wording from the entry point, never from a caller label."""
    result = WeatherQueryResult(QueryOutcome.PRESET_NOT_SET)

    assert build_weather_reply(result, kind) == TextRecipe(expected)


def test_query_kind_does_not_change_other_outcomes() -> None:
    """Keep non-preset outcomes independent of the query kind."""
    result = WeatherQueryResult(
        QueryOutcome.FORECAST,
        locations=(ResolvedLocation(1, "臺北市松山區"),),
        forecast=(_forecast(0),),
    )

    replies: set[ReplyRecipe] = {build_weather_reply(result, kind) for kind in QueryKind}

    assert len(replies) == 1


def test_forecast_renders_in_taiwan_time() -> None:
    """Format immutable forecast data without ORM or Session access."""
    result = WeatherQueryResult(
        QueryOutcome.FORECAST,
        locations=(ResolvedLocation(1, "臺北市松山區"),),
        forecast=(_forecast(0),),
    )

    assert build_weather_reply(result, QueryKind.TEXT) == TextRecipe(
        "🗺️ 臺北市松山區\n\n☀️ 08-11 🌡️30°💧10%\n\n08/12 08:00 更新"
    )


def test_forecast_inserts_blank_line_after_four_periods() -> None:
    """Separate the first four forecast periods from the rest with a blank line."""
    result = WeatherQueryResult(
        QueryOutcome.FORECAST,
        locations=(ResolvedLocation(1, "臺北市松山區"),),
        forecast=tuple(_forecast(index * 3, emoji=None) for index in range(5)),
    )

    recipe = build_weather_reply(result, QueryKind.TEXT)
    assert isinstance(recipe, TextRecipe)
    lines = recipe.text.split("\n")

    # Header, blank, 4 periods, blank separator, then the fifth period.
    assert lines[6] == ""
    assert lines[7].startswith("⛅")
    assert sum(1 for line in lines if line.startswith("⛅")) == 5


def test_forecast_renders_at_most_eight_periods() -> None:
    """Keep the reply short by rendering only the first eight forecast periods."""
    result = WeatherQueryResult(
        QueryOutcome.FORECAST,
        locations=(ResolvedLocation(1, "臺北市松山區"),),
        forecast=tuple(_forecast(index, emoji="☀️") for index in range(10)),
    )

    recipe = build_weather_reply(result, QueryKind.TEXT)
    assert isinstance(recipe, TextRecipe)

    assert sum(1 for line in recipe.text.split("\n") if line.startswith("☀️")) == 8
