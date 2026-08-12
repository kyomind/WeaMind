"""Contain LINE SDK webhook parsing and dispatch implementation details."""

from typing import Protocol, cast

from linebot.v3 import WebhookHandler
from linebot.v3.webhooks import MessageEvent


class ParsedWebhookPayload(Protocol):
    """Describe the parsed payload data needed by application orchestration."""

    events: list[object]
    destination: str | None


class LineSdkWebhookDispatcher:
    """Hide volatile LINE SDK webhook implementation behind a small interface."""

    def __init__(self, webhook_handler: WebhookHandler) -> None:
        """Initialize the dispatcher with the configured LINE SDK handler."""
        self._webhook_handler = webhook_handler

    def parse(self, body_text: str, signature: str) -> ParsedWebhookPayload:
        """Validate and parse a raw webhook request into its event payload."""
        return cast(
            ParsedWebhookPayload,
            self._webhook_handler.parser.parse(body_text, signature, as_payload=True),
        )

    def dispatch(self, event: object, payload: ParsedWebhookPayload) -> bool:
        """Invoke the registered handler and report whether one was available."""
        handler = self._resolve_handler(event)
        if handler is None:
            return False
        self._webhook_handler._WebhookHandler__invoke_func(handler, event, payload)  # type: ignore[attr-defined]
        return True

    def _resolve_handler(self, event: object) -> object | None:
        """Resolve a message-specific, event-specific, or default SDK handler."""
        handler = None

        if isinstance(event, MessageEvent):
            message = getattr(event, "message", None)
            handler_key = self._webhook_handler._WebhookHandler__get_handler_key(  # type: ignore[attr-defined]
                event.__class__,
                message.__class__,
            )
            handler = self._webhook_handler._handlers.get(handler_key)

        if handler is None:
            handler_key = self._webhook_handler._WebhookHandler__get_handler_key(  # type: ignore[attr-defined]
                event.__class__
            )
            handler = self._webhook_handler._handlers.get(handler_key)

        if handler is None:
            return self._webhook_handler._default
        return handler
