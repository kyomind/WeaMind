"""Test Quick Reply presentation from workflow output."""

from unittest.mock import Mock, patch

from linebot.v3.webhooks import MessageEvent, TextMessageContent

from app.line.service import handle_message_event
from app.weather.workflow import LocationData, QueryOutcome, WeatherQueryResult


def test_multiple_locations_create_quick_reply() -> None:
    """Create choices exclusively from the workflow DTO."""
    event = Mock(spec=MessageEvent)
    event.reply_token = "token"
    event.source = None
    event.message = Mock(spec=TextMessageContent)
    event.message.text = "永和"
    result = WeatherQueryResult(
        QueryOutcome.MULTIPLE_LOCATIONS,
        locations=(LocationData(1, "新北市永和區"), LocationData(2, "臺南市永和區")),
    )
    with (
        patch("app.line.service.query_text", return_value=result) as query,
        patch("app.line.service.MessagingApi") as messaging,
        patch("app.line.service.ApiClient"),
    ):
        handle_message_event(event)
    query.assert_called_once_with("永和", None)
    message = messaging.return_value.reply_message.call_args.args[0].messages[0]
    assert [item.action.text for item in message.quick_reply.items] == [
        "新北市永和區",
        "臺南市永和區",
    ]


def test_non_multiple_result_has_no_quick_reply() -> None:
    """Do not create choices for a workflow result without locations."""
    event = Mock(spec=MessageEvent)
    event.reply_token = "token"
    event.source = None
    event.message = Mock(spec=TextMessageContent)
    event.message.text = "不存在"
    result = WeatherQueryResult(QueryOutcome.LOCATION_NOT_FOUND)
    with (
        patch("app.line.service.query_text", return_value=result),
        patch("app.line.service.MessagingApi") as messaging,
        patch("app.line.service.ApiClient"),
    ):
        handle_message_event(event)
    message = messaging.return_value.reply_message.call_args.args[0].messages[0]
    assert message.quick_reply is None
