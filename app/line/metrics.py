"""Prometheus metrics for the LINE webhook processing path."""

import json
from collections.abc import Iterable
from typing import Any

from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

# This W7 MVP uses the default in-process registry to keep instrumentation minimal.
# Cross-worker aggregation can be added later if the deployment moves to
# Prometheus multiprocess mode.
line_webhook_events_total = Counter(
    "line_webhook_events_total",
    "Total number of LINE webhook events received.",
    labelnames=("event_type",),
)

line_webhook_events_success_total = Counter(
    "line_webhook_events_success_total",
    "Total number of LINE webhook events processed successfully.",
    labelnames=("event_type",),
)

line_webhook_events_error_total = Counter(
    "line_webhook_events_error_total",
    "Total number of LINE webhook events that failed during processing.",
    labelnames=("event_type", "error_type"),
)

line_webhook_event_duration_seconds = Histogram(
    "line_webhook_event_duration_seconds",
    "Duration of LINE webhook event processing in seconds.",
    labelnames=("event_type",),
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)


def metrics_response() -> Response:
    """
    Render the current Prometheus registry as an HTTP response.

    Returns:
        FastAPI response containing the Prometheus text exposition format.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def extract_event_types_from_body(body_text: str) -> list[str]:
    """
    Extract event_type labels from a raw webhook request body.

    This helper is used at the router boundary so the received counter can be
    updated before background processing starts. If the payload cannot be parsed
    or does not contain a usable events list, the function falls back to
    ``unknown`` to keep the metrics pipeline stable.

    Args:
        body_text: Raw webhook request body decoded as UTF-8 text.

    Returns:
        A list of normalized event_type labels for every parsable event in the
        payload, or ``["unknown"]`` when classification is not possible.
    """
    try:
        payload = json.loads(body_text)
    except json.JSONDecodeError:
        return ["unknown"]

    events = payload.get("events")
    if not isinstance(events, list) or not events:
        return ["unknown"]

    event_types = [normalize_event_type(event) for event in events if isinstance(event, dict)]
    return event_types or ["unknown"]


def normalize_event_type(event: dict[str, Any]) -> str:
    """
    Map a raw webhook event payload to the MVP event_type label set.

    Args:
        event: A single event object parsed from the webhook JSON payload.

    Returns:
        The normalized event_type label used by the Prometheus counters and
        histogram.
    """
    raw_event_type = event.get("type")

    if raw_event_type == "message":
        message = event.get("message")
        if not isinstance(message, dict):
            return "default"

        message_type = message.get("type")
        if message_type == "text":
            return "message_text"
        if message_type == "location":
            return "message_location"
        return "default"

    if raw_event_type in {"follow", "unfollow", "postback"}:
        return str(raw_event_type)
    if raw_event_type is None:
        return "unknown"
    return "default"


def normalize_runtime_event_type(event: object) -> str:
    """
    Map a parsed LINE SDK event object to the MVP event_type label set.

    This variant is used after the LINE SDK has already parsed the webhook into
    runtime objects, so it reads attributes instead of raw JSON keys.

    Args:
        event: Parsed LINE SDK event object.

    Returns:
        The normalized event_type label used by event-level metrics.
    """
    raw_event_type = getattr(event, "type", None)

    if raw_event_type == "message":
        message = getattr(event, "message", None)
        message_type = getattr(message, "type", None)
        if message_type == "text":
            return "message_text"
        if message_type == "location":
            return "message_location"
        return "default"

    if raw_event_type in {"follow", "unfollow", "postback"}:
        return str(raw_event_type)
    if raw_event_type is None:
        return "unknown"
    return "default"


def record_webhook_received(event_types: Iterable[str]) -> None:
    """
    Increment received counters for the classified events in one webhook request.

    Args:
        event_types: Normalized event_type labels extracted from the request
            payload.
    """
    for event_type in event_types:
        line_webhook_events_total.labels(event_type=event_type).inc()


def record_webhook_success(event_types: Iterable[str]) -> None:
    """
    Increment success counters for completed webhook events.

    Args:
        event_types: Normalized event_type labels that finished successfully.
    """
    for event_type in event_types:
        line_webhook_events_success_total.labels(event_type=event_type).inc()


def record_webhook_error(event_types: Iterable[str], error_type: str) -> None:
    """
    Increment error counters for failed webhook events.

    Args:
        event_types: Normalized event_type labels that failed.
        error_type: High-level error classification used for metric labels.
    """
    for event_type in event_types:
        line_webhook_events_error_total.labels(
            event_type=event_type,
            error_type=error_type,
        ).inc()


def record_webhook_duration(event_types: Iterable[str], duration_seconds: float) -> None:
    """
    Observe processing duration for webhook events.

    Args:
        event_types: Normalized event_type labels to associate with the
            observation.
        duration_seconds: Measured processing duration in seconds.
    """
    for event_type in event_types:
        line_webhook_event_duration_seconds.labels(event_type=event_type).observe(duration_seconds)
