"""Utilities for building and sending LINE Bot responses."""

from __future__ import annotations

import logging

from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    QuickReply,
    QuickReplyItem,
    ReplyMessageRequest,
    TextMessage,
    URIAction,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

# Shared LINE SDK configuration for all messaging helpers
configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)


def send_text_response(reply_token: str | None, text: str) -> None:
    """Send a simple text response to the user."""
    if not reply_token:
        logger.warning("Cannot send text response: reply_token is None")
        return

    with ApiClient(configuration) as api_client:
        messaging_api_client = MessagingApi(api_client)
        try:
            messaging_api_client.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,  # type: ignore[call-arg]
                    messages=[
                        TextMessage(
                            text=text,
                            quoteToken=None,  # type: ignore[call-arg]
                            quickReply=None,  # type: ignore[call-arg]
                        )
                    ],  # type: ignore
                    notificationDisabled=False,  # type: ignore[call-arg]
                )
            )
        except Exception:
            logger.exception("Error sending text response")


def send_error_response(reply_token: str | None, message: str) -> None:
    """Send a standardized error response."""
    send_text_response(reply_token, message)


def send_location_not_set_response(reply_token: str | None, location_name: str) -> None:
    """Notify the user that a preset location (home/office) is missing."""
    message = f"請先設定{location_name}地址，點擊下方「設定地點」按鈕即可設定。"
    send_text_response(reply_token, message)


def send_liff_location_setting_response(reply_token: str | None) -> None:
    """Send LIFF location setting instructions to the user."""
    if not reply_token:
        logger.warning("Cannot send LIFF response: reply_token is None")
        return

    liff_url = f"{settings.BASE_URL}/static/liff/location/index.html"
    response_message = (
        "地點設定\n\n"
        "請點擊下方連結設定您的常用地點：\n"
        f"{liff_url}\n\n"
        "設定完成後，您就可以透過快捷功能查詢住家或公司的天氣了！"
    )

    with ApiClient(configuration) as api_client:
        messaging_api_client = MessagingApi(api_client)
        try:
            messaging_api_client.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,  # type: ignore[call-arg]
                    messages=[
                        TextMessage(
                            text=response_message,
                            quoteToken=None,  # type: ignore[call-arg]
                            quickReply=None,  # type: ignore[call-arg]
                        )
                    ],  # type: ignore
                    notificationDisabled=False,  # type: ignore[call-arg]
                )
            )
            logger.info("LIFF location setting response sent", extra={"liff_url": liff_url})
        except Exception:
            logger.exception("Failed to send LIFF location setting response")


def send_other_menu_quick_reply(reply_token: str | None) -> None:
    """Send the quick reply menu for the "其它" Rich Menu entry."""
    if not reply_token:
        logger.warning("Cannot send other menu: reply_token is None")
        return

    quick_reply_items = [
        QuickReplyItem(
            type="action",
            imageUrl=None,
            action=URIAction(
                type="uri",
                label="🔄 更新",
                uri="https://github.com/kyomind/WeaMind/blob/main/CHANGELOG.md",
                altUri=None,
            ),
        ),
        QuickReplyItem(
            type="action",
            imageUrl=None,
            action=URIAction(
                type="uri",
                label="📖 使用說明",
                uri="https://github.com/kyomind/WeaMind/blob/main/README.md",
                altUri=None,
            ),
        ),
        QuickReplyItem(
            type="action",
            imageUrl=None,
            action=URIAction(
                type="uri",
                label="ℹ️ 專案介紹",
                uri="https://api.kyomind.tw/static/about/index.html",
                altUri=None,
            ),
        ),
    ]

    quick_reply = QuickReply(items=quick_reply_items)

    with ApiClient(configuration) as api_client:
        messaging_api_client = MessagingApi(api_client)
        try:
            messaging_api_client.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[
                        TextMessage(
                            text="請選擇想了解的資訊：",
                            quoteToken=None,
                            quickReply=quick_reply,
                        )
                    ],
                    notificationDisabled=False,
                )
            )
            logger.info("Other menu Quick Reply sent successfully")
        except Exception:
            logger.exception("Error sending other menu Quick Reply")
