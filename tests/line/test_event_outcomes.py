"""Verify business outcomes through the real router, SDK parser, and callbacks."""

import json
from collections.abc import Callable
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.line.messaging import InMemoryReplyMessenger, SendErrorCategory, TextRecipe


@pytest.mark.parametrize(
    "event_kind,failure,expected_error",
    [
        ("text", None, None),
        ("location", None, None),
        ("postback", None, None),
        ("follow", None, None),
        ("unfollow", None, None),
        ("text", "reply", "reply_error"),
        ("location", "reply", "reply_error"),
        ("postback", "reply", "reply_error"),
        ("follow", "reply", "reply_error"),
        ("text", "business", "handler_error"),
        ("location", "business", "handler_error"),
        ("postback", "business", "handler_error"),
        ("follow", "business", "handler_error"),
        ("unfollow", "business", "handler_error"),
        ("unknown", None, "skipped"),
    ],
)
def test_webhook_records_business_outcome(
    client: TestClient,
    generate_line_signature: Callable[[bytes], str],
    event_kind: str,
    failure: str | None,
    expected_error: str | None,
) -> None:
    """Count each event once and retain business failure after a successful error reply."""
    event: dict = {
        "type": event_kind,
        "mode": "active",
        "timestamp": 1,
        "webhookEventId": "outcome-test",
        "deliveryContext": {"isRedelivery": False},
        "source": {"type": "user", "userId": "Utest"},
        "replyToken": "reply-token",
    }
    if event_kind in {"text", "location"}:
        event["type"] = "message"
        event["message"] = (
            {"type": "text", "id": "1", "text": "臺北市中正區", "quoteToken": "quote"}
            if event_kind == "text"
            else {"type": "location", "id": "1", "latitude": 25.0, "longitude": 121.0}
        )
    elif event_kind == "postback":
        event["postback"] = {"data": "action=weather&type=home"}
    elif event_kind == "follow":
        event["follow"] = {"isUnblocked": False}
    body = json.dumps({"destination": "Ubot", "events": [event]}).encode()
    messenger = InMemoryReplyMessenger(
        failure_category=SendErrorCategory.TRANSPORT if failure == "reply" else None
    )
    business_error = RuntimeError("injected business failure") if failure == "business" else None
    with (
        patch("app.line.service.production_reply_messenger", messenger),
        patch("app.line.service.query_text", side_effect=business_error),
        patch("app.line.service.query_shared_location", side_effect=business_error),
        patch("app.line.service.build_weather_reply", return_value=TextRecipe("weather")),
        patch("app.line.postback.query_preset", side_effect=business_error),
        patch("app.line.postback.build_weather_reply", return_value=TextRecipe("weather")),
        patch("app.line.service.SessionLocal", side_effect=business_error),
        patch("app.line.service.create_user_if_not_exists"),
        patch("app.line.service.deactivate_user"),
        patch("app.line.service.processing_lock_service.try_acquire_lock", return_value=True),
        patch("app.line.service.line_metrics.record_webhook_success") as success,
        patch("app.line.service.line_metrics.record_webhook_error") as error,
        patch("app.line.service.line_metrics.record_webhook_duration") as duration,
    ):
        response = client.post(
            "/line/webhook",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Line-Signature": generate_line_signature(body),
            },
        )
    assert response.status_code == 200
    label = f"message_{event_kind}" if event_kind in {"text", "location"} else event_kind
    if expected_error == "skipped":
        success.assert_not_called()
        error.assert_not_called()
    elif expected_error:
        success.assert_not_called()
        error.assert_called_once_with([label], expected_error)
    else:
        success.assert_called_once_with([label])
        error.assert_not_called()
    assert duration.call_count == 1
    if failure == "business" and event_kind in {"text", "location", "postback"}:
        expected_text = (
            "查詢時發生錯誤，請稍後再試。"
            if event_kind == "postback"
            else "系統暫時有點忙，請稍後再試一次。"
        )
        assert messenger.sent_replies[0].recipe == TextRecipe(expected_text)
