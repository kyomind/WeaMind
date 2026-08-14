"""Provide a stable recipe-based boundary for replying through LINE Messaging API."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol
from urllib.parse import urlsplit

from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    LocationAction,
    MessageAction,
    MessagingApi,
    QuickReply,
    QuickReplyItem,
    ReplyMessageRequest,
    TextMessage,
    URIAction,
)
from linebot.v3.messaging.exceptions import ApiException
from urllib3.exceptions import HTTPError

logger = logging.getLogger(__name__)

_MAX_QUICK_REPLY_ITEMS = 13


def _validate_text(value: str, field_name: str) -> None:
    """Validate a required recipe string."""
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _validate_choices(choices: tuple[object, ...]) -> None:
    """Validate the number of choices supported by LINE Quick Reply."""
    if not choices:
        raise ValueError("choices must not be empty")
    if len(choices) > _MAX_QUICK_REPLY_ITEMS:
        raise ValueError(f"choices must contain at most {_MAX_QUICK_REPLY_ITEMS} items")


@dataclass(frozen=True, slots=True)
class MessageChoice:
    """Represent an immutable message Quick Reply choice."""

    label: str
    text: str

    def __post_init__(self) -> None:
        """Validate the message choice."""
        _validate_text(self.label, "label")
        _validate_text(self.text, "text")


@dataclass(frozen=True, slots=True)
class UriChoice:
    """Represent an immutable URI Quick Reply choice."""

    label: str
    uri: str

    def __post_init__(self) -> None:
        """Validate the URI choice."""
        _validate_text(self.label, "label")
        _validate_text(self.uri, "uri")
        parsed_uri = urlsplit(self.uri)
        if parsed_uri.scheme not in {"http", "https"} or not parsed_uri.netloc:
            raise ValueError("uri must be an absolute HTTP(S) URL")


@dataclass(frozen=True, slots=True)
class TextRecipe:
    """Describe a plain text reply without exposing LINE SDK models."""

    text: str

    def __post_init__(self) -> None:
        """Validate the text recipe."""
        _validate_text(self.text, "text")


@dataclass(frozen=True, slots=True)
class MessageChoicesRecipe:
    """Describe a text reply with message Quick Reply choices."""

    text: str
    choices: tuple[MessageChoice, ...]

    def __post_init__(self) -> None:
        """Validate the message choices recipe."""
        _validate_text(self.text, "text")
        _validate_choices(self.choices)


@dataclass(frozen=True, slots=True)
class LocationRequestRecipe:
    """Describe a text reply that asks the user to share a location."""

    text: str
    label: str

    def __post_init__(self) -> None:
        """Validate the location request recipe."""
        _validate_text(self.text, "text")
        _validate_text(self.label, "label")


@dataclass(frozen=True, slots=True)
class UriChoicesRecipe:
    """Describe a text reply with URI Quick Reply choices."""

    text: str
    choices: tuple[UriChoice, ...]

    def __post_init__(self) -> None:
        """Validate the URI choices recipe."""
        _validate_text(self.text, "text")
        _validate_choices(self.choices)


type ReplyRecipe = TextRecipe | MessageChoicesRecipe | LocationRequestRecipe | UriChoicesRecipe


class SendErrorCategory(StrEnum):
    """Classify reply failures without leaking LINE SDK exceptions."""

    INVALID_REQUEST = "invalid_request"
    AUTHENTICATION = "authentication"
    RATE_LIMITED = "rate_limited"
    LINE_API = "line_api"
    TRANSPORT = "transport"
    INTERNAL = "internal"


@dataclass(frozen=True, slots=True)
class SendResult:
    """Expose the explicit outcome of one reply attempt."""

    success: bool
    error_category: SendErrorCategory | None = None

    def __post_init__(self) -> None:
        """Ensure success and error fields describe a coherent outcome."""
        if self.success == (self.error_category is not None):
            raise ValueError("success must be true exactly when error_category is absent")

    @classmethod
    def sent(cls) -> SendResult:
        """Create a successful send result."""
        return cls(success=True)

    @classmethod
    def failed(cls, category: SendErrorCategory) -> SendResult:
        """Create a failed send result with a stable category."""
        return cls(success=False, error_category=category)


class ReplyMessenger(Protocol):
    """Define the application seam for one LINE reply attempt."""

    def reply(self, reply_token: str | None, recipe: ReplyRecipe) -> SendResult:
        """Send one recipe using the supplied reply token."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class SentReply:
    """Record one reply accepted by the in-memory adapter."""

    reply_token: str
    recipe: ReplyRecipe


@dataclass(slots=True)
class InMemoryReplyMessenger:
    """Record recipes for tests without constructing LINE SDK object graphs."""

    failure_category: SendErrorCategory | None = None
    sent_replies: list[SentReply] = field(default_factory=list, init=False)

    def reply(self, reply_token: str | None, recipe: ReplyRecipe) -> SendResult:
        """Record a valid reply or return the configured failure."""
        if not reply_token:
            return SendResult.failed(SendErrorCategory.INVALID_REQUEST)
        if self.failure_category is not None:
            return SendResult.failed(self.failure_category)
        self.sent_replies.append(SentReply(reply_token=reply_token, recipe=recipe))
        return SendResult.sent()


class LineSdkReplyMessenger:
    """Translate recipes and contain the complete LINE SDK reply lifecycle."""

    def __init__(self, access_token: str) -> None:
        """Create an adapter configured with a LINE channel access token."""
        _validate_text(access_token, "access_token")
        self._configuration = Configuration(access_token=access_token)

    def reply(self, reply_token: str | None, recipe: ReplyRecipe) -> SendResult:
        """Translate and send one recipe without leaking SDK exceptions."""
        if not reply_token:
            logger.warning("Cannot send LINE reply without a reply token")
            return SendResult.failed(SendErrorCategory.INVALID_REQUEST)

        try:
            request = self._build_request(reply_token, recipe)
            # A fresh SDK client is intentionally scoped to each reply; reply tokens
            # are single-use, so this adapter never retries a failed request.
            with ApiClient(self._configuration) as api_client:
                MessagingApi(api_client).reply_message(request)
        except ApiException as exc:
            category = self._classify_api_error(exc.status)
            logger.warning(
                "LINE reply rejected by API",
                extra={"category": category.value, "status_code": exc.status},
            )
            return SendResult.failed(category)
        except (HTTPError, OSError):
            logger.exception("LINE reply failed during transport")
            return SendResult.failed(SendErrorCategory.TRANSPORT)
        except Exception:
            logger.exception("Unexpected failure while sending LINE reply")
            return SendResult.failed(SendErrorCategory.INTERNAL)

        logger.info("LINE reply sent")
        return SendResult.sent()

    @staticmethod
    def _classify_api_error(status_code: int | None) -> SendErrorCategory:
        """Map reliably identifiable LINE HTTP statuses to stable categories."""
        if status_code == 400:
            return SendErrorCategory.INVALID_REQUEST
        if status_code in {401, 403}:
            return SendErrorCategory.AUTHENTICATION
        if status_code == 429:
            return SendErrorCategory.RATE_LIMITED
        return SendErrorCategory.LINE_API

    @staticmethod
    def _build_request(reply_token: str, recipe: ReplyRecipe) -> ReplyMessageRequest:
        """Translate an application recipe into LINE SDK message models."""
        quick_reply: QuickReply | None = None

        if isinstance(recipe, MessageChoicesRecipe):
            quick_reply = QuickReply(
                items=[
                    QuickReplyItem(
                        type="action",
                        imageUrl=None,
                        action=MessageAction(label=choice.label, text=choice.text),
                    )
                    for choice in recipe.choices
                ]
            )
        elif isinstance(recipe, LocationRequestRecipe):
            quick_reply = QuickReply(
                items=[
                    QuickReplyItem(
                        type="action",
                        imageUrl=None,
                        action=LocationAction(label=recipe.label),
                    )
                ]
            )
        elif isinstance(recipe, UriChoicesRecipe):
            quick_reply = QuickReply(
                items=[
                    QuickReplyItem(
                        type="action",
                        imageUrl=None,
                        action=URIAction(label=choice.label, uri=choice.uri, altUri=None),
                    )
                    for choice in recipe.choices
                ]
            )

        return ReplyMessageRequest(
            replyToken=reply_token,
            messages=[TextMessage(text=recipe.text, quickReply=quick_reply, quoteToken=None)],
            notificationDisabled=False,
        )
