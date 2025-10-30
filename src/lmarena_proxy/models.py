"""Pydantic models for OpenAI compatible payloads."""
from __future__ import annotations

from typing import List, Optional, Union
from pydantic import BaseModel, Field


class ChatMessageContentPart(BaseModel):
    type: str
    text: Optional[str] = None


ChatMessageContent = Union[str, List[ChatMessageContentPart]]


class ChatMessage(BaseModel):
    role: str
    content: ChatMessageContent


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: bool = False
    max_tokens: Optional[int] = Field(default=None, alias="max_tokens")
    temperature: Optional[float] = None

    class Config:
        populate_by_name = True


class DeltaMessage(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class Choice(BaseModel):
    index: int = 0
    message: Optional[ChatMessage] = None
    delta: Optional[DeltaMessage] = None
    finish_reason: Optional[str] = Field(default=None, alias="finish_reason")

    class Config:
        populate_by_name = True


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = None


class ModelItem(BaseModel):
    id: str
    object: str = "model"
    owned_by: str = "lmarena.ai"


class ModelListResponse(BaseModel):
    object: str = "list"
    data: List[ModelItem]
