"""
Verify corrected webhook outcomes and remaining delivery limits locally.

Run from the repository root with uv run python docs/experiments/webhook_state_probe.py.
The formal regression contract is covered by tests/line/test_event_outcomes.py.
"""

# This diagnostic uses assertions and synthetic credentials, never service secrets.
# ruff: noqa: S101, S106

import base64
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Override service credentials before importing application configuration.
os.environ.update(
    DATABASE_URL="sqlite+pysqlite:///:memory:",
    POSTGRES_USER="test",
    POSTGRES_PASSWORD="test",  # pragma: allowlist secret -- synthetic local test credential
    POSTGRES_HOST="localhost",
    POSTGRES_DB="test",
    LINE_CHANNEL_SECRET="state-probe",  # pragma: allowlist secret -- synthetic signature key
    LINE_CHANNEL_ACCESS_TOKEN="test",
    REDIS_URL="",
)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.line.messaging import SendErrorCategory, SendResult, TextRecipe  # noqa: E402
from app.line.router import router  # noqa: E402


def send_events(client: TestClient, events: list[dict]) -> int:
    """Submit signed synthetic events through the real router and SDK parser."""
    body = json.dumps({"destination": "Ubot", "events": events}).encode()
    signature = base64.b64encode(hmac.new(b"state-probe", body, hashlib.sha256).digest())
    return client.post(
        "/line/webhook",
        content=body,
        headers={"Content-Type": "application/json", "X-Line-Signature": signature.decode()},
    ).status_code


def text_event(event_id: str) -> dict:
    """Build a text event with a stable identity for replay observations."""
    return {
        "type": "message",
        "timestamp": 1,
        "mode": "active",
        "webhookEventId": event_id,
        "deliveryContext": {"isRedelivery": False},
        "source": {"type": "user", "userId": "Utest"},
        "replyToken": event_id,
        "message": {"id": event_id, "type": "text", "text": "臺北市中正區", "quoteToken": "quote"},
    }


def main() -> None:
    """Print deterministic observations using injected database and reply failures."""
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        with (
            patch("app.line.service.query_text"),
            patch("app.line.service.build_weather_reply", return_value=TextRecipe("test")),
            patch("app.line.service.production_reply_messenger") as messenger,
            patch("app.line.service.line_metrics.record_webhook_success") as success,
            patch("app.line.service.line_metrics.record_webhook_error") as error,
        ):
            messenger.reply.return_value = SendResult.failed(SendErrorCategory.INVALID_REQUEST)
            assert send_events(client, [text_event("rejected")]) == 200
            assert success.call_count == 0 and error.call_count == 1
            print("reply_rejected: success_events=0, error_events=1")

        with (
            patch("app.line.service.query_text") as query,
            patch("app.line.service.build_weather_reply", return_value=TextRecipe("test")),
            patch("app.line.service.production_reply_messenger") as messenger,
            patch("app.line.service.line_metrics.record_webhook_error") as error,
        ):
            messenger.reply.side_effect = RuntimeError("injected reply failure")
            status = send_events(client, [text_event("first"), text_event("second")])
            assert status == 200 and query.call_count == 1 and error.call_count == 1
            print("batch_failure: HTTP=200, query_calls=1/2, error_events=1")

        with (
            patch("app.line.service.SessionLocal", side_effect=RuntimeError("injected DB failure")),
            patch("app.line.service.line_metrics.record_webhook_success") as success,
            patch("app.line.service.line_metrics.record_webhook_error") as error,
        ):
            event = text_event("follow")
            event.pop("message")
            event["type"] = "follow"
            event["follow"] = {"isUnblocked": False}
            status = send_events(client, [event])
            assert status == 200 and success.call_count == 0 and error.call_count == 1
            print("follow_db_failure: HTTP=200, success_events=0, error_events=1")

        with (
            patch("app.line.service.query_text") as query,
            patch("app.line.service.build_weather_reply", return_value=TextRecipe("test")),
            patch("app.line.service.production_reply_messenger", Mock()) as messenger,
        ):
            messenger.reply.return_value = SendResult.sent()
            event = text_event("replayed")
            assert send_events(client, [event]) == 200
            event["deliveryContext"]["isRedelivery"] = True
            assert send_events(client, [event]) == 200
            assert query.call_count == 2 and messenger.reply.call_count == 2
            print("same_event_replay: query_calls=2, reply_attempts=2")


if __name__ == "__main__":
    main()
