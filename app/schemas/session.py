from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import CamelModel, PaginationMeta
from app.schemas.gallery import Category

MessageSender = Literal["user", "assistant"]
MessageType = Literal["message", "parameters", "grid_result", "loading"]


class SessionConfig(CamelModel):
    model: str = "gemini-banana"
    aspect_ratio: str = Field(default="1:1", alias="aspectRatio")
    resolution: str = "2k"
    quantity: int = Field(default=1, ge=1, le=8)
    prompt: str = ""
    uploaded_image_url: str = Field(default="", alias="uploadedImageUrl")


class ChatMessage(CamelModel):
    id: str
    sender: MessageSender
    text: str
    created_at: str = Field(alias="createdAt")
    type: MessageType = "message"
    payload: dict | None = None


class ChatSession(CamelModel):
    id: str
    title: str
    category: Category
    created_at: str = Field(alias="createdAt")
    messages: list[ChatMessage]
    config: SessionConfig


class SessionCreateRequest(BaseModel):
    category: Category = "main"
    title: str | None = None


class SessionRenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class SessionListData(CamelModel):
    sessions: list[ChatSession]
    pagination: PaginationMeta


class MessageListData(CamelModel):
    messages: list[ChatMessage]
