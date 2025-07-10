"""Pydantic schemas for LINE webhook events."""

from pydantic import BaseModel


class LineMessage(BaseModel):
    """LINE message model."""

    type: str
    text: str | None = None


class LineEvent(BaseModel):
    """LINE webhook event model."""

    type: str
    replyToken: str | None = None
    message: LineMessage | None = None


class LineWebhook(BaseModel):
    """LINE webhook request model."""

    events: list[LineEvent]
