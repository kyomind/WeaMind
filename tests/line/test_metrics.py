"""Test LINE webhook metrics helpers."""

from unittest.mock import Mock, patch

import pytest
from linebot.v3.exceptions import InvalidSignatureError

from app.line.metrics import (
    extract_event_types_from_body,
    line_webhook_event_duration_seconds,
    line_webhook_events_error_total,
    line_webhook_events_success_total,
    line_webhook_events_total,
    normalize_event_type,
    normalize_runtime_event_type,
    record_webhook_duration,
    record_webhook_error,
    record_webhook_received,
    record_webhook_success,
)
from app.line.service import _resolve_event_handler, process_webhook_events


class TestLineMetrics:
    """Test webhook metric labeling helpers."""

    def test_extract_event_types_for_text_and_postback(self) -> None:
        """Test extracting the MVP event_type labels from a webhook body."""
        body = (
            '{"events":[{"type":"message","message":{"type":"text"}},'
            '{"type":"postback","postback":{"data":"x"}}]}'
        )

        assert extract_event_types_from_body(body) == ["message_text", "postback"]

    def test_extract_event_types_returns_unknown_for_invalid_json(self) -> None:
        """Test invalid webhook JSON falls back to the unknown label."""
        assert extract_event_types_from_body("not-json") == ["unknown"]

    def test_extract_event_types_returns_unknown_for_non_dict_events(self) -> None:
        """Test non-dict events fall back to the unknown label."""
        body = '{"events":["not-a-dict"]}'

        assert extract_event_types_from_body(body) == ["unknown"]

    def test_normalize_event_type_for_location_message(self) -> None:
        """Test location messages map to the dedicated MVP label."""
        event = {"type": "message", "message": {"type": "location"}}

        assert normalize_event_type(event) == "message_location"

    def test_normalize_event_type_for_unhandled_message(self) -> None:
        """Test unsupported message types collapse into the default label."""
        event = {"type": "message", "message": {"type": "image"}}

        assert normalize_event_type(event) == "default"

    def test_normalize_event_type_without_message_dict(self) -> None:
        """Test message events without a message dict fall back to default."""
        event = {"type": "message", "message": "invalid"}

        assert normalize_event_type(event) == "default"

    def test_normalize_event_type_without_type_returns_unknown(self) -> None:
        """Test events without a type fall back to the unknown label."""
        event = {"replyToken": "test"}

        assert normalize_event_type(event) == "unknown"

    def test_normalize_event_type_for_unknown_non_message_type(self) -> None:
        """Test unsupported non-message event types fall back to the default label."""
        event = {"type": "join"}

        assert normalize_event_type(event) == "default"

    def test_normalize_runtime_event_type_for_follow_event(self) -> None:
        """Test parsed event objects map to the expected event_type label."""
        event = Mock()
        event.type = "follow"

        assert normalize_runtime_event_type(event) == "follow"

    def test_normalize_runtime_event_type_for_message_variants(self) -> None:
        """Test runtime message events map to text, location, or default labels."""
        text_event = Mock()
        text_event.type = "message"
        text_event.message = Mock(type="text")

        location_event = Mock()
        location_event.type = "message"
        location_event.message = Mock(type="location")

        default_event = Mock()
        default_event.type = "message"
        default_event.message = Mock(type="image")

        assert normalize_runtime_event_type(text_event) == "message_text"
        assert normalize_runtime_event_type(location_event) == "message_location"
        assert normalize_runtime_event_type(default_event) == "default"

    def test_normalize_runtime_event_type_fallbacks(self) -> None:
        """Test runtime events fall back to unknown or default when needed."""
        unknown_event = Mock()
        unknown_event.type = None

        default_event = Mock()
        default_event.type = "join"

        assert normalize_runtime_event_type(unknown_event) == "unknown"
        assert normalize_runtime_event_type(default_event) == "default"

    def test_record_webhook_helpers_increment_metrics(self) -> None:
        """Test metric helper functions increment their Prometheus series."""
        received_metric = line_webhook_events_total.labels(event_type="received_test")
        success_metric = line_webhook_events_success_total.labels(event_type="success_test")
        error_metric = line_webhook_events_error_total.labels(
            event_type="error_test",
            error_type="handler_error",
        )
        duration_metric = line_webhook_event_duration_seconds.labels(event_type="duration_test")

        received_before = received_metric._value.get()
        success_before = success_metric._value.get()
        error_before = error_metric._value.get()
        duration_sum_before = duration_metric._sum.get()
        duration_bucket_before = duration_metric._buckets[0].get()

        record_webhook_received(["received_test"])
        record_webhook_success(["success_test"])
        record_webhook_error(["error_test"], "handler_error")
        record_webhook_duration(["duration_test"], 0.005)

        assert received_metric._value.get() == received_before + 1
        assert success_metric._value.get() == success_before + 1
        assert error_metric._value.get() == error_before + 1
        assert duration_metric._sum.get() == pytest.approx(duration_sum_before + 0.005)
        assert duration_metric._buckets[0].get() == duration_bucket_before + 1

    def test_process_webhook_events_records_per_event_metrics(self) -> None:
        """Test webhook processing records metrics for each dispatched event."""
        first_event = Mock()
        first_event.type = "follow"
        second_event = Mock()
        second_event.type = "postback"
        payload = Mock(events=[first_event, second_event])

        with patch("app.line.service.webhook_handler.parser.parse", return_value=payload):
            with patch("app.line.service._resolve_event_handler", return_value=object()):
                with patch("app.line.service.webhook_handler._WebhookHandler__invoke_func"):
                    with patch(
                        "app.line.service.line_metrics.record_webhook_success"
                    ) as mock_success:
                        with patch(
                            "app.line.service.line_metrics.record_webhook_duration"
                        ) as mock_duration:
                            process_webhook_events("{}", "signature")

        assert mock_success.call_args_list == [((["follow"],),), ((["postback"],),)]
        assert mock_duration.call_count == 2

    def test_resolve_event_handler_uses_message_registration_first(self) -> None:
        """Test message events prefer the message-specific registered handler."""

        class FakeMessageEvent:
            """Lightweight stand-in for MessageEvent in handler resolution tests."""

            def __init__(self, message: object) -> None:
                """Store a message object for handler-key resolution."""
                self.message = message

        event = FakeMessageEvent(object())
        handler = object()

        with patch("app.line.service.MessageEvent", FakeMessageEvent):
            with patch(
                "app.line.service.webhook_handler._WebhookHandler__get_handler_key",
                side_effect=["message-key"],
            ) as mock_get_handler_key:
                with patch.dict(
                    "app.line.service.webhook_handler._handlers",
                    {"message-key": handler},
                    clear=True,
                ):
                    resolved_handler = _resolve_event_handler(event)

        assert resolved_handler is handler
        mock_get_handler_key.assert_called_once_with(FakeMessageEvent, object)

    def test_resolve_event_handler_falls_back_to_default_handler(self) -> None:
        """Test handler resolution returns the SDK default when no registration matches."""
        event = Mock()
        default_handler = object()

        with patch(
            "app.line.service.webhook_handler._WebhookHandler__get_handler_key",
            return_value="missing-key",
        ):
            with patch.dict("app.line.service.webhook_handler._handlers", {}, clear=True):
                with patch("app.line.service.webhook_handler._default", default_handler):
                    resolved_handler = _resolve_event_handler(event)

        assert resolved_handler is default_handler

    def test_process_webhook_events_records_signature_error_during_parse(self) -> None:
        """Test parse-time signature errors use fallback labels and record failure metrics."""
        with patch(
            "app.line.service.webhook_handler.parser.parse",
            side_effect=InvalidSignatureError("bad signature"),
        ):
            with patch("app.line.service.line_metrics.record_webhook_error") as mock_error:
                with patch(
                    "app.line.service.line_metrics.record_webhook_duration"
                ) as mock_duration:
                    with pytest.raises(InvalidSignatureError):
                        process_webhook_events("{}", "signature", ["follow"])

        mock_error.assert_called_once_with(["follow"], "signature_error")
        mock_duration.assert_called_once()

    def test_process_webhook_events_records_parse_failure_as_handler_error(self) -> None:
        """Test parse-time non-signature failures fall back to handler_error metrics."""
        with patch(
            "app.line.service.webhook_handler.parser.parse",
            side_effect=RuntimeError("parse failed"),
        ):
            with patch("app.line.service.line_metrics.record_webhook_error") as mock_error:
                with patch(
                    "app.line.service.line_metrics.record_webhook_duration"
                ) as mock_duration:
                    with pytest.raises(RuntimeError, match="parse failed"):
                        process_webhook_events("{}", "signature")

        mock_error.assert_called_once_with(["unknown"], "handler_error")
        mock_duration.assert_called_once()

    def test_process_webhook_events_skips_metrics_when_no_handler_is_resolved(self) -> None:
        """Test events without a resolved handler only record duration before continuing."""
        event = Mock()
        event.type = "follow"
        payload = Mock(events=[event])

        with patch("app.line.service.webhook_handler.parser.parse", return_value=payload):
            with patch("app.line.service._resolve_event_handler", return_value=None):
                with patch("app.line.service.line_metrics.record_webhook_success") as mock_success:
                    with patch("app.line.service.line_metrics.record_webhook_error") as mock_error:
                        with patch(
                            "app.line.service.line_metrics.record_webhook_duration"
                        ) as mock_duration:
                            process_webhook_events("{}", "signature")

        mock_success.assert_not_called()
        mock_error.assert_not_called()
        mock_duration.assert_called_once()

    def test_process_webhook_events_records_signature_error_during_invoke(self) -> None:
        """Test invoke-time signature errors are recorded for the current event only."""
        event = Mock()
        event.type = "follow"
        payload = Mock(events=[event])

        with patch("app.line.service.webhook_handler.parser.parse", return_value=payload):
            with patch("app.line.service._resolve_event_handler", return_value=object()):
                with patch(
                    "app.line.service.webhook_handler._WebhookHandler__invoke_func",
                    side_effect=InvalidSignatureError("expired"),
                ):
                    with patch("app.line.service.line_metrics.record_webhook_error") as mock_error:
                        with patch(
                            "app.line.service.line_metrics.record_webhook_duration"
                        ) as mock_duration:
                            with pytest.raises(InvalidSignatureError):
                                process_webhook_events("{}", "signature")

        mock_error.assert_called_once_with(["follow"], "signature_error")
        mock_duration.assert_called_once()

    def test_process_webhook_events_stops_after_failing_event(self) -> None:
        """Test webhook processing records failure for the current event only."""
        first_event = Mock()
        first_event.type = "follow"
        second_event = Mock()
        second_event.type = "unfollow"
        third_event = Mock()
        third_event.type = "postback"
        payload = Mock(events=[first_event, second_event, third_event])

        with patch("app.line.service.webhook_handler.parser.parse", return_value=payload):
            with patch("app.line.service._resolve_event_handler", return_value=object()):
                with patch(
                    "app.line.service.webhook_handler._WebhookHandler__invoke_func",
                    side_effect=[None, Exception("boom")],
                ):
                    with patch(
                        "app.line.service.line_metrics.record_webhook_success"
                    ) as mock_success:
                        with patch(
                            "app.line.service.line_metrics.record_webhook_error"
                        ) as mock_error:
                            with patch(
                                "app.line.service.line_metrics.record_webhook_duration"
                            ) as mock_duration:
                                try:
                                    process_webhook_events("{}", "signature")
                                except Exception as exc:
                                    assert str(exc) == "boom"

        assert mock_success.call_args_list == [((["follow"],),)]
        mock_error.assert_called_once_with(["unfollow"], "handler_error")
        assert mock_duration.call_count == 2
