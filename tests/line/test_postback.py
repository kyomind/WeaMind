"""Test PostBack handlers through the recipe-based messenger seam."""

from unittest.mock import Mock, patch

import pytest
from linebot.v3.webhooks import PostbackEvent

from app.core.config import settings
from app.line.messaging import (
    InMemoryReplyMessenger,
    LocationRequestRecipe,
    MessageChoice,
    MessageChoicesRecipe,
    SendErrorCategory,
    SentReply,
    TextRecipe,
    UriChoice,
    UriChoicesRecipe,
)
from app.line.postback import (
    dispatch_postback,
    handle_current_location_weather,
    handle_other_postback,
    handle_recent_queries_postback,
    handle_settings_postback,
    handle_weather_postback,
    parse_postback_data,
    should_use_processing_lock,
)
from app.line.service import handle_postback_event
from app.weather.workflow import QueryOutcome, WeatherQueryResult


def _postback_event(
    *,
    reply_token: str | None = "test_token",
    user_id: str | None = "test_user_id",
    data: str = "action=unknown",
) -> Mock:
    """Create a minimal PostBack event double without SDK model construction."""
    event = Mock(spec=PostbackEvent)
    event.reply_token = reply_token
    event.postback = Mock(data=data)
    event.source = Mock(user_id=user_id) if user_id is not None else None
    return event


@pytest.mark.parametrize(
    ("raw_data", "expected"),
    [
        ("action=weather&type=home", {"action": "weather", "type": "home"}),
        ("action=recent_queries", {"action": "recent_queries"}),
        ("", {}),
        ("invalid_format", {}),
    ],
)
def test_parse_postback_data(raw_data: str, expected: dict[str, str]) -> None:
    """Parse valid query strings and reject values without assignments."""
    assert parse_postback_data(raw_data) == expected


def test_parse_postback_data_contains_parser_exception() -> None:
    """Return an empty mapping when query parsing unexpectedly fails."""
    with patch("app.line.postback.parse_qs", side_effect=RuntimeError("parse error")):
        assert parse_postback_data("action=weather") == {}


@pytest.mark.parametrize(
    ("postback_data", "expected"),
    [
        ({"action": "weather", "type": "home"}, True),
        ({"action": "weather", "type": "office"}, True),
        ({"action": "recent_queries"}, True),
        ({"action": "weather", "type": "current"}, False),
        ({"action": "settings", "type": "location"}, False),
        ({"action": "other", "type": "menu"}, False),
        ({"action": "unknown"}, False),
        ({}, False),
    ],
)
def test_should_use_processing_lock(postback_data: dict[str, str], expected: bool) -> None:
    """Use the processing lock only for database-backed query actions."""
    assert should_use_processing_lock(postback_data) is expected


def test_handle_postback_event_requires_reply_token() -> None:
    """Ignore a PostBack event without a reply token."""
    messenger = InMemoryReplyMessenger()

    handle_postback_event(_postback_event(reply_token=None), messenger)

    assert messenger.sent_replies == []


def test_handle_postback_event_requires_user_id() -> None:
    """Ignore a PostBack event without a user identifier."""
    messenger = InMemoryReplyMessenger()

    handle_postback_event(_postback_event(user_id=None), messenger)

    assert messenger.sent_replies == []


def test_handle_postback_event_unknown_action_replies_with_recipe() -> None:
    """Reply with a stable text recipe for an unknown PostBack action."""
    messenger = InMemoryReplyMessenger()

    handle_postback_event(_postback_event(), messenger)

    assert messenger.sent_replies == [SentReply("test_token", TextRecipe("未知的操作"))]


def test_handle_postback_event_contains_dispatch_exception() -> None:
    """Contain dispatch failures and send the generic error recipe."""
    messenger = InMemoryReplyMessenger()
    event = _postback_event()

    with patch("app.line.service.dispatch_postback", side_effect=RuntimeError("boom")):
        handle_postback_event(event, messenger)

    assert messenger.sent_replies == [
        SentReply("test_token", TextRecipe("系統暫時有點忙，請稍後再試一次。"))
    ]


def test_handle_weather_postback_preset_not_set() -> None:
    """Prompt for setup when the requested preset has not been configured."""
    messenger = InMemoryReplyMessenger()
    event = _postback_event()
    query_result = WeatherQueryResult(QueryOutcome.PRESET_NOT_SET)

    with patch("app.line.postback.query_preset", return_value=query_result) as query:
        handle_weather_postback(
            event,
            "test_user_id",
            {"action": "weather", "type": "home"},
            messenger,
        )

    query.assert_called_once_with("test_user_id", "home")
    assert messenger.sent_replies == [
        SentReply(
            "test_token",
            TextRecipe("請先設定住家地址，點擊下方「設定地點」按鈕即可設定。"),
        )
    ]


def test_handle_weather_postback_success() -> None:
    """Reply with formatted weather when a preset query succeeds."""
    messenger = InMemoryReplyMessenger()
    event = _postback_event()
    query_result = WeatherQueryResult(QueryOutcome.FORECAST)

    with (
        patch("app.line.postback.query_preset", return_value=query_result) as query,
        patch("app.line.postback.format_weather_query", return_value="晴朗") as format_query,
    ):
        handle_weather_postback(
            event,
            "test_user_id",
            {"action": "weather", "type": "office"},
            messenger,
        )

    query.assert_called_once_with("test_user_id", "office")
    format_query.assert_called_once_with(query_result)
    assert messenger.sent_replies == [SentReply("test_token", TextRecipe("晴朗"))]


def test_handle_weather_postback_unknown_type() -> None:
    """Reply with an error recipe for an unknown weather location type."""
    messenger = InMemoryReplyMessenger()

    handle_weather_postback(
        _postback_event(),
        "test_user_id",
        {"action": "weather", "type": "unknown"},
        messenger,
    )

    assert messenger.sent_replies == [SentReply("test_token", TextRecipe("未知的地點類型"))]


def test_handle_current_location_weather_creates_location_recipe() -> None:
    """Create a location-request recipe for current-location weather."""
    messenger = InMemoryReplyMessenger()

    handle_current_location_weather(_postback_event(), messenger)

    assert messenger.sent_replies == [
        SentReply(
            "test_token",
            LocationRequestRecipe(
                text="請點擊地圖上任意位置，將為您查詢該地天氣",
                label="開啟地圖選擇",
            ),
        )
    ]


def test_handle_settings_postback_location_creates_text_recipe() -> None:
    """Create the LIFF settings text without invoking a transport adapter."""
    messenger = InMemoryReplyMessenger()

    handle_settings_postback(
        _postback_event(), {"action": "settings", "type": "location"}, messenger
    )

    sent_recipe = messenger.sent_replies[0].recipe
    assert isinstance(sent_recipe, TextRecipe)
    assert "地點設定" in sent_recipe.text
    assert settings.BASE_URL in sent_recipe.text


def test_handle_settings_postback_unknown_type() -> None:
    """Reply with an error recipe for an unknown settings type."""
    messenger = InMemoryReplyMessenger()

    handle_settings_postback(
        _postback_event(), {"action": "settings", "type": "unknown"}, messenger
    )

    assert messenger.sent_replies == [SentReply("test_token", TextRecipe("未知的設定類型"))]


def test_handle_recent_queries_postback_no_history() -> None:
    """Reply with guidance after releasing the session when history is empty."""
    event = _postback_event()
    messenger = InMemoryReplyMessenger()

    with (
        patch("app.line.postback.SessionLocal") as session_factory,
        patch("app.line.postback.get_user_by_line_id") as get_user,
        patch("app.line.postback.get_recent_queries", return_value=[]),
    ):
        user = Mock(id=1)
        get_user.return_value = user
        handle_recent_queries_postback(event, messenger)

    session_factory.return_value.__exit__.assert_called_once()
    assert messenger.sent_replies == [
        SentReply(
            "test_token",
            TextRecipe("您還沒有查詢過其他地點的天氣\n\n試試看輸入地點名稱來查詢天氣吧！"),
        )
    ]


def test_handle_recent_queries_postback_creates_user() -> None:
    """Create a missing user before querying recent locations."""
    event = _postback_event()
    messenger = InMemoryReplyMessenger()

    with (
        patch("app.line.postback.SessionLocal") as session_factory,
        patch("app.line.postback.get_user_by_line_id", return_value=None),
        patch("app.line.postback.create_user_if_not_exists") as create_user,
        patch("app.line.postback.get_recent_queries", return_value=[]),
    ):
        created_user = Mock(id=7)
        create_user.return_value = created_user
        handle_recent_queries_postback(event, messenger)

    session = session_factory.return_value.__enter__.return_value
    create_user.assert_called_once_with(session, "test_user_id")


def test_handle_recent_queries_postback_with_history() -> None:
    """Translate recent location names into message choices."""
    event = _postback_event()
    messenger = InMemoryReplyMessenger()
    recent_locations = [
        Mock(full_name="臺北市中正區"),
        Mock(full_name="新北市板橋區"),
    ]

    with (
        patch("app.line.postback.SessionLocal") as session_factory,
        patch("app.line.postback.get_user_by_line_id", return_value=Mock(id=1)),
        patch("app.line.postback.get_recent_queries", return_value=recent_locations),
    ):
        handle_recent_queries_postback(event, messenger)

    session_factory.return_value.__exit__.assert_called_once()
    assert messenger.sent_replies == [
        SentReply(
            "test_token",
            MessageChoicesRecipe(
                text="最近查過的 5 個地點：",
                choices=(
                    MessageChoice("臺北市中正區", "臺北市中正區"),
                    MessageChoice("新北市板橋區", "新北市板橋區"),
                ),
            ),
        )
    ]


def test_handle_recent_queries_does_not_retry_failed_reply() -> None:
    """Do not consume a reply token twice after a failed history reply."""
    event = _postback_event()
    messenger = InMemoryReplyMessenger(failure_category=SendErrorCategory.TRANSPORT)

    reply = Mock(side_effect=messenger.reply)
    messenger_double = Mock(reply=reply)
    with (
        patch("app.line.postback.SessionLocal"),
        patch("app.line.postback.get_user_by_line_id", return_value=Mock(id=1)),
        patch(
            "app.line.postback.get_recent_queries",
            return_value=[Mock(full_name="臺北市中正區")],
        ),
    ):
        handle_recent_queries_postback(event, messenger_double)

    reply.assert_called_once()
    assert messenger.sent_replies == []


def test_handle_recent_queries_postback_contains_database_error() -> None:
    """Contain database failures and send the generic error recipe."""
    messenger = InMemoryReplyMessenger()

    with patch("app.line.postback.SessionLocal", side_effect=RuntimeError("db error")):
        handle_recent_queries_postback(_postback_event(), messenger)

    assert messenger.sent_replies == [
        SentReply("test_token", TextRecipe("系統暫時有點忙，請稍後再試一次。"))
    ]


def test_handle_other_postback_menu_creates_uri_choices() -> None:
    """Create stable URI choices for the other-information menu."""
    messenger = InMemoryReplyMessenger()

    handle_other_postback(_postback_event(), {"action": "other", "type": "menu"}, messenger)

    assert messenger.sent_replies == [
        SentReply(
            "test_token",
            UriChoicesRecipe(
                text="請選擇想了解的資訊：",
                choices=(
                    UriChoice(
                        "🔄 更新",
                        "https://github.com/kyomind/WeaMind/blob/main/CHANGELOG.md",
                    ),
                    UriChoice(
                        "📖 使用說明",
                        "https://github.com/kyomind/WeaMind/blob/main/README.md",
                    ),
                    UriChoice("ℹ️ 專案介紹", "https://api.kyomind.tw/static/about/index.html"),
                ),
            ),
        )
    ]


def test_dispatch_postback_routes_weather_action() -> None:
    """Route the weather action to a preset query and reply with its forecast text."""
    messenger = InMemoryReplyMessenger()
    query_result = WeatherQueryResult(QueryOutcome.FORECAST)

    with (
        patch("app.line.postback.query_preset", return_value=query_result) as query,
        patch("app.line.postback.format_weather_query", return_value="晴朗"),
    ):
        dispatch_postback(
            _postback_event(),
            "test_user_id",
            {"action": "weather", "type": "home"},
            messenger,
        )

    query.assert_called_once_with("test_user_id", "home")
    assert messenger.sent_replies == [SentReply("test_token", TextRecipe("晴朗"))]


def test_dispatch_postback_routes_settings_action() -> None:
    """Route the settings action to the LIFF location-settings reply."""
    messenger = InMemoryReplyMessenger()

    dispatch_postback(
        _postback_event(),
        "test_user_id",
        {"action": "settings", "type": "location"},
        messenger,
    )

    sent_recipe = messenger.sent_replies[0].recipe
    assert isinstance(sent_recipe, TextRecipe)
    assert "地點設定" in sent_recipe.text


def test_dispatch_postback_routes_recent_queries_action() -> None:
    """Route the recent-queries action to the history handler."""
    messenger = InMemoryReplyMessenger()

    with (
        patch("app.line.postback.SessionLocal"),
        patch("app.line.postback.get_user_by_line_id", return_value=Mock(id=1)),
        patch("app.line.postback.get_recent_queries", return_value=[]),
    ):
        dispatch_postback(
            _postback_event(),
            "test_user_id",
            {"action": "recent_queries"},
            messenger,
        )

    assert messenger.sent_replies == [
        SentReply(
            "test_token",
            TextRecipe("您還沒有查詢過其他地點的天氣\n\n試試看輸入地點名稱來查詢天氣吧！"),
        )
    ]


def test_dispatch_postback_routes_other_action() -> None:
    """Route the other action to the information menu of URI choices."""
    messenger = InMemoryReplyMessenger()

    dispatch_postback(
        _postback_event(),
        "test_user_id",
        {"action": "other", "type": "menu"},
        messenger,
    )

    sent_recipe = messenger.sent_replies[0].recipe
    assert isinstance(sent_recipe, UriChoicesRecipe)
    assert sent_recipe.text == "請選擇想了解的資訊："


def test_dispatch_postback_unknown_action() -> None:
    """Reply with the unknown-operation text for an unroutable action."""
    messenger = InMemoryReplyMessenger()

    dispatch_postback(_postback_event(), "test_user_id", {"action": "nope"}, messenger)

    assert messenger.sent_replies == [SentReply("test_token", TextRecipe("未知的操作"))]


def test_handle_weather_postback_current_type_requests_location() -> None:
    """Route the current location type to the map location-request recipe."""
    messenger = InMemoryReplyMessenger()

    handle_weather_postback(
        _postback_event(),
        "test_user_id",
        {"action": "weather", "type": "current"},
        messenger,
    )

    assert messenger.sent_replies == [
        SentReply(
            "test_token",
            LocationRequestRecipe(
                text="請點擊地圖上任意位置，將為您查詢該地天氣",
                label="開啟地圖選擇",
            ),
        )
    ]


def test_handle_weather_postback_contains_query_error() -> None:
    """Contain preset query failures and send the query-error recipe."""
    messenger = InMemoryReplyMessenger()

    with patch("app.line.postback.query_preset", side_effect=RuntimeError("query error")):
        handle_weather_postback(
            _postback_event(),
            "test_user_id",
            {"action": "weather", "type": "home"},
            messenger,
        )

    assert messenger.sent_replies == [
        SentReply("test_token", TextRecipe("查詢時發生錯誤，請稍後再試。"))
    ]


def test_handle_recent_queries_postback_requires_user_id() -> None:
    """Reply with an identification error and skip the database without a user id."""
    messenger = InMemoryReplyMessenger()

    with patch("app.line.postback.SessionLocal") as session_factory:
        handle_recent_queries_postback(_postback_event(user_id=None), messenger)

    session_factory.assert_not_called()
    assert messenger.sent_replies == [SentReply("test_token", TextRecipe("用戶識別錯誤"))]


def test_handle_other_postback_unknown_type() -> None:
    """Reply with the unknown-operation text for an unknown other type."""
    messenger = InMemoryReplyMessenger()

    handle_other_postback(_postback_event(), {"action": "other", "type": "unknown"}, messenger)

    assert messenger.sent_replies == [SentReply("test_token", TextRecipe("未知的操作"))]
