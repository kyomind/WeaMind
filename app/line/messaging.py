"""Utilities for building and sending LINE Bot responses."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    FlexContainer,
    FlexMessage,
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
                uri="https://api.kyomind.tw/static/help/index.html",
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


def handle_announcements(reply_token: str | None) -> None:
    """Send the latest announcement as a Flex Message carousel."""
    if not reply_token:
        logger.warning("Cannot send announcements: reply_token is None")
        return

    try:
        announcements_path = Path("static/announcements.json")
        if not announcements_path.exists():
            logger.warning("Announcements file not found")
            send_error_response(reply_token, "公告資料載入失敗")
            return

        with announcements_path.open(encoding="utf-8") as file:
            announcements_data = json.load(file)

        visible_announcements = [
            item for item in announcements_data.get("items", []) if item.get("visible", False)
        ]
        visible_announcements.sort(key=lambda x: x.get("start_at", ""), reverse=True)

        latest_announcements = visible_announcements[:1]
        if not latest_announcements:
            send_text_response(reply_token, "目前沒有新公告")
            return

        flex_message = create_announcements_flex_message(latest_announcements)

        with ApiClient(configuration) as api_client:
            messaging_api_client = MessagingApi(api_client)
            messaging_api_client.reply_message(
                ReplyMessageRequest(
                    replyToken=reply_token,
                    messages=[flex_message],
                    notificationDisabled=False,
                )
            )
            logger.info("Announcements Flex Message sent successfully")

    except Exception:
        logger.exception("Error handling announcements")
        send_error_response(reply_token, "載入公告時發生錯誤")


def create_announcements_flex_message(announcements: list[dict[str, Any]]) -> FlexMessage:
    """Construct a Flex Message carousel for announcement items."""
    bubbles: list[dict[str, Any]] = []

    for announcement in announcements:
        title = announcement.get("title", "")
        body = smart_truncate_body(announcement.get("body", ""))
        level = announcement.get("level", "info")
        start_at = announcement.get("start_at", "")

        formatted_date = format_announcement_date(start_at)

        level_colors = {"info": "#2196F3", "warning": "#FF9800", "maintenance": "#F44336"}
        level_color = level_colors.get(level, "#2196F3")

        level_texts = {"info": "一般資訊", "warning": "重要提醒", "maintenance": "維護公告"}
        level_text = level_texts.get(level, "資訊")

        bubble: dict[str, Any] = {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": title,
                        "weight": "bold",
                        "size": "xl",
                        "wrap": True,
                        "color": "#333333",
                    },
                    {
                        "type": "text",
                        "text": level_text,
                        "size": "lg",
                        "color": level_color,
                        "margin": "sm",
                    },
                    {
                        "type": "text",
                        "text": formatted_date,
                        "size": "lg",
                        "color": "#888888",
                        "margin": "xs",
                    },
                ],
                "backgroundColor": "#F8F9FA",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": body, "wrap": True, "size": "lg", "color": "#666666"}
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "前往公告頁面",
                            "uri": "https://api.kyomind.tw/static/announcements/index.html",
                        },
                        "style": "primary",
                        "color": level_color,
                    }
                ],
            },
        }
        bubbles.append(bubble)

    carousel_container: dict[str, Any] = {"type": "carousel", "contents": bubbles}

    return FlexMessage(
        altText="系統公告",
        contents=FlexContainer.from_dict(carousel_container),  # type: ignore[arg-type]
    )


def format_announcement_date(date_string: str) -> str:
    """Format ISO timestamp strings for announcement display."""
    try:
        dt = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        return dt.strftime("%Y/%m/%d %H:%M")
    except (ValueError, TypeError):
        return "日期未知"


def smart_truncate_body(text: str) -> str:
    """Truncate announcement body text with ellipsis handling."""
    if len(text) <= 50:
        return text

    truncated = text[:50]
    if truncated[-1] in ["，", "、", "：", "；", "。", "！", "？", "（", "）", "(", ")"]:
        return truncated[:-1] + "..."
    return truncated + "..."
