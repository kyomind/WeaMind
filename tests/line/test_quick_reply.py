"""Test Quick Reply functionality for location selection."""

from unittest.mock import Mock, patch

from linebot.v3.webhooks import MessageEvent, TextMessageContent

from app.line.service import handle_message_event
from app.weather.models import Location
from app.weather.service import WeatherQueryResult


class TestQuickReplyFeature:
    """Test Quick Reply functionality for location selection."""

    def test_handle_message_event_with_multiple_locations(self) -> None:
        """Test message handling with multiple location results creates Quick Reply."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_reply_token"
        mock_message = Mock(spec=TextMessageContent)
        mock_message.text = "永和"
        mock_event.message = mock_message

        # Mock locations returned by service
        mock_location1 = Mock(spec=Location)
        mock_location1.full_name = "新北市永和區"
        mock_location2 = Mock(spec=Location)
        mock_location2.full_name = "臺南市永和區"

        with patch("app.line.service.SessionLocal") as mock_session_factory:
            mock_session = Mock()
            mock_session_factory.return_value.__enter__.return_value = mock_session

            with patch(
                "app.line.service.WeatherService.handle_text_weather_query"
            ) as mock_weather_query:
                mock_weather_query.return_value = WeatherQueryResult(
                    response_message="找到多個符合的地點，請選擇：",
                    locations=(mock_location1, mock_location2),
                )

                with patch("app.line.service.MessagingApi") as mock_messaging_api:
                    mock_api_instance = Mock()
                    mock_messaging_api.return_value = mock_api_instance

                    with patch("app.line.service.ApiClient"):
                        handle_message_event(mock_event)

                        # Verify the reply_message was called with Quick Reply
                        mock_api_instance.reply_message.assert_called_once()
                        call_args = mock_api_instance.reply_message.call_args[0]
                        request = call_args[0]  # First positional argument

                        # Check that the message includes Quick Reply
                        message = request.messages[0]
                        assert hasattr(message, "quick_reply")
                        quick_reply = message.quick_reply
                        assert quick_reply is not None

                        assert len(quick_reply.items) == 2

                        # Check Quick Reply items
                        quick_reply_items = quick_reply.items
                        assert quick_reply_items[0].action.text == "新北市永和區"
                        assert quick_reply_items[1].action.text == "臺南市永和區"

    def test_handle_message_event_single_location_no_quick_reply(self) -> None:
        """Test message handling with single location result (no Quick Reply)."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_reply_token"
        mock_message = Mock(spec=TextMessageContent)
        mock_message.text = "臺北市"
        mock_event.message = mock_message

        mock_location = Mock(spec=Location)
        mock_location.full_name = "臺北市中山區"

        with patch("app.line.service.SessionLocal") as mock_session_factory:
            mock_session = Mock()
            mock_session_factory.return_value.__enter__.return_value = mock_session

            with patch(
                "app.line.service.WeatherService.handle_text_weather_query"
            ) as mock_weather_query:
                mock_weather_query.return_value = WeatherQueryResult(
                    response_message="找到了 臺北市中山區，正在查詢天氣...",
                    locations=(mock_location,),
                )

                with patch("app.line.service.MessagingApi") as mock_messaging_api:
                    mock_api_instance = Mock()
                    mock_messaging_api.return_value = mock_api_instance

                    with patch("app.line.service.ApiClient"):
                        handle_message_event(mock_event)

                        # Verify the reply_message was called without Quick Reply
                        mock_api_instance.reply_message.assert_called_once()
                        call_args = mock_api_instance.reply_message.call_args[0]
                        request = call_args[0]  # First positional argument

                        # Check that there's no Quick Reply
                        message = request.messages[0]
                        assert message.quick_reply is None

    def test_handle_message_event_three_locations_quick_reply(self) -> None:
        """Test message handling with three location results creates Quick Reply."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_reply_token"
        mock_message = Mock(spec=TextMessageContent)
        mock_message.text = "中山"
        mock_event.message = mock_message

        # Mock 3 locations returned by service
        mock_location1 = Mock(spec=Location)
        mock_location1.full_name = "台北市中山區"
        mock_location2 = Mock(spec=Location)
        mock_location2.full_name = "高雄市中山區"
        mock_location3 = Mock(spec=Location)
        mock_location3.full_name = "台中市中山路"

        with patch("app.line.service.SessionLocal") as mock_session_factory:
            mock_session = Mock()
            mock_session_factory.return_value.__enter__.return_value = mock_session

            with patch(
                "app.line.service.WeatherService.handle_text_weather_query"
            ) as mock_weather_query:
                mock_weather_query.return_value = WeatherQueryResult(
                    response_message="找到多個符合的地點，請選擇：",
                    locations=(mock_location1, mock_location2, mock_location3),
                )

                with patch("app.line.service.MessagingApi") as mock_messaging_api:
                    mock_api_instance = Mock()
                    mock_messaging_api.return_value = mock_api_instance

                    with patch("app.line.service.ApiClient"):
                        handle_message_event(mock_event)

                        # Verify the reply_message was called with Quick Reply
                        mock_api_instance.reply_message.assert_called_once()
                        call_args = mock_api_instance.reply_message.call_args[0]
                        request = call_args[0]

                        # Check that the message includes Quick Reply with 3 items
                        message = request.messages[0]
                        assert message.quick_reply is not None
                        assert len(message.quick_reply.items) == 3

    def test_handle_message_event_too_many_matches_no_quick_reply(self) -> None:
        """Test message handling with too many matches doesn't create Quick Reply."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_reply_token"
        mock_message = Mock(spec=TextMessageContent)
        mock_message.text = "中正"
        mock_event.message = mock_message

        with patch("app.line.service.SessionLocal") as mock_session_factory:
            mock_session = Mock()
            mock_session_factory.return_value.__enter__.return_value = mock_session

            with patch(
                "app.line.service.WeatherService.handle_text_weather_query"
            ) as mock_weather_query:
                mock_weather_query.return_value = WeatherQueryResult(
                    response_message="找到太多符合的地點，請提供更具體的資訊",
                    locations=(),
                )

                with patch("app.line.service.MessagingApi") as mock_messaging_api:
                    mock_api_instance = Mock()
                    mock_messaging_api.return_value = mock_api_instance

                    with patch("app.line.service.ApiClient"):
                        handle_message_event(mock_event)

                        # Verify no Quick Reply for >3 locations
                        mock_api_instance.reply_message.assert_called_once()
                        call_args = mock_api_instance.reply_message.call_args[0]
                        request = call_args[0]

                        message = request.messages[0]
                        assert message.quick_reply is None

    def test_handle_message_event_zero_locations_no_quick_reply(self) -> None:
        """Test message handling with zero locations doesn't create Quick Reply."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_reply_token"
        mock_message = Mock(spec=TextMessageContent)
        mock_message.text = "不存在的地點"
        mock_event.message = mock_message

        with patch("app.line.service.SessionLocal") as mock_session_factory:
            mock_session = Mock()
            mock_session_factory.return_value.__enter__.return_value = mock_session

            with patch(
                "app.line.service.WeatherService.handle_text_weather_query"
            ) as mock_weather_query:
                mock_weather_query.return_value = WeatherQueryResult(
                    response_message="找不到符合的地點",
                    locations=(),
                )

                with patch("app.line.service.MessagingApi") as mock_messaging_api:
                    mock_api_instance = Mock()
                    mock_messaging_api.return_value = mock_api_instance

                    with patch("app.line.service.ApiClient"):
                        handle_message_event(mock_event)

                        # Verify no Quick Reply for 0 locations
                        mock_api_instance.reply_message.assert_called_once()
                        call_args = mock_api_instance.reply_message.call_args[0]
                        request = call_args[0]

                        message = request.messages[0]
                        assert message.quick_reply is None
