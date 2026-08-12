"""Test Quick Reply recipes created from weather workflow output."""

from collections.abc import Callable
from unittest.mock import Mock, patch

from app.line.messaging import (
    InMemoryReplyMessenger,
    MessageChoice,
    MessageChoicesRecipe,
    SentReply,
    TextRecipe,
)
from app.line.service import handle_message_event
from app.weather.workflow import LocationData, QueryOutcome, WeatherQueryResult


def test_multiple_locations_create_message_choices_recipe(
    create_mock_message_event: Callable[..., Mock],
) -> None:
    """Create message choices exclusively from the workflow DTO."""
    event = create_mock_message_event(reply_token="token", text="永和", user_id=None)
    query_result = WeatherQueryResult(
        QueryOutcome.MULTIPLE_LOCATIONS,
        locations=(LocationData(1, "新北市永和區"), LocationData(2, "臺南市永和區")),
    )
    messenger = InMemoryReplyMessenger()

    with patch("app.line.service.query_text", return_value=query_result) as query:
        handle_message_event(event, messenger)

    query.assert_called_once_with("永和", None)
    assert messenger.sent_replies == [
        SentReply(
            reply_token="token",
            recipe=MessageChoicesRecipe(
                text="找到多個符合的地點，請選擇：",
                choices=(
                    MessageChoice(label="新北市永和區", text="新北市永和區"),
                    MessageChoice(label="臺南市永和區", text="臺南市永和區"),
                ),
            ),
        )
    ]


def test_non_multiple_result_creates_plain_text_recipe(
    create_mock_message_event: Callable[..., Mock],
) -> None:
    """Create plain text when the workflow returns no location choices."""
    event = create_mock_message_event(reply_token="token", text="不存在", user_id=None)
    query_result = WeatherQueryResult(QueryOutcome.LOCATION_NOT_FOUND)
    messenger = InMemoryReplyMessenger()

    with patch("app.line.service.query_text", return_value=query_result):
        handle_message_event(event, messenger)

    assert len(messenger.sent_replies) == 1
    assert messenger.sent_replies[0].reply_token == "token"
    assert isinstance(messenger.sent_replies[0].recipe, TextRecipe)
