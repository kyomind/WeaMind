"""Test the deep PostBack action module and its LINE event adapter."""

from dataclasses import FrozenInstanceError
from unittest.mock import ANY, Mock, patch

import pytest
from linebot.v3.webhooks import PostbackEvent

from app.line.messaging import (
    InMemoryReplyMessenger,
    LocationRequestRecipe,
    MessageChoice,
    MessageChoicesRecipe,
    SentReply,
    TextRecipe,
    UriChoice,
    UriChoicesRecipe,
)
from app.line.postback import (
    CurrentWeatherAction,
    InvalidAction,
    LocationSettingsAction,
    OtherMenuAction,
    PresetWeatherAction,
    RecentQueriesAction,
    execute_postback,
    prepare_postback,
)
from app.line.service import handle_postback_event
from app.line.weather_presentation import QueryKind
from app.weather.location_resolution import QueryOutcome
from app.weather.workflow import WeatherQueryResult


def _event(
    *, token: str | None = "token", user_id: str | None = "user", data: str = "action=unknown"
) -> Mock:
    """Create a minimal SDK event double for adapter tests."""
    event = Mock(spec=PostbackEvent)
    event.reply_token = token
    event.source = Mock(user_id=user_id) if user_id else None
    event.postback = Mock(data=data)
    return event


@pytest.mark.parametrize(
    ("data", "action_type", "requires_lock"),
    [
        ("action=weather&type=home", PresetWeatherAction, True),
        ("action=weather&type=current", CurrentWeatherAction, False),
        ("action=settings&type=location", LocationSettingsAction, False),
        ("action=recent_queries", RecentQueriesAction, True),
        ("action=other&type=menu", OtherMenuAction, False),
        ("action=other&type=nope", InvalidAction, False),
        ("action=nope", InvalidAction, False),
    ],
)
def test_prepare_postback_creates_typed_plan(
    data: str, action_type: type[object], requires_lock: bool
) -> None:
    """Prepare closed action variants with their lock policy."""
    plan = prepare_postback(data, "user")
    assert isinstance(plan.action, action_type)
    assert plan.requires_lock is requires_lock


def test_prepare_preserves_specific_invalid_recipe() -> None:
    """Keep detailed validation copy in invalid action variants."""
    assert prepare_postback("action=weather", "user").action == InvalidAction(
        TextRecipe("未知的地點類型")
    )
    assert prepare_postback("action=settings&type=nope", "user").action == InvalidAction(
        TextRecipe("未知的設定類型")
    )


@pytest.mark.parametrize("raw_data", ["", "action=unknown"])
def test_prepare_contains_empty_or_unknown_data(raw_data: str) -> None:
    """Turn empty or unknown data into the compatible invalid action."""
    assert prepare_postback(raw_data, "user").action == InvalidAction(TextRecipe("未知的操作"))


def test_prepare_contains_parser_exception() -> None:
    """Turn parser failures into the compatible invalid action."""
    with patch("app.line.postback.parse_qs", side_effect=ValueError("broken data")):
        plan = prepare_postback("action=weather", "user")
    assert plan.action == InvalidAction(TextRecipe("未知的操作"))


def test_plan_is_immutable() -> None:
    """Prevent policy mutation between preparation and execution."""
    plan = prepare_postback("action=recent_queries", "user")
    with pytest.raises(FrozenInstanceError):
        plan.requires_lock = False  # type: ignore[misc]


def test_execute_preset_weather() -> None:
    """Execute preset weather and return its presentation recipe."""
    result = WeatherQueryResult(QueryOutcome.FORECAST)
    plan = prepare_postback("action=weather&type=office", "user")
    with (
        patch("app.line.postback.query_preset", return_value=result) as query,
        patch("app.line.postback.build_weather_reply", return_value=TextRecipe("晴朗")) as build,
    ):
        assert execute_postback(plan) == TextRecipe("晴朗")
    query.assert_called_once_with("user", "office")
    build.assert_called_once_with(result, QueryKind.PRESET_OFFICE)


def test_execute_closes_history_session_before_returning() -> None:
    """Close query-history DB resources before returning the recipe."""
    plan = prepare_postback("action=recent_queries", "user")
    with (
        patch("app.line.postback.SessionLocal") as factory,
        patch("app.line.postback.get_user_by_line_id", return_value=Mock(id=1)),
        patch("app.line.postback.get_recent_queries", return_value=[]),
    ):
        recipe = execute_postback(plan)
    factory.return_value.__exit__.assert_called_once()
    assert recipe == TextRecipe("您還沒有查詢過其他地點的天氣\n\n試試看輸入地點名稱來查詢天氣吧！")


def test_execute_recent_queries_creates_user_and_returns_choices() -> None:
    """Create an unknown user and preserve recent-location choice ordering."""
    locations = [Mock(full_name="臺北市信義區"), Mock(full_name="嘉義縣水上鄉")]
    plan = prepare_postback("action=recent_queries", "user")
    with (
        patch("app.line.postback.SessionLocal"),
        patch("app.line.postback.get_user_by_line_id", return_value=None),
        patch("app.line.postback.create_user_if_not_exists", return_value=Mock(id=7)) as create,
        patch("app.line.postback.get_recent_queries", return_value=locations) as recent,
    ):
        recipe = execute_postback(plan)
    create.assert_called_once()
    recent.assert_called_once_with(ANY, 7, limit=5)
    assert recipe == MessageChoicesRecipe(
        text="最近查過的 5 個地點：",
        choices=(
            MessageChoice("臺北市信義區", "臺北市信義區"),
            MessageChoice("嘉義縣水上鄉", "嘉義縣水上鄉"),
        ),
    )


def test_execute_contains_unexpected_exception() -> None:
    """Always return the action-compatible error recipe after failures."""
    plan = prepare_postback("action=weather&type=home", "user")
    with patch("app.line.postback.query_preset", side_effect=RuntimeError("boom")):
        assert execute_postback(plan) == TextRecipe("查詢時發生錯誤，請稍後再試。")


def test_execute_contains_recent_query_exception() -> None:
    """Return the generic compatible recipe after a Query History failure."""
    plan = prepare_postback("action=recent_queries", "user")
    with patch("app.line.postback.SessionLocal", side_effect=RuntimeError("database error")):
        assert execute_postback(plan) == TextRecipe("系統暫時有點忙，請稍後再試一次。")


def test_execute_current_location_recipe() -> None:
    """Build the existing map request recipe without a messenger dependency."""
    recipe = execute_postback(prepare_postback("action=weather&type=current", "user"))
    assert recipe == LocationRequestRecipe(
        "請點擊地圖上任意位置，將為您查詢該地天氣", "開啟地圖選擇"
    )


def test_execute_location_settings_recipe() -> None:
    """Build the existing LIFF location-settings reply."""
    with patch("app.line.postback.settings.BASE_URL", "https://example.test"):
        recipe = execute_postback(prepare_postback("action=settings&type=location", "user"))
    assert recipe == TextRecipe(
        "地點設定\n\n請點擊下方連結設定您的常用地點：\n"
        "https://example.test/static/liff/location/index.html\n\n"
        "設定完成後，您就可以透過快捷功能查詢住家或公司的天氣了！"
    )


def test_execute_other_menu_recipe() -> None:
    """Build all existing information links in their stable order."""
    recipe = execute_postback(prepare_postback("action=other&type=menu", "user"))
    assert recipe == UriChoicesRecipe(
        text="請選擇想了解的資訊：",
        choices=(
            UriChoice("🔄 更新", "https://github.com/kyomind/WeaMind/blob/main/CHANGELOG.md"),
            UriChoice("📖 使用說明", "https://github.com/kyomind/WeaMind/blob/main/README.md"),
            UriChoice("ℹ️ 專案介紹", "https://api.kyomind.tw/static/about/index.html"),
        ),
    )


def test_service_adapter_prepares_executes_and_replies() -> None:
    """Extract SDK fields and send the module's returned recipe once."""
    messenger = InMemoryReplyMessenger()
    handle_postback_event(_event(data="action=unknown"), messenger)
    assert messenger.sent_replies == [SentReply("token", TextRecipe("未知的操作"))]


@pytest.mark.parametrize("event", [_event(token=None), _event(user_id=None)])
def test_service_adapter_requires_reply_token_and_user(event: Mock) -> None:
    """Ignore SDK events lacking the context required by the action module."""
    messenger = InMemoryReplyMessenger()
    with patch("app.line.service.prepare_postback") as prepare:
        handle_postback_event(event, messenger)
    prepare.assert_not_called()
    assert messenger.sent_replies == []


def test_service_adapter_contains_preparation_exception() -> None:
    """Send the compatible fallback when the adapter itself fails."""
    messenger = InMemoryReplyMessenger()
    with patch("app.line.service.prepare_postback", side_effect=RuntimeError("boom")):
        handle_postback_event(_event(), messenger)
    assert messenger.sent_replies == [
        SentReply("token", TextRecipe("系統暫時有點忙，請稍後再試一次。"))
    ]


def test_service_adapter_uses_plan_lock_denied_recipe() -> None:
    """Apply plan lock policy before action execution."""
    messenger = InMemoryReplyMessenger()
    with (
        patch("app.line.service.settings.PROCESSING_LOCK_ENABLED", True),
        patch("app.line.service.processing_lock_service.build_lock_key", return_value="key"),
        patch("app.line.service.processing_lock_service.try_acquire_lock", return_value=False),
        patch("app.line.service.execute_postback") as execute,
    ):
        handle_postback_event(_event(data="action=recent_queries"), messenger)
    execute.assert_not_called()
    assert messenger.sent_replies == [SentReply("token", TextRecipe("操作太過頻繁，請放慢腳步 ☕️"))]
