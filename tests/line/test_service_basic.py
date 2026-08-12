"""Test basic LINE service handlers through the reply messenger seam."""

from collections.abc import Callable
from unittest.mock import Mock, patch

from app.core.config import settings
from app.line.messaging import (
    InMemoryReplyMessenger,
    SendResult,
    SentReply,
    TextRecipe,
)
from app.line.service import (
    _handle_follow_event_callback,
    _handle_location_message_event_callback,
    _handle_message_event_callback,
    _handle_postback_event_callback,
    handle_default_event,
    handle_follow_event,
    handle_location_message_event,
    handle_message_event,
    handle_postback_event,
    handle_unfollow_event,
    production_reply_messenger,
)
from app.line.weather_presentation import QueryKind, build_weather_reply
from app.weather.workflow import LocationData, QueryOutcome, WeatherQueryResult


class TestMessageHandler:
    """Test text message handler behavior."""

    def test_handle_message_event_non_text_message(
        self, create_mock_message_event: Callable[..., Mock]
    ) -> None:
        """Ignore message events whose content is not text."""
        event = create_mock_message_event()
        event.message = Mock()
        messenger = InMemoryReplyMessenger()

        handle_message_event(event, messenger)

        assert messenger.sent_replies == []

    def test_handle_message_event_empty_reply_token(
        self, create_mock_message_event: Callable[..., Mock]
    ) -> None:
        """Ignore text events without a reply token."""
        event = create_mock_message_event(reply_token=None)
        messenger = InMemoryReplyMessenger()

        handle_message_event(event, messenger)

        assert messenger.sent_replies == []

    def test_handle_message_event_sends_presentation_recipe(
        self, create_mock_message_event: Callable[..., Mock]
    ) -> None:
        """Send exactly the recipe the presentation module decides."""
        event = create_mock_message_event(text="永和")
        query_result = WeatherQueryResult(
            QueryOutcome.MULTIPLE_LOCATIONS,
            locations=(LocationData(1, "新北市永和區"), LocationData(2, "臺南市永和區")),
        )
        messenger = InMemoryReplyMessenger()

        with patch("app.line.service.query_text", return_value=query_result) as query:
            handle_message_event(event, messenger)

        query.assert_called_once_with("永和", "test_user_id")
        assert messenger.sent_replies == [
            SentReply("test_token", build_weather_reply(query_result, QueryKind.TEXT))
        ]

    def test_handle_message_event_contains_query_error(
        self, create_mock_message_event: Callable[..., Mock]
    ) -> None:
        """Contain query errors and send the generic text recipe."""
        event = create_mock_message_event(text="永和")
        messenger = InMemoryReplyMessenger()

        with patch("app.line.service.query_text", side_effect=RuntimeError("query error")):
            handle_message_event(event, messenger)

        assert messenger.sent_replies == [
            SentReply("test_token", TextRecipe("系統暫時有點忙，請稍後再試一次。"))
        ]

    def test_handle_default_event(self) -> None:
        """Accept an unhandled event without raising an exception."""
        handle_default_event({"type": "unknown"})


class TestLocationMessageHandler:
    """Test shared-location message handler behavior."""

    def test_handle_location_message_event_empty_reply_token(
        self, create_mock_location_message_event: Callable[..., Mock]
    ) -> None:
        """Ignore location events without a reply token."""
        event = create_mock_location_message_event(reply_token=None)
        messenger = InMemoryReplyMessenger()

        handle_location_message_event(event, messenger)

        assert messenger.sent_replies == []

    def test_handle_location_message_event_wrong_message_type(
        self, create_mock_location_message_event: Callable[..., Mock]
    ) -> None:
        """Ignore location events whose content has the wrong type."""
        event = create_mock_location_message_event()
        event.message = Mock()
        messenger = InMemoryReplyMessenger()

        handle_location_message_event(event, messenger)

        assert messenger.sent_replies == []

    def test_handle_location_message_event_success(
        self, create_mock_location_message_event: Callable[..., Mock]
    ) -> None:
        """Query shared coordinates and send the formatted text recipe."""
        event = create_mock_location_message_event(
            latitude=25.03,
            longitude=121.56,
            address="臺北市",
        )
        query_result = WeatherQueryResult(QueryOutcome.LOCATION_NOT_FOUND)
        messenger = InMemoryReplyMessenger()

        with patch("app.line.service.query_shared_location", return_value=query_result) as query:
            handle_location_message_event(event, messenger)

        query.assert_called_once_with(25.03, 121.56, "臺北市", "test_user_id")
        assert messenger.sent_replies == [
            SentReply("test_token", build_weather_reply(query_result, QueryKind.SHARED_LOCATION))
        ]

    def test_handle_location_message_event_contains_query_error(
        self, create_mock_location_message_event: Callable[..., Mock]
    ) -> None:
        """Contain location query errors and send the generic recipe."""
        event = create_mock_location_message_event()
        messenger = InMemoryReplyMessenger()

        with patch(
            "app.line.service.query_shared_location",
            side_effect=RuntimeError("query error"),
        ):
            handle_location_message_event(event, messenger)

        assert messenger.sent_replies == [
            SentReply("test_token", TextRecipe("系統暫時有點忙，請稍後再試一次。"))
        ]


class TestFollowHandler:
    """Test follow event persistence and reply behavior."""

    def test_handle_follow_event_success(
        self,
        create_mock_follow_event: Callable[..., Mock],
        mock_db_session: Mock,
    ) -> None:
        """Create the user and reply after releasing the database session."""
        event = create_mock_follow_event()
        messenger = InMemoryReplyMessenger()

        with (
            patch("app.line.service.SessionLocal") as session_factory,
            patch("app.line.service.create_user_if_not_exists") as create_user,
        ):
            session_factory.return_value.__enter__.return_value = mock_db_session

            def assert_session_closed(reply_token: str | None, recipe: TextRecipe) -> SendResult:
                """Assert the session exits before handing the recipe to the adapter."""
                session_factory.return_value.__exit__.assert_called_once()
                return messenger.reply(reply_token, recipe)

            messenger_double = Mock(reply=Mock(side_effect=assert_session_closed))
            handle_follow_event(event, messenger_double)

        create_user.assert_called_once_with(mock_db_session, "test_user_id")
        assert messenger.sent_replies == [
            SentReply(
                "test_token",
                TextRecipe("Welcome! You can now start interacting with me."),
            )
        ]

    def test_handle_follow_event_no_user_id(
        self, create_mock_follow_event: Callable[..., Mock]
    ) -> None:
        """Ignore a follow event without a user identifier."""
        event = create_mock_follow_event()
        event.source = None
        messenger = InMemoryReplyMessenger()

        handle_follow_event(event, messenger)

        assert messenger.sent_replies == []

    def test_handle_follow_event_no_reply_token(
        self,
        create_mock_follow_event: Callable[..., Mock],
        mock_db_session: Mock,
    ) -> None:
        """Persist a followed user even when no reply token is supplied."""
        event = create_mock_follow_event(reply_token=None)
        messenger = InMemoryReplyMessenger()

        with (
            patch("app.line.service.SessionLocal") as session_factory,
            patch("app.line.service.create_user_if_not_exists") as create_user,
        ):
            session_factory.return_value.__enter__.return_value = mock_db_session
            handle_follow_event(event, messenger)

        create_user.assert_called_once_with(mock_db_session, "test_user_id")
        assert messenger.sent_replies == []

    def test_handle_follow_event_contains_database_error(
        self, create_mock_follow_event: Callable[..., Mock]
    ) -> None:
        """Contain follow persistence failures without attempting a reply."""
        messenger = InMemoryReplyMessenger()

        with patch("app.line.service.SessionLocal", side_effect=RuntimeError("db error")):
            handle_follow_event(create_mock_follow_event(), messenger)

        assert messenger.sent_replies == []


class TestUnfollowHandler:
    """Test unfollow event persistence behavior."""

    def test_handle_unfollow_event_success(
        self,
        create_mock_unfollow_event: Callable[..., Mock],
        mock_db_session: Mock,
    ) -> None:
        """Deactivate the user inside a managed database session."""
        event = create_mock_unfollow_event()

        with (
            patch("app.line.service.SessionLocal") as session_factory,
            patch("app.line.service.deactivate_user", return_value=Mock()) as deactivate,
        ):
            session_factory.return_value.__enter__.return_value = mock_db_session
            handle_unfollow_event(event)

        deactivate.assert_called_once_with(mock_db_session, "test_user_id")
        session_factory.return_value.__exit__.assert_called_once()

    def test_handle_unfollow_event_no_user_id(
        self, create_mock_unfollow_event: Callable[..., Mock]
    ) -> None:
        """Ignore an unfollow event without a user identifier."""
        event = create_mock_unfollow_event()
        event.source = None

        with patch("app.line.service.deactivate_user") as deactivate:
            handle_unfollow_event(event)

        deactivate.assert_not_called()

    def test_handle_unfollow_event_unknown_user(
        self,
        create_mock_unfollow_event: Callable[..., Mock],
        mock_db_session: Mock,
    ) -> None:
        """Tolerate an unfollow event for a user that was never persisted."""
        event = create_mock_unfollow_event(user_id="ghost_user")

        with (
            patch("app.line.service.SessionLocal") as session_factory,
            patch("app.line.service.deactivate_user", return_value=None) as deactivate,
        ):
            session_factory.return_value.__enter__.return_value = mock_db_session
            handle_unfollow_event(event)

        deactivate.assert_called_once_with(mock_db_session, "ghost_user")
        session_factory.return_value.__exit__.assert_called_once()

    def test_handle_unfollow_event_contains_database_error(
        self, create_mock_unfollow_event: Callable[..., Mock]
    ) -> None:
        """Contain unfollow persistence failures."""
        with patch("app.line.service.SessionLocal", side_effect=RuntimeError("db error")):
            handle_unfollow_event(create_mock_unfollow_event())


class TestPostbackLock:
    """Test the processing-lock guard around PostBack dispatch."""

    def test_handle_postback_event_rejects_locked_user(
        self, create_mock_postback_event: Callable[..., Mock]
    ) -> None:
        """Reply with the throttling text and skip dispatch when the lock is held."""
        event = create_mock_postback_event()
        event.postback = Mock(data="action=recent_queries")
        event.source = Mock(user_id="test_user_id")
        messenger = InMemoryReplyMessenger()

        with (
            patch("app.line.service.processing_lock_service") as lock_service,
            patch.object(settings, "PROCESSING_LOCK_ENABLED", True),
            patch("app.line.service.dispatch_postback") as dispatch,
        ):
            lock_service.build_lock_key.return_value = "lock:test_user_id"
            lock_service.try_acquire_lock.return_value = False
            handle_postback_event(event, messenger)

        lock_service.try_acquire_lock.assert_called_once_with("lock:test_user_id")
        dispatch.assert_not_called()
        assert messenger.sent_replies == [
            SentReply("test_token", TextRecipe("操作太過頻繁，請放慢腳步 ☕️"))
        ]

    def test_handle_postback_event_dispatches_when_lock_acquired(
        self, create_mock_postback_event: Callable[..., Mock]
    ) -> None:
        """Dispatch the PostBack once the processing lock has been acquired."""
        event = create_mock_postback_event()
        event.postback = Mock(data="action=recent_queries")
        event.source = Mock(user_id="test_user_id")
        messenger = InMemoryReplyMessenger()

        with (
            patch("app.line.service.processing_lock_service") as lock_service,
            patch.object(settings, "PROCESSING_LOCK_ENABLED", True),
            patch("app.line.service.dispatch_postback") as dispatch,
        ):
            lock_service.build_lock_key.return_value = "lock:test_user_id"
            lock_service.try_acquire_lock.return_value = True
            handle_postback_event(event, messenger)

        dispatch.assert_called_once_with(
            event, "test_user_id", {"action": "recent_queries"}, messenger
        )
        assert messenger.sent_replies == []

    def test_handle_postback_event_skips_lock_when_disabled(
        self, create_mock_postback_event: Callable[..., Mock]
    ) -> None:
        """Dispatch without acquiring a lock when the feature flag is disabled."""
        event = create_mock_postback_event()
        event.postback = Mock(data="action=recent_queries")
        event.source = Mock(user_id="test_user_id")
        messenger = InMemoryReplyMessenger()

        with (
            patch("app.line.service.processing_lock_service") as lock_service,
            patch.object(settings, "PROCESSING_LOCK_ENABLED", False),
            patch("app.line.service.dispatch_postback") as dispatch,
        ):
            handle_postback_event(event, messenger)

        lock_service.try_acquire_lock.assert_not_called()
        dispatch.assert_called_once()

    def test_handle_postback_event_skips_lock_for_unlocked_action(
        self, create_mock_postback_event: Callable[..., Mock]
    ) -> None:
        """Never build a lock key for actions that do not touch the database."""
        event = create_mock_postback_event()
        event.postback = Mock(data="action=settings&type=location")
        event.source = Mock(user_id="test_user_id")
        messenger = InMemoryReplyMessenger()

        with (
            patch("app.line.service.processing_lock_service") as lock_service,
            patch.object(settings, "PROCESSING_LOCK_ENABLED", True),
            patch("app.line.service.dispatch_postback") as dispatch,
        ):
            handle_postback_event(event, messenger)

        lock_service.build_lock_key.assert_not_called()
        dispatch.assert_called_once()


class TestProductionCallbacks:
    """Test that SDK-decorated callbacks compose handlers with the production messenger."""

    def test_text_message_callback_uses_production_messenger(
        self, create_mock_message_event: Callable[..., Mock]
    ) -> None:
        """Pass the production messenger to the text message handler."""
        event = create_mock_message_event()

        with patch("app.line.service.handle_message_event") as handler:
            _handle_message_event_callback(event)

        handler.assert_called_once_with(event, production_reply_messenger)

    def test_location_message_callback_uses_production_messenger(
        self, create_mock_location_message_event: Callable[..., Mock]
    ) -> None:
        """Pass the production messenger to the location message handler."""
        event = create_mock_location_message_event()

        with patch("app.line.service.handle_location_message_event") as handler:
            _handle_location_message_event_callback(event)

        handler.assert_called_once_with(event, production_reply_messenger)

    def test_follow_callback_uses_production_messenger(
        self, create_mock_follow_event: Callable[..., Mock]
    ) -> None:
        """Pass the production messenger to the follow handler."""
        event = create_mock_follow_event()

        with patch("app.line.service.handle_follow_event") as handler:
            _handle_follow_event_callback(event)

        handler.assert_called_once_with(event, production_reply_messenger)

    def test_postback_callback_uses_production_messenger(
        self, create_mock_postback_event: Callable[..., Mock]
    ) -> None:
        """Pass the production messenger to the PostBack handler."""
        event = create_mock_postback_event()

        with patch("app.line.service.handle_postback_event") as handler:
            _handle_postback_event_callback(event)

        handler.assert_called_once_with(event, production_reply_messenger)
