"""Define event outcomes independently of SDK callbacks and metrics."""

from enum import StrEnum

from .messaging import SendResult


class EventOutcome(StrEnum):
    """Separate completed business work, failures, and intentionally ignored events."""

    SUCCESS = "success"
    HANDLER_ERROR = "handler_error"
    REPLY_ERROR = "reply_error"
    SKIPPED = "skipped"

    @classmethod
    def from_reply(cls, result: SendResult) -> "EventOutcome":
        """Require a successful reply for a reply-producing event to succeed."""
        return cls.SUCCESS if result.success else cls.REPLY_ERROR
