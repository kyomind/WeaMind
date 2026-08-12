"""Test recipe validation and the isolated LINE SDK messaging adapter."""

import ast
from collections.abc import Callable
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from linebot.v3.messaging import (
    LocationAction,
    MessageAction,
    ReplyMessageRequest,
    TextMessage,
    URIAction,
)
from linebot.v3.messaging.exceptions import ApiException
from urllib3.exceptions import HTTPError

from app.line.messaging import (
    InMemoryReplyMessenger,
    LineSdkReplyMessenger,
    LocationRequestRecipe,
    MessageChoice,
    MessageChoicesRecipe,
    SendErrorCategory,
    SendResult,
    SentReply,
    TextRecipe,
    UriChoice,
    UriChoicesRecipe,
)


class TestRecipeValidation:
    """Test recipe value-object validation."""

    @pytest.mark.parametrize(
        "factory",
        [
            lambda: TextRecipe(""),
            lambda: TextRecipe("   "),
            lambda: MessageChoice("", "臺北市"),
            lambda: MessageChoice("臺北", " "),
            lambda: LocationRequestRecipe("請選地點", ""),
            lambda: MessageChoicesRecipe("請選地點", ()),
            lambda: UriChoicesRecipe("請選連結", ()),
            lambda: MessageChoicesRecipe(
                "請選地點",
                tuple(MessageChoice(str(index), str(index)) for index in range(14)),
            ),
            lambda: UriChoice("文件", "/relative/path"),
            lambda: UriChoice("文件", "ftp://example.com/file"),
            lambda: UriChoice("文件", "https:///missing-host"),
        ],
    )
    def test_recipe_rejects_invalid_values(self, factory: Callable[[], object]) -> None:
        """Reject empty, excessive, or structurally invalid recipe values."""
        with pytest.raises(ValueError):
            factory()

    def test_recipe_accepts_maximum_quick_reply_choices(self) -> None:
        """Accept LINE's maximum of thirteen Quick Reply choices."""
        choices = tuple(MessageChoice(label=str(index), text=str(index)) for index in range(13))

        recipe = MessageChoicesRecipe("請選擇", choices)

        assert recipe.choices == choices

    @pytest.mark.parametrize("access_token", ["", " "])
    def test_adapter_rejects_empty_access_token(self, access_token: str) -> None:
        """Reject an empty channel access token during adapter construction."""
        with pytest.raises(ValueError):
            LineSdkReplyMessenger(access_token)


class TestSendResult:
    """Test explicit send outcome invariants."""

    def test_sent_result(self) -> None:
        """Create a successful result without an error category."""
        assert SendResult.sent() == SendResult(success=True)

    def test_failed_result(self) -> None:
        """Create a failed result with the supplied stable category."""
        assert SendResult.failed(SendErrorCategory.TRANSPORT) == SendResult(
            success=False,
            error_category=SendErrorCategory.TRANSPORT,
        )

    @pytest.mark.parametrize(
        ("success", "category"),
        [
            (True, SendErrorCategory.INTERNAL),
            (False, None),
        ],
    )
    def test_result_rejects_incoherent_state(
        self, success: bool, category: SendErrorCategory | None
    ) -> None:
        """Reject outcomes whose success flag conflicts with their error field."""
        with pytest.raises(ValueError):
            SendResult(success=success, error_category=category)


class TestInMemoryReplyMessenger:
    """Test the deterministic in-memory adapter."""

    def test_reply_records_recipe(self) -> None:
        """Record a valid reply token and immutable recipe."""
        messenger = InMemoryReplyMessenger()
        recipe = TextRecipe("Hello")

        send_result = messenger.reply("token", recipe)

        assert send_result == SendResult.sent()
        assert messenger.sent_replies == [SentReply("token", recipe)]

    def test_reply_rejects_missing_token(self) -> None:
        """Return invalid request without recording a missing reply token."""
        messenger = InMemoryReplyMessenger()

        send_result = messenger.reply(None, TextRecipe("Hello"))

        assert send_result == SendResult.failed(SendErrorCategory.INVALID_REQUEST)
        assert messenger.sent_replies == []

    def test_reply_returns_configured_failure(self) -> None:
        """Return a configured failure without recording the recipe."""
        messenger = InMemoryReplyMessenger(SendErrorCategory.RATE_LIMITED)

        send_result = messenger.reply("token", TextRecipe("Hello"))

        assert send_result == SendResult.failed(SendErrorCategory.RATE_LIMITED)
        assert messenger.sent_replies == []


class TestRecipeTranslation:
    """Test translation from application recipes to LINE SDK requests."""

    def test_text_recipe_translation(self) -> None:
        """Translate plain text without adding Quick Reply data."""
        request = LineSdkReplyMessenger._build_request("token", TextRecipe("Hello"))

        assert isinstance(request, ReplyMessageRequest)
        assert request.reply_token == "token"
        assert request.notification_disabled is False
        assert len(request.messages) == 1
        message = request.messages[0]
        assert isinstance(message, TextMessage)
        assert message.text == "Hello"
        assert message.quick_reply is None

    def test_message_choices_translation(self) -> None:
        """Translate message choices while preserving labels and sent text."""
        recipe = MessageChoicesRecipe(
            "請選擇",
            (
                MessageChoice("臺北", "臺北市"),
                MessageChoice("新北", "新北市"),
            ),
        )

        request = LineSdkReplyMessenger._build_request("token", recipe)

        actions = [item.action for item in request.messages[0].quick_reply.items]
        assert all(isinstance(action, MessageAction) for action in actions)
        assert [(action.label, action.text) for action in actions] == [
            ("臺北", "臺北市"),
            ("新北", "新北市"),
        ]

    def test_location_request_translation(self) -> None:
        """Translate a location recipe into one location action."""
        recipe = LocationRequestRecipe("請分享地點", "開啟地圖")

        request = LineSdkReplyMessenger._build_request("token", recipe)

        actions = [item.action for item in request.messages[0].quick_reply.items]
        assert len(actions) == 1
        assert isinstance(actions[0], LocationAction)
        assert actions[0].label == "開啟地圖"

    def test_uri_choices_translation(self) -> None:
        """Translate URI choices while preserving absolute URLs."""
        recipe = UriChoicesRecipe(
            "請選擇",
            (
                UriChoice("文件", "https://example.com/docs"),
                UriChoice("首頁", "http://example.com"),
            ),
        )

        request = LineSdkReplyMessenger._build_request("token", recipe)

        actions = [item.action for item in request.messages[0].quick_reply.items]
        assert all(isinstance(action, URIAction) for action in actions)
        assert [(action.label, action.uri) for action in actions] == [
            ("文件", "https://example.com/docs"),
            ("首頁", "http://example.com"),
        ]


class TestLineSdkReplyMessenger:
    """Test SDK lifecycle ownership and stable error containment."""

    def test_reply_owns_client_lifecycle(self) -> None:
        """Build, send, and close one SDK client for one reply attempt."""
        adapter = LineSdkReplyMessenger("access-token")
        sdk_client = Mock(name="sdk_client")

        with (
            patch("app.line.messaging.ApiClient") as api_client_class,
            patch("app.line.messaging.MessagingApi") as messaging_api_class,
        ):
            api_client_class.return_value.__enter__.return_value = sdk_client
            send_result = adapter.reply("reply-token", TextRecipe("Hello"))

        assert send_result == SendResult.sent()
        api_client_class.assert_called_once_with(adapter._configuration)
        api_client_class.return_value.__enter__.assert_called_once_with()
        api_client_class.return_value.__exit__.assert_called_once()
        messaging_api_class.assert_called_once_with(sdk_client)
        request = messaging_api_class.return_value.reply_message.call_args.args[0]
        assert request.reply_token == "reply-token"
        assert request.messages[0].text == "Hello"
        messaging_api_class.return_value.reply_message.assert_called_once_with(request)

    def test_reply_rejects_missing_token_before_sdk_lifecycle(self) -> None:
        """Classify a missing token without opening an SDK client."""
        adapter = LineSdkReplyMessenger("access-token")

        with patch("app.line.messaging.ApiClient") as api_client_class:
            send_result = adapter.reply(None, TextRecipe("Hello"))

        assert send_result == SendResult.failed(SendErrorCategory.INVALID_REQUEST)
        api_client_class.assert_not_called()

    @pytest.mark.parametrize(
        ("status_code", "expected_category"),
        [
            (400, SendErrorCategory.INVALID_REQUEST),
            (401, SendErrorCategory.AUTHENTICATION),
            (403, SendErrorCategory.AUTHENTICATION),
            (429, SendErrorCategory.RATE_LIMITED),
            (404, SendErrorCategory.LINE_API),
            (500, SendErrorCategory.LINE_API),
            (None, SendErrorCategory.LINE_API),
        ],
    )
    def test_reply_classifies_api_exception_without_retry(
        self,
        status_code: int | None,
        expected_category: SendErrorCategory,
    ) -> None:
        """Map SDK API failures and make exactly one single-use-token attempt."""
        adapter = LineSdkReplyMessenger("access-token")

        with (
            patch("app.line.messaging.ApiClient") as api_client_class,
            patch("app.line.messaging.MessagingApi") as messaging_api_class,
        ):
            messaging_api_class.return_value.reply_message.side_effect = ApiException(
                status=status_code,
                reason="rejected",
            )
            send_result = adapter.reply("reply-token", TextRecipe("Hello"))

        assert send_result == SendResult.failed(expected_category)
        api_client_class.assert_called_once()
        messaging_api_class.return_value.reply_message.assert_called_once()

    @pytest.mark.parametrize(
        "raw_exception",
        [HTTPError("connection failed"), OSError("socket failed")],
    )
    def test_reply_contains_transport_exception(self, raw_exception: Exception) -> None:
        """Contain transport exceptions behind the stable transport category."""
        adapter = LineSdkReplyMessenger("access-token")

        with (
            patch("app.line.messaging.ApiClient"),
            patch("app.line.messaging.MessagingApi") as messaging_api_class,
        ):
            messaging_api_class.return_value.reply_message.side_effect = raw_exception
            send_result = adapter.reply("reply-token", TextRecipe("Hello"))

        assert send_result == SendResult.failed(SendErrorCategory.TRANSPORT)
        messaging_api_class.return_value.reply_message.assert_called_once()

    def test_reply_contains_unexpected_exception(self) -> None:
        """Contain arbitrary raw exceptions behind the stable internal category."""
        adapter = LineSdkReplyMessenger("access-token")

        with (
            patch("app.line.messaging.ApiClient"),
            patch("app.line.messaging.MessagingApi") as messaging_api_class,
        ):
            messaging_api_class.return_value.reply_message.side_effect = RuntimeError(
                "unexpected raw failure"
            )
            send_result = adapter.reply("reply-token", TextRecipe("Hello"))

        assert send_result == SendResult.failed(SendErrorCategory.INTERNAL)
        messaging_api_class.return_value.reply_message.assert_called_once()


def test_messaging_sdk_symbols_are_isolated_to_adapter_boundary() -> None:
    """Forbid LINE messaging SDK imports and symbols outside the adapter boundary."""
    allowed_paths = {
        Path("app/line/messaging.py"),
        Path("tests/line/test_messaging.py"),
    }
    forbidden_names = {
        "ApiClient",
        "ApiException",
        "Configuration",
        "LocationAction",
        "MessageAction",
        "MessagingApi",
        "QuickReply",
        "QuickReplyItem",
        "ReplyMessageRequest",
        "TextMessage",
        "URIAction",
    }
    violations: list[str] = []

    source_roots = (Path("app"), Path("tests"), Path("migrations"), Path("scripts"))
    python_paths = sorted(path for root in source_roots for path in root.rglob("*.py"))
    for path in python_paths:
        if path in allowed_paths:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            imports_messaging_sdk = (
                isinstance(node, ast.ImportFrom)
                and (node.module or "").startswith("linebot.v3.messaging")
            ) or (
                isinstance(node, ast.Import)
                and any(alias.name.startswith("linebot.v3.messaging") for alias in node.names)
            )
            if imports_messaging_sdk:
                violations.append(
                    f"{path}:{getattr(node, 'lineno', 0)}: forbidden messaging SDK import"
                )
            elif isinstance(node, ast.Name) and node.id in forbidden_names:
                violations.append(f"{path}:{node.lineno}: forbidden messaging SDK symbol {node.id}")

    assert violations == []
