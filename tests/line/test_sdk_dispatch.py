"""Contract tests for the LINE SDK webhook dispatch adapter."""

import inspect
from unittest.mock import Mock, patch

from linebot.v3 import WebhookHandler

from app.line.sdk_dispatch import LineSdkWebhookDispatcher


def test_parse_requests_payload_from_sdk_parser() -> None:
    """Test parsing validates the signature and requests a payload object."""
    payload = Mock(events=[])
    webhook_handler = Mock()
    webhook_handler.parser.parse.return_value = payload
    dispatcher = LineSdkWebhookDispatcher(webhook_handler)

    result = dispatcher.parse("{}", "signature")

    assert result is payload
    webhook_handler.parser.parse.assert_called_once_with("{}", "signature", as_payload=True)


def test_dispatch_prefers_message_specific_registration() -> None:
    """Test message events use their message-specific registration first."""

    class FakeMessageEvent:
        """Provide the message shape required by SDK handler resolution."""

        def __init__(self, message: object) -> None:
            """Store the message used to derive the handler key."""
            self.message = message

    event = FakeMessageEvent(object())
    payload = Mock(events=[event])
    registered_handler = object()
    webhook_handler = Mock()
    webhook_handler._handlers = {"message-key": registered_handler}
    webhook_handler._WebhookHandler__get_handler_key.return_value = "message-key"
    dispatcher = LineSdkWebhookDispatcher(webhook_handler)

    with patch("app.line.sdk_dispatch.MessageEvent", FakeMessageEvent):
        dispatched = dispatcher.dispatch(event, payload)

    assert dispatched is True
    webhook_handler._WebhookHandler__get_handler_key.assert_called_once_with(
        FakeMessageEvent, object
    )
    webhook_handler._WebhookHandler__invoke_func.assert_called_once_with(
        registered_handler, event, payload
    )


def test_dispatch_uses_event_registration_after_message_specific_miss() -> None:
    """Test dispatch falls back from a message-specific key to its event key."""

    class FakeMessageEvent:
        """Provide the message shape required by SDK handler resolution."""

        def __init__(self, message: object) -> None:
            """Store the message used to derive the handler key."""
            self.message = message

    event = FakeMessageEvent(object())
    payload = Mock(events=[event])
    registered_handler = object()
    webhook_handler = Mock()
    webhook_handler._handlers = {"event-key": registered_handler}
    webhook_handler._WebhookHandler__get_handler_key.side_effect = [
        "message-key",
        "event-key",
    ]
    dispatcher = LineSdkWebhookDispatcher(webhook_handler)

    with patch("app.line.sdk_dispatch.MessageEvent", FakeMessageEvent):
        dispatched = dispatcher.dispatch(event, payload)

    assert dispatched is True
    assert webhook_handler._WebhookHandler__get_handler_key.call_args_list == [
        ((FakeMessageEvent, object),),
        ((FakeMessageEvent,),),
    ]
    webhook_handler._WebhookHandler__invoke_func.assert_called_once_with(
        registered_handler, event, payload
    )


def test_dispatch_falls_back_to_default_registration() -> None:
    """Test dispatch invokes the SDK default when no event registration exists."""
    event = object()
    payload = Mock(events=[event])
    default_handler = object()
    webhook_handler = Mock()
    webhook_handler._handlers = {}
    webhook_handler._default = default_handler
    webhook_handler._WebhookHandler__get_handler_key.return_value = "missing-key"
    dispatcher = LineSdkWebhookDispatcher(webhook_handler)

    dispatched = dispatcher.dispatch(event, payload)

    assert dispatched is True
    webhook_handler._WebhookHandler__invoke_func.assert_called_once_with(
        default_handler, event, payload
    )


def test_sdk_private_dispatch_surface_still_exists() -> None:
    """Fail clearly when an SDK upgrade changes the private dispatch surface."""
    webhook_handler = WebhookHandler("contract-test-secret")

    assert hasattr(webhook_handler, "_WebhookHandler__get_handler_key")
    assert hasattr(webhook_handler, "_WebhookHandler__invoke_func")
    assert hasattr(webhook_handler, "_handlers")
    assert hasattr(webhook_handler, "_default")
    assert "as_payload" in inspect.signature(webhook_handler.parser.parse).parameters


def test_dispatch_reports_missing_registration() -> None:
    """Test dispatch reports false when neither a specific nor default handler exists."""
    event = object()
    payload = Mock(events=[event])
    webhook_handler = Mock()
    webhook_handler._handlers = {}
    webhook_handler._default = None
    webhook_handler._WebhookHandler__get_handler_key.return_value = "missing-key"
    dispatcher = LineSdkWebhookDispatcher(webhook_handler)

    dispatched = dispatcher.dispatch(event, payload)

    assert dispatched is False
    webhook_handler._WebhookHandler__invoke_func.assert_not_called()
